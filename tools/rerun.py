import shutil
from pathlib import Path

# ==========================================
# 路徑設定（以執行指令時所在的資料夾為工作目錄）
# ==========================================
WORK_DIR = Path.cwd()
INPUT_DIR = WORK_DIR / "input"
OUTPUT_DIR = WORK_DIR / "output"
LOG_FILE = WORK_DIR / "processed_papers.md"


# ==========================================
# 單篇重跑處理
# ==========================================
def rerun_paper(filename: str) -> bool:
    # 在三個分類資料夾中尋找 PDF
    found_path = None
    for cls in ["A1", "A2", "A3"]:
        candidate = OUTPUT_DIR / cls / "pdf" / filename
        if candidate.exists():
            found_path = candidate
            break

    # 找不到則跳過
    if not found_path:
        print(f"正在處理：{filename}... 找不到，請確認檔名是否正確 ❌")
        return False

    # 把 PDF 移回 input/
    shutil.move(str(found_path), str(INPUT_DIR / filename))

    # 從 processed_papers.md 刪除該筆紀錄
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        new_lines = [line for line in lines if line.strip() != f"- {filename}"]
        LOG_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    print(f"正在處理：{filename}... 完成 ✅")
    return True


# ==========================================
# 主程式
# ==========================================
if __name__ == "__main__":
    filenames = []
    print("請輸入論文檔名（一行一篇，輸入空白行結束）：")
    while True:
        name = input("> ").strip()
        if name == "":
            break
        filenames.append(name)

    if not filenames:
        print("未輸入任何檔名，結束。")
    else:
        success = 0
        failed = 0

        for filename in filenames:
            if rerun_paper(filename):
                success += 1
            else:
                failed += 1

        print(f"\n完成！成功 {success} 篇 / 失敗 {failed} 篇")
        if success > 0:
            print("請執行 python main.py 開始重新處理。")
