import json
import re
from pathlib import Path
from typing import Callable

from core.state import PaperState


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def summarize(state: PaperState, llm_invoke: Callable) -> PaperState:
    text = state["extracted_text"]
    criteria_met = state["criteria_met"]
    classification = state["classification"]

    template = (PROMPTS_DIR / "summarize_en.md").read_text(encoding="utf-8")
    prompt = (template
        .replace("{classification}", classification)
        .replace("{criteria_met}", ", ".join(criteria_met))
        .replace("{text}", text))

    try:
        response = llm_invoke(prompt)
    except Exception as e:
        return {
            **state,
            "summary": {},
            "failed_node": "summarizer",
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
        summary = json.loads(text_result)
    except json.JSONDecodeError as e:
        return {
            **state,
            "summary": {},
            "failed_node": "summarizer",
            "error_message": f"LLM 回傳無法解析為 JSON（{e}）",
            "permanent_error": False,
        }

    if not isinstance(summary, dict) or not summary:
        return {
            **state,
            "summary": {},
            "failed_node": "summarizer",
            "error_message": "LLM 回傳內容無法解析為摘要欄位",
            "permanent_error": False,
        }

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
