# TASK 03 — GitHub 雙向同步（安全、可追蹤）

## 目標
GitHub 作為原始碼版本事實來源，支援使用者指定 repo 自動導入、近即時偵測更新、建立 PR 與可審核合併。

## 技術與權限
- 正式使用 GitHub App，而非長期 PAT 或把使用者登入密碼交給 Agent。
- 安裝時只允許使用者選定的 repos；最小權限建議 Metadata: Read、Contents: Read/Write、Pull requests: Read/Write（按功能增減）。
- App 私鑰及 webhook secret 只能儲存於服務端安全位置；短期 installation token 不可持久化。
- 驗證 X-Hub-Signature-256、拒絕重放 delivery、處理 webhook 重送/排序及 rate limit。
- 本地使用 Git worktree 或 per-task feature branch，禁止兩個 Agent 在同一工作目錄改檔。
- 監測 GitHub push/PR events：拉取遠端更新前先確認本地是否有未提交內容；衝突則停下來等使用者選擇。
- Agent 提交 commit 前需 `git diff` + 測試 + secrets scan；自動 push 到 feature branch，建立 PR（可選使用者核准）。
- 禁止直接 force push、刪除 repo、覆蓋 main；自動 merge 僅在明確授權及 Quality Gate 通過的策略下啟用。

## UI
顯示：Repo、Branch、最新 commit、ahead/behind、最後 webhook 時間、待審核 PR、conflicts、同步故障。

## 驗收
1. 授權指定 repo 後成功 import。
2. 外部 push 能觸發 webhook，Studio 於合理延遲內更新狀態；失敗有重試。
3. 每個任務在獨立 branch 產生 commit 和 PR，不直接碰 main。
4. 重複 webhook delivery 不產生重複任務。
5. API token 不寫入 repo 和 log；未授權 repo 存取被拒絕。
6. 斷線恢復後的事件能補償同步。

## 備註
Webhook 接收器須是 GitHub 可到達的 HTTPS URL；只有 127.0.0.1 的私人服務無法直接接收外部推送。可使用安全的 tunnel 或部署狹權限 relay；該入口必須實作驗證與認證。
