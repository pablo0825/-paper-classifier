import fitz
import shutil
from pathlib import Path

from core.state import PaperState


def extract(state: PaperState) -> PaperState:
    input_dir = Path(state["input_dir"])
    error_dir = Path(state["error_dir"])
    current = state["papers_to_process"][0]
    pdf_path = input_dir / current

    print(f"\n正在處理：{current}")

    # 嘗試開啟並擷取 PDF 文字
    try:
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        shutil.move(str(pdf_path), str(error_dir / current))
        return {
            **state,
            "current_paper": current,
            "extracted_text": "",
            "failed_node": "extractor",
            "error_message": str(e),
        }

    # 純圖片 PDF，無法擷取文字
    if len(text.strip()) < 100:
        shutil.move(str(pdf_path), str(error_dir / current))
        return {
            **state,
            "current_paper": current,
            "extracted_text": "",
            "failed_node": "extractor",
            "error_message": "無法擷取文字，可能為純圖片 PDF",
        }

    # 限制字數，避免超過 LLM token 上限
    text = text[:35000]

    return {
        **state,
        "current_paper": current,
        "extracted_text": text,
        "failed_node": "",
        "error_message": "",
    }
