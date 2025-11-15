from google.adk.agents import LlmAgent

from typing import List, Dict, Optional
import datetime

# Import database query helper
from data.query_data import query_employees

import os
from dotenv import load_dotenv, dotenv_values
# Load environment variables from .env file
load_dotenv()

def _format_employee_row(row: Dict) -> str:
    """Return a compact single-line representation for one employee row."""
    print("row::::",row)
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
    print("list_all_employees::::")
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


# Register tools with LlmAgent if available
root_agent = LlmAgent(
name="ai_administrative",
model=os.getenv("MODEL_USE"),
description=("Agent to help with administrative tasks such as managing employee data"),
instruction=("You are an AI administrative assistant. Use the provided tools to answer user queries about employees."),
tools=[list_all_employees, find_employees_by_role],
)
