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
from data.insert_data import (
    insert_performance_review_data,
    insert_performance_review,
    resolve_employee_identifier,
    insert_employee,
)
from data.update_data import update_employee_by_id
from data.delete_data import delete_employee_by_id
from rag_tool import search_company_policies

from dotenv import load_dotenv, dotenv_values
# Load environment variables from .env file
load_dotenv()

def _format_employee_row(row: Dict) -> str:
    """Return a compact single-line representation for one employee row."""
    name = f"{row.get('first_name','')} {row.get('last_name','')}".strip()
    pos = row.get('position') or ''
    dept = row.get('department') or ''
    email = row.get('email') or ''
    return f"{name} — {pos} ({dept}) <{email}>"


def create_employee(first_name: str, last_name: str, email: str, department: Optional[str] = None, position: Optional[str] = None, salary: Optional[float] = None, hire_date: Optional[str] = None) -> Dict:
    """Tool: create a single employee row.

    Returns a dict with status and message (and `id` when successful).
    """
    if not first_name or not last_name or not email:
        return {"status": "error", "text": "請提供 `first_name`, `last_name` 與 `email`。"}
    try:
        eid = insert_employee(
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department or "",
            position=position or "",
            salary=salary,
            hire_date=hire_date,
        )
        return {"status": "success", "text": f"員工已建立 (id={eid})。", "id": eid}
    except Exception as e:
        return {"status": "error", "text": "建立員工時發生錯誤。", "detail": str(e)}


def get_employee(identifier: str) -> Dict:
    """Tool: retrieve employee(s) by id/email/name-like identifier."""
    candidates = resolve_employee_identifier(identifier)
    if not candidates:
        return {"status": "error", "text": f"找不到符合 '{identifier}' 的員工。"}
    if len(candidates) > 1:
        lines = [f"找到多位符合 '{identifier}' 的員工，請提供更精確的名稱或 ID："]
        for c in candidates:
            lines.append(_format_employee_row(c))
        return {"status": "ambiguous", "text": "\n".join(lines), "candidates": candidates}
    emp = candidates[0]
    text = _format_employee_row(emp)
    return {"status": "success", "text": text, "employee": emp}


def update_employee(
    identifier: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    department: Optional[str] = None,
    position: Optional[str] = None,
    salary: Optional[float] = None,
    hire_date: Optional[str] = None,
):
    """Tool: update an employee identified by id/email/name-like.

    Provide one or more optional fields (first_name, last_name, email,
    department, position, salary, hire_date). This simpler signature is
    easier for automatic function-calling schemas to parse.
    """
    candidates = resolve_employee_identifier(identifier)
    if not candidates:
        return {"status": "error", "text": f"找不到符合 '{identifier}' 的員工。"}
    if len(candidates) > 1:
        lines = [f"找到多位符合 '{identifier}' 的員工，請提供更精確的名稱或 ID："]
        for c in candidates:
            lines.append(_format_employee_row(c))
        return {"status": "ambiguous", "text": "\n".join(lines), "candidates": candidates}
    emp = candidates[0]

    updates = {}
    if first_name is not None:
        updates['first_name'] = first_name
    if last_name is not None:
        updates['last_name'] = last_name
    if email is not None:
        updates['email'] = email
    if department is not None:
        updates['department'] = department
    if position is not None:
        updates['position'] = position
    if salary is not None:
        updates['salary'] = salary
    if hire_date is not None:
        updates['hire_date'] = hire_date

    if not updates:
        return {"status": "error", "text": "請提供至少一個要更新的欄位（例如 position 或 salary）。"}

    try:
        updated = update_employee_by_id(emp_id=int(emp["id"]), updates=updates)
        if updated:
            return {"status": "success", "text": f"已更新員工 (id={emp['id']})。", "rows_updated": updated}
        return {"status": "success", "text": "沒有可更新的欄位或資料未變更。", "rows_updated": 0}
    except Exception as e:
        return {"status": "error", "text": "更新員工時發生錯誤。", "detail": str(e)}


def delete_employee(identifier: str) -> Dict:
    """Tool: delete an employee identified by id/email/name-like. Returns deletion count."""
    candidates = resolve_employee_identifier(identifier)
    if not candidates:
        return {"status": "error", "text": f"找不到符合 '{identifier}' 的員工。"}
    if len(candidates) > 1:
        lines = [f"找到多位符合 '{identifier}' 的員工，請提供更精確的名稱或 ID："]
        for c in candidates:
            lines.append(_format_employee_row(c))
        return {"status": "ambiguous", "text": "\n".join(lines), "candidates": candidates}
    emp = candidates[0]
    try:
        deleted = delete_employee_by_id(int(emp["id"]))
        if deleted:
            return {"status": "success", "text": f"已刪除員工 (id={emp['id']})。", "rows_deleted": deleted}
        return {"status": "error", "text": "刪除失敗（找不到資料或已被移除）。", "rows_deleted": 0}
    except Exception as e:
        return {"status": "error", "text": "刪除員工時發生錯誤。", "detail": str(e)}


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


# Register tools with LlmAgent if available
root_agent = LlmAgent(
name="ai_administrative",
model=os.getenv("MODEL_USE"),
description=("Agent to help with administrative tasks such as managing employee data"),
instruction=("You are an AI administrative assistant. Use the provided tools to answer user queries about employees."),
tools=[
    list_all_employees,
    find_employees_by_role,
    create_employee,
    get_employee,
    update_employee,
    delete_employee,
    add_performance_review,
    get_employee_performance_reviews,
    search_company_policies,
],
)
