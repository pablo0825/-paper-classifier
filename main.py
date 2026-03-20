import os
import time
from pathlib import Path
from dotenv import load_dotenv

# 必須在 core.orchestrator import 之前執行，否則模組層級常數（PRICE_INPUT_PER_M 等）會在 .env 載入前初始化
load_dotenv()

from langchain_openai import ChatOpenAI

from core.orchestrator import build_graph, rebuild_summaries, PRICE_INPUT_PER_M, PRICE_OUTPUT_PER_M
from core.schemas import ClassifierOutput, SummarizerOutput
from core.scan import scan_papers
from core.state import PaperState

# ==========================================
# 主程式
# ==========================================
PROMPTS_DIR = Path(__file__).parent / "prompts"

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
    ERROR_FILENAMES = WORK_DIR / "error_filenames.md"

    # 確保所有資料夾存在（容錯）
    for folder in [
        INPUT_DIR,
        OUTPUT_DIR / "A1" / "pdf", OUTPUT_DIR / "A1" / "summary", OUTPUT_DIR / "A1" / "json",
        OUTPUT_DIR / "A2" / "pdf", OUTPUT_DIR / "A2" / "summary", OUTPUT_DIR / "A2" / "json",
        OUTPUT_DIR / "A3" / "pdf", OUTPUT_DIR / "A3" / "summary", OUTPUT_DIR / "A3" / "json",
        ERROR_DIR,
        WORK_DIR / "logs",
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

    # 驗證通過後才初始化 LLM
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=120,
    )

    classifier_chain = llm.with_structured_output(ClassifierOutput, include_raw=True)
    summarizer_chain = llm.with_structured_output(SummarizerOutput, include_raw=True)

    def make_invoke_with_retry(chain, max_retries=3, wait_seconds=10):
        def invoke(prompt):
            for attempt in range(max_retries):
                try:
                    return chain.invoke(prompt)
                except Exception as e:
                    if attempt < max_retries - 1:
                        error_str = str(e).lower()
                        wait = 60 if ("429" in error_str or "rate_limit" in error_str) else wait_seconds
                        print(f"LLM 呼叫失敗（{e}），等待 {wait} 秒後重試...")
                        time.sleep(wait)
                    else:
                        raise
        return invoke

    # 掃描待處理論文
    all_pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    papers_to_process = scan_papers(INPUT_DIR, LOG_FILE, ERROR_FILENAMES)
    print(f"發現 {len(all_pdfs)} 篇論文，其中 {len(papers_to_process)} 篇尚未處理")

    if not papers_to_process:
        print("沒有需要處理的論文。")
        exit(0)

    # 重建總表
    rebuild_summaries(OUTPUT_DIR)

    # 建立 graph
    app = build_graph(
        make_invoke_with_retry(classifier_chain),
        make_invoke_with_retry(summarizer_chain),
    )

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
        "permanent_error": False,
        "input_dir": str(INPUT_DIR),
        "output_dir": str(OUTPUT_DIR),
        "error_dir": str(ERROR_DIR),
        "log_file": str(LOG_FILE),
        "error_log": str(ERROR_LOG),
    }

    # 執行
    try:
        result = app.invoke(initial_state)
    except Exception as e:
        print(f"\n⚠️  系統發生未預期錯誤：{e}")
        print("已處理論文仍已儲存，可重新執行 python main.py 繼續處理。")
        exit(1)

    total_input = result["total_input_tokens"]
    total_output = result["total_output_tokens"]
    total_cost = (total_input / 1_000_000 * PRICE_INPUT_PER_M) + (total_output / 1_000_000 * PRICE_OUTPUT_PER_M)

    print(f"\n=== 完成！共處理 {result['processed_count']} 篇論文，錯誤 {result['error_count']} 篇 ===")
    print(f"總 Token：輸入 {total_input:,} / 輸出 {total_output:,}")
    print(f"總費用約：${total_cost:.4f} USD")
