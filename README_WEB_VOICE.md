# 網頁版語音助理

本專案提供網頁介面的語音助理，支援語音輸入、文字轉語音回應，以及隨時打斷功能。

## 啟動方式

1.  確保已安裝所有依賴套件：
    ```powershell
    pip install -r requirements.txt
    ```

2.  啟動網頁伺服器：
    ```powershell
    python web_voice_server.py
    ```

3.  開啟瀏覽器（建議使用 Chrome 或 Edge），訪問：
    [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

## 功能特色

-   **語音對話**：點擊「開始對話」後，瀏覽器會持續監聽您的語音。
-   **即時打斷**：當 Agent 正在說話時，如果您開始說話，Agent 會立即停止並聆聽您的新指令。
-   **對話紀錄**：網頁下方會顯示完整的對話歷史。

## 注意事項

-   請允許瀏覽器使用麥克風權限。
-   若 Agent 回應聲音太小或沒有聲音，請檢查系統音量或瀏覽器分頁是否靜音。
-   「打斷」功能依賴瀏覽器的語音偵測，建議在安靜環境下使用以獲得最佳體驗。
