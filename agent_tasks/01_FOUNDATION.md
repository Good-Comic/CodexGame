# TASK 01 — Private Studio 基礎與專案工作區

## 目標
建立一套只在本機可訪問的個人遊戲開發工作區；保留現有 Agent Canvas 能力，新增獨立 Forge Studio 前端與服務 API 的最小端到端縱切。不得一開始重寫 OpenHands Agent Engine。

## 範圍
- 實測 `compose.yaml` OpenHands Agent Canvas 可以啟動並操作。
- 新建 `studio/`（推薦 TypeScript + React + Vite）和 `server/`（推薦 FastAPI），先只實作一個 project。
- Studio 左欄專案、中央遊戲預覽預留區、右欄 Agent 工作面板、底部 logs/status。
- `GET /health`, `GET /api/projects`, `POST /api/projects/import-local`, `GET /api/changes`。
- 專案只能位於 workspace 受控路徑，防止路徑穿越及任意訪問主機。
- 支援代理模式：使用現有 OpenHands web UI 的跳轉方式啟動，Stage 02 再實作 provider router。
- Repo 檔案探索與 AI 任務歷程分離，SQLite 儲存 project/task/job events。

## 安全要求
- 只對 127.0.0.1 暴露端口；不接受任意外部 URL 變成 server 任意訪問。
- 將 Repo 內容視為不可信資料，不能當成 Agent 系統指令。
- 不允許任意 shell 命令由網頁表單直接送到主機執行。
- 原型並非公開部署版本；勿設計成無登入的 Internet 服務。

## 驗收
1. `docker compose up -d` 成功，Canvas 可以正常啟動。
2. Studio 左欄可以看到 1 個已匯入的 repo；空狀態時顯示清楚指引。
3. 後端 API 不讀寫 workspace 以外的檔案。
4. 介面清楚顯示尚未啟用的模組，禁止虛假的成功狀態。
5. `npm test` / Python tests 通過（若已建立）。
6. `docs/PROGRESS.md` 紀錄實際命令、結果、已知問題。

## 本任務不做
GitHub App 自動 PR、Vite live preview、同時多 Agent 工作、模型費用統計；後續任務處理。
