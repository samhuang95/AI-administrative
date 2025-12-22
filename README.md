# AI-administrative

## 快速開始

1. 建立並啟用虛擬環境（Python 3.13+）：

```powershell
py -3.13 -m venv venv
venv\Scripts\activate
```

2. 安裝相依：

```powershell
pip install -r requirements.txt
```

3. 啟動本專案（開發預覽）：

```powershell
# 選項 A（推薦，若已設定 adk command）
adk web

# 或 選項 B：靜態預覽
python -m http.server 8000
```

4. 打開瀏覽器：

```
http://localhost:8000/static/index.html
```

## 1. 環境啟動

在 `ai-agent` 資料中，建立 `.env` 檔，格式如下

# AI-administrative

## 1. 環境啟動

在 `ai-agent` 資料中，建立 `.env` 檔，格式如下：

```powershell
GOOGLE_GENAI_USE_VERTEXAI=FALSE
MODEL_USE=gemini-2.5-flash
GOOGLE_API_KEY={輸入自己的 Google API key}
```

建立虛擬環境（請使用 Python 3.13 或以上）：

```powershell
py -3.13 -m venv venv
```

啟動虛擬環境：

```powershell
venv\Scripts\activate
```

安裝相依套件：

```powershell
pip install -r requirements.txt
```

## 2. 專案啟動

在專案根目錄中執行：

```powershell
adk web
```

該指令（若可用）會啟動本專案的互動界面，預設連結為 `http://127.0.0.1:51530`。

---

## Web 介面語音助理

此專案包含一個網頁版的語音助理介面（位於 `static/index.html`），提供語音輸入、文字轉語音、即時中斷與對話紀錄。

快速啟用（開發/測試）：

1. 確認相依已安裝：

```powershell
pip install -r requirements.txt
```

2. 啟動靜態伺服器（開發用）：

```powershell
# 選項 A：若使用專案的開發工具
adk web

# 選項 B：簡易靜態伺服器（預覽 static）
python -m http.server 8000
```

3. 打開瀏覽器並訪問：

```
http://localhost:8000/static/index.html
```

功能重點：

- 點擊「開始對話」以啟動語音辨識（建議使用 Chrome / Edge）。
- Agent 回覆時若偵測到使用者語音會自動中斷回覆並轉為聆聽。
- 頁面下方會顯示對話歷史（log）。

注意與除錯：

- 請允許瀏覽器使用麥克風權限。瀏覽器在非 HTTPS 環境下對麥克風權限會有限制；如需完整功能建議在 HTTPS 或 localhost 下執行。
- 若無聲音，請確認系統音量、瀏覽器分頁靜音設定及 TTS 權限。
- 若語音辨識無效，請檢查瀏覽器是否支援 Web Speech API（Chrome/Edge 支援較佳）。

進階：

- 要在本機快速預覽，使用 `python -m http.server 8000` 並開啟 `/static/index.html`。
- 生產或內網部署時，請確保後端提供 `/chat` 與 `/cancel` API，並使用 HTTPS。

---

## 開發者必讀

### 安裝 Git hook（自動記錄 commit 到 `log.md`）

本專案已把 hook 腳本納入版本控制（資料夾 `.githooks/`），並提供安裝器 `scripts/install_hooks.ps1`（Windows/PowerShell）。

注意：Git 出於安全考量不會自動在 clone 時啟用 repository 內的 hook；因此每個開發者在 clone 後需**執行一次安裝步驟**以啟用 hooks（設定本地 repo 的 `core.hooksPath` 指向 `.githooks`）。

推薦安裝步驟（Windows / PowerShell，請在 repo 根目錄執行）：

```powershell
# 下載/更新後執行（第一次只需執行一次）
.\scripts\install_hooks.ps1

# 檢查是否成功
git config --get core.hooksPath
# 應回傳: .githooks
```

若你在 Bash/WSL/macOS/Linux 環境，也可以直接把 `.githooks/post-commit` 加到你的 hooksPath，或建立等效的安裝腳本。預設 repo 同時提供 POSIX 與 PowerShell 版本的 post-commit 腳本（在 `.githooks/` 下）。

安裝完成後，建議測試一次 commit（會把 commit 訊息自動 append 到 `log.md`）：

```powershell
git commit --allow-empty -m "test: verify post-commit hook"
Get-Content .\log.md -Tail 10
```

常見注意事項：

- Hook 會嘗試依序使用 `py`, `python3`, `python` 作為執行器；請確保你系統或虛擬環境的 PATH 可找到其中一個執行器。
- 若你使用 Sourcetree 或其他 GUI，請確認該工具使用的 Git 與你在終端可用的 Git 相同，並且能存取 Python。若無法執行，請參考下方「疑難排解」。

疑難排解快速提示：

- 若 commit 後 `log.md` 沒有更新：在 repo 根手動執行 `python .\log_writer.py --from-hook`，可檢查是否有例外或權限問題。
- 若多人作業：請把安裝步驟加入團隊 onboarding（或 README），以確保每個人 clone 後執行一次安裝。

如需我替你把安裝步驟自動寫入 README 或建立 CI 檢查，我可以代為完成。

## 新增：Agent CRUD 工具（建立 / 讀取 / 更新 / 刪除）

本專案在 `ai-agent/agent.py` 中新增了簡單的 CRUD 工具，用以管理 `employee` 資料表：

- `create_employee(first_name, last_name, email, department=None, position=None, salary=None, hire_date=None)`
- `get_employee(identifier)` — 支援 id、email 或模糊姓名查詢，若多筆會回傳 `ambiguous`。
- `update_employee(identifier, updates)` — 以 identifier 定位單筆員工，`updates` 為欄位->值的 dict。
- `delete_employee(identifier)` — 以 identifier 定位並刪除員工。

這些工具會被註冊在 `LlmAgent` 的 `tools` 列表中，供 ADK agent 使用。

### 簡單測試（已提供腳本）

專案包含一個簡單的測試腳本 `scripts/test_agent_tools.py`，可用來在開發環境快速驗證 CRUD 行為。請先啟用虛擬環境並安裝依賴，然後在 repo 根目錄執行：

```powershell
& .\venv\Scripts\Activate.ps1
python .\scripts\test_agent_tools.py
```

> 注意：該測試腳本會在匯入 `ai-agent/agent.py` 時使用輕量的 mock 物件繞過 `google`, `chromadb`, `dotenv` 等外部 SDK，以便在未安裝完整依賴時也能進行功能驗證。

### Pytest 範例

另外專案也包含 `tests/test_agent_crud.py`，示範如何在 CI 或本地以 pytest 執行 CRUD 測試。範例會在執行期間建立一個臨時 sqlite 資料庫並指向 agent 使用，避免改動開發者的主資料庫。

要執行 pytest 範例：

```powershell
pip install pytest
pytest -q
```

如果你希望我把該測試整合到 CI pipeline（例如 GitHub Actions），我可以幫你撰寫 workflow 檔案。
