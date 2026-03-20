from langgraph.graph import END

from core.orchestrator import (
    route_after_agent,
    route_after_error,
    route_after_save,
    should_continue,
    MAX_RETRIES,
)


def make_state(**overrides):
    base = {
        "papers_to_process": [],
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
        "input_dir": "/tmp/input",
        "output_dir": "/tmp/output",
        "error_dir": "/tmp/error",
        "log_file": "/tmp/processed.md",
        "error_log": "/tmp/errors.md",
    }
    base.update(overrides)
    return base


# ==========================================
# route_after_agent
# ==========================================

def test_route_after_agent_success():
    assert route_after_agent(make_state()) == "continue"


def test_route_after_agent_permanent_error():
    state = make_state(failed_node="extractor", permanent_error=True)
    assert route_after_agent(state) == "handle_permanent_error"


def test_route_after_agent_temporary_error():
    state = make_state(failed_node="classifier", permanent_error=False)
    assert route_after_agent(state) == "handle_error"


# ==========================================
# route_after_error
# ==========================================

def test_route_after_error_retries_failed_node():
    state = make_state(failed_node="classifier", retry_count=1)
    assert route_after_error(state) == "classifier"


def test_route_after_error_routes_to_dead_letter_at_limit():
    state = make_state(failed_node="classifier", retry_count=MAX_RETRIES)
    assert route_after_error(state) == "write_dead_letter"


def test_route_after_error_retries_each_node():
    for node in ["extractor", "summarizer", "save_results"]:
        state = make_state(failed_node=node, retry_count=0)
        assert route_after_error(state) == node


# ==========================================
# route_after_save
# ==========================================

def test_route_after_save_continues_when_papers_remain():
    state = make_state(papers_to_process=["paper.pdf"])
    assert route_after_save(state) == "init_paper"


def test_route_after_save_ends_when_done():
    assert route_after_save(make_state()) == END


def test_route_after_save_handles_permanent_error():
    state = make_state(permanent_error=True)
    assert route_after_save(state) == "handle_permanent_error"


def test_route_after_save_handles_temporary_error():
    state = make_state(failed_node="save_results")
    assert route_after_save(state) == "handle_error"


# ==========================================
# should_continue
# ==========================================

def test_should_continue_with_remaining_papers():
    state = make_state(papers_to_process=["paper.pdf"])
    assert should_continue(state) == "init_paper"


def test_should_continue_ends_when_done():
    assert should_continue(make_state()) == END
