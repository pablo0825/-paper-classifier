from pathlib import Path
from typing import Callable

from core.state import PaperState


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def classify(state: PaperState, llm_invoke: Callable) -> PaperState:
    text = state["extracted_text"]

    template = (PROMPTS_DIR / "classify_en.md").read_text(encoding="utf-8")
    prompt = template.format(text=text)

    try:
        response = llm_invoke(prompt)
    except Exception as e:
        return {
            **state,
            "classification": "",
            "criteria_met": [],
            "failed_node": "classifier",
            "error_message": str(e),
        }

    result = response.content

    # 取得 token 用量
    usage = response.response_metadata.get("token_usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)

    # 解析分類結果
    classification = None
    criteria_met = []

    for line in result.splitlines():
        if "Classification:" in line:
            if "A1" in line:
                classification = "A1"
            elif "A2" in line:
                classification = "A2"
            elif "A3" in line:
                classification = "A3"
        for i in range(1, 8):
            if f"Criterion {i}: Yes" in line:
                criteria_met.append(f"Criterion {i}")

    # 驗證分類結果
    if classification not in ("A1", "A2", "A3"):
        return {
            **state,
            "classification": "",
            "criteria_met": [],
            "failed_node": "classifier",
            "error_message": f"LLM 回傳無效分類值：{classification!r}",
        }

    criteria_display = ", ".join(criteria_met) if criteria_met else "none"
    print(f"分類結果：{classification}，符合 {len(criteria_met)} 項標準（{criteria_display}）")

    return {
        **state,
        "classification": classification,
        "criteria_met": criteria_met,
        "total_input_tokens": state["total_input_tokens"] + input_tokens,
        "total_output_tokens": state["total_output_tokens"] + output_tokens,
        "paper_input_tokens": input_tokens,
        "paper_output_tokens": output_tokens,
        "failed_node": "",
        "error_message": "",
    }
