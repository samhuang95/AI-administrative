# AI-administrative

## 安裝 Git hook（自動記錄 commit 到 log.md）

本專案已提供一個簡單的 post-commit hook，會在每次 commit 後自動將 commit 訊息與變更檔案清單附加到根目錄的 `log.md`。

有兩種安裝方式，請依你的環境選擇：

- Windows / PowerShell（建議 Windows 使用者）

	在專案根目錄執行：

	```powershell
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_git_hook.ps1
	```

	此腳本會在 `.git/hooks/post-commit` 寫入一個 LF（Unix）格式、UTF-8 無 BOM 的 hook，並嘗試在系統上設定為可執行。

- Git Bash / WSL / Linux（bash 環境）

	在專案根目錄執行：

	```bash
	bash scripts/install_git_hook.sh
	```

	此腳本同樣會寫入 `.git/hooks/post-commit` 並設定可執行權限。

安裝後，建議測試一次 commit：

```bash
git add -A
git commit -m "test: verify post-commit hook"
```

然後查看 `log.md` 最末端是否新增了以 `COMMIT` 為 action 的條目。

註：hook 會用 Python 直接呼叫 `git` 取得最後一次 commit 的資訊，避免在 hook 中依賴 `tr`、`paste`、`sed` 等在某些 Windows 環境可能缺少的工具。
