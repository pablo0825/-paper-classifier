## Why

目前輸出資料夾（`output/A1/`、`output/A2/`、`output/A3/`）不論新舊論文都混放在一起，使用者無法快速判斷某篇論文是哪一天處理的，導致新舊論文容易混淆。加入日期子資料夾後，使用者可依日期瀏覽，清楚辨識閱讀進度。

## What Changes

- 輸出路徑結構從 `output/A1/pdf/` 改為 `output/A1/YYYY-MM-DD/pdf/`（json / summary 同理）
- 日期取自每篇論文的**處理當天**（`date.today()`）
- `rebuild_summaries` 的 glob 改為跨日期資料夾掃描（`*/json/*.json`）
- `tools/init.py` 與 `main.py` 不再預先建立 `pdf/`、`summary/`、`json/` 固定子資料夾（改為執行時動態建立）
- 新增 `tools/migrate.py`：讀取現有 `processed_papers.md`，將舊有輸出檔案搬移至對應日期資料夾

## Non-Goals

- 不更動 `input/`、`output/error/`、`logs/` 的結構
- 遷移腳本只處理 `processed_papers.md` 中有紀錄的論文；無法對應到日期的檔案不移動
- 不更動 `processed_papers.md` 本身的格式

## Capabilities

### New Capabilities

- `date-folder-output`: 輸出路徑加入 YYYY-MM-DD 日期層，新舊批次可依日期區分
- `migrate-to-date-folder`: 一次性遷移工具，將舊有輸出搬入日期資料夾

### Modified Capabilities

（無現有 spec，不適用）

## Impact

- Affected code:
  - `core/orchestrator.py`（`save_results`、`rebuild_summaries`）
  - `tools/init.py`（移除預建固定子資料夾）
  - `main.py`（移除預建固定子資料夾）
  - `tools/migrate.py`（新增）
