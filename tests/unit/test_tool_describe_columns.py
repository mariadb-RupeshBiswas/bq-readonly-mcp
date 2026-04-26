# tests/unit/test_tool_describe_columns.py
from unittest.mock import MagicMock

from bq_readonly_mcp.models import ColumnSchema
from bq_readonly_mcp.tools.describe_columns import handle


def test_returns_columns():
    bq = MagicMock()
    bq.describe_columns.return_value = [ColumnSchema(name="x", type="INT64", mode="NULLABLE")]
    out = handle({"dataset_id": "d", "table_id": "t"}, bq=bq)
    assert out == [{"name": "x", "type": "INT64", "mode": "NULLABLE", "description": None}]
