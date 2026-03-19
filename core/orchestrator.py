import json
import shutil
from datetime import datetime, date
from pathlib import Path
from langgraph.graph import StateGraph, END

from agents.extractor import extract
from agents.classifier import classify
from agents.summarizer import summarize
from core.state import PaperState

MAX_RETRIES = 3


# ==========================================
# 重建總表
# ==========================================
def rebuild_summaries(output_dir: Path):
    for classification in ["A1", "A2", "A3"]:
        summary_path = output_dir / f"summary_{classification}.md"
        entries = []
        for json_file in sorted((output_dir / classification / "json").glob("*.json")):
            data = json.loads(json_file.read_text(encoding="utf-8"))
            entries.append(f"""
---

## {data["title"]}

- **評分依據**：{data["評分依據"]}
- **主要發現**：{data["主要發現"]}
""")
        summary_path.write_text("".join(entries), encoding="utf-8")


# ==========================================
# Thread ID 產生
# ==========================================
def make_thread_id(paper_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    stem = Path(paper_name).stem
    return f"{timestamp}-{stem}"


# ==========================================
# Node：初始化每篇論文的任務
# ==========================================
def init_paper(state: PaperState) -> PaperState:
    current = state["papers_to_process"][0]
    thread_id = make_thread_id(current)
    return {
        **state,
        "current_paper": current,
        "thread_id": thread_id,
        "retry_count": 0,
        "failed_node": "",
        "error_message": "",
        "paper_input_tokens": 0,
        "paper_output_tokens": 0,
    }


# ==========================================
# Node：執行各 Agent
# ==========================================
def run_extractor(state: PaperState) -> PaperState:
    return extract(state)


def make_run_classifier(llm_invoke):
    def run_classifier(state: PaperState) -> PaperState:
        return classify(state, llm_invoke)
    return run_classifier


def make_run_summarizer(llm_invoke):
    def run_summarizer(state: PaperState) -> PaperState:
        return summarize(state, llm_invoke)
    return run_summarizer


# ==========================================
# Node：錯誤處理（重試計數）
# ==========================================
def handle_error(state: PaperState) -> PaperState:
    retry_count = state["retry_count"] + 1
    print(f"節點 {state['failed_node']} 失敗（第 {retry_count} 次），原因：{state['error_message']}")
    return {**state, "retry_count": retry_count}


# ==========================================
# Node：Dead Letter 處理
# ==========================================
def write_dead_letter(state: PaperState) -> PaperState:
    work_dir = Path(state["input_dir"]).parent
    dead_letter_path = work_dir / "logs" / "dead_letter.md"
    dead_letter_path.parent.mkdir(parents=True, exist_ok=True)

    today = date.today().strftime("%Y-%m-%d")
    existing = dead_letter_path.read_text(encoding="utf-8") if dead_letter_path.exists() else ""

    with open(dead_letter_path, "a", encoding="utf-8") as f:
        if f"## {today}" not in existing:
            f.write(f"## {today}\n\n")
        f.write(f"- thread_id: {state['thread_id']}\n")
        f.write(f"  failed_node: {state['failed_node']}\n")
        f.write(f"  reason: {state['error_message']}\n")
        f.write(f"  retries: {state['retry_count']}\n\n")

    print(f"已記錄至 dead letter：{state['current_paper']}")

    remaining = state["papers_to_process"][1:]
    return {
        **state,
        "papers_to_process": remaining,
        "error_count": state["error_count"] + 1,
    }


# ==========================================
# Node：儲存結果
# ==========================================
def save_results(state: PaperState) -> PaperState:
    output_dir = Path(state["output_dir"])
    input_dir = Path(state["input_dir"])
    log_file = Path(state["log_file"])
    current = state["current_paper"]
    classification = state["classification"]
    summary = state["summary"]

    title = summary.get("論文標題", current)

    # 清除其他分類資料夾中的同名舊檔案
    stem = Path(current).stem
    for cls in ["A1", "A2", "A3"]:
        for old_file in [
            output_dir / cls / "summary" / f"{stem}.md",
            output_dir / cls / "json" / f"{stem}.json",
        ]:
            if old_file.exists():
                old_file.unlink()

    # 生成個別摘要 .md
    md_content = f"""# {title}

| 欄位 | 內容 |
|------|------|
| APA7引用 | {summary.get("APA7引用", "")} |
| 分類結果 | {classification} |
| 評分依據 | {summary.get("評分依據", "")} |
| 研究目的 | {summary.get("研究目的", "")} |
| 研究方法 | {summary.get("研究方法", "")} |
| 研究模型 | {summary.get("研究模型", "")} |
| 主要發現 | {summary.get("主要發現", "")} |
| 研究貢獻 | {summary.get("研究貢獻", "")} |
| 研究限制 | {summary.get("研究限制", "")} |
"""
    md_filename = stem + ".md"
    cls_folder = classification if classification in ["A1", "A2", "A3"] else "A3"
    md_path = output_dir / cls_folder / "summary" / md_filename
    md_path.write_text(md_content, encoding="utf-8")

    # 儲存總表重建用的 .json
    json_filename = stem + ".json"
    json_path = output_dir / classification / "json" / json_filename
    json_data = {
        "title": title,
        "評分依據": summary.get("評分依據", ""),
        "主要發現": summary.get("主要發現", ""),
    }
    json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 移動 PDF 到對應資料夾
    src = input_dir / current
    dst = output_dir / classification / "pdf" / current
    try:
        shutil.move(str(src), str(dst))
    except FileNotFoundError as e:
        return {
            **state,
            "failed_node": "save_results",
            "error_message": str(e),
        }

    # 更新 processed_papers.md
    if state["processed_count"] == 0:
        today = date.today().strftime("%Y-%m-%d")
        existing = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
    else:
        today = None
        existing = ""

    with open(log_file, "a", encoding="utf-8") as f:
        if today and f"## {today}" not in existing:
            f.write(f"\n## {today}\n\n")
        f.write(f"- {current}\n")

    # 從待處理清單移除目前這篇
    remaining = state["papers_to_process"][1:]
    count = state["processed_count"] + 1

    paper_input = state["paper_input_tokens"]
    paper_output = state["paper_output_tokens"]
    cost = (paper_input / 1_000_000 * 2.5) + (paper_output / 1_000_000 * 10.0)

    print(f"已完成：{current}，分類：{classification}")
    print(f"本篇 Token：輸入 {paper_input:,} / 輸出 {paper_output:,} / 費用約 ${cost:.4f}")

    return {**state, "papers_to_process": remaining, "processed_count": count}


# ==========================================
# 條件判斷
# ==========================================
def route_after_agent(state: PaperState) -> str:
    if state["failed_node"]:
        return "handle_error"
    return "continue"


def route_after_error(state: PaperState) -> str:
    if state["retry_count"] >= MAX_RETRIES:
        return "write_dead_letter"
    return state["failed_node"]


def should_continue(state: PaperState) -> str:
    if state["papers_to_process"]:
        return "init_paper"
    return END


# ==========================================
# 建立 Graph
# ==========================================
def build_graph(llm_invoke):
    graph = StateGraph(PaperState)

    graph.add_node("init_paper", init_paper)
    graph.add_node("run_extractor", run_extractor)
    graph.add_node("run_classifier", make_run_classifier(llm_invoke))
    graph.add_node("run_summarizer", make_run_summarizer(llm_invoke))
    graph.add_node("handle_error", handle_error)
    graph.add_node("write_dead_letter", write_dead_letter)
    graph.add_node("save_results", save_results)

    graph.set_entry_point("init_paper")

    graph.add_edge("init_paper", "run_extractor")

    graph.add_conditional_edges("run_extractor", route_after_agent, {
        "handle_error": "handle_error",
        "continue": "run_classifier",
    })

    graph.add_conditional_edges("run_classifier", route_after_agent, {
        "handle_error": "handle_error",
        "continue": "run_summarizer",
    })

    graph.add_conditional_edges("run_summarizer", route_after_agent, {
        "handle_error": "handle_error",
        "continue": "save_results",
    })

    graph.add_conditional_edges("handle_error", route_after_error, {
        "extractor": "run_extractor",
        "classifier": "run_classifier",
        "summarizer": "run_summarizer",
        "write_dead_letter": "write_dead_letter",
    })

    graph.add_conditional_edges("write_dead_letter", should_continue, {
        "init_paper": "init_paper",
        END: END,
    })

    graph.add_conditional_edges("save_results", should_continue, {
        "init_paper": "init_paper",
        END: END,
    })

    return graph.compile()
