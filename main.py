import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from core.orchestrator import build_graph, rebuild_summaries
from core.scan import scan_papers
from core.state import PaperState

# 載入 .env 中的 API Key
load_dotenv()

# ==========================================
# 設定 LLM
# ==========================================
PROMPTS_DIR = Path(__file__).parent / "prompts"

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY")
)


def invoke_with_retry(prompt, max_retries=3, wait_seconds=10):
    for attempt in range(max_retries):
        try:
            return llm.invoke([HumanMessage(content=prompt)])
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"LLM 呼叫失敗（{e}），等待 {wait_seconds} 秒後重試...")
                time.sleep(wait_seconds)
            else:
                raise


# ==========================================
# 主程式
# ==========================================
if __name__ == "__main__":
    print("=== 學術論文分類與摘要系統 ===\n")

    # 工作目錄為執行指令時所在的資料夾
    WORK_DIR = Path.cwd()
    print(f"工作目錄：{WORK_DIR}\n")

    # 路徑設定
    INPUT_DIR = WORK_DIR / "input"
    OUTPUT_DIR = WORK_DIR / "output"
    ERROR_DIR = WORK_DIR / "output" / "error"
    LOG_FILE = WORK_DIR / "processed_papers.md"
    ERROR_LOG = WORK_DIR / "error_papers.md"

    # 確保所有資料夾存在（容錯）
    for folder in [
        INPUT_DIR,
        OUTPUT_DIR / "A1" / "pdf", OUTPUT_DIR / "A1" / "summary", OUTPUT_DIR / "A1" / "json",
        OUTPUT_DIR / "A2" / "pdf", OUTPUT_DIR / "A2" / "summary", OUTPUT_DIR / "A2" / "json",
        OUTPUT_DIR / "A3" / "pdf", OUTPUT_DIR / "A3" / "summary", OUTPUT_DIR / "A3" / "json",
        ERROR_DIR,
    ]:
        Path(folder).mkdir(parents=True, exist_ok=True)

    # 確認 prompt 檔案存在
    for prompt_file in [PROMPTS_DIR / "classify_en.md", PROMPTS_DIR / "summarize_en.md"]:
        if not prompt_file.exists():
            print(f"錯誤：找不到 {prompt_file}，請確認 prompts/ 資料夾內容")
            exit(1)

    # 確認 API Key 與模型存在
    if not os.getenv("OPENAI_API_KEY"):
        print("錯誤：找不到 OPENAI_API_KEY，請確認 .env 檔案內容")
        exit(1)
    if not os.getenv("OPENAI_MODEL"):
        print("錯誤：找不到 OPENAI_MODEL，請確認 .env 檔案內容")
        exit(1)

    # 掃描待處理論文
    papers_to_process = scan_papers(INPUT_DIR, LOG_FILE)
    print(f"發現 {len(list(INPUT_DIR.glob('*.pdf')))} 篇論文，其中 {len(papers_to_process)} 篇尚未處理")

    if not papers_to_process:
        print("沒有需要處理的論文。")
        exit(0)

    # 重建總表
    rebuild_summaries(OUTPUT_DIR)

    # 建立 graph
    app = build_graph(invoke_with_retry)

    # 初始 state
    initial_state: PaperState = {
        "papers_to_process": papers_to_process,
        "current_paper": "",
        "thread_id": "",
        "extracted_text": "",
        "classification": "",
        "criteria_met": [],
        "summary": {},
        "processed_count": 0,
        "error_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "paper_input_tokens": 0,
        "paper_output_tokens": 0,
        "retry_count": 0,
        "failed_node": "",
        "error_message": "",
        "input_dir": str(INPUT_DIR),
        "output_dir": str(OUTPUT_DIR),
        "error_dir": str(ERROR_DIR),
        "log_file": str(LOG_FILE),
        "error_log": str(ERROR_LOG),
    }

    # 執行
    result = app.invoke(initial_state)

    total_input = result["total_input_tokens"]
    total_output = result["total_output_tokens"]
    total_cost = (total_input / 1_000_000 * 2.5) + (total_output / 1_000_000 * 10.0)

    print(f"\n=== 完成！共處理 {result['processed_count']} 篇論文 ===")
    print(f"總 Token：輸入 {total_input:,} / 輸出 {total_output:,}")
    print(f"總費用約：${total_cost:.4f} USD")
