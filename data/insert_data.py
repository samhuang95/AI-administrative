"""Data seeding utilities.

This module provides `insert_employee_data(db_path)` which inserts sample rows
into an existing `employee` table. It does not create the DB or table; that is
handled by `create_database.create_database`.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Sequence, Tuple
import random
from datetime import datetime, timedelta
import sys


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "employee.db"

employee_data: Sequence[Tuple] = [
    ("Alice", "Wang", "alice.wang@example.com", "Engineering", "Software Engineer", 85000, "2022-03-15"),
    ("Bob", "Chen", "bob.chen@example.com", "Sales", "Account Manager", 65000, "2021-07-01"),
    ("Carol", "Lin", "carol.lin@example.com", "HR", "HR Manager", 72000, "2020-11-20"),
]


def insert_employee_data(db_path: Optional[Path | str] = None, data: Optional[Sequence[Tuple]] = None) -> int:
    """Insert sample rows into the `employee` table if it's empty.

    Args:
        db_path: Optional database path. Uses default if omitted.
        data: Optional sequence of rows to insert. If omitted, uses employee_data.

    Returns:
        Number of rows inserted.
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    data = data if data is not None else employee_data

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM employee")
        row = cur.fetchone()
        count = int(row[0]) if row is not None else 0
        if count == 0:
            cur.executemany(
                "INSERT INTO employee (first_name,last_name,email,department,position,salary,hire_date) VALUES (?,?,?,?,?,?,?)",
                data,
            )
            conn.commit()
            return len(data)
        return 0
    finally:
        conn.close()

def insert_performance_review_data(db_path: Optional[Path | str] = None, data: Optional[Sequence[Tuple]] = None, force: bool = False) -> int:
    """Insert sample rows into the `employee` table if it's empty.

    Args:
        db_path: Optional database path. Uses default if omitted.
        data: Optional sequence of rows to insert. If omitted, uses performance_review_data.

    Returns:
        Number of rows inserted.
    """
    # If data is None there's nothing to insert
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    print("data::::",data)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM performance_review")
        row = cur.fetchone()
        count = int(row[0]) if row is not None else 0
        # By default this helper will only insert when the table is empty to avoid accidental duplicates.
        # Pass `force=True` to append regardless of existing rows.
        if count == 0 or force:
            cur.executemany(
                "INSERT INTO performance_review (employee_id, reviewer_employee_id, score, comments, created_at) VALUES (?,?,?,?,?)",
                data,
            )
            conn.commit()
            return len(data)
        return 0
    finally:
        conn.close()


def find_employees(query: str, db_path: Optional[Path | str] = None, limit: int = 10):
    """Search employees by name / position / department using LIKE (case-insensitive).

    Returns list of dict rows.
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    q = f"%{query.strip()}%"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM employee
            WHERE (first_name || ' ' || last_name) LIKE ?
               OR first_name LIKE ?
               OR last_name LIKE ?
               OR position LIKE ?
               OR department LIKE ?
            ORDER BY id
            LIMIT ?
            """,
            (q, q, q, q, q, limit),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def resolve_employee_identifier(identifier, db_path: Optional[Path | str] = None):
    """Resolve an identifier (id, email, or fuzzy name/role) to matching employee rows.

    Returns a list (may be empty or contain multiple candidates).
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        # numeric id
        if isinstance(identifier, int) or (isinstance(identifier, str) and str(identifier).isdigit()):
            eid = int(identifier)
            cur.execute("SELECT * FROM employee WHERE id = ?", (eid,))
            row = cur.fetchone()
            return [dict(row)] if row else []
        # email
        if isinstance(identifier, str) and "@" in identifier:
            cur.execute("SELECT * FROM employee WHERE email = ?", (identifier.strip(),))
            row = cur.fetchone()
            return [dict(row)] if row else []
        # fallback fuzzy search
        return find_employees(str(identifier), db_path=db_path, limit=20)
    finally:
        conn.close()


def is_manager_of(reviewer_id: int, target_id: int, db_path: Optional[Path | str] = None) -> bool:
    """Return True if reviewer_id is an ancestor (manager) of target_id via supervisor_id chain."""
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        current = int(target_id)
        while True:
            cur.execute("SELECT supervisor_id FROM employee WHERE id = ?", (current,))
            row = cur.fetchone()
            if not row:
                return False
            supervisor_id = row[0]
            if supervisor_id is None:
                return False
            if int(supervisor_id) == int(reviewer_id):
                return True
            current = int(supervisor_id)
    finally:
        conn.close()


def insert_performance_review(
    employee_id: int,
    reviewer_employee_id: int,
    score: int,
    comments: str,
    db_path: Optional[Path | str] = None,
    created_at: Optional[str] = None,
) -> int:
    """Insert a single performance review and return the new review id."""
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO performance_review (employee_id, reviewer_employee_id, score, comments, created_at) VALUES (?,?,?,?,?)",
            (int(employee_id), int(reviewer_employee_id), int(score), str(comments), created_at),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def insert_employee(
    first_name: str,
    last_name: str,
    email: str,
    department: str = "",
    position: str = "",
    salary: int | float | None = None,
    hire_date: str | None = None,
    supervisor_id: int | None = None,
    db_path: Optional[Path | str] = None,
) -> int:
    """Insert a single employee and return the new employee id.

    This is a small helper used by higher-level code (e.g. the agent) to
    create a single employee row without touching the seeding helpers.
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO employee (first_name, last_name, email, department, position, salary, hire_date, supervisor_id) VALUES (?,?,?,?,?,?,?,?)",
            (
                str(first_name),
                str(last_name),
                str(email),
                str(department) if department is not None else None,
                str(position) if position is not None else None,
                float(salary) if salary is not None else None,
                str(hire_date) if hire_date is not None else None,
                int(supervisor_id) if supervisor_id is not None else None,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def prepare_and_insert_review(
    reviewer_identifier=None,
    target_identifier=None,
    score: Optional[int] = None,
    comments: Optional[str] = None,
    db_path: Optional[Path | str] = None,
    acting_reviewer_id: Optional[int] = None,
):
    """High-level helper for LLM-driven review insertion.

    Returns dict with status:
      - need_disambiguation: contains candidate lists
      - need_input: lists missing fields
      - forbidden: reviewer not manager of target
      - inserted: insertion successful with id and summary
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH

    # If reviewer_identifier wasn't provided, but acting_reviewer_id is available (caller identity), use it.
    if reviewer_identifier is None and acting_reviewer_id is not None:
        reviewer_matches = resolve_employee_identifier(int(acting_reviewer_id), db_path=db_path)
    else:
        reviewer_matches = resolve_employee_identifier(reviewer_identifier, db_path=db_path)

    target_matches = resolve_employee_identifier(target_identifier, db_path=db_path)

    if not reviewer_matches:
        return {"status": "error", "message": f"No reviewer found for '{reviewer_identifier or acting_reviewer_id}'"}
    if not target_matches:
        return {"status": "error", "message": f"No target employee found for '{target_identifier}'"}

    if len(reviewer_matches) > 1 or len(target_matches) > 1:
        return {"status": "need_disambiguation", "reviewer_candidates": reviewer_matches, "target_candidates": target_matches}

    reviewer = reviewer_matches[0]
    target = target_matches[0]

    # If acting_reviewer_id provided, ensure it matches the resolved reviewer (caller cannot act as another id)
    if acting_reviewer_id is not None and int(reviewer.get("id")) != int(acting_reviewer_id):
        return {
            "status": "forbidden",
            "message": "您提供的主管員工編號與您目前身份不符，無法代為建立考核。請確認您自己的員工編號或登入正確的帳號。",
            "resolved_reviewer": reviewer,
            "acting_reviewer_id": acting_reviewer_id,
        }

    # Check manager relationship
    if not is_manager_of(int(reviewer["id"]), int(target["id"]), db_path=db_path):
        return {
            "status": "forbidden",
            "message": "Reviewer is not a manager/ancestor of the target employee. Only managers can review their subordinates.",
            "reviewer": reviewer,
            "target": target,
        }

    # Validate score: must be integer 0-100
    missing = []
    if score is None:
        missing.append("score")
    else:
        # allow numeric strings
        try:
            score_int = int(float(score))
        except Exception:
            return {"status": "invalid_score", "message": "分數需為 0-100 的整數。"}
        if score_int < 0 or score_int > 100:
            return {"status": "invalid_score", "message": "分數需在 0 到 100 的範圍內。"}
        score = score_int

    if comments is None or str(comments).strip() == "":
        missing.append("comments")

    if missing:
        return {"status": "need_input", "missing": missing, "reviewer": reviewer, "target": target}

    # Attempt insert and catch DB errors to return a helpful message
    try:
        review_id = insert_performance_review(
            employee_id=int(target["id"]),
            reviewer_employee_id=int(reviewer["id"]),
            score=int(score),
            comments=str(comments),
            db_path=db_path,
        )
    except sqlite3.IntegrityError as e:
        return {"status": "error", "message": "資料不完整或違反資料庫限制，無法新增考核。", "detail": str(e)}
    except sqlite3.DatabaseError as e:
        return {"status": "error", "message": "資料庫錯誤，請稍後再試。", "detail": str(e)}
    except Exception as e:
        return {"status": "error", "message": "新增考核時發生未知錯誤。", "detail": str(e)}

    return {
        "status": "inserted",
        "id": review_id,
        "review": {
            "employee_id": target["id"],
            "employee_name": f"{target.get('first_name','')} {target.get('last_name','')}".strip(),
            "reviewer_id": reviewer["id"],
            "reviewer_name": f"{reviewer.get('first_name','')} {reviewer.get('last_name','')}".strip(),
            "score": score,
            "comments": comments,
        },
    }


if __name__ == "__main__":
    print("This module provides helpers for seeding and LLM-driven review insertion.")






