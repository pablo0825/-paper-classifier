from tools.rerun import _remove_orphaned_headers


def test_keeps_header_with_entries():
    lines = ["## 2026-03-20", "", "- paper_a.pdf", "- paper_b.pdf"]
    assert _remove_orphaned_headers(lines) == lines


def test_removes_orphaned_header_before_another():
    lines = ["## 2026-03-20", "", "## 2026-03-21", "", "- paper_b.pdf"]
    result = _remove_orphaned_headers(lines)
    assert "## 2026-03-20" not in result
    assert "## 2026-03-21" in result
    assert "- paper_b.pdf" in result


def test_removes_trailing_orphaned_header():
    lines = ["## 2026-03-20", "", "- paper_a.pdf", "", "## 2026-03-21"]
    result = _remove_orphaned_headers(lines)
    assert "## 2026-03-20" in result
    assert "## 2026-03-21" not in result


def test_empty_list():
    assert _remove_orphaned_headers([]) == []


def test_no_headers_unchanged():
    lines = ["- paper_a.pdf", "- paper_b.pdf"]
    assert _remove_orphaned_headers(lines) == lines


def test_all_orphaned_headers_removed():
    # 兩個孤立標題都被移除，中間的空行保留
    lines = ["## 2026-03-20", "", "## 2026-03-21"]
    result = _remove_orphaned_headers(lines)
    assert "## 2026-03-20" not in result
    assert "## 2026-03-21" not in result
