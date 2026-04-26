# src/bq_readonly_mcp/tools/get_table_metadata.py
"""Tool: get table metadata (no schema, no samples)."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import GetTableMetadataInput

NAME = "get_table_metadata"
DESCRIPTION = (
    "Return metadata for a single table: type (TABLE/VIEW/MATERIALIZED_VIEW/EXTERNAL), "
    "description, labels, created/modified timestamps, row count, size in bytes, "
    "partitioning config, clustering columns, and expiration. Cheap — no query bytes consumed."
)
INPUT_SCHEMA = GetTableMetadataInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient) -> dict[str, Any]:
    parsed = GetTableMetadataInput(**args)
    md = bq.get_table_metadata(parsed.dataset_id, parsed.table_id)
    return md.model_dump()
