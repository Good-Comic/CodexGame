# TASK 02 — 可切換本地／雲端 AI 模型與 Agent

## 目標
使用者能在 Forge Studio 選擇模型提供者與 Agent 類型，不必修改遊戲源碼。

## 設計
- 首批提供者：Ollama 本機 OpenAI-compatible endpoint、OpenAI-compatible API、OpenHands 既有 providers。
- Agents：優先銜接 OpenHands 的 agent backend；OpenCode/其他 ACP agents 作為擴充 adapter，不能假設所有模型都支援完整 agent 工具呼叫。
- UI 顯示 Provider、Model ID、連線狀態、Context Window（確認可用才顯示）、費用提示、操作模式（plan/edit/test）。
- 建立 provider capability registry：tool calls / vision / context / JSON support 等，未知值顯示 Unknown。
- 設置連線測試，不得暴露 API key；儲存於操作系統密鑰管理或受限 server vault，不寫入 repo、log、瀏覽器 localStorage。
- 支援 fallback model，但切換必須保留工作狀態與任務摘要。

## 重要觀察
部分 local LLM 不擅長長程工具調用，即使 API 相容也不代表 Agent 能成功操作。先建立模型能力檢驗：讀取小檔、修改小函式、跑測試、回報 diffs。

## 驗收
1. 不重啟 Studio 即可切換一個可用的 Ollama 模型與一個自行配置的 API provider。
2. API key 從不經由 GET 端點、瀏覽器或任何 log 回傳。
3. Agent 失敗時清楚顯示原因和 retry，不能假裝已完成提交。
4. 模型不支援 tool call 時適時降級到純規劃模式。
5. 單次 Agent task 支援讀取檔案索引/摘要，不把整個大型 spec 丟進 context。
