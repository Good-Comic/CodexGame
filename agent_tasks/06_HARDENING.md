# TASK 06 — 安全硬化、可靠性與產品發佈

## 目標
由本地個人 Demo 轉成可以長期使用的私人 Game Studio；確認功能、安全與運作可靠性後再考慮遠端存取。

## 必需事項
- 設計 OAuth/OIDC 認證、session 和 CSRF 防護；局域網／網際網路使用時需 HTTPS。
- Secrets server-side encryption & access control，不能交給 Model context。
- Sandbox 限制 CPU/RAM/disk/time/network；避免 Mount host Docker socket。
- Prompt injection threat model：repo README、PR、Issue、遊戲資產皆視為不可信輸入。
- Security headers、上傳限制、檔案存取範圍、SSR F、shell injection、依賴掃描。
- Backup/Restore：定時 Git refs、資料庫備份、工作區快照，進行還原演練。
- Worker queue + idempotency + crash recovery + webhook dead-letter/replay。
- 對模型 API 費用、耗時、成功率、Token、回歸測試維持 dashboard。
- 動態權限：可讀、可改、可執行、可推送、可合併，不同高風險操作分級授權。
- 無外網、GitHub 故障、模型故障、Git conflicts 時要有明確降級行為。

## 驗收
1. 自動化端到端測試包含 GitHub webhook 簽章成功/失敗案例。
2. 完成最小權限威脅模型及公開存取安全清單。
3. 快照可還原、Git commit 可回滾，失敗不遺失遊戲程式碼。
4. API 密鑰及私密 Repo 內容不出現在前端 Bundle 或 logs。
5. 無使用者許可不向公共平台部署/公開遊戲。
