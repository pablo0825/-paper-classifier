from unittest.mock import MagicMock, patch

import pytest

from core.orchestrator import build_graph
from core.schemas import ClassifierOutput, SummarizerOutput


# ==========================================
# Mock helpers
# ==========================================

def make_classifier_result(cls="A1", fail=False):
    """回傳假的 classifier chain 結果（符合 include_raw=True 格式）"""
    raw = MagicMock()
    raw.usage_metadata = {"input_tokens": 100, "output_tokens": 50}
    if fail:
        return {"parsed": None, "parsing_error": "mock parsing failure", "raw": raw}
    parsed = ClassifierOutput(
        criterion_1=True, criterion_2=True, criterion_3=True,
        criterion_4=True, criterion_5=True, criterion_6=True, criterion_7=True,
        classification=cls,
    )
    return {"parsed": parsed, "parsing_error": None, "raw": raw}


def make_summarizer_result():
    """回傳假的 summarizer chain 結果（符合 include_raw=True 格式）"""
    raw = MagicMock()
    raw.usage_metadata = {"input_tokens": 200, "output_tokens": 100}
    parsed = SummarizerOutput(
        title="Test Paper Title",
        apa7_citation="Author, A. (2026). Test paper. Journal, 1(1), 1-10.",
        classification="A1",
        scoring_basis="Quantitative survey with hypothesis testing",
        objective="To test the integration pipeline",
        method="Survey questionnaire",
        research_model="TAM",
        findings="Pipeline works correctly",
        contribution="Validated integration testing approach",
        limitations="Only tested in controlled environment",
    )
    return {"parsed": parsed, "parsing_error": None, "raw": raw}


def mock_extract_success(state):
    """模擬 extractor 成功擷取文字"""
    return {
        **state,
        "extracted_text": "This is a sample academic paper text for testing purposes.",
        "failed_node": "",
        "error_message": "",
        "permanent_error": False,
    }


def mock_extract_permanent_error(state):
    """模擬 extractor 遇到永久性錯誤（如 PDF 損壞）"""
    return {
        **state,
        "extracted_text": "",
        "failed_node": "extractor",
        "error_message": "PDF 無法開啟（mock error）",
        "permanent_error": True,
    }


# ==========================================
# Fixture：建立工作目錄與初始 state
# ==========================================

@pytest.fixture
def workspace(tmp_path):
    """建立符合 main.py 規格的完整目錄結構，並放入假 PDF"""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    error_dir = tmp_path / "output" / "error"

    input_dir.mkdir()
    error_dir.mkdir(parents=True)
    (tmp_path / "logs").mkdir()
    for cls in ["A1", "A2", "A3"]:
        for sub in ["pdf", "summary", "json"]:
            (output_dir / cls / sub).mkdir(parents=True)

    (input_dir / "paper_001.pdf").write_bytes(b"%PDF-1.4 fake")
    (input_dir / "paper_002.pdf").write_bytes(b"%PDF-1.4 fake")

    return {
        "tmp_path": tmp_path,
        "input_dir": input_dir,
        "output_dir": output_dir,
        "error_dir": error_dir,
        "log_file": tmp_path / "processed_papers.md",
        "error_log": tmp_path / "error_papers.md",
    }


def make_initial_state(workspace, papers):
    ws = workspace
    return {
        "papers_to_process": papers,
        "current_paper": "",
        "thread_id": "",
        "extracted_text": "",
        "classification": "",
        "criteria_met": [],
        "summary": {},
        "processed_count": 0,
        "error_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "paper_input_tokens": 0,
        "paper_output_tokens": 0,
        "retry_count": 0,
        "failed_node": "",
        "error_message": "",
        "permanent_error": False,
        "input_dir": str(ws["input_dir"]),
        "output_dir": str(ws["output_dir"]),
        "error_dir": str(ws["error_dir"]),
        "log_file": str(ws["log_file"]),
        "error_log": str(ws["error_log"]),
    }


# ==========================================
# 測試 1：單篇論文完整成功
# ==========================================

def test_single_paper_happy_path(workspace):
    app = build_graph(
        lambda prompt: make_classifier_result("A1"),
        lambda prompt: make_summarizer_result(),
    )
    initial = make_initial_state(workspace, ["paper_001.pdf"])

    with patch("core.orchestrator.extract", side_effect=mock_extract_success):
        result = app.invoke(initial)

    assert result["processed_count"] == 1
    assert result["error_count"] == 0

    # PDF 搬移至正確分類資料夾
    assert (workspace["output_dir"] / "A1" / "pdf" / "paper_001.pdf").exists()
    # 個別摘要 .md 寫入
    assert (workspace["output_dir"] / "A1" / "summary" / "paper_001.md").exists()
    # 總表重建用 .json 寫入
    assert (workspace["output_dir"] / "A1" / "json" / "paper_001.json").exists()
    # processed_papers.md 記錄論文檔名
    log = workspace["log_file"].read_text(encoding="utf-8")
    assert "paper_001.pdf" in log


# ==========================================
# 測試 2：多篇論文連續處理
# ==========================================

def test_multiple_papers_happy_path(workspace):
    app = build_graph(
        lambda prompt: make_classifier_result("A2"),
        lambda prompt: make_summarizer_result(),
    )
    initial = make_initial_state(workspace, ["paper_001.pdf", "paper_002.pdf"])

    with patch("core.orchestrator.extract", side_effect=mock_extract_success):
        result = app.invoke(initial)

    assert result["processed_count"] == 2
    assert result["error_count"] == 0
    assert (workspace["output_dir"] / "A2" / "pdf" / "paper_001.pdf").exists()
    assert (workspace["output_dir"] / "A2" / "pdf" / "paper_002.pdf").exists()

    log = workspace["log_file"].read_text(encoding="utf-8")
    assert "paper_001.pdf" in log
    assert "paper_002.pdf" in log


# ==========================================
# 測試 3：classifier 失敗 → 重試 → 第二次成功
# ==========================================

def test_classifier_retry_then_success(workspace):
    call_count = {"n": 0}

    def classifier_invoke(prompt):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return make_classifier_result(fail=True)
        return make_classifier_result("A1")

    app = build_graph(classifier_invoke, lambda prompt: make_summarizer_result())
    initial = make_initial_state(workspace, ["paper_001.pdf"])

    with patch("core.orchestrator.extract", side_effect=mock_extract_success):
        result = app.invoke(initial)

    assert result["processed_count"] == 1
    assert result["error_count"] == 0
    assert call_count["n"] == 2  # 第一次失敗，第二次成功
    assert (workspace["output_dir"] / "A1" / "pdf" / "paper_001.pdf").exists()


# ==========================================
# 測試 4：超過重試上限 → 進 dead letter
# ==========================================

def test_dead_letter_after_max_retries(workspace):
    app = build_graph(
        lambda prompt: make_classifier_result(fail=True),
        lambda prompt: make_summarizer_result(),
    )
    initial = make_initial_state(workspace, ["paper_001.pdf"])

    with patch("core.orchestrator.extract", side_effect=mock_extract_success):
        result = app.invoke(initial)

    assert result["processed_count"] == 0
    assert result["error_count"] == 1  # 搬移成功才計入

    # dead_letter.md 已寫入，且包含 failed_node 資訊
    dead_letter = workspace["tmp_path"] / "logs" / "dead_letter.md"
    assert dead_letter.exists()
    content = dead_letter.read_text(encoding="utf-8")
    assert "classifier" in content

    # error_papers.md 已寫入
    assert workspace["error_log"].exists()
    assert "paper_001.pdf" in workspace["error_log"].read_text(encoding="utf-8")

    # PDF 已搬移至 error 資料夾
    assert (workspace["error_dir"] / "paper_001.pdf").exists()


# ==========================================
# 測試 5：extractor 永久性錯誤 → 跳過，不進 dead letter
# ==========================================

def test_extractor_permanent_error_skips_paper(workspace):
    app = build_graph(
        lambda prompt: make_classifier_result("A1"),
        lambda prompt: make_summarizer_result(),
    )
    initial = make_initial_state(workspace, ["paper_001.pdf"])

    with patch("core.orchestrator.extract", side_effect=mock_extract_permanent_error):
        result = app.invoke(initial)

    assert result["processed_count"] == 0

    # error_papers.md 有記錄
    assert workspace["error_log"].exists()
    assert "paper_001.pdf" in workspace["error_log"].read_text(encoding="utf-8")

    # 不應產生 dead_letter.md（永久性錯誤走 handle_permanent_error，不走 write_dead_letter）
    dead_letter = workspace["tmp_path"] / "logs" / "dead_letter.md"
    assert not dead_letter.exists()
