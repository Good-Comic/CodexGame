# TASK 05 — 自動遊戲打造：規劃 → 實作 → 測試 → 修復

## 目標
從使用者自然語言或 v3.0 企劃章節產生可追溯任務，經 Agent 分工後完成修改、測試、提交 PR；失敗時有安全停止與人類接管。

## 需求分片與上下文控制
- 大型 Markdown 企劃使用 MANIFEST / section chunks；單個任務輸入目標 <6000 中文字元。
- 每次只載入該任務關聯 spec、相依模組、當前狀態；不要貼入整份 v3.0。
- 任務完成寫摘要、改檔清單、測試、未解決缺陷、下一步。
- 建立需求追蹤矩陣：每個 v3.0 requirement -> source location -> code/test -> status。

## Agent 工作流
1. Planner 將需求拆成具有可測量結果的 Tickets。
2. Engineer 建獨立 worktree/branch 編寫程式。
3. QA 執行 Lint/Unit/E2E/畫面檢查。
4. Reviewer 以紅隊角度找 Regression、無效修改、安全問題。
5. 失敗最多自動重試 N 次（預設 2 次），之後停下並回報，不可無限迴圈消耗 Token。
6. 通過 Gate 後建立 PR；合併需要使用者核准。
7. Merge 後同步正式展示分支並標記快照。

## 預算與邊界
- 對 Agent 設 time/token/API budget、最大重試、可讀可寫檔案清單。
- 圖像/聲音等資產的生成依工具能力與授權獨立列項。
- 預設禁止購買、雲端發佈、安裝高權限套件、上傳私密資料。

## 驗收
1. 從一條自然語言需求可以產生 Ticket -> branch -> tests -> PR。
2. 故意造成編譯錯誤後系統能發現，重試達上限則停止。
3. 兩個 agent 不會同時覆寫同一工作區。
4. 可從進度介面追蹤 v3.0 需求覆蓋度；指標可重現。
