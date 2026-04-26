# tests/unit/test_tool_list_tables.py
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from bq_readonly_mcp.models import TableInfo
from bq_readonly_mcp.tools.list_tables import handle


def test_returns_tables():
    bq = MagicMock()
    bq.list_tables.return_value = [TableInfo(table_id="t", type="TABLE")]
    out = handle({"dataset_id": "d"}, bq=bq)
    assert out[0]["table_id"] == "t"
    bq.list_tables.assert_called_once_with(dataset_id="d", name_contains=None)


def test_requires_dataset_id():
    with pytest.raises(ValidationError):
        handle({}, bq=MagicMock())
