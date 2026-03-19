from pathlib import Path


def scan_papers(input_dir: Path, log_file: Path) -> list:
    # 讀取已處理的論文清單
    processed = set()
    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("- "):
                processed.add(line[2:].strip())

    # 找出所有 PDF，過濾已處理的
    all_pdfs = [f.name for f in input_dir.glob("*.pdf")]
    new_pdfs = [pdf for pdf in all_pdfs if pdf not in processed]

    return new_pdfs
