# src/bq_readonly_mcp/tools/estimate_query_cost.py
"""Tool: estimate the cost of a query without executing it."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import EstimateQueryCostInput
from ..safety import validate_select_query

NAME = "estimate_query_cost"
DESCRIPTION = (
    "Run a free dry-run against BigQuery and return the estimated bytes processed and USD cost. "
    "Useful for the LLM to reason about query expense before deciding to execute. "
    "The query is validated as SELECT-only first; DML/DDL is rejected."
)
INPUT_SCHEMA = EstimateQueryCostInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient, max_bytes_billed: int) -> dict[str, Any]:
    parsed = EstimateQueryCostInput(**args)
    validate_select_query(parsed.query)
    est = bq.estimate_query_cost(parsed.query, max_bytes_billed=max_bytes_billed)
    return est.model_dump()
