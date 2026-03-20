from pathlib import Path
from typing import Callable

from core.state import PaperState


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
try:
    _CLASSIFY_TEMPLATE = (PROMPTS_DIR / "classify_en.md").read_text(encoding="utf-8")
except FileNotFoundError:
    raise FileNotFoundError(f"找不到 prompt 檔案：{PROMPTS_DIR / 'classify_en.md'}")


def classify(state: PaperState, chain_invoke: Callable) -> PaperState:
    text = state["extracted_text"]

    prompt = _CLASSIFY_TEMPLATE.replace("{text}", text)

    try:
        result = chain_invoke(prompt)
    except Exception as e:
        return {
            **state,
            "classification": "",
            "criteria_met": [],
            "failed_node": "classifier",
            "error_message": str(e),
            "permanent_error": False,
        }

    if result["parsing_error"] or result["parsed"] is None:
        return {
            **state,
            "classification": "",
            "criteria_met": [],
            "failed_node": "classifier",
            "error_message": f"LLM 回傳解析失敗（{result['parsing_error']}）",
            "permanent_error": False,
        }

    parsed = result["parsed"]
    classification = parsed.classification

    usage = result["raw"].usage_metadata or {}
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    criteria_met = [
        f"Criterion {i}"
        for i in range(1, 8)
        if getattr(parsed, f"criterion_{i}")
    ]
    criteria_display = ", ".join(criteria_met) if criteria_met else "none"
    print(f"分類結果：{classification}，符合 {len(criteria_met)} 項標準（{criteria_display}）")

    return {
        **state,
        "classification": classification,
        "criteria_met": criteria_met,
        "total_input_tokens": state["total_input_tokens"] + input_tokens,
        "total_output_tokens": state["total_output_tokens"] + output_tokens,
        "paper_input_tokens": state["paper_input_tokens"] + input_tokens,
        "paper_output_tokens": state["paper_output_tokens"] + output_tokens,
        "failed_node": "",
        "error_message": "",
    }
