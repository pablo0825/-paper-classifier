import json
import re
from pathlib import Path
from typing import Callable

from core.state import PaperState


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def classify(state: PaperState, llm_invoke: Callable) -> PaperState:
    text = state["extracted_text"]

    template = (PROMPTS_DIR / "classify_en.md").read_text(encoding="utf-8")
    prompt = template.replace("{text}", text)

    try:
        response = llm_invoke(prompt)
    except Exception as e:
        return {
            **state,
            "classification": "",
            "criteria_met": [],
            "failed_node": "classifier",
            "error_message": str(e),
            "permanent_error": False,
        }

    result = response.content

    # 取得 token 用量
    usage = response.response_metadata.get("token_usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)

    # 剝除 markdown code block wrapper（若有）
    text_result = result.strip()
    if text_result.startswith("```"):
        text_result = re.sub(r'^```(?:json)?\s*\n?', '', text_result)
        text_result = re.sub(r'\n?```\s*$', '', text_result)

    # 解析 JSON
    try:
        data = json.loads(text_result)
    except json.JSONDecodeError as e:
        return {
            **state,
            "classification": "",
            "criteria_met": [],
            "failed_node": "classifier",
            "error_message": f"LLM 回傳無法解析為 JSON（{e}）",
            "permanent_error": False,
        }

    classification = data.get("classification", "")
    criteria = data.get("criteria", {})

    # 驗證 criteria 格式並建立符合清單
    if not isinstance(criteria, dict):
        return {
            **state,
            "classification": "",
            "criteria_met": [],
            "failed_node": "classifier",
            "error_message": "LLM 回傳 criteria 非物件格式",
            "permanent_error": False,
        }

    try:
        criteria_met = [
            f"Criterion {k}"
            for k, v in sorted(criteria.items(), key=lambda x: int(x[0]))
            if v is True or str(v).lower() == "true"
        ]
    except (ValueError, TypeError) as e:
        return {
            **state,
            "classification": "",
            "criteria_met": [],
            "failed_node": "classifier",
            "error_message": f"LLM 回傳 criteria 鍵格式無效（{e}）",
            "permanent_error": False,
        }

    # 驗證分類結果
    if classification not in ("A1", "A2", "A3"):
        return {
            **state,
            "classification": "",
            "criteria_met": [],
            "failed_node": "classifier",
            "error_message": f"LLM 回傳無效分類值：{classification!r}",
            "permanent_error": False,
        }

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
