## Context

目前 `save_results`（`core/orchestrator.py`）將輸出檔案寫入固定路徑 `output/<cls>/pdf/`、`output/<cls>/json/`、`output/<cls>/summary/`。隨著使用次數增加，不同批次的論文混放在同一層，使用者難以追蹤閱讀進度。

`processed_papers.md` 已以 `## YYYY-MM-DD` 段落記錄每篇論文的處理日期，可作為遷移舊資料的唯一依據。

## Goals / Non-Goals

**Goals:**

- 新輸出路徑加入日期層：`output/<cls>/YYYY-MM-DD/<type>/`
- `rebuild_summaries` 能正確跨日期資料夾掃描
- 提供一次性遷移工具，依 `processed_papers.md` 將舊檔移入日期資料夾
- 不影響現有的錯誤處理、retry、dead letter 邏輯

**Non-Goals:**

- 不更動 `input/`、`output/error/`、`logs/` 結構
- 遷移工具不處理 `processed_papers.md` 以外的論文（無法對應日期者原地保留）
- 不改動 `processed_papers.md` 格式

## Decisions

### 日期取自 `date.today()`

在 `save_results` 執行時取當天日期，與 `append_log` 寫入 `processed_papers.md` 的日期邏輯保持一致。

**替代方案**：從 PDF metadata 讀取日期 → 增加解析複雜度且不可靠，不採用。

### rebuild_summaries 改用 `*/json/*.json` glob

原本的 `(output_dir / cls / "json").glob("*.json")` 在加入日期層後會找不到任何檔案。改為 `(output_dir / cls).glob("*/json/*.json")` 即可跨所有日期資料夾掃描，無需知道具體日期。

### 遷移腳本以「最後一次出現的日期」為準

若同一篇論文在 `processed_papers.md` 中出現多次（例如曾使用 `rerun`），磁碟上的檔案是最後一次處理的結果，應對應最後一次的日期，避免日期與內容不一致。

解析邏輯：從頭到尾掃描，每次遇到同一 stem 就覆蓋記錄，掃描結束後保留最後一筆。

### `init.py` / `main.py` 移除預建固定子資料夾

原本預建 `A1/pdf/`、`A1/summary/`、`A1/json/` 等固定路徑，改為日期資料夾後這些路徑不再固定。`save_results` 已使用 `mkdir(parents=True, exist_ok=True)` 動態建立，預建邏輯移除即可，不影響執行。

## Risks / Trade-offs

- **遷移後舊路徑殘留空資料夾**：`pdf/`、`summary/`、`json/` 空資料夾會留在原位。遷移腳本執行後提示使用者手動確認並刪除，不自動清除（避免誤刪非遷移資料）。
- **`rerun` 跨日期覆寫**：若使用者在 2026-04-20 重新處理某篇 2026-04-14 的論文，新檔寫入 `2026-04-20/`，舊的 `2026-04-14/` 資料夾中的同名檔案需一併清除。`save_results` 已有清除其他分類舊檔的邏輯，需擴展為清除**所有日期子資料夾**中的同名檔案。
- **`rebuild_summaries` 掃描範圍變大**：跨日期掃描不影響功能，但若日期資料夾很多，glob 耗時略增，可接受。
