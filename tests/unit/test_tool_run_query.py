# tests/unit/test_tool_run_query.py
from unittest.mock import MagicMock

import pytest

from bq_readonly_mcp.models import QueryResult
from bq_readonly_mcp.tools.run_query import handle


def make_bq():
    bq = MagicMock()
    bq.run_query.return_value = QueryResult(
        rows=[{"x": 1}],
        column_schema=[],
        total_bytes_processed=100,
        total_bytes_billed=0,
        cache_hit=False,
        job_id="j1",
        location="US",
    )
    return bq


def test_select_query_executes_with_auto_limit():
    bq = make_bq()
    handle(
        {"query": "SELECT * FROM t"},
        bq=bq,
        default_limit=50,
        max_limit=10000,
        max_bytes_billed=1_000_000_000,
    )
    sent = bq.run_query.call_args.args[0]
    assert sent.rstrip().rstrip(";").endswith("LIMIT 50")


def test_explicit_limit_used():
    bq = make_bq()
    handle(
        {"query": "SELECT * FROM t", "limit": 200},
        bq=bq,
        default_limit=50,
        max_limit=10000,
        max_bytes_billed=1_000_000_000,
    )
    sent = bq.run_query.call_args.args[0]
    assert sent.endswith("LIMIT 200")


def test_no_limit_skips_injection():
    bq = make_bq()
    handle(
        {"query": "SELECT * FROM t", "no_limit": True},
        bq=bq,
        default_limit=50,
        max_limit=10000,
        max_bytes_billed=1_000_000_000,
    )
    sent = bq.run_query.call_args.args[0]
    assert "LIMIT" not in sent.upper()


def test_limit_above_cap_rejected():
    with pytest.raises(ValueError, match="exceeds max_limit"):
        handle(
            {"query": "SELECT * FROM t", "limit": 99999},
            bq=make_bq(),
            default_limit=50,
            max_limit=10000,
            max_bytes_billed=1_000_000_000,
        )


def test_dry_run_returns_estimate_only(monkeypatch):
    bq = make_bq()
    bq.estimate_query_cost.return_value.model_dump.return_value = {"total_bytes_processed": 999}
    handle(
        {"query": "SELECT * FROM t", "dry_run": True},
        bq=bq,
        default_limit=50,
        max_limit=10000,
        max_bytes_billed=1_000_000_000,
    )
    bq.run_query.assert_not_called()
    bq.estimate_query_cost.assert_called_once()


def test_dml_query_rejected_before_executing():
    from bq_readonly_mcp.safety import SafetyError

    bq = make_bq()
    with pytest.raises(SafetyError):
        handle(
            {"query": "DELETE FROM t WHERE 1=1"},
            bq=bq,
            default_limit=50,
            max_limit=10000,
            max_bytes_billed=1_000_000_000,
        )
    bq.run_query.assert_not_called()
