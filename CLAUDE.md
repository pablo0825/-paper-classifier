<!-- SPECTRA:START v1.0.1 -->

# Spectra Instructions

This project uses Spectra for Spec-Driven Development(SDD). Specs live in `openspec/specs/`, change proposals in `openspec/changes/`.

## Use `/spectra:*` skills when:

- A discussion needs structure before coding → `/spectra:discuss`
- User wants to plan, propose, or design a change → `/spectra:propose`
- Tasks are ready to implement → `/spectra:apply`
- There's an in-progress change to continue → `/spectra:ingest`
- User asks about specs or how something works → `/spectra:ask`
- Implementation is done → `/spectra:archive`

## Workflow

discuss? → propose → apply ⇄ ingest → archive

- `discuss` is optional — skip if requirements are clear
- Requirements change mid-work? Plan mode → `ingest` → resume `apply`

## Parked Changes

Changes can be parked（暫存）— temporarily moved out of `openspec/changes/`. Parked changes won't appear in `spectra list` but can be found with `spectra list --parked`. To restore: `spectra unpark <name>`. The `/spectra:apply` and `/spectra:ingest` skills handle parked changes automatically.

<!-- SPECTRA:END -->

## 專案概覽

**學術論文自動分類與摘要系統** — 批次處理學術論文 PDF，使用 LangGraph 驅動 AI 工作流程，自動分類（A1/A2/A3）並生成結構化摘要。

### 技術棧

| 類別 | 技術 |
|------|------|
| 語言 | Python 3.12 |
| LLM 框架 | LangGraph 1.1.2 |
| LLM 提供者 | OpenAI API（gpt-5.3-chat-latest） |
| PDF 解析 | PyMuPDF (fitz) |
| 測試 | pytest + GitHub Actions CI |

### 目錄結構

```
main.py               主程式入口
core/
  orchestrator.py     LangGraph graph 構建與路由
  state.py            PaperState TypedDict 定義
  scan.py             掃描 input/ 找出未處理 PDF
agents/
  extractor.py        PDF 文字提取
  classifier.py       論文分類（7 項標準 → A1/A2/A3）
  summarizer.py       生成結構化摘要（10 個欄位）
prompts/
  classify_en.md      分類 prompt（當前使用）
  summarize_en.md     摘要 prompt（當前使用）
tools/
  init.py             初始化工作目錄與 .env
  list_papers.py      查看已處理/錯誤紀錄
  rerun.py            重新處理指定論文
docs/
  design.md           設計決策紀錄
openspec/             Spectra 規格與變更提案
```

### 執行方式

```bash
# 初始化（第一次）
python tools/init.py

# 主程式
python main.py

# 查看紀錄 / 重跑論文
python tools/list_papers.py
python tools/rerun.py
```

Windows 可用 `pa-start.bat` 啟動 venv 並設定 `pa-run`、`pa-list`、`pa-init`、`pa-redo` 等快捷指令。

### 關鍵慣例

- **Prompt 以檔案管理**：分類與摘要 prompt 存放於 `prompts/`，調整標準不需動程式碼
- **增量處理**：`processed_papers.md` 記錄已完成論文，`error_filenames.md` 記錄永久性錯誤
- **輸出結構**：每篇論文產出 `.md` 和 `.json`，按分類存入 `output/A1/A2/A3/`
- **環境設定**：API Key 與模型選擇存於 `.env`（不上傳）

---

## Commit Message 規範

| Prefix | 用途 |
|--------|------|
| `feat:` | 新功能 |
| `fix:` | 修復 Bug |
| `refactor:` | 重構（無功能變更） |
| `test:` | 測試相關修改 |
| `docs:` | 文件更新 |

commit 訊息的說明一律使用**繁體中文**。

## 協作規則

1. **逐段處理**：一次處理一段，展現思考過程，確認後再繼續
2. **禁止捏造**：數據、發現與引用必須來自文章或提供網址中明確記載的內容；若不確定，直接說不知道
3. **一問一答**：遇到需要討論多個問題時，改用一問一答模式，確認後再繼續，避免資訊量過多導致回答品質下降
4. **一步步思考**：在回答前先展示思考過程，確保每一步的推論都清楚可見
5. **主動釐清**：若 prompt 不清楚、不明確或模糊空間大，應要求說明，或透過持續討論明確使用者的意圖與目的，再開始執行
