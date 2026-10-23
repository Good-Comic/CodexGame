# 產品需求概要 — Project Forge AI

## 核心目標
打造類似 OmGithub 的遊戲創作體驗，但平台「私人擁有、可自架、可自由選模型／Agent、綁定 GitHub、持續測試、持續迭代」。

## 使用者故事
- 身為創作者，我可以選擇本機 Ollama 或 API 模型來和 AI Agent 對話，不受單一家平台限制。
- 身為創作者，我可以連到自己選定的 GitHub 私人/公開 Repo，匯入既有遊戲並開始修改。
- 身為創作者，我修改需求後，Agent 能讀取適當規格章節、編修程式並顯示 diff。
- 身為創作者，我可以立即遊玩修改後的 Web 遊戲並看到錯誤、性能與自動測試結果。
- 身為創作者，我希望 AI 主動拆解後續需求，但不能在無審核時破壞穩定分支。
- 身為創作者，我可以在模型切換、失敗重試或中止後繼續未完成任務。

## 六大模組與基本狀態
| 模組 | MVP 基本功能 | 後續階段 |
|---|---|---|
| Game Projects | clone/import/list, project profile | 多 repo 和多引擎 |
| AI Agent | OpenHands Canvas | 多 Agent router / 批量佇列 |
| Models | 於 Canvas 設定 local/API model | Studio 統一模型切換、費用與能力識別 |
| GitHub Sync | gh CLI 主機登入 + git fetch | GitHub App + Webhooks + PR |
| Preview | Vite 本地預覽 | 遊戲內嵌、Playwright、自動截圖 |
| Quality | 手動執行測試與 PR review | 完整自動 Regression、快照、回滾 |

## 不在 MVP 的承諾
- 目前並未實際登入 GitHub 或取得使用者 Token。
- 不能承諾任何 local model 都能完成複雜 Agent coding。
- 所謂即時 GitHub 同步不是無條件改動 main；預設以 feature branch/PR 工作。
- 不能宣稱完全離線同時又能雲端 API 或 GitHub 即時同步。
- 不對尚未載入完整企劃的 v3.0 功能做 100% parity 承諾。

## 預設工程堆疊
- 首期：Docker Desktop + OpenHands Agent Canvas + Git / gh CLI + Vite。
- Studio UI：React + TypeScript；API：FastAPI；metadata：SQLite（先個人版），後期可用 Postgres。
- Queue：先單 Agent job，之後 Redis queue/worker；sandbox per job。
- GitHub：GitHub App + Webhooks + PR + Git worktrees。
- 支援引擎：先 HTML/CSS/JS ES Modules，後 Godot；Unity 視本機安裝條件擴充。
