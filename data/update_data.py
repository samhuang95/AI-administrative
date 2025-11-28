"""Update utilities for the employee database (by id).

Contains `update_employee_by_id` which updates allowed columns for a given id.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

from data.query_data import query_employees

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "employee.db"

# Allowed columns that can be updated
ALLOWED_COLUMNS = {"first_name", "last_name", "email", "department", "position", "salary", "hire_date"}


def update_employee_by_id(emp_id: int, updates: Dict[str, Any], db_path: Optional[Path | str] = None) -> int:
    """Update an employee row by id. Returns number of rows updated (0 or 1).

    Args:
        emp_id: employee id (primary key)
        updates: dict of column->value to update
        db_path: optional DB path
    """
    if not updates:
        return 0
    # filter keys
    keys = [k for k in updates.keys() if k in ALLOWED_COLUMNS]
    if not keys:
        return 0

    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    set_clause = ", ".join([f"{k}=?" for k in keys])
    params = [updates[k] for k in keys] + [emp_id]

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE employee SET {set_clause} WHERE id=?", params)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


if __name__ == "__main__":
    print("Before update (DB must already exist):")
    print(query_employees())
    updated = update_employee_by_id(1, {"salary": 90000})
    print("updated rows:", updated)
    print("After update:")
    print(query_employees())
