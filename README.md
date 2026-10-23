# Project Forge AI — 私人 AI 遊戲開發工廠（啟動包 v0.1）

本包提供 **可啟動的自架 Agent 基礎環境**、Windows 操作腳本，以及分階段建造專屬遊戲工廠的 Agent 工作檔。
**這不是完整產品**：目前透過 OpenHands Agent Canvas 提供真正的 AI coding agent 工作台；自訂 Studio 控制台、GitHub App 事件雙向同步、持續自動測試與多引擎預覽仍需依任務檔實作。

## 目前能做什麼
- 本機以 Docker Compose 啟動 OpenHands Agent Canvas，瀏覽器 http://127.0.0.1:8000/canvas
- 使用介面配置 Agent 與模型後端（本地 Ollama 或可用的雲端 LLM API）；需依 OpenHands 版本和模型能力設定
- 在隔離的 `workspace/` 中編修 Git 專案（仍須注意 agent 的執行權限）
- 使用 Windows 腳本登入 GitHub 後複製專案、查詢同步狀態
- 對既有 HTML/CSS/JS ES modules 遊戲以 Vite 開啟具熱更新的本機預覽
- 把 `START_AGENT.md` 交給 Agent，依 `agent_tasks/` 逐段完成 Studio 平台

## 啟動（Windows 11 / PowerShell）
先安裝 Docker Desktop（使用 WSL2 Linux containers）、Git、GitHub CLI (`gh`)、Node.js。
1. 將整個資料夾解壓到本機，例如 `D:\\ProjectForgeAI`。
2. 開啟 PowerShell，執行 `cd D:\\ProjectForgeAI`。
3. 執行 `powershell -ExecutionPolicy Bypass -File .\\windows\\START.ps1`。首次啟動須下載 Docker 映像。
4. 瀏覽器打開 http://127.0.0.1:8000/canvas ，依官方說明設置模型及工作空間。
5. 執行 `gh auth login`（使用 GitHub 官方互動式登入，不要把 Token 放在 Agent 提示詞）。
6. 匯入 GitHub 專案：`powershell -File .\\windows\\IMPORT-GITHUB.ps1 -Repo OWNER/REPO`。
7. 啟動遊戲預覽：`powershell -File .\\windows\\START-PREVIEW.ps1 -Project REPO`，於 http://127.0.0.1:4173 開啟。
8. 將 `START_AGENT.md` 內容送入 Agent，**每次只讀一個 task 檔**。

## 啟動（Linux / Debian）

需要 Docker Engine 與 Docker Compose v2。從 repository 根目錄執行：

```bash
docker compose up --build --detach --wait
curl --fail http://127.0.0.1:8080/api/health
```

Studio Web 位於 `http://127.0.0.1:8080/`，能力狀態位於
`http://127.0.0.1:8080/api/capabilities`。若主機有足夠空間且 Docker 使用適合大型映像的儲存驅動，
可另行啟動 OpenHands Agent Canvas：

```bash
docker compose --profile agent up --detach --wait
```

**注意**：在 Windows 的 Docker 容器中，本機 `gh auth` 認證不會自動傳入容器。PowerShell 匯入腳本使用主機 GitHub 認證；要在 Agent 容器內建立 PR，應另外設置最小權限 GitHub App 或安全的 git credentials。切勿把 GH 認證檔直接掛入不受信任的 Agent 容器。

## 與 GitHub 連線的策略
- 第一階段：主機 `gh auth login` + `git clone`，在隔離分支工作；人工確認 push/PR。
- 第二階段：Studio GitHub App，僅授權指定 repo；使用短期 Token、Webhook HMAC 驗證、事件冪等、排程重試。
- 嚴禁 AI 自動 force-push 或直接修改 `main`；通過測試及人類核准後合併。
- **即時更新**包含兩件事：本地檔案熱更新（Vite）和遠端 GitHub webhook 驅動的近即時同步。兩者不同，Webhooks 須可被 GitHub 存取，不能只綁定 localhost。

## 專屬遊戲專案
參見 `game_profiles/RIFTWATCH.md`。當前原型採純 HTML/CSS/JS ES modules，建議保留原框架，先建立測試與回歸工具，再考慮任何重大遷移。

## 安全與權限
- Compose 將服務僅綁定 127.0.0.1；不建議直接公開至外網。
- Docker 沙箱不等於完全無風險；不要將系統磁碟、Docker socket、SSH 金鑰或雲端密鑰掛入 Agent。
- Agent 只能使用指定工作目錄，重大刪改須先建立分支與備份；正式權限隔離需在 Studio 階段實作。
- 只有 HTTPS、認證、權限、審計及 Rate Limit 完成後，才考慮遠端存取。

## 官方參考
- OmGithub: https://omgithub.com/
- OpenHands Agent Canvas: https://github.com/OpenHands/OpenHands
- OpenCode/Ollama: https://docs.opencode.ai/docs/providers/
- GitHub Apps: https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps
- GitHub Webhook 驗證: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries

## 驗收狀態
- [x] 提供 Docker Compose 啟動設定（尚未在使用者電腦實測）
- [x] 提供 Windows 啟動／匯入／預覽指令
- [x] 提供拆分 Agent 任務與驗收條件
- [ ] 實際部署到使用者電腦
- [ ] GitHub App 已授權
- [ ] 新 Studio UI 與多 Agent 排程已開發
- [ ] 即時遠端 webhook 已連上
