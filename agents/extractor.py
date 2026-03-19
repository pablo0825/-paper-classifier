import fitz
from pathlib import Path

from core.state import PaperState


def extract(state: PaperState) -> PaperState:
    input_dir = Path(state["input_dir"])
    current = state["current_paper"]
    pdf_path = input_dir / current

    print(f"\n正在處理：{current}")

    # 嘗試開啟並擷取 PDF 文字
    try:
        with fitz.open(str(pdf_path)) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
    except fitz.FileDataError as e:
        # 永久性錯誤（損壞、加密）：回報，不重試
        return {
            **state,
            "current_paper": current,
            "extracted_text": "",
            "failed_node": "extractor",
            "error_message": f"PDF 無法開啟（{e}）",
            "permanent_error": True,
        }
    except Exception as e:
        # 暫時性錯誤（鎖定等）：回報，進重試流程
        return {
            **state,
            "current_paper": current,
            "extracted_text": "",
            "failed_node": "extractor",
            "error_message": str(e),
            "permanent_error": False,
        }

    # 純圖片 PDF：永久性錯誤，回報，不重試
    if len(text.strip()) < 100:
        return {
            **state,
            "current_paper": current,
            "extracted_text": "",
            "failed_node": "extractor",
            "error_message": "無法擷取文字，可能為純圖片 PDF",
            "permanent_error": True,
        }

    # 限制字數，避免超過 LLM token 上限
    if len(text) > 35000:
        print(f"  ⚠️  論文文字較長（{len(text):,} 字），已截斷至 35,000 字")
        text = text[:35000]

    return {
        **state,
        "current_paper": current,
        "extracted_text": text,
        "failed_node": "",
        "error_message": "",
        "permanent_error": False,
    }
