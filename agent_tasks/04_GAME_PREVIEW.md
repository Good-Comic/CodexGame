# TASK 04 — 遊戲引擎 Adapter、試玩與即時預覽

## 目標
第一優先是對既有 HTML/CSS/JS ES modules 遊戲實現「邊寫邊玩」，其後擴充 Godot/Unity 等引擎。

## 第一階段：Web RTS
- 從 `workspace/<repo>/index.html` 啟動 Vite 開發伺服器。
- Live reload/HMR：AI 寫入檔案後更新遊戲預覽，支援在 Studio 中 reload。
- 預覽頁 iframe 有 sandbox / 權限隔離；程式碼由受控 sandbox 執行，不共享平台 session cookies。
- 可以讀取 browser console/errors，顯示最近修改檔案和截圖。
- Playwright E2E：載入遊戲、四語系選項、主要操作、10 波流程的 smoke tests。
- 記錄成功與失敗截圖，僅允許使用者核准後更新 goldens。
- FPS、載入時間、長時間資源消耗與基本操作延遲可量測，不憑空假定。

## 後續引擎
- Godot：執行 engine headless import/export，支援 Web build preview；保留原生桌面版本導出。
- Unity：需要正確安裝及授權本地 Unity Editor；可自動建置與測試，但不能只靠瀏覽器取代原生 Editor。
- 任何引擎轉換均需使用者批准且在新分支驗證，不得默默遷移舊遊戲。

## 驗收
1. Vite 本地預覽可以直接玩既有遊戲。
2. 改動 UI/CSS 後預覽反映修改；console errors 可見。
3. Playwright 能至少完成啟動與主要選單的回歸測試。
4. Agent 修改導致遊戲無法載入時 Quality Gate 失敗且保留 log 與回滾點。
