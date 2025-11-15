"""Database creation utilities.

This module provides a function `create_database(db_path)` that ensures the
SQLite database and the `employee` table exist. It does NOT perform seeding on
import; seeding is provided by `insert_data.py`.
"""

import sqlite3
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "employee.db"


def create_database_employee(db_path: Optional[Path | str] = None) -> Path:
    """Ensure the database file and `employee` table exist.

    Args:
        db_path: Optional path to the database file. If omitted, a default
                 `data/employee.db` under the project root is used.

    Returns:
        The Path to the database file that was created/ensured.
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema = """
    CREATE TABLE IF NOT EXISTS employee (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT,
        position TEXT,
        salary REAL,
        hire_date TEXT
    );
    """

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.executescript(schema)
        conn.commit()
    finally:
        conn.close()

    return db_path


if __name__ == "__main__":
    p = create_database_employee()
    print(f"Database initialized at: {p}")