"""Delete utilities for the employee database (by id).

Contains `delete_employee_by_id` which deletes a row by primary key id.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from query_data import query_employees


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "employee.db"


def delete_employee_by_id(emp_id: int, db_path: Optional[Path | str] = None) -> int:
    """Delete an employee row by id. Returns number of rows deleted (0 or 1)."""
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM employee WHERE id=?", (emp_id,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


if __name__ == "__main__":
    print("Before delete (DB must already exist):")
    print(query_employees())
    deleted = delete_employee_by_id(3)
    print("deleted rows:", deleted)
    print("After delete:")
    print(query_employees())
