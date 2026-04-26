# tests/unit/test_tool_list_datasets.py
from unittest.mock import MagicMock

from bq_readonly_mcp.models import DatasetInfo
from bq_readonly_mcp.tools.list_datasets import handle


def test_returns_all_datasets():
    bq = MagicMock()
    bq.list_datasets.return_value = [DatasetInfo(dataset_id="a", location="US")]
    out = handle({}, bq=bq)
    assert out == [
        {"dataset_id": "a", "location": "US", "friendly_name": None, "description": None}
    ]
    bq.list_datasets.assert_called_once_with(name_contains=None)


def test_passes_name_contains():
    bq = MagicMock()
    bq.list_datasets.return_value = []
    handle({"name_contains": "sales"}, bq=bq)
    bq.list_datasets.assert_called_once_with(name_contains="sales")
