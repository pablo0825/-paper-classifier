from pathlib import Path
from typing import Callable

from core.state import PaperState


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
try:
    _SUMMARIZE_TEMPLATE = (PROMPTS_DIR / "summarize_en.md").read_text(encoding="utf-8")
except FileNotFoundError:
    raise FileNotFoundError(f"找不到 prompt 檔案：{PROMPTS_DIR / 'summarize_en.md'}")


def summarize(state: PaperState, chain_invoke: Callable) -> PaperState:
    text = state["extracted_text"]
    criteria_met = state["criteria_met"]
    classification = state["classification"]

    prompt = (_SUMMARIZE_TEMPLATE
        .replace("{classification}", classification)
        .replace("{criteria_met}", ", ".join(criteria_met))
        .replace("{text}", text))

    try:
        result = chain_invoke(prompt)
    except Exception as e:
        return {
            **state,
            "summary": {},
            "failed_node": "summarizer",
            "error_message": str(e),
            "permanent_error": False,
        }

    if result["parsing_error"] or result["parsed"] is None:
        return {
            **state,
            "summary": {},
            "failed_node": "summarizer",
            "error_message": f"LLM 回傳解析失敗（{result['parsing_error']}）",
            "permanent_error": False,
        }

    parsed = result["parsed"]
    summary = parsed.model_dump()

    usage = result["raw"].usage_metadata or {}
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    return {
        **state,
        "summary": summary,
        "total_input_tokens": state["total_input_tokens"] + input_tokens,
        "total_output_tokens": state["total_output_tokens"] + output_tokens,
        "paper_input_tokens": state["paper_input_tokens"] + input_tokens,
        "paper_output_tokens": state["paper_output_tokens"] + output_tokens,
        "failed_node": "",
        "error_message": "",
    }
