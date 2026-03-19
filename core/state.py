from typing import TypedDict


class PaperState(TypedDict):
    # 待處理的 PDF 檔名清單，每處理完一篇就從清單移除
    papers_to_process: list[str]
    # 目前正在處理的 PDF 檔名（例如 paper_001.pdf）
    current_paper: str
    # 任務識別碼，格式為「時間戳記-檔名」（例如 20260319-143022-paper_001）
    thread_id: str
    # 從 PDF 擷取出的文字內容（最多 35,000 字）
    extracted_text: str
    # 分類結果，值為 A1、A2 或 A3
    classification: str
    # 符合的標準清單（例如 ["Criterion 1", "Criterion 3"]）
    criteria_met: list[str]
    # 摘要各欄位內容（例如 {"論文標題": "...", "研究目的": "..."}）
    summary: dict
    # 本次執行已成功處理的論文數量
    processed_count: int
    # 本次執行累計的錯誤論文數量
    error_count: int
    # 本次執行所有論文的累計輸入 token 數
    total_input_tokens: int
    # 本次執行所有論文的累計輸出 token 數
    total_output_tokens: int
    # 本篇論文的輸入 token 數（用於顯示單篇費用）
    paper_input_tokens: int
    # 本篇論文的輸出 token 數（用於顯示單篇費用）
    paper_output_tokens: int
    # 目前論文的重試次數，達到上限（3 次）後移至 dead letter
    retry_count: int
    # 失敗的節點名稱（extractor / classifier / summarizer），成功時為空字串
    failed_node: str
    # 失敗原因描述，成功時為空字串
    error_message: str
    # 待處理 PDF 所在資料夾的路徑
    input_dir: str
    # 分類結果輸出資料夾的路徑
    output_dir: str
    # 無法處理的 PDF 移至此資料夾
    error_dir: str
    # 已處理論文的 log 檔路徑（processed_papers.md）
    log_file: str
    # 錯誤論文的 log 檔路徑（error_papers.md）
    error_log: str
