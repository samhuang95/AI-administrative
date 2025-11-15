"""Data seeding utilities.

This module provides `insert_employee_data(db_path)` which inserts sample rows
into an existing `employee` table. It does not create the DB or table; that is
handled by `create_database.create_database`.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Sequence, Tuple


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


if __name__ == "__main__":
    inserted = insert_employee_data()
    print(f"Inserted {inserted} rows (0 means table already had rows).")