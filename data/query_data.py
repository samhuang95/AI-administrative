"""Query utilities for the employee database.

Provides `query_employees(db_path, limit)` which returns rows as dictionaries.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "employee.db"


def query_employees(db_path: Optional[Path | str] = None, limit: int = 100) -> List[Dict]:
    """Return up to `limit` employee rows as a list of dicts.

    Args:
        db_path: Optional path to SQLite DB file. Uses default if omitted.
        limit: Max rows to return.
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM employee ORDER BY id LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()





