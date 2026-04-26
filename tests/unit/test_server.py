import json
from unittest.mock import MagicMock, patch

import pytest

from bq_readonly_mcp.config import Config
from bq_readonly_mcp.models import DatasetInfo
from bq_readonly_mcp.server import _warn_if_no_allowlist, build_tool_registry, dispatch_tool


def _make_cfg(allowed_datasets=None):
    return Config(
        project="test-proj",
        location="US",
        allowed_datasets=allowed_datasets,
        default_limit=50,
        max_limit=10000,
        max_bytes_billed=1_073_741_824,
        sample_rows=3,
        key_file=None,
    )


def _make_bq(datasets=None):
    bq = MagicMock()
    bq.list_datasets.return_value = [
        DatasetInfo(dataset_id=d, location="US") for d in (datasets or [])
    ]
    return bq


def test_registry_has_seven_tools():
    registry = build_tool_registry()
    names = [t["name"] for t in registry]
    assert set(names) == {
        "list_datasets",
        "list_tables",
        "get_table_metadata",
        "describe_columns",
        "get_table",
        "run_query",
        "estimate_query_cost",
    }


def test_each_tool_has_schema_and_description():
    registry = build_tool_registry()
    for t in registry:
        assert isinstance(t["description"], str) and t["description"]
        assert isinstance(t["input_schema"], dict)


# --- _warn_if_no_allowlist tests ---


def test_warn_printed_when_no_allowlist(capsys):
    cfg = _make_cfg(allowed_datasets=None)
    bq = _make_bq(["ds_a", "ds_b"])
    _warn_if_no_allowlist(cfg, bq)
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "ds_a" in err


def test_warn_truncates_long_dataset_list(capsys):
    # More than 3 datasets: only first 3 shown, rest summarized
    names = [f"ds_{i:02d}" for i in range(10)]
    cfg = _make_cfg(allowed_datasets=None)
    bq = _make_bq(names)
    _warn_if_no_allowlist(cfg, bq)
    err = capsys.readouterr().err
    assert "and 7 more" in err
    # Full list must NOT appear verbatim (would be too long to paste safely)
    assert "ds_09" not in err


def test_warn_silent_when_allowlist_set(capsys):
    cfg = _make_cfg(allowed_datasets=["only_this"])
    bq = _make_bq()
    _warn_if_no_allowlist(cfg, bq)
    err = capsys.readouterr().err
    assert err == ""


def test_warn_handles_list_datasets_error(capsys):
    cfg = _make_cfg(allowed_datasets=None)
    bq = MagicMock()
    bq.list_datasets.side_effect = RuntimeError("network failure")
    # Should not raise; logs a warning instead
    _warn_if_no_allowlist(cfg, bq)


# --- dispatch_tool tests ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name,patch_path,args",
    [
        ("list_datasets", "bq_readonly_mcp.tools.list_datasets.handle", {}),
        ("list_tables", "bq_readonly_mcp.tools.list_tables.handle", {"dataset_id": "ds"}),
        (
            "get_table_metadata",
            "bq_readonly_mcp.tools.get_table_metadata.handle",
            {"dataset_id": "ds", "table_id": "t"},
        ),
        (
            "describe_columns",
            "bq_readonly_mcp.tools.describe_columns.handle",
            {"dataset_id": "ds", "table_id": "t"},
        ),
        (
            "get_table",
            "bq_readonly_mcp.tools.get_table.handle",
            {"dataset_id": "ds", "table_id": "t"},
        ),
        (
            "run_query",
            "bq_readonly_mcp.tools.run_query.handle",
            {"query": "SELECT 1"},
        ),
        (
            "estimate_query_cost",
            "bq_readonly_mcp.tools.estimate_query_cost.handle",
            {"query": "SELECT 1"},
        ),
    ],
)
async def test_dispatch_routes_to_correct_handler(tool_name, patch_path, args):
    cfg = _make_cfg()
    bq = _make_bq()
    sentinel = {"dispatched": tool_name}

    with patch(patch_path, return_value=sentinel) as mock_handle:
        result = await dispatch_tool(tool_name, args, cfg, bq)

    mock_handle.assert_called_once()
    assert json.loads(result[0].text) == sentinel


@pytest.mark.asyncio
async def test_dispatch_unknown_tool_returns_error():
    cfg = _make_cfg()
    bq = _make_bq()
    result = await dispatch_tool("no_such_tool", {}, cfg, bq)
    assert result[0].text.startswith("error:")


@pytest.mark.asyncio
async def test_dispatch_validation_error_returns_error_message():
    """A pydantic.ValidationError from a tool returns 'error: invalid input:' text."""
    from pydantic import ValidationError

    cfg = _make_cfg()
    bq = _make_bq()

    with patch(
        "bq_readonly_mcp.tools.list_datasets.handle",
        side_effect=ValidationError.from_exception_data(
            "ListDatasetsInput", []
        ),
    ):
        result = await dispatch_tool("list_datasets", {}, cfg, bq)

    assert "error: invalid input:" in result[0].text
