# src/bq_readonly_mcp/tools/get_table.py
"""Tool: get full table info — metadata, columns, and N sample rows."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import GetTableInput

NAME = "get_table"
DESCRIPTION = (
    "Return everything about a single table: metadata, column schema, and N sample rows "
    "(default 3). Combines `get_table_metadata` + `describe_columns` + a small SELECT * sample. "
    "The sample query is subject to the same dry-run cost guard as `run_query`."
)
INPUT_SCHEMA = GetTableInput.model_json_schema()


def handle(
    args: dict[str, Any],
    *,
    bq: BQClient,
    default_sample_rows: int,
    max_bytes_billed: int,
) -> dict[str, Any]:
    parsed = GetTableInput(**args)
    n = parsed.sample_rows if parsed.sample_rows is not None else default_sample_rows

    md = bq.get_table_metadata(parsed.dataset_id, parsed.table_id)
    cols = bq.describe_columns(parsed.dataset_id, parsed.table_id)
    samples = bq.run_query(
        f"SELECT * FROM `{bq.client.project}.{parsed.dataset_id}.{parsed.table_id}` LIMIT {n}",
        max_bytes_billed=max_bytes_billed,
    )

    return {
        "metadata": md.model_dump(),
        "columns": [c.model_dump() for c in cols],
        "sample_rows": samples.rows,
    }
