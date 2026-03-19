from pathlib import Path
from typing import Callable

from core.state import PaperState


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def summarize(state: PaperState, llm_invoke: Callable) -> PaperState:
    text = state["extracted_text"]
    criteria_met = state["criteria_met"]
    classification = state["classification"]

    template = (PROMPTS_DIR / "summarize_en.md").read_text(encoding="utf-8")
    prompt = template.format(
        text=text,
        classification=classification,
        criteria_met=", ".join(criteria_met),
    )

    try:
        response = llm_invoke(prompt)
    except Exception as e:
        return {
            **state,
            "summary": {},
            "failed_node": "summarizer",
            "error_message": str(e),
        }

    result = response.content

    # 取得 token 用量
    usage = response.response_metadata.get("token_usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)

    # 解析摘要各欄位
    summary = {}
    for line in result.splitlines():
        if ": " in line:
            parts = line.split(": ", 1)
            field = parts[0].strip()
            value = parts[1].strip()
            summary[field] = value

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
