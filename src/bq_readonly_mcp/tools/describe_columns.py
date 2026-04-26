# src/bq_readonly_mcp/tools/describe_columns.py
"""Tool: describe columns of a table."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import DescribeColumnsInput

NAME = "describe_columns"
DESCRIPTION = (
    "Return the column schema (name, type, mode, description) of a single table. "
    "Lighter than `get_table` — no metadata, no samples. Use this when the LLM only "
    "needs schema to write a query. Cheap — no query bytes consumed."
)
INPUT_SCHEMA = DescribeColumnsInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient) -> list[dict[str, Any]]:
    parsed = DescribeColumnsInput(**args)
    return [c.model_dump() for c in bq.describe_columns(parsed.dataset_id, parsed.table_id)]
