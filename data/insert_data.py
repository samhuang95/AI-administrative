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


if __name__ == "__main__":
    inserted = insert_employee_data()
    print(f"Inserted {inserted} rows (0 means table already had rows).")


def insert_many_employees(db_path: Optional[Path | str] = None, n: int = 20) -> int:
    """Insert `n` synthetic employees into the employee table.

    Returns number of rows inserted.
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    # Ensure DB and table exist
    try:
        from data.create_database import create_database_employee
    except Exception:
        # running as script: ensure repo root is on sys.path
        repo_root = Path(__file__).resolve().parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from data.create_database import create_database_employee

    create_database_employee(db_path)

    # sample pools
    first_names = ["Alex","Bryan","Cindy","Diana","Ethan","Fiona","George","Hannah","Ivan","Julia","Kevin","Lily","Marcus","Nina","Oliver","Penny","Quinn","Rita","Samuel","Tina"]
    last_names = ["Lee","Wong","Huang","Chen","Lin","Wu","Chang","Kao","Tsai","Cheng"]
    departments = {
        "Engineering": ["Junior Engineer","Engineer","Senior Engineer","Tech Lead"],
        "Sales": ["Sales Rep","Senior Sales","Sales Manager"],
        "HR": ["HR Specialist","HR Manager"],
        "Finance": ["Accountant","Senior Accountant","Finance Manager"],
        "Support": ["Support Agent","Support Lead"]
    }

    # create deterministic list of employees across departments
    employees = []
    email_domain = "example.com"
    idx = 0
    dept_list = list(departments.keys())
    while len(employees) < n:
        fn = first_names[idx % len(first_names)]
        ln = last_names[idx % len(last_names)]
        dept = dept_list[len(employees) % len(dept_list)]
        # choose position distribution skewed by index
        pos_list = departments[dept]
        pos = pos_list[min(len(pos_list)-1, (len(employees)//len(dept_list)) % len(pos_list))]
        email = f"{fn.lower()}.{ln.lower()}{idx}@{email_domain}"
        salary = float(50000 + (idx % 10) * 5000)
        hire_date = datetime(2020, 1, 1) + idx * timedelta(days=30)
        hire_date_str = hire_date.strftime("%Y-%m-%d")
        employees.append((fn, ln, email, dept, pos, salary, hire_date_str))
        idx += 1

    # insert into DB
    return insert_employee_data(db_path=db_path, data=employees)


def create_performance_reviews_by_managers(db_path: Optional[Path | str] = None) -> int:
    """Create performance reviews where each employee (except top-level) is reviewed by a manager.

    Returns number of reviews inserted.
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    # ensure performance table exists
    try:
        from data.create_database import create_performance_table
    except Exception:
        repo_root = Path(__file__).resolve().parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from data.create_database import create_performance_table

    create_performance_table(db_path)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        # load employees
        cur.execute("SELECT id, department, position FROM employee ORDER BY id")
        rows = cur.fetchall()
        if not rows:
            return 0

        # simple mapping of seniority: pick reviewer as first employee in same department with lower id but different position
        reviews = []
        for emp in rows:
            emp_id, dept, pos = emp
            # find possible reviewers: someone with same dept and id < emp_id
            cur.execute("SELECT id FROM employee WHERE department = ? AND id < ? ORDER BY id DESC LIMIT 1", (dept, emp_id))
            r = cur.fetchone()
            if r:
                reviewer_id = r[0]
            else:
                # fallback: pick any other employee with id != emp_id
                cur.execute("SELECT id FROM employee WHERE id != ? LIMIT 1", (emp_id,))
                rf = cur.fetchone()
                reviewer_id = rf[0] if rf else None

            if reviewer_id is None:
                continue

            score = round(3.0 + random.random() * 2.0, 1)
            comments = "Auto-generated review"
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            reviews.append((emp_id, reviewer_id, score, comments, created_at))

        cur.executemany(
            "INSERT INTO performance_review (employee_id, reviewer_employee_id, score, comments, created_at) VALUES (?,?,?,?,?)",
            reviews,
        )
        conn.commit()
        return len(reviews)
    finally:
        conn.close()


def query_employees_and_reviews(db_path: Optional[Path | str] = None):
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, first_name, last_name, department, position, email FROM employee ORDER BY id")
        emps = cur.fetchall()
        cur.execute("SELECT pr.id, pr.employee_id, pr.reviewer_employee_id, pr.score, pr.comments, pr.created_at FROM performance_review pr ORDER BY pr.id")
        revs = cur.fetchall()
        return emps, revs
    finally:
        conn.close()


def create_n_performance_reviews(db_path: Optional[Path | str] = None, n: int = 100) -> int:
    """Create `n` performance reviews across employees.

    Rules:
    - For each review pick a target employee at random.
    - Choose a reviewer prefering same-department senior employees; if none, pick any other employee.
    - Allow the same reviewer to review the same subordinate multiple times.

    Returns number of reviews inserted.
    """
    db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    # ensure performance table exists
    try:
        from data.create_database import create_performance_table
    except Exception:
        repo_root = Path(__file__).resolve().parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from data.create_database import create_performance_table

    create_performance_table(db_path)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, department, position FROM employee ORDER BY id")
        rows = cur.fetchall()
        if not rows:
            return 0

        # Build potential reviewer lists per employee
        emp_list = [dict(id=r[0], department=r[1], position=r[2]) for r in rows]
        id_to_index = {e['id']: i for i, e in enumerate(emp_list)}

        # Precompute seniority candidates per department (prefer managers/leads/senior)
        dept_candidates = {}
        for e in emp_list:
            dept = e['department']
            dept_candidates.setdefault(dept, []).append(e)

        reviews = []
        for _ in range(n):
            target = random.choice(emp_list)
            candidates = []
            # Prefer same-department candidates with 'Manager','Lead','Senior' or lower id
            for c in dept_candidates.get(target['department'], []):
                if c['id'] != target['id'] and (
                    any(k in (c['position'] or '').lower() for k in ['manager', 'lead', 'senior'])
                    or c['id'] < target['id']
                ):
                    candidates.append(c)

            if not candidates:
                # fallback: any other employee
                candidates = [c for c in emp_list if c['id'] != target['id']]

            if not candidates:
                continue

            reviewer = random.choice(candidates)
            score = round(2.5 + random.random() * 2.5, 1)  # range ~2.5-5.0
            comments = random.choice([
                'Meets expectations',
                'Exceeds expectations',
                'Needs improvement',
                'Outstanding contribution',
                'Solid performance'
            ])
            # random recent timestamp within last 365 days
            from datetime import timedelta
            days_back = random.randint(0, 365)
            created_at = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d %H:%M:%S")
            reviews.append((target['id'], reviewer['id'], score, comments, created_at))

        cur.executemany(
            "INSERT INTO performance_review (employee_id, reviewer_employee_id, score, comments, created_at) VALUES (?,?,?,?,?)",
            reviews,
        )
        conn.commit()
        return len(reviews)
    finally:
        conn.close()


if __name__ == "__main__":
    # If executed directly, perform full seed: ensure DB, insert many employees, create reviews, and print summary
    print("Initializing DB and seeding employees + performance reviews...")
    # ensure base DB
    try:
        from data.create_database import create_database_employee, create_performance_table
    except Exception:
        repo_root = Path(__file__).resolve().parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from data.create_database import create_database_employee, create_performance_table

    db = create_database_employee()
    create_performance_table(db)
    inserted = insert_many_employees(db, n=20)
    print(f"Inserted {inserted} employees")
    rev_count = create_performance_reviews_by_managers(db)
    print(f"Inserted {rev_count} performance reviews")
    emps, revs = query_employees_and_reviews(db)
    print("\nEmployees:")
    for e in emps:
        print(e)
    print("\nReviews:")
    for r in revs:
        print(r)