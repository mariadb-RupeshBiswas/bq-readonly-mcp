# src/bq_readonly_mcp/tools/list_tables.py
"""Tool: list tables in a dataset."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import ListTablesInput

NAME = "list_tables"
DESCRIPTION = (
    "List tables, views, materialized views, and external tables in a BigQuery dataset. "
    "Returns table_id and type for each. Optional `name_contains` filters by substring."
)
INPUT_SCHEMA = ListTablesInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient) -> list[dict[str, Any]]:
    parsed = ListTablesInput(**args)
    return [
        t.model_dump()
        for t in bq.list_tables(dataset_id=parsed.dataset_id, name_contains=parsed.name_contains)
    ]
