import json
import os
import shutil
from datetime import datetime, date
from pathlib import Path
from langgraph.graph import StateGraph, END

# 定價常數（可在 .env 設定 PRICE_INPUT / PRICE_OUTPUT 覆寫，單位：美元 / 百萬 token）
PRICE_INPUT_PER_M  = float(os.getenv("PRICE_INPUT",  "2.5"))
PRICE_OUTPUT_PER_M = float(os.getenv("PRICE_OUTPUT", "10.0"))

from agents.extractor import extract
from agents.classifier import classify
from agents.summarizer import summarize
from core.state import PaperState

MAX_RETRIES = 3

# 摘要欄位：英文 key（LLM 輸出）→ 中文標籤（顯示給使用者）
FIELD_LABELS = {
    "title":          "論文標題",
    "apa7_citation":  "APA7引用",
    "classification": "分類結果",
    "scoring_basis":  "評分依據",
    "objective":      "研究目的",
    "method":         "研究方法",
    "research_model": "研究模型",
    "findings":       "主要發現",
    "contribution":   "研究貢獻",
    "limitations":    "研究限制",
}

# md 摘要表格的顯示順序（title 作為標題、classification 從 state 取，均不在此列）
DISPLAY_FIELDS = [
    "apa7_citation",
    "scoring_basis",
    "objective",
    "method",
    "research_model",
    "findings",
    "contribution",
    "limitations",
]


# ==========================================
# 共用 Log 寫入工具
# ==========================================
def append_log(path: Path, entry: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().strftime("%Y-%m-%d")
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    with open(path, "a", encoding="utf-8") as f:
        if f"## {today}" not in existing:
            f.write(f"\n## {today}\n\n")
        f.write(entry)


# ==========================================
# 重建總表
# ==========================================
def rebuild_summaries(output_dir: Path, only: str = None):
    targets = [only] if only else ["A1", "A2", "A3"]
    for classification in targets:
        summary_path = output_dir / f"summary_{classification}.md"
        entries = []
        for json_file in sorted((output_dir / classification / "json").glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                entries.append(f"""
---

## {data["title"]}

- **評分依據**：{data["scoring_basis"]}
- **主要發現**：{data["findings"]}
""")
            except Exception as e:
                print(f"警告：總表重建時跳過 {json_file.name}（{e}）")
                warnings_path = output_dir.parent / "logs" / "rebuild_warnings.md"
                append_log(warnings_path, f"- {classification}/json/{json_file.name}（{e}）\n")
        if entries:
            summary_path.write_text("".join(entries), encoding="utf-8")
        else:
            summary_path.unlink(missing_ok=True)


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
        "permanent_error": False,
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
# Node：永久性錯誤處理（不重試，直接跳過）
# ==========================================
def handle_permanent_error(state: PaperState) -> PaperState:
    current = state["current_paper"]
    error_dir = Path(state["error_dir"])
    pdf_path = Path(state["input_dir"]) / current

    print(f"跳過：{current}（{state['error_message']}）")

    # 先寫入 error_papers.md，確保錯誤一定有記錄
    error_log = Path(state["error_log"])
    error_filenames = error_log.parent / "error_filenames.md"
    append_log(error_log, f"- {current}（{state['error_message']}）\n")

    # 再嘗試搬移 PDF 到 output/error/
    try:
        shutil.move(str(pdf_path), str(error_dir / current))
    except Exception as e:
        print(f"警告：無法移動 {current} 到 error 資料夾（{e}），PDF 保留在 input/，下次執行將重試")
        append_log(error_log, f"- {current}（搬移至 error 資料夾失敗：{e}，PDF 保留在 input/）\n")
        # 搬移失敗：不寫 error_filenames.md，讓下次 scan_papers 繼續掃到重試
        return {
            **state,
            "papers_to_process": state["papers_to_process"][1:],
            "failed_node": "",
            "error_message": "",
            "permanent_error": False,
        }

    # 搬移成功：寫入 error_filenames.md 排除下次掃描，正式結案
    append_log(error_filenames, f"- {current}\n")
    return {
        **state,
        "papers_to_process": state["papers_to_process"][1:],
        "error_count": state["error_count"] + 1,
        "failed_node": "",
        "error_message": "",
        "permanent_error": False,
    }


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
    dead_letter_entry = (
        f"- thread_id: {state['thread_id']}\n"
        f"  failed_node: {state['failed_node']}\n"
        f"  reason: {state['error_message']}\n"
        f"  retries: {state['retry_count']}\n\n"
    )
    append_log(dead_letter_path, dead_letter_entry)

    print(f"已記錄至 dead letter：{state['current_paper']}")

    # 寫入 error_papers.md
    node_descriptions = {
        "extractor": "PDF 讀取失敗",
        "classifier": "論文分類失敗",
        "summarizer": "摘要生成失敗",
        "save_results": "結果儲存失敗",
    }
    node_desc = node_descriptions.get(state["failed_node"], "處理失敗")
    reason = f"{node_desc}：{state['error_message']}"
    error_log = Path(state["error_log"])
    append_log(error_log, f"- {state['current_paper']}（{reason}）\n")

    # 嘗試搬移 PDF 至 output/error/
    # 搬移成功才寫入 error_filenames.md，確保排除清單與 PDF 實際位置一致
    # 搬移失敗時不寫 error_filenames.md，PDF 留在 input/，下次 scan_papers 自然撿到重試
    pdf_path = Path(state["input_dir"]) / state["current_paper"]
    error_dir = Path(state["error_dir"])
    try:
        shutil.move(str(pdf_path), str(error_dir / state["current_paper"]))
        append_log(error_log.parent / "error_filenames.md", f"- {state['current_paper']}\n")
        moved = True
    except Exception as e:
        print(f"警告：無法移動 {state['current_paper']} 到 error 資料夾（{e}），PDF 保留在 input/，下次執行將重試")
        moved = False

    remaining = state["papers_to_process"][1:]
    return {
        **state,
        "papers_to_process": remaining,
        "error_count": state["error_count"] + (1 if moved else 0),
    }


def _rollback_files(md_path, old_md, md_written, json_path, old_json, json_written):
    """save_results 失敗時還原或刪除已寫入的 md/json 檔案。"""
    if json_written:
        if old_json is not None:
            try:
                json_path.write_text(old_json, encoding="utf-8")
            except Exception:
                json_path.unlink(missing_ok=True)
        else:
            json_path.unlink(missing_ok=True)
    if md_written:
        if old_md is not None:
            try:
                md_path.write_text(old_md, encoding="utf-8")
            except Exception:
                md_path.unlink(missing_ok=True)
        else:
            md_path.unlink(missing_ok=True)


# ==========================================
# Node：儲存結果
# ==========================================
def save_results(state: PaperState) -> PaperState:
    output_dir = Path(state["output_dir"])
    input_dir = Path(state["input_dir"])
    log_file = Path(state["log_file"])
    current = state["current_paper"]
    classification = state["classification"]
    # classifier 的分類結果為唯一權威來源，覆蓋 summarizer 可能輸出的不同值
    summary = {**state["summary"], "classification": classification}
    title = summary.get("title", current)
    stem = Path(current).stem
    cls_folder = classification if classification in ["A1", "A2", "A3"] else "A3"

    src = input_dir / current
    dst = output_dir / cls_folder / "pdf" / current
    md_path = output_dir / cls_folder / "summary" / (stem + ".md")
    json_path = output_dir / cls_folder / "json" / (stem + ".json")

    md_written = False
    json_written = False
    pdf_moved = False

    # 備份現有檔案內容（rerun 同分類時，rollback 可恢復舊資料）
    try:
        old_md = md_path.read_text(encoding="utf-8") if md_path.exists() else None
    except Exception:
        old_md = None
    try:
        old_json = json_path.read_text(encoding="utf-8") if json_path.exists() else None
    except Exception:
        old_json = None

    try:
        # 確保目錄存在，避免 write_text 因目錄不存在而丟出 FileNotFoundError
        # 讓 FileNotFoundError 只剩 shutil.move（PDF 遺失）能觸發，語意精確
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. 寫入個別摘要 .md
        # 跳脫 | 避免破壞 markdown table 格式
        s = {k: str(v).replace("|", "\\|") for k, v in summary.items()}
        title_safe = str(title).replace("|", "\\|")
        field_rows = "\n".join(
            f"| {FIELD_LABELS[k]} | {s.get(k, '')} |"
            for k in DISPLAY_FIELDS
        )
        md_content = f"""# {title_safe}

| 欄位 | 內容 |
|------|------|
| 分類結果 | {classification} |
{field_rows}
"""
        md_path.write_text(md_content, encoding="utf-8")
        md_written = True

        # 2. 寫入總表重建用的 .json
        json_data = {
            "title":         title,
            "scoring_basis": summary.get("scoring_basis", ""),
            "findings":      summary.get("findings", ""),
        }
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
        json_written = True

        # 3. 搬移 PDF
        shutil.move(str(src), str(dst))
        pdf_moved = True

        # 4. 更新 processed_papers.md
        append_log(log_file, f"- {current}\n")

    except FileNotFoundError as e:
        # PDF 不存在（永久性錯誤，不重試）：rollback 已寫入的檔案
        _rollback_files(md_path, old_md, md_written, json_path, old_json, json_written)
        return {
            **state,
            "failed_node": "save_results",
            "error_message": f"儲存時找不到 PDF（{e}）",
            "permanent_error": True,
        }

    except Exception as e:
        # 其他 I/O 錯誤（暫時性，可重試）：rollback 所有已完成步驟
        if pdf_moved:
            try:
                shutil.move(str(dst), str(src))
            except Exception:
                pass
        _rollback_files(md_path, old_md, md_written, json_path, old_json, json_written)
        return {
            **state,
            "failed_node": "save_results",
            "error_message": str(e),
            "permanent_error": False,
        }

    # 成功：清除其他分類資料夾中的同名舊檔案（當前分類已由 write_text 覆蓋）
    affected_cls = set()
    for cls in ["A1", "A2", "A3"]:
        if cls == cls_folder:
            continue
        for old_file in [
            output_dir / cls / "summary" / f"{stem}.md",
            output_dir / cls / "json" / f"{stem}.json",
        ]:
            if old_file.exists():
                try:
                    old_file.unlink()
                    affected_cls.add(cls)
                except Exception as e:
                    print(f"警告：無法刪除舊檔 {old_file.name}（{e}），繼續執行")

    remaining = state["papers_to_process"][1:]
    count = state["processed_count"] + 1

    paper_input = state["paper_input_tokens"]
    paper_output = state["paper_output_tokens"]
    cost = (paper_input / 1_000_000 * PRICE_INPUT_PER_M) + (paper_output / 1_000_000 * PRICE_OUTPUT_PER_M)

    print(f"已完成：{current}，分類：{classification}")
    print(f"本篇 Token：輸入 {paper_input:,} / 輸出 {paper_output:,} / 費用約 ${cost:.4f}")

    rebuild_summaries(output_dir, only=cls_folder)
    for cls in affected_cls:
        rebuild_summaries(output_dir, only=cls)

    return {
        **state,
        "papers_to_process": remaining,
        "processed_count": count,
        "failed_node": "",
        "error_message": "",
        "permanent_error": False,
    }


# ==========================================
# 條件判斷
# ==========================================
def route_after_agent(state: PaperState) -> str:
    if state["failed_node"] and state["permanent_error"]:
        return "handle_permanent_error"
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


def route_after_save(state: PaperState) -> str:
    if state["permanent_error"]:
        return "handle_permanent_error"
    if state["failed_node"]:
        return "handle_error"
    if state["papers_to_process"]:
        return "init_paper"
    return END


# ==========================================
# 建立 Graph
# ==========================================
def build_graph(classifier_chain_invoke, summarizer_chain_invoke):
    graph = StateGraph(PaperState)

    graph.add_node("init_paper", init_paper)
    graph.add_node("run_extractor", run_extractor)
    graph.add_node("run_classifier", make_run_classifier(classifier_chain_invoke))
    graph.add_node("run_summarizer", make_run_summarizer(summarizer_chain_invoke))
    graph.add_node("handle_permanent_error", handle_permanent_error)
    graph.add_node("handle_error", handle_error)
    graph.add_node("write_dead_letter", write_dead_letter)
    graph.add_node("save_results", save_results)

    graph.set_entry_point("init_paper")

    graph.add_edge("init_paper", "run_extractor")

    graph.add_conditional_edges("run_extractor", route_after_agent, {
        "handle_permanent_error": "handle_permanent_error",
        "handle_error": "handle_error",
        "continue": "run_classifier",
    })

    graph.add_conditional_edges("run_classifier", route_after_agent, {
        "handle_permanent_error": "handle_permanent_error",
        "handle_error": "handle_error",
        "continue": "run_summarizer",
    })

    graph.add_conditional_edges("run_summarizer", route_after_agent, {
        "handle_permanent_error": "handle_permanent_error",
        "handle_error": "handle_error",
        "continue": "save_results",
    })

    graph.add_conditional_edges("handle_error", route_after_error, {
        "extractor": "run_extractor",
        "classifier": "run_classifier",
        "summarizer": "run_summarizer",
        "save_results": "save_results",
        "write_dead_letter": "write_dead_letter",
    })

    graph.add_conditional_edges("handle_permanent_error", should_continue, {
        "init_paper": "init_paper",
        END: END,
    })

    graph.add_conditional_edges("write_dead_letter", should_continue, {
        "init_paper": "init_paper",
        END: END,
    })

    graph.add_conditional_edges("save_results", route_after_save, {
        "handle_permanent_error": "handle_permanent_error",
        "handle_error": "handle_error",
        "init_paper": "init_paper",
        END: END,
    })

    return graph.compile()
