# tests/unit/test_tool_get_table.py
from unittest.mock import MagicMock

from bq_readonly_mcp.models import ColumnSchema, QueryResult, TableMetadata
from bq_readonly_mcp.tools.get_table import handle


def test_bundles_metadata_columns_and_samples():
    bq = MagicMock()
    bq.client.project = "p"
    bq.get_table_metadata.return_value = TableMetadata(
        table_id="t",
        type="TABLE",
        created="2026-01-01T00:00:00",
        modified="2026-01-01T00:00:00",
        row_count=10,
        size_bytes=100,
    )
    bq.describe_columns.return_value = [ColumnSchema(name="x", type="INT64", mode="NULLABLE")]
    bq.run_query.return_value = QueryResult(
        rows=[{"x": 1}],
        schema=[],
        total_bytes_processed=1,
        total_bytes_billed=0,
        cache_hit=False,
        job_id="j",
        location="US",
    )

    out = handle(
        {"dataset_id": "d", "table_id": "t"},
        bq=bq,
        default_sample_rows=3,
        max_bytes_billed=1_000_000_000,
    )
    assert out["metadata"]["table_id"] == "t"
    assert out["columns"][0]["name"] == "x"
    assert out["sample_rows"] == [{"x": 1}]
