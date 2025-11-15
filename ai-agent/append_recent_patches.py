import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('log_writer', Path(__file__).resolve().parent / 'log_writer.py')
log_writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(log_writer)
append_log = log_writer.append_log

entries = [
    {
        "action": "UPDATE",
        "description": "Simplified ai-agent/agent.py: removed Google ADK content and added SQLite query_employees module.",
        "command": "apply_patch: replace agent.py with simplified SQLite-based module",
        "files": ["ai-agent/agent.py"],
    },
    {
        "action": "CREATE",
        "description": "Refactor create_database.py: add create_database(db_path) and avoid side-effects on import.",
        "command": "apply_patch: refactor create_database.py to provide create_database",
        "files": ["ai-agent/create_database.py"],
    },
    {
        "action": "UPDATE",
        "description": "Refactor insert_data.py: provide insert_employee_data(db_path) and avoid side-effects on import.",
        "command": "apply_patch: refactor insert_data.py to provide insert_employee_data",
        "files": ["ai-agent/insert_data.py"],
    },
    {
        "action": "CREATE",
        "description": "Add ai-agent/query.py: query_employees function to return employee rows as dicts.",
        "command": "apply_patch: add query.py with query_employees",
        "files": ["ai-agent/query.py"],
    },
    {
        "action": "UPDATE",
        "description": "Export new functions from package: update __init__.py to include create_database, insert_employee_data, query_employees.",
        "command": "apply_patch: update __init__.py exports",
        "files": ["ai-agent/__init__.py"],
    },
    {
        "action": "CREATE",
        "description": "Add test_db.py to validate DB creation, seed, and query behavior.",
        "command": "create_file: add test_db.py for verification",
        "files": ["ai-agent/test_db.py"],
    },
    {
        "action": "CREATE",
        "description": "Add modify_data.py: email-based update/delete (kept) and initial demo.",
        "command": "apply_patch: add modify_data.py with email-based functions",
        "files": ["ai-agent/modify_data.py"],
    },
    {
        "action": "CREATE",
        "description": "Add update_data.py: update_employee_by_id function (moved id-based update here).",
        "command": "apply_patch: add update_data.py",
        "files": ["ai-agent/update_data.py"],
    },
    {
        "action": "CREATE",
        "description": "Add delete_data.py: delete_employee_by_id function (moved id-based delete here).",
        "command": "apply_patch: add delete_data.py",
        "files": ["ai-agent/delete_data.py"],
    },
    {
        "action": "UPDATE",
        "description": "Refactor modify_data.py: remove id-based functions and import id-based functions from new modules in demo.",
        "command": "apply_patch: update modify_data.py to use new id-based modules",
        "files": ["ai-agent/modify_data.py"],
    },
    {
        "action": "UPDATE",
        "description": "Update __init__.py to re-export id-based functions from update_data and delete_data.",
        "command": "apply_patch: update __init__ imports and exports",
        "files": ["ai-agent/__init__.py"],
    },
    {
        "action": "UPDATE",
        "description": "Update test_modify.py to load and test update_data and delete_data modules.",
        "command": "apply_patch: update test_modify.py to call new modules",
        "files": ["ai-agent/test_modify.py"],
    },
    {
        "action": "UPDATE",
        "description": "Fix create_database function name and update references (create_database_employee -> create_database).",
        "command": "apply_patch: rename create_database_employee to create_database",
        "files": ["ai-agent/create_database.py", "ai-agent/__init__.py"],
    },
    {
        "action": "CREATE",
        "description": "Add top-level log.md changelog summarizing major changes.",
        "command": "apply_patch: add log.md",
        "files": ["log.md"],
    },
    {
        "action": "CREATE",
        "description": "Add ai-agent/log_writer.py to programmatically append structured entries to log.md.",
        "command": "apply_patch: add log_writer.py",
        "files": ["ai-agent/log_writer.py"],
    },
    {
        "action": "CREATE",
        "description": "Add scripts/install_git_hook.ps1 to optionally install a post-commit hook that calls log_writer.",
        "command": "apply_patch: add install_git_hook.ps1",
        "files": ["scripts/install_git_hook.ps1"],
    },
]

for e in entries:
    append_log(e["action"], e["description"], command=e.get("command"), files=e.get("files"))

print("Appended recent apply_patch entries to log.md")
