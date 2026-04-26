from bq_readonly_mcp.server import build_tool_registry


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
