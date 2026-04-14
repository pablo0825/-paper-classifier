## 1. 修改 core/orchestrator.py

- [x] 1.1 在 `save_results` 中加入 `today = date.today().strftime("%Y-%m-%d")`（日期取自 `date.today()`），並更新 `dst`、`md_path`、`json_path` 三條路徑，使其符合「output path includes processing date」規格（新增日期層）
- [x] 1.2 將 `save_results` 中清除其他分類舊檔的迴圈（第 356-368 行）改為跨所有日期子資料夾掃描，以符合「rerun clears stale files from all date subfolders」規格
- [x] 1.3 rebuild_summaries 改用 `*/json/*.json` glob：將 `rebuild_summaries` 的 glob 從 `(output_dir / cls / "json").glob("*.json")` 改為 `(output_dir / cls).glob("*/json/*.json")`，以符合「summary rebuild scans across all date subfolders」規格

## 2. 移除靜態子資料夾的預建邏輯

- [x] 2.1 `init.py` / `main.py` 移除預建固定子資料夾：在 `tools/init.py` 的 `folders` 清單中，移除所有 `A1/pdf`、`A1/summary`、`A1/json`、`A2/pdf`、`A2/summary`、`A2/json`、`A3/pdf`、`A3/summary`、`A3/json` 項目（日期資料夾由 `save_results` 動態建立）
- [x] 2.2 在 `main.py` 的容錯目錄建立迴圈中，同樣移除上述九個靜態子資料夾項目（`init.py` / `main.py` 移除預建固定子資料夾）

## 3. 新增遷移工具 tools/migrate.py

- [x] 3.1 實作 `parse_processed_papers(log_file)` 函式：解析 `processed_papers.md`，回傳 `{stem: date_str}` 字典；遷移腳本以「最後一次出現的日期」為準，同一 stem 出現多次時保留最後一筆，以符合「migration script reads processed_papers.md to determine dates」規格
- [x] 3.2 實作 `find_paper_files(output_dir, stem)` 函式：在 `output/A1/pdf/`、`output/A1/json/`、`output/A1/summary/` 等舊平層路徑中，找出該 stem 對應的所有檔案，回傳 `(cls, type, filepath)` 清單
- [x] 3.3 實作 `migrate_paper(output_dir, stem, date_str, files)` 函式：建立目標日期資料夾並移動每個檔案，以符合「migration moves files from old flat structure to date subfolders」規格；找不到檔案時印出警告並跳過
- [x] 3.4 在 `__main__` 區塊中：以 `WORK_DIR = Path.cwd()` 取得工作目錄（與 `main.py`、`tools/list_papers.py` 相同模式），讀取 `processed_papers.md` → 逐一遷移 → 印出移動數量與未找到數量，並提示使用者手動刪除空資料夾，以符合「migration script reports summary and prompts cleanup」規格

## 4. 更新 pa-start.bat

- [x] 4.1 在 `pa-start.bat` 中新增 `doskey pa-migrate=python C:\Users\owner\Documents\project\2026-03-PDFagent\tools\migrate.py`，並在 echo 說明區塊補上 `pa-migrate - migrate old output to date folders`
