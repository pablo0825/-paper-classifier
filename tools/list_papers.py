from pathlib import Path


def print_log(filepath: Path):
    if not filepath.exists():
        print(f"找不到 {filepath.name}，尚未有任何紀錄。")
        return

    lines = filepath.read_text(encoding="utf-8").splitlines()
    output = [line for line in lines if line.startswith("## ") or line.startswith("- ")]

    if not output:
        print("目前無任何紀錄。")
        return

    for line in output:
        if line.startswith("## "):
            print()
        print(line)


if __name__ == "__main__":
    print("=== 論文處理紀錄查詢 ===\n")

    # 工作目錄為執行指令時所在的資料夾
    WORK_DIR = Path.cwd()
    LOG_FILE = WORK_DIR / "processed_papers.md"
    ERROR_LOG = WORK_DIR / "error_papers.md"

    print(f"工作目錄：{WORK_DIR}\n")

    while True:
        print("請選擇要查看的紀錄（輸入空白行結束）：")
        print("1. 已處理論文清單")
        print("2. 錯誤論文清單")
        choice = input("> ").strip()

        if choice == "":
            print("結束。")
            break
        elif choice == "1":
            print("\n=== 已處理論文清單 ===\n")
            print_log(LOG_FILE)
        elif choice == "2":
            print("\n=== 錯誤論文清單 ===\n")
            print_log(ERROR_LOG)
        else:
            print("請輸入 1 或 2。")
        print()
