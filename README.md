# AI-administrative

### 1. 環境啟動

在 `ai-agent` 資料中，建立 `.env` 檔，格式如下

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

可以使用 `pip list` 確認是否為全新的虛擬環境。安裝相依套件：

```powershell
pip install -r requirements.txt
```

### 2. 專案啟動

在專案`根目錄`中，執行下方指令，就會開啟 `127.0.0.1:51530` 互動式介面連結

```powershell
adk web
```

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
