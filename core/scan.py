from pathlib import Path


def scan_papers(input_dir: Path, log_file: Path, error_filenames: Path) -> list:
    # 讀取已處理的論文清單
    processed = set()
    if log_file.exists():
        for line in log_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("- "):
                processed.add(line[2:].strip())

    # 讀取已知永久性錯誤的論文清單（格式與 processed_papers.md 相同）
    if error_filenames.exists():
        for line in error_filenames.read_text(encoding="utf-8").splitlines():
            if line.startswith("- "):
                processed.add(line[2:].strip())

    # 找出所有 PDF，過濾已處理與已知錯誤的
    all_pdfs = [f.name for f in sorted(input_dir.glob("*.pdf"))]
    return [pdf for pdf in all_pdfs if pdf not in processed]
