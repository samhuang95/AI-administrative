from google.adk.agents import LlmAgent

from typing import List, Dict, Optional
import datetime
import sys
import os

# Add current directory to sys.path to ensure local modules like rag_tool can be imported
# This is necessary because the folder name 'ai-agent' contains a hyphen and cannot be imported as a package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import database query helper
from data.query_data import query_employees, query_performance_reviews
from data.insert_data import insert_performance_review_data, insert_performance_review, resolve_employee_identifier, insert_employee_data, insert_employee
from rag_tool import search_company_policies, GoogleGenAIEmbeddingFunction

from dotenv import load_dotenv, dotenv_values
# Load environment variables from .env file
load_dotenv()

# Rules / triggers to detect culture-related issues in free-text comments.
CULTURE_MISMATCH_RULES = [
    {
        "dimension": "誠信正直",
        "description": "保持誠實、透明並遵守流程。",
        "triggers": [
            "誠信不足",
            "缺乏誠信",
            "資訊不透明",
            "不誠實",
            "違反流程",
            "隱瞞",
            "造假",
            "舞弊",
            "integrity issue",
            "lack of transparency",
        ],
    },
    {
        "dimension": "創新求變",
        "description": "勇於嘗試、擁抱改變並提出新解法。",
        "triggers": [
            "缺乏創新",
            "抗拒改變",
            "不願嘗試",
            "保守",
            "沒有新點子",
            "不擅長創新",
            "innovation issue",
            "resistant to change",
        ],
    },
    {
        "dimension": "團隊合作",
        "description": "主動協作、分享資訊並支持團隊。",
        "triggers": [
            "缺乏團隊",
            "合作不足",
            "不配合",
            "溝通不足",
            "孤立作業",
            "不分享資訊",
            "teamwork issue",
            "poor collaboration",
        ],
    },
    {
        "dimension": "文化契合度",
        "description": "整體未展現公司核心價值。",
        "triggers": [
            "文化不符",
            "文化契合度低",
            "不符合文化",
            "未展現核心價值",
            "culture mismatch",
        ],
    },
]


def _detect_culture_flags_from_comment(comment: Optional[str], extra_rules: Optional[List[Dict]] = None) -> List[Dict]:
    """Return list of matched culture dimensions found in a free-text comment.

    Args:
        comment: review comment text
        extra_rules: optional list of rule dicts to augment `CULTURE_MISMATCH_RULES`
    """
    if not comment:
        return []
    lowered = comment.lower()
    matches: List[Dict] = []
    # Combine built-in rules with any extra rules (dynamic from policy)
    all_rules = list(CULTURE_MISMATCH_RULES)
    if extra_rules:
        # ensure we don't mutate the originals
        for r in extra_rules:
            # normalize to expected keys
            dr = {
                "dimension": r.get("dimension", "policy"),
                "description": r.get("description", ""),
                "triggers": r.get("triggers", []),
            }
            all_rules.append(dr)

    for rule in all_rules:
        for phrase in rule["triggers"]:
            try:
                if phrase.lower() in lowered:
                    matches.append({
                        "dimension": rule["dimension"],
                        "phrase": phrase,
                        "description": rule["description"],
                        "comment": comment,
                    })
                    break
            except Exception:
                # ignore any bad trigger values
                continue
    return matches


def _extract_rules_from_policy(policy_text: Optional[str]) -> List[Dict]:
    """Attempt to extract culture rule dimensions and simple triggers from policy text.

    This is a heuristic parser that looks for headings (lines starting with '##')
    and uses the heading as a dimension name and the following paragraph as description
    and triggers. It returns a list of rule-like dicts compatible with
    `CULTURE_MISMATCH_RULES` format.
    """
    if not policy_text:
        return []
    rules: List[Dict] = []
    lines = [l.rstrip() for l in str(policy_text).splitlines()]
    cur_heading = None
    cur_paragraph = []

    def flush_heading(h, para_lines):
        if not h:
            return
        desc = "\n".join([p for p in para_lines if p.strip()])
        # create simple triggers: the heading text and split sentences from description
        triggers = []
        heading_text = h.strip().lstrip('#').strip()
        if heading_text:
            triggers.append(heading_text)
            # also add short tokens from heading
            for tok in heading_text.replace('(', ' ').replace(')', ' ').replace('/', ' ').split():
                if tok:
                    triggers.append(tok)
        # sentences
        for p in desc.split('。'):
            s = p.strip()
            if s:
                # add the full sentence as a trigger and also comma-separated chunks
                triggers.append(s)
                for sub in s.split('，'):
                    if sub.strip():
                        triggers.append(sub.strip())

        # dedupe and limit trigger length
        clean_triggers = []
        seen = set()
        for t in triggers:
            tt = t.lower()
            if tt in seen:
                continue
            seen.add(tt)
            if len(tt) > 1:
                clean_triggers.append(t)

        rules.append({
            "dimension": heading_text or "policy",
            "description": desc or heading_text,
            "triggers": clean_triggers,
        })

    for line in lines:
        if line.strip().startswith('##'):
            # flush previous
            flush_heading(cur_heading, cur_paragraph)
            cur_heading = line.strip()
            cur_paragraph = []
        else:
            cur_paragraph.append(line)

    # final flush
    flush_heading(cur_heading, cur_paragraph)
    return rules


def _summarize_policy_text(policy_text: Optional[str], max_chars: int = 800) -> str:
    if not policy_text:
        return ""
    s = str(policy_text).strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3].rstrip() + "..."


def _cosine_sim(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    try:
        import math

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    except Exception:
        return 0.0


def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts using the project's GenAI embedding function.

    This reuses the `GoogleGenAIEmbeddingFunction` defined in `rag_tool.py`.
    """
    try:
        ef = GoogleGenAIEmbeddingFunction()
        return ef(texts)
    except Exception as e:
        # Fallback: return zero vectors of length 1 to avoid crashes
        print(f"Embedding error: {e}")
        return [[0.0] for _ in texts]


def find_culture_misaligned_employees() -> Dict:
    """Tool: search company policy (RAG) and performance reviews, then report employees with evidence of culture mismatch.

    Returns a dict with textual summary and structured list of flagged employees.
    """
    # 1) Get policy/context from RAG
    try:
        policy_res = search_company_policies("公司文化 考核 標準 文化契合")
    except Exception:
        policy_res = None

    policy_text = ""
    if isinstance(policy_res, dict):
        policy_text = policy_res.get("text", "")
    policy_summary = _summarize_policy_text(policy_text)
    # extract simple rules from the policy text to improve detection recall
    dynamic_rules = _extract_rules_from_policy(policy_text)

    # 2) Walk employees and their reviews
    rows = query_employees()
    flagged: List[Dict] = []

    # Prepare policy chunks and embeddings for semantic matching
    policy_chunks: List[str] = []
    policy_embeddings: List[List[float]] = []
    if policy_text:
        # Split into chunks similar to rag_tool: by double newline
        policy_chunks = [c.strip() for c in str(policy_text).split("\n\n") if c.strip()]
        if policy_chunks:
            policy_embeddings = _embed_texts(policy_chunks)

    # similarity threshold (tunable)
    SEMANTIC_THRESHOLD = 0.72

    for emp in rows:
        emp_reviews = query_performance_reviews(emp["id"]) or []
        reasons: List[Dict] = []
        for rev in emp_reviews:
            comments = rev.get("comments") or ""
            # run detection with both built-in and dynamic rules
            matches = _detect_culture_flags_from_comment(comments, extra_rules=dynamic_rules)
            for m in matches:
                reasons.append({
                    "dimension": m["dimension"],
                    "description": m["description"],
                    "evidence": comments,
                    "highlight": m["phrase"],
                    "score": rev.get("score"),
                    "date": rev.get("created_at"),
                    "review_id": rev.get("id"),
                })

            # Semantic matching: embed the comment and compare to policy chunks
            if policy_embeddings and comments.strip():
                try:
                    comment_emb = _embed_texts([comments.strip()])[0]
                    # compute max similarity
                    best_score = 0.0
                    best_idx = -1
                    for i, pe in enumerate(policy_embeddings):
                        sim = _cosine_sim(comment_emb, pe)
                        if sim > best_score:
                            best_score = sim
                            best_idx = i
                    if best_score >= SEMANTIC_THRESHOLD and best_idx >= 0:
                        snippet = policy_chunks[best_idx]
                        reasons.append({
                            "dimension": "文化相關(語意匹配)",
                            "description": f"與政策片段語意相似 (score={best_score:.2f})",
                            "evidence": comments,
                            "highlight": snippet,
                            "similarity": float(best_score),
                            "score": rev.get("score"),
                            "date": rev.get("created_at"),
                            "review_id": rev.get("id"),
                        })
                except Exception as e:
                    # don't crash on embedding errors
                    print(f"Semantic matching error: {e}")

        if reasons:
            flagged.append({"employee": emp, "reasons": reasons})

    # 3) Format text response
    if not flagged:
        text = "目前沒有發現明確提到文化不符的考核評論。"
        if policy_summary:
            text += "\n\n公司文化摘要：\n" + policy_summary
        return {"status": "success", "text": text, "policy_context": policy_summary, "employees": []}

    lines = []
    if policy_summary:
        lines.append("公司文化摘要：")
        lines.append(policy_summary)
        lines.append("")
    lines.append("以下員工在考核評論中出現可能與公司文化不符的描述：")
    for item in flagged:
        emp = item["employee"]
        name = f"{emp.get('first_name','')} {emp.get('last_name','')}".strip()
        lines.append(f"- {name} (ID: {emp.get('id')})")
        for i, r in enumerate(item["reasons"], start=1):
            lines.append(f"  {i}. {r['dimension']} — {r['description']}")
            lines.append(f"     評語摘錄: {r['evidence']}")
            lines.append(f"     關鍵字: {r['highlight']} | 分數: {r.get('score')} | 日期: {r.get('date')}")
    return {"status": "success", "text": "\n".join(lines), "policy_context": policy_summary, "employees": flagged}

def _format_employee_row(row: Dict) -> str:
    """Return a compact single-line representation for one employee row."""
    name = f"{row.get('first_name','')} {row.get('last_name','')}".strip()
    pos = row.get('position') or ''
    dept = row.get('department') or ''
    email = row.get('email') or ''
    return f"{name} — {pos} ({dept}) <{email}>"


def list_all_employees() -> Dict:
    """Tool: return all employees as text.

    Returns a dict so the ADK tool runner can serialize the result. The
    'text' key contains a human-readable string for direct display in chat.
    """
    rows = query_employees()
    if not rows:
        return {"status": "success", "text": "沒有找到任何員工資料。"}
    lines = ["所有員工："]
    for r in rows:
        lines.append(_format_employee_row(r))
    return {"status": "success", "text": "\n".join(lines), "employees": rows}


def find_employees_by_role(query: str) -> Dict:
    """Tool: find employees whose department/position/name match the query.

    The function is intentionally tolerant: it accepts Chinese and English
    role words (e.g. '工程師', '軟體', 'developer', 'engineer'). It returns a
    readable `text` plus the raw `employees` list.
    """
    if not query:
        return {"status": "error", "text": "請提供要查詢的職稱或關鍵字。"}

    q = query.lower()
    # map some Chinese keywords to English equivalents for more matches
    syns = []
    if any(k in q for k in ["工程", "工程師", "軟體", "軟體開發", "軟體工程", "開發"]):
        syns.extend(["engineer", "software", "developer", "technical"])
    if any(k in q for k in ["技術", "技術人員"]):
        syns.append("technical")
    # also include the original words
    syns.append(q)

    rows = query_employees()
    matches: List[Dict] = []
    for r in rows:
        combined = " ".join([str(r.get('first_name','')), str(r.get('last_name','')), str(r.get('department','')), str(r.get('position','')), str(r.get('email',''))]).lower()
        if any(s.lower() in combined for s in syns):
            matches.append(r)

    if not matches:
        return {"status": "success", "text": f"沒有找到與 '{query}' 相關的員工。", "employees": []}

    lines = [f"找到 {len(matches)} 位與 '{query}' 相關的員工："]
    for m in matches:
        lines.append(_format_employee_row(m))
    return {"status": "success", "text": "\n".join(lines), "employees": matches}


def add_performance_review(employee_id: int, reviewer_employee_id: int, score: float, comments: str) -> Dict:
    """Tool: Add a performance review for an employee.

    Args:
        employee_id: ID of the employee being reviewed.
        reviewer_employee_id: ID of the employee who is the reviewer.
        score: Performance score (e.g., 0 to 100).
        comments: Review comments.
    """
    # Validate and coerce score to integer 0-100
    try:
        score_int = int(float(score))
    except Exception:
        return {"status": "error", "text": "分數格式錯誤，請提供 0 到 100 的整數。"}
    if score_int < 0 or score_int > 100:
        return {"status": "error", "text": "分數需在 0 到 100 的範圍內。"}

    # Insert single review using insert_performance_review (works regardless of table non-empty)
    try:
        rid = insert_performance_review(employee_id=employee_id, reviewer_employee_id=reviewer_employee_id, score=score_int, comments=comments)
        return {"status": "success", "text": f"Performance review added successfully (id={rid})."}
    except Exception as e:
        return {"status": "error", "text": "Failed to add performance review.", "detail": str(e)}


def get_employee_performance_reviews(employee_name: str) -> Dict:
    """Tool: Get performance reviews for a specific employee by name or ID.

    Args:
        employee_name: The name or ID of the employee to query.
    """
    candidates = resolve_employee_identifier(employee_name)

    if not candidates:
        return {"status": "error", "text": f"找不到名為 '{employee_name}' 的員工。"}

    if len(candidates) > 1:
        lines = [f"找到多位符合 '{employee_name}' 的員工，請提供更精確的名稱或 ID："]
        for c in candidates:
            lines.append(_format_employee_row(c))
        return {"status": "ambiguous", "text": "\n".join(lines), "candidates": candidates}

    target = candidates[0]
    reviews = query_performance_reviews(target['id'])

    if not reviews:
        return {"status": "success", "text": f"{target['first_name']} {target['last_name']} 目前沒有任何考核紀錄。"}

    lines = [f"{target['first_name']} {target['last_name']} 的考核紀錄："]
    for r in reviews:
        lines.append(f"- 日期: {r['created_at']}")
        lines.append(f"  評分: {r['score']}")
        lines.append(f"  評語: {r['comments']}")
        lines.append(f"  評核主管: {r['reviewer_name']}")
        lines.append("")

    return {"status": "success", "text": "\n".join(lines), "reviews": reviews}


def seed_employee_data() -> Dict:
    """Tool: seed `employee` table using `insert_employee_data` helper.

    Returns a dict with status and number of rows inserted.
    """
    try:
        inserted = insert_employee_data()
        return {"status": "success", "text": f"Inserted {int(inserted)} employee rows.", "inserted": int(inserted)}
    except Exception as e:
        return {"status": "error", "text": "Failed to insert employee data.", "detail": str(e)}


def create_employee(
    first_name: str,
    last_name: str,
    email: str,
    department: str = "",
    position: str = "",
    salary: Optional[float] = None,
    hire_date: Optional[str] = None,
    supervisor_id: Optional[int] = None,
) -> Dict:
    """Tool: create a single employee row via `insert_employee` helper.

    Returns a dict with status and the new employee id on success.
    """
    try:
        new_id = insert_employee(
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department,
            position=position,
            salary=salary,
            hire_date=hire_date,
            supervisor_id=supervisor_id,
        )
        return {"status": "success", "text": f"Created employee id={new_id}", "id": int(new_id)}
    except Exception as e:
        return {"status": "error", "text": "Failed to create employee.", "detail": str(e)}


# Register tools with LlmAgent if available
root_agent = LlmAgent(
    name="ai_administrative",
    model=os.getenv("MODEL_USE"),
    description=("Agent to help with administrative tasks such as managing employee data"),
    instruction=("You are an AI administrative assistant. Use the provided tools to answer user queries about employees."),
    tools=[
        list_all_employees,
        find_employees_by_role,
        add_performance_review,
        get_employee_performance_reviews,
        search_company_policies,
        find_culture_misaligned_employees,
        seed_employee_data,
        create_employee,
    ],
)
