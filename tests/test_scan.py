from pathlib import Path
import pytest

from core.scan import scan_papers


def test_returns_all_pdfs_when_no_logs(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "paper_a.pdf").touch()
    (input_dir / "paper_b.pdf").touch()

    result = scan_papers(input_dir, tmp_path / "processed.md", tmp_path / "errors.md")
    assert result == ["paper_a.pdf", "paper_b.pdf"]


def test_excludes_processed_paper(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "paper_a.pdf").touch()
    (input_dir / "paper_b.pdf").touch()

    log = tmp_path / "processed.md"
    log.write_text("## 2026-03-20\n\n- paper_a.pdf\n", encoding="utf-8")

    result = scan_papers(input_dir, log, tmp_path / "errors.md")
    assert result == ["paper_b.pdf"]


def test_excludes_error_paper(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "paper_a.pdf").touch()
    (input_dir / "paper_b.pdf").touch()

    error_filenames = tmp_path / "errors.md"
    error_filenames.write_text("## 2026-03-20\n\n- paper_b.pdf\n", encoding="utf-8")

    result = scan_papers(input_dir, tmp_path / "processed.md", error_filenames)
    assert result == ["paper_a.pdf"]


def test_returns_empty_when_all_processed(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "paper_a.pdf").touch()

    log = tmp_path / "processed.md"
    log.write_text("- paper_a.pdf\n", encoding="utf-8")

    result = scan_papers(input_dir, log, tmp_path / "errors.md")
    assert result == []


def test_returns_empty_when_input_dir_empty(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    result = scan_papers(input_dir, tmp_path / "processed.md", tmp_path / "errors.md")
    assert result == []


def test_ignores_non_pdf_files(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "paper_a.pdf").touch()
    (input_dir / "readme.txt").touch()
    (input_dir / "data.docx").touch()

    result = scan_papers(input_dir, tmp_path / "processed.md", tmp_path / "errors.md")
    assert result == ["paper_a.pdf"]
