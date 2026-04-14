import shutil
from pathlib import Path


def parse_processed_papers(log_file: Path) -> dict:
    """解析 processed_papers.md，回傳 {stem: date_str}。
    同一篇論文出現多次時，保留最後一次（最近日期）。
    """
    mapping = {}
    current_date = None

    if not log_file.exists():
        return mapping

    for line in log_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current_date = line[3:].strip()
        elif line.startswith("- ") and current_date:
            filename = line[2:].strip()
            stem = Path(filename).stem
            mapping[stem] = current_date  # 後出現的覆蓋前面的

    return mapping


def find_paper_files(output_dir: Path, stem: str) -> list:
    """在舊平層路徑尋找論文的輸出檔案。
    回傳 [(cls, file_type, filepath), ...] 清單。
    """
    found = []
    for cls in ["A1", "A2", "A3"]:
        for file_type, filename in [
            ("pdf", f"{stem}.pdf"),
            ("json", f"{stem}.json"),
            ("summary", f"{stem}.md"),
        ]:
            candidate = output_dir / cls / file_type / filename
            if candidate.exists():
                found.append((cls, file_type, candidate))
    return found


def migrate_paper(output_dir: Path, stem: str, date_str: str, files: list) -> int:
    """將找到的檔案搬移至日期資料夾，回傳成功搬移的數量。"""
    moved = 0
    for cls, file_type, filepath in files:
        target_dir = output_dir / cls / date_str / file_type
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / filepath.name
        try:
            shutil.move(str(filepath), str(target))
            moved += 1
        except Exception as e:
            print(f"  警告：無法移動 {filepath.name}（{e}），跳過")
    return moved


if __name__ == "__main__":
    print("=== 輸出資料夾遷移工具 ===\n")

    WORK_DIR = Path.cwd()
    OUTPUT_DIR = WORK_DIR / "output"
    LOG_FILE = WORK_DIR / "processed_papers.md"

    print(f"工作目錄：{WORK_DIR}\n")

    # 解析日期對應表
    stem_to_date = parse_processed_papers(LOG_FILE)
    if not stem_to_date:
        print("processed_papers.md 不存在或無紀錄，無需遷移。")
        exit(0)

    print(f"找到 {len(stem_to_date)} 篇論文的日期紀錄，開始遷移...\n")

    total_moved = 0
    total_not_found = 0

    for stem, date_str in stem_to_date.items():
        files = find_paper_files(OUTPUT_DIR, stem)
        if not files:
            print(f"未找到：{stem}（可能已遷移或不存在）")
            total_not_found += 1
            continue
        moved = migrate_paper(OUTPUT_DIR, stem, date_str, files)
        total_moved += moved
        print(f"已遷移：{stem} → {date_str}/ （{moved} 個檔案）")

    print(f"\n=== 遷移完成 ===")
    print(f"成功移動：{total_moved} 個檔案")
    print(f"未找到：{total_not_found} 篇")
    print("""
請手動確認並刪除以下空資料夾（若已清空）：
  output/A1/pdf/
  output/A1/json/
  output/A1/summary/
  output/A2/pdf/
  output/A2/json/
  output/A2/summary/
  output/A3/pdf/
  output/A3/json/
  output/A3/summary/
""")
