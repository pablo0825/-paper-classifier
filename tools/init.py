from pathlib import Path

MODELS = [
    "gpt-5.3-chat-latest",
    "gpt-5.1",
    "gpt-5.2-chat-latest",
]

PROJECT_DIR = Path(__file__).parent.parent


def setup_env():
    env_path = PROJECT_DIR / ".env"

    # 檢查 .env 是否已存在
    if env_path.exists():
        answer = input(".env 已存在，是否覆蓋？(y/n) > ").strip().lower()
        if answer != "y":
            print("已跳過 .env 設定。")
            return

    # 詢問 API Key
    api_key = input("\n請貼入 OpenAI API Key：\n> ").strip()
    if not api_key:
        print("未輸入 API Key，已跳過 .env 設定。")
        return

    # 詢問模型
    print("\n請選擇模型：")
    for i, model in enumerate(MODELS, 1):
        print(f"  {i}. {model}")

    choice = input("> ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(MODELS)):
        print("無效選擇，已跳過 .env 設定。")
        return

    model = MODELS[int(choice) - 1]

    # 寫入 .env
    env_path.write_text(
        f"OPENAI_API_KEY={api_key}\n"
        f"OPENAI_MODEL={model}\n",
        encoding="utf-8",
    )
    print(f"\n已建立 .env（模型：{model}）✅")


if __name__ == "__main__":
    WORK_DIR = Path.cwd()
    print(f"工作目錄：{WORK_DIR}\n")

    # 建立資料夾結構
    folders = [
        WORK_DIR / "input",
        WORK_DIR / "output" / "A1" / "pdf",
        WORK_DIR / "output" / "A1" / "summary",
        WORK_DIR / "output" / "A1" / "json",
        WORK_DIR / "output" / "A2" / "pdf",
        WORK_DIR / "output" / "A2" / "summary",
        WORK_DIR / "output" / "A2" / "json",
        WORK_DIR / "output" / "A3" / "pdf",
        WORK_DIR / "output" / "A3" / "summary",
        WORK_DIR / "output" / "A3" / "json",
        WORK_DIR / "output" / "error",
        WORK_DIR / "logs",
    ]

    for folder in folders:
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            print(f"已建立：{folder.relative_to(WORK_DIR)}")
        else:
            print(f"已存在：{folder.relative_to(WORK_DIR)}")

    # 設定 .env
    print()
    setup_env()

    print("\n初始化完成，請將 PDF 放入 input\\ 後執行 pa-run")
