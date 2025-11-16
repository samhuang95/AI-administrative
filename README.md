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

本專案提供一個 post-commit hook，會在每次 commit 後自動把 commit 訊息與變更檔案附加到專案根的 `log.md`。請用下列命令安裝：

- Windows / PowerShell（推薦）

  ```powershell
  # 於 repo 根目錄執行（允許腳本執行）
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_git_hook.ps1
  ```

- Git Bash / WSL / Linux（bash 環境）

  ```bash
  bash scripts/install_git_hook.sh
  ```

安裝完成後，建議測試一次 commit：

```powershell
git add -A
git commit -m "test: verify post-commit hook"

# 然後檢查 log.md 是否新增 COMMIT 條目
notepad.exe log.md  # 或用你喜歡的編輯器
```

注意：

- Hook 會嘗試尋找 `py`, `python3`, `python`（依序）作為執行器；確保虛擬環境或系統 PATH 可以找到 Python。
- 若 hook 沒有動作，可以手動在 repo 根跑 `python .\log_writer.py --from-hook` 做同樣的 append（有助於除錯）。

如果需要我把流程改成更自動化（例如在每次我修改檔案時自動呼叫 `scripts/assistant_append_log.py` 幫你寫入 log），告訴我你希望的自動化行為，我會幫你加上範例或腳本。
