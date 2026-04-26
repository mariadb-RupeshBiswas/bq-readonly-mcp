# tests/unit/test_tool_get_table_metadata.py
from unittest.mock import MagicMock

from bq_readonly_mcp.models import TableMetadata
from bq_readonly_mcp.tools.get_table_metadata import handle


def test_returns_metadata_dict():
    bq = MagicMock()
    bq.get_table_metadata.return_value = TableMetadata(
        table_id="t",
        type="TABLE",
        created="2026-01-01T00:00:00",
        modified="2026-01-01T00:00:00",
        row_count=10,
        size_bytes=100,
    )
    out = handle({"dataset_id": "d", "table_id": "t"}, bq=bq)
    assert out["table_id"] == "t"
    assert out["row_count"] == 10
