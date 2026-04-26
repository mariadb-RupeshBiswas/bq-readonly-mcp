import pytest
from pydantic import ValidationError

from bq_readonly_mcp.models import (
    ColumnSchema,
    DatasetInfo,
    DescribeColumnsInput,
    EstimateQueryCostInput,
    GetTableInput,
    GetTableMetadataInput,
    ListDatasetsInput,
    ListTablesInput,
    PartitioningInfo,
    QueryResult,
    RunQueryInput,
    TableMetadata,
)


def test_list_datasets_input_optional_filter():
    obj = ListDatasetsInput()
    assert obj.name_contains is None
    obj = ListDatasetsInput(name_contains="sales")
    assert obj.name_contains == "sales"


def test_list_tables_input_requires_dataset():
    with pytest.raises(ValidationError):
        ListTablesInput()
    obj = ListTablesInput(dataset_id="foo")
    assert obj.dataset_id == "foo"


def test_describe_columns_input_requires_both():
    with pytest.raises(ValidationError):
        DescribeColumnsInput(dataset_id="ds")
    DescribeColumnsInput(dataset_id="ds", table_id="t")


def test_get_table_input_sample_rows_default():
    obj = GetTableInput(dataset_id="ds", table_id="t")
    assert obj.sample_rows is None
    obj = GetTableInput(dataset_id="ds", table_id="t", sample_rows=5)
    assert obj.sample_rows == 5


def test_get_table_input_negative_sample_rows_rejected():
    with pytest.raises(ValidationError):
        GetTableInput(dataset_id="ds", table_id="t", sample_rows=-1)


def test_run_query_input_requires_query():
    with pytest.raises(ValidationError):
        RunQueryInput()
    RunQueryInput(query="SELECT 1")


def test_run_query_input_limit_must_be_positive():
    with pytest.raises(ValidationError):
        RunQueryInput(query="SELECT 1", limit=0)
    RunQueryInput(query="SELECT 1", limit=100)


def test_estimate_query_cost_input_requires_query():
    with pytest.raises(ValidationError):
        EstimateQueryCostInput()


def test_dataset_info_serializes():
    d = DatasetInfo(dataset_id="foo", location="US")
    assert d.model_dump()["dataset_id"] == "foo"


def test_column_schema_required_fields():
    c = ColumnSchema(name="x", type="STRING", mode="NULLABLE")
    assert c.description is None


def test_table_metadata_optional_partitioning():
    m = TableMetadata(
        table_id="t",
        type="TABLE",
        created="2026-01-01T00:00:00",
        modified="2026-01-01T00:00:00",
        row_count=0,
        size_bytes=0,
    )
    assert m.partitioning is None
    assert m.clustering is None


def test_partitioning_info_validates_type():
    p = PartitioningInfo(type="DAY", column="ts", expiration_ms=None)
    assert p.type == "DAY"


def test_dataset_id_pattern_rejects_injection():
    with pytest.raises(ValidationError):
        ListTablesInput(dataset_id="foo`; DROP TABLE x;--")
    with pytest.raises(ValidationError):
        GetTableInput(dataset_id="ok", table_id="bad`)id")


def test_dataset_id_pattern_accepts_valid_identifiers():
    ListTablesInput(dataset_id="my_dataset")
    GetTableMetadataInput(dataset_id="ds1", table_id="tbl_name")
    DescribeColumnsInput(dataset_id="_private", table_id="Table123")


def test_query_result_round_trip():
    r = QueryResult(
        rows=[{"a": 1}],
        column_schema=[ColumnSchema(name="a", type="INT64", mode="NULLABLE")],
        total_bytes_processed=100,
        total_bytes_billed=10485760,
        cache_hit=False,
        job_id="abc",
        location="US",
    )
    dumped = r.model_dump()
    assert dumped["rows"] == [{"a": 1}]
    assert dumped["column_schema"][0]["name"] == "a"
