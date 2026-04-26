# tests/unit/test_tool_estimate_query_cost.py
from unittest.mock import MagicMock

import pytest

from bq_readonly_mcp.safety import SafetyError
from bq_readonly_mcp.tools.estimate_query_cost import handle


def test_dml_rejected_before_estimate():
    bq = MagicMock()
    with pytest.raises(SafetyError):
        handle({"query": "DELETE FROM t"}, bq=bq, max_bytes_billed=1_000_000_000)
    bq.estimate_query_cost.assert_not_called()


def test_select_calls_estimate():
    bq = MagicMock()
    bq.estimate_query_cost.return_value.model_dump.return_value = {
        "total_bytes_processed": 100,
        "estimated_usd": 0.000001,
        "would_be_blocked": False,
    }
    out = handle({"query": "SELECT 1"}, bq=bq, max_bytes_billed=1_000_000_000)
    assert out["total_bytes_processed"] == 100
