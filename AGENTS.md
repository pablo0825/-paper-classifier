<!-- SPECTRA:START v1.0.1 -->

# Spectra Instructions

This project uses Spectra for Spec-Driven Development (SDD). Specs live in `openspec/specs/`, change proposals in `openspec/changes/`.

## Use `$spectra-*` skills when:

- A discussion needs structure before coding -> `$spectra-discuss`
- User wants to plan, propose, or design a change -> `$spectra-propose`
- Tasks are ready to implement -> `$spectra-apply`
- There's an in-progress change to continue -> `$spectra-ingest`
- User asks about specs or how something works -> `$spectra-ask`
- Implementation is done -> `$spectra-archive`

## Workflow

`discuss` -> `propose` -> `apply` -> `ingest` -> `archive`

- `discuss` is optional when requirements are already clear
- If requirements change mid-work, use `ingest` and then resume `apply`

## Parked Changes

Changes can be parked, which means they are temporarily moved out of `openspec/changes/`. Parked changes will not appear in `spectra list`, but can be found with `spectra list --parked`. To restore one, run `spectra unpark <name>`. The `$spectra-apply` and `$spectra-ingest` skills handle parked changes automatically.

<!-- SPECTRA:END -->

# AGENTS.md

## 專案定位

這個專案是以 Python 實作的 PDF 論文處理流程，使用 LangGraph 串接三個節點：

1. `agents/extractor.py`：用 PyMuPDF 擷取 PDF 文字
2. `agents/classifier.py`：呼叫 OpenAI 結構化輸出，將論文分類為 `A1`、`A2`、`A3`
3. `agents/summarizer.py`：根據分類與抽取文字產生摘要欄位

主入口是 `main.py`，流程編排在 `core/orchestrator.py`。

## 主要技術與依賴

- Python `3.12+`
- LangGraph
- `langchain-openai`
- PyMuPDF
- Pydantic v2
- `python-dotenv`
- pytest

依賴版本以 `requirements.txt` 為準，不要用 `pip freeze` 風格覆蓋成大量無關套件。

## 工作目錄約定

此專案會以執行當下的工作目錄作為資料根目錄，不是固定綁在 repo 根目錄。

- `input/`：待處理 PDF
- `output/A1|A2|A3/pdf/`：分類後搬移的 PDF
- `output/A1|A2|A3/summary/`：單篇 Markdown 摘要
- `output/A1|A2|A3/json/`：彙整摘要用的 JSON
- `output/summary_A1.md`、`summary_A2.md`、`summary_A3.md`：各分類總表
- `output/error/`：永久失敗或 dead letter 後移出的 PDF
- `logs/`：`dead_letter.md`、`rebuild_warnings.md`
- `processed_papers.md`：已完成檔名清單
- `error_papers.md`：失敗紀錄
- `error_filenames.md`：失敗檔名清單，供下次掃描排除

修改流程時，不要破壞這套目錄契約，因為 `scan_papers`、`save_results`、`rerun.py` 都依賴這些路徑。

## 執行方式

常用指令：

```powershell
python main.py
python -m pytest
python tools\init.py
python tools\rerun.py
python tools\list_papers.py
```

`main.py` 會先：

- 建立必要資料夾
- 檢查 `prompts/classify_en.md` 與 `prompts/summarize_en.md`
- 檢查 `OPENAI_API_KEY` 與 `OPENAI_MODEL`
- 掃描 `input/*.pdf`
- 先重建分類總表，再執行 LangGraph pipeline

## 環境變數

至少需要：

```env
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

可選價格參數：

```env
PRICE_INPUT=2.5
PRICE_OUTPUT=10.0
```

注意：

- `main.py` 在 import `core.orchestrator` 前就會 `load_dotenv()`
- `core/orchestrator.py` 會在 import 階段讀取 `PRICE_INPUT` / `PRICE_OUTPUT`
- 若調整價格讀取邏輯，必須注意 import 時機，避免 `.env` 尚未載入

## Prompt 與結構化輸出規則

- 分類 prompt 使用 `prompts/classify_en.md`
- 摘要 prompt 使用 `prompts/summarize_en.md`
- `classifier.py` 與 `summarizer.py` 在 module import 時就會讀取 prompt 檔案
- OpenAI 結構化輸出 schema 定義在 `core/schemas.py`

修改時請遵守：

- `ClassifierOutput` 維持 `criterion_1` 到 `criterion_7` 與 `classification`
- `SummarizerOutput` 的欄位名稱必須與 `save_results()`、`FIELD_LABELS`、摘要輸出格式一致
- 若新增或改名摘要欄位，必須同步更新：
  - `core/schemas.py`
  - `core/orchestrator.py` 內的 `FIELD_LABELS` 與 `DISPLAY_FIELDS`
  - prompt 模板
  - 相關測試

## 流程修改規則

這個 repo 的主要狀態結構是 `core/state.py` 的 `PaperState`。修改流程時：

- 保持 state key 與實際資料流一致
- `extracted_text` 長度上限目前是 `50_000` 字元，若調整，需同步檢查 `state.py` 註解與測試預期
- `save_results()` 寫檔時要維持 rollback 邏輯，避免只寫入一半
- `save_results()` 目前會以 `summary = {**state["summary"], "classification": classification}` 避免原地修改 state，這個行為不要退回成 in-place mutation
- `handle_error`、`write_dead_letter`、`handle_permanent_error` 的分工要保持清楚
- `scan_papers()` 會排除 `processed_papers.md` 與 `error_filenames.md` 中的檔名，變更 log 格式時要一併檢查掃描邏輯

## 測試規則

- 測試使用 `pytest`
- 設定在 `pytest.ini`
- 任何修改 pipeline、state、schema、路由或輸出格式的變更，應優先補或更新測試
- 若只改 prompt 或文案，至少確認現有測試是否仍合理

建議優先檢查：

- `tests/test_routes.py`
- `tests/test_scan.py`
- `tests/test_rerun.py`
- `tests/test_integration.py`

## 文件更新規則

當程式行為改動時，應同步檢查是否需要更新：

- `AGENTS.md`
- `CLAUDE.md`
- `docs/design.md`
- `prompts/*.md`
- `requirements.txt`

如果實作已經和文件不一致，應以目前程式碼的真實行為為準更新文件，不要把文件當成舊規格硬套回程式。

## 與 Claude 協作規則

1. **逐段處理**：一次處理一段，確認後再繼續
2. **禁止捏造**：數據、發現與引用必須來自文章、程式碼或你提供的網址；不確定就直接說不知道
3. **一問一答**：遇到多個需要討論的問題時，改用一問一答模式
4. **主動釐清**：若 prompt 不清楚、不明確或模糊空間大，應先釐清再執行
5. **Commit 說明語言**：commit 訊息一律使用繁體中文說明

## Commit Prefix 規則

使用以下通用 prefix：

| Prefix | 用途 |
|--------|------|
| `feat:` | 新功能 |
| `fix:` | 修復 Bug |
| `refactor:` | 重構（無功能變更） |
| `test:` | 測試相關修改 |
| `docs:` | 文件更新 |

補充規則：

- commit 訊息內容一律使用繁體中文
- 每次 commit 只使用一個主要 prefix
- 若同時包含文件與程式碼，請以主要變更目的選擇 prefix
