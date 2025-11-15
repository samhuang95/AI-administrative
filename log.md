# 變更紀錄（Changelog）

以下紀錄從專案最初包含 Google ADK agent 範例，到後來簡化、加入 SQLite 資料庫與完整 CRUD（Create/Read/Update/Delete）員工資料的所有重要變更。

---

## 起點：原始 agent（Google ADK 範例）
- 檔案：`ai-agent/agent.py`
- 說明：最初的 `agent.py` 包含多個工具函式與 Google ADK（例如 `LlmAgent`、`MCPToolset`）與功能：
  - get_weather(city) 【透過 OpenWeatherMap 或範例回傳】
  - get_current_time(tz_identifier) / agent_receive_range
  - 建立並設定 `root_agent = LlmAgent(...)`（含多個 MCPToolset）

用途：這是專案早期的範例 agent 程式碼，含許多外部依賴（google.adk 等）。

---

## 簡化與目標變更（將 agent 簡化為單一 SQLite 查詢功能）
- 動作：將 `ai-agent/agent.py` 的原始內容移除或重寫為精簡模組，移除不必要的函式與第三方依賴，改以本地 SQLite 為示範。
- 新增行為：在模組匯入時（初期實作）會建立 `data/employee.db`、建立 `employee` table 並在空時加入示範資料。
- 新檔案（初版）：
  - `ai-agent/agent.py`（後來被重寫為簡化版）

目的：把複雜的範例轉為更小、易於測試和本地跑的示範，專注於資料管理而非外部 API。

---

## 模組化：把 DB 行為拆成單一責任模組
為了清楚分離責任，程式被拆成多個小模組：

- `ai-agent/create_database.py`
  - 函式：`create_database(db_path=None)`
  - 作用：建立 `data/employee.db` 與 `employee` table（不在 import 時執行副作用）。

- `ai-agent/insert_data.py`（後更名/重構為 `insert_employee_data`）
  - 函式：`insert_employee_data(db_path=None, data=None)`
  - 作用：若 `employee` table 為空，插入示範員工資料（Alice、Bob、Carol）。

- `ai-agent/query.py`（或曾見 `query_data.py` 在 data 目錄）
  - 函式：`query_employees(db_path=None, limit=100)` 或 `query_employee_list`（視檔案版本而定）
  - 作用：查詢 `employee` table，回傳 list[dict]。

設計原則：模組不在 import 時做寫入或建立 db，改以顯示、可被呼叫的函式為主，減少非預期副作用。

---

## 新增修改（Update）與刪除（Delete）功能
為了實作完整 CRUD，加入修改與刪除功能，並將它們拆成獨立檔案：

- `ai-agent/update_data.py`
  - 函式：`update_employee_by_id(emp_id, updates, db_path=None)`
  - 允許更新欄位：`first_name, last_name, email, department, position, salary, hire_date`。
  - 回傳：受影響的列數（int）。
  - 範例 demo：現在只會在 `__main__` 中顯示 demo（但不會自動建立 DB 或插入資料），並提供註解指引如何初始化 DB。

- `ai-agent/delete_data.py`
  - 函式：`delete_employee_by_id(emp_id, db_path=None)`
  - 回傳：刪除的列數（int）。
  - 範例 demo：同樣不會自動初始化 DB，只假設 DB 已存在。

此外，早期存在的 `ai-agent/modify_data.py` 保留 email-based update/delete 的實作（例如 `update_employee_by_email`, `delete_employee_by_email`），但 id-based 的 update/delete 已被移到上述兩個新檔案中。

---

## 套件匯出與測試腳本
- `ai-agent/__init__.py` 被更新以匯出主要函式，方便 `from ai_agent import ...` 的使用：
  - create_database, insert_employee_data, query_employees, update_employee_by_id, update_employee_by_email, delete_employee_by_id, delete_employee_by_email

- 測試腳本：
  - `ai-agent/test_db.py`（早期）：直接從檔案路徑載入模組來建立 DB / seed / query，驗證查詢功能。
  - `ai-agent/test_modify.py`（後續）：驗證 update 與 delete 的功能，執行流程：create_database -> insert_employee_data -> query -> update_by_id -> delete_by_id -> query。

我已在你的環境執行過 `test_modify.py`，並驗證：
  - 建立/找到 DB：`D:\AI-administrative\data\employee.db`
  - 初始資料（示範）可被查出
  - 更新（例如 id=1 salary -> 90000）會回傳 updated rows: 1
  - 刪除（例如 id=3）會回傳 deleted rows: 1（若該 id 尚存在）

---

## 安全設計與使用說明（重要）
- 為避免匯入模組時發生非預期寫入，目前各功能模組**不會在 import 時自動建立或寫入資料**。若要建立 DB 與插入示範資料，請呼叫：

```python
from ai_agent.create_database import create_database
from ai_agent.insert_data import insert_employee_data
create_database()
insert_employee_data()
```

- 查詢/更新/刪除示例（程式內使用）：
```python
from ai_agent.query import query_employees
from ai_agent.update_data import update_employee_by_id
from ai_agent.delete_data import delete_employee_by_id

rows = query_employees()
update_employee_by_id(1, {"salary": 90000})
delete_employee_by_id(3)
```

或使用我在 repo 中提供的測試腳本：

```powershell
py -3 d:\AI-administrative\ai-agent\test_modify.py
```

---

## 檔案清單（重要檔案與其目的）
- ai-agent/agent.py — 原始 Google ADK 範例（後來被簡化或替換為 SQLite demo）
- ai-agent/create_database.py — 建立 DB 與 schema
- ai-agent/insert_data.py — 插入示範員工資料（函式：insert_employee_data）
- ai-agent/query.py 或 data/query_data.py — 查詢函式（query_employees / query_employee_list）
- ai-agent/update_data.py — 更新（by id）
- ai-agent/delete_data.py — 刪除（by id）
- ai-agent/modify_data.py — email-based update/delete（保留）
- ai-agent/test_db.py, ai-agent/test_modify.py — 本地驗證腳本
- data/employee.db — 實際 SQLite DB（位於 `data` 目錄）

---

## 建議的下一步（選項）
1. 若要在專案中保留示範初始化腳本，建議建立一個單獨的 CLI 初始化腳本（例如 `scripts/init_db.py`），避免模組匯入副作用。
2. 若要更完善的 API，可建立小型 FastAPI 服務以提供 CRUD REST 介面。
3. 若需自動化測試，建議加入 `tests/` 目錄與 pytest 測試，並在 CI 中執行（需為測試準備臨時資料庫）。

---

## 後續
如果你要我把這個 `log.md` 放到其他路徑或加入更詳細的每次提交紀錄（含每個 apply_patch 的 diff 摘要），我可以再擴充。也可以把測試步驟轉成可執行的 PowerShell 腳本供你一鍵初始化與測試。請告訴我下一步的優先項目。
- [2025-11-16 01:58:25] UPDATE: Simplified ai-agent/agent.py: removed Google ADK content and added SQLite query_employees module.
  - command: `apply_patch: replace agent.py with simplified SQLite-based module`
  - files:
    - `ai-agent/agent.py`
- [2025-11-16 01:58:25] CREATE: Refactor create_database.py: add create_database(db_path) and avoid side-effects on import.
  - command: `apply_patch: refactor create_database.py to provide create_database`
  - files:
    - `ai-agent/create_database.py`
- [2025-11-16 01:58:25] UPDATE: Refactor insert_data.py: provide insert_employee_data(db_path) and avoid side-effects on import.
  - command: `apply_patch: refactor insert_data.py to provide insert_employee_data`
  - files:
    - `ai-agent/insert_data.py`
- [2025-11-16 01:58:25] CREATE: Add ai-agent/query.py: query_employees function to return employee rows as dicts.
  - command: `apply_patch: add query.py with query_employees`
  - files:
    - `ai-agent/query.py`
- [2025-11-16 01:58:25] UPDATE: Export new functions from package: update __init__.py to include create_database, insert_employee_data, query_employees.
  - command: `apply_patch: update __init__.py exports`
  - files:
    - `ai-agent/__init__.py`
- [2025-11-16 01:58:25] CREATE: Add test_db.py to validate DB creation, seed, and query behavior.
  - command: `create_file: add test_db.py for verification`
  - files:
    - `ai-agent/test_db.py`
- [2025-11-16 01:58:25] CREATE: Add modify_data.py: email-based update/delete (kept) and initial demo.
  - command: `apply_patch: add modify_data.py with email-based functions`
  - files:
    - `ai-agent/modify_data.py`
- [2025-11-16 01:58:25] CREATE: Add update_data.py: update_employee_by_id function (moved id-based update here).
  - command: `apply_patch: add update_data.py`
  - files:
    - `ai-agent/update_data.py`
- [2025-11-16 01:58:25] CREATE: Add delete_data.py: delete_employee_by_id function (moved id-based delete here).
  - command: `apply_patch: add delete_data.py`
  - files:
    - `ai-agent/delete_data.py`
- [2025-11-16 01:58:25] UPDATE: Refactor modify_data.py: remove id-based functions and import id-based functions from new modules in demo.
  - command: `apply_patch: update modify_data.py to use new id-based modules`
  - files:
    - `ai-agent/modify_data.py`
- [2025-11-16 01:58:25] UPDATE: Update __init__.py to re-export id-based functions from update_data and delete_data.
  - command: `apply_patch: update __init__ imports and exports`
  - files:
    - `ai-agent/__init__.py`
- [2025-11-16 01:58:25] UPDATE: Update test_modify.py to load and test update_data and delete_data modules.
  - command: `apply_patch: update test_modify.py to call new modules`
  - files:
    - `ai-agent/test_modify.py`
- [2025-11-16 01:58:25] UPDATE: Fix create_database function name and update references (create_database_employee -> create_database).
  - command: `apply_patch: rename create_database_employee to create_database`
  - files:
    - `ai-agent/create_database.py`
    - `ai-agent/__init__.py`
- [2025-11-16 01:58:25] CREATE: Add top-level log.md changelog summarizing major changes.
  - command: `apply_patch: add log.md`
  - files:
    - `log.md`
- [2025-11-16 01:58:25] CREATE: Add ai-agent/log_writer.py to programmatically append structured entries to log.md.
  - command: `apply_patch: add log_writer.py`
  - files:
    - `ai-agent/log_writer.py`
- [2025-11-16 01:58:25] CREATE: Add scripts/install_git_hook.ps1 to optionally install a post-commit hook that calls log_writer.
  - command: `apply_patch: add install_git_hook.ps1`
  - files:
    - `scripts/install_git_hook.ps1`
- [2025-11-16 02:14:22] COMMIT: Create DB controllers and log record hook feature.  
  - command: `git commit -m "Create DB controllers and log record hook feature.  "`
  - files:
    - `.gitignore`
    - `.vscode/settings.json`
    - `ai-agent/__init__.py`
    - `ai-agent/__pycache__/agent.cpython-310.pyc`
    - `ai-agent/__pycache__/create_database.cpython-313.pyc`
    - `ai-agent/__pycache__/delete_data.cpython-313.pyc`
    - `ai-agent/__pycache__/insert_data.cpython-313.pyc`
    - `ai-agent/__pycache__/log_writer.cpython-313.pyc`
    - `ai-agent/__pycache__/modify_data.cpython-313.pyc`
    - `ai-agent/__pycache__/query.cpython-313.pyc`
    - `ai-agent/__pycache__/update_data.cpython-313.pyc`
    - `ai-agent/agent.py`
    - `ai-agent/append_recent_patches.py`
    - `ai-agent/log_writer.py`
    - `data/create_database.py`
    - `data/delete_data.py`
    - `data/employee.db`
    - `data/insert_data.py`
    - `data/query_data.py`
    - `data/update_data.py`
    - `log.md`
    - `requirements.txt`
    - `scripts/install_git_hook.ps1`
- [2025-11-16 02:24:08] COMMIT: Create DB controllers and log record hook feature.
  - command: `git commit -m "Create DB controllers and log record hook feature."`
  - files:
    - `.gitignore`
    - `.vscode/settings.json`
    - `ai-agent/__init__.py`
    - `ai-agent/__pycache__/agent.cpython-310.pyc`
    - `ai-agent/__pycache__/create_database.cpython-313.pyc`
    - `ai-agent/__pycache__/delete_data.cpython-313.pyc`
    - `ai-agent/__pycache__/insert_data.cpython-313.pyc`
    - `ai-agent/__pycache__/log_writer.cpython-313.pyc`
    - `ai-agent/__pycache__/modify_data.cpython-313.pyc`
    - `ai-agent/__pycache__/query.cpython-313.pyc`
    - `ai-agent/__pycache__/update_data.cpython-313.pyc`
    - `ai-agent/agent.py`
    - `ai-agent/append_recent_patches.py`
    - `ai-agent/log_writer.py`
    - `data/create_database.py`
    - `data/delete_data.py`
    - `data/employee.db`
    - `data/insert_data.py`
    - `data/query_data.py`
    - `data/update_data.py`
    - `log.md`
    - `requirements.txt`
    - `scripts/install_git_hook.ps1`
- [2025-11-16 02:29:10] COMMIT: Create DB controllers and log record hook feature.
  - command: `git commit -m "Create DB controllers and log record hook feature."`
  - files:
    - `.gitignore`
    - `.vscode/settings.json`
    - `ai-agent/__init__.py`
    - `ai-agent/__pycache__/agent.cpython-310.pyc`
    - `ai-agent/__pycache__/create_database.cpython-313.pyc`
    - `ai-agent/__pycache__/delete_data.cpython-313.pyc`
    - `ai-agent/__pycache__/insert_data.cpython-313.pyc`
    - `ai-agent/__pycache__/log_writer.cpython-313.pyc`
    - `ai-agent/__pycache__/modify_data.cpython-313.pyc`
    - `ai-agent/__pycache__/query.cpython-313.pyc`
    - `ai-agent/__pycache__/update_data.cpython-313.pyc`
    - `ai-agent/agent.py`
    - `ai-agent/append_recent_patches.py`
    - `ai-agent/log_writer.py`
    - `data/create_database.py`
    - `data/delete_data.py`
    - `data/employee.db`
    - `data/insert_data.py`
    - `data/query_data.py`
    - `data/update_data.py`
    - `log.md`
    - `requirements.txt`
    - `scripts/install_git_hook.ps1`
- [2025-11-16 02:29:44] COMMIT: Create DB controllers and log record hook feature.
  - command: `git commit -m "Create DB controllers and log record hook feature."`
  - files:
    - `.gitignore`
    - `.vscode/settings.json`
    - `ai-agent/__init__.py`
    - `ai-agent/__pycache__/agent.cpython-310.pyc`
    - `ai-agent/__pycache__/create_database.cpython-313.pyc`
    - `ai-agent/__pycache__/delete_data.cpython-313.pyc`
    - `ai-agent/__pycache__/insert_data.cpython-313.pyc`
    - `ai-agent/__pycache__/log_writer.cpython-313.pyc`
    - `ai-agent/__pycache__/modify_data.cpython-313.pyc`
    - `ai-agent/__pycache__/query.cpython-313.pyc`
    - `ai-agent/__pycache__/update_data.cpython-313.pyc`
    - `ai-agent/agent.py`
    - `ai-agent/append_recent_patches.py`
    - `ai-agent/log_writer.py`
    - `data/create_database.py`
    - `data/delete_data.py`
    - `data/employee.db`
    - `data/insert_data.py`
    - `data/query_data.py`
    - `data/update_data.py`
    - `log.md`
    - `requirements.txt`
    - `scripts/install_git_hook.ps1`
- [2025-11-16 02:33:59] COMMIT: Create the log auto record feature.
  - command: `git commit -m "Create the log auto record feature."`
  - files:
    - `README.md`
    - `ai-agent/log_writer.py`
    - `log.md`
    - `scripts/install_git_hook.ps1`
    - `scripts/install_git_hook.sh`
