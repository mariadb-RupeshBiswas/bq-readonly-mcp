from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from bq_readonly_mcp.bq import BQClient, DatasetNotAllowedError


def make_table_obj(
    table_id="t1",
    table_type="TABLE",
    description=None,
    labels=None,
    num_rows=42,
    num_bytes=4096,
    time_partitioning=None,
    range_partitioning=None,
    clustering_fields=None,
    expires=None,
    schema=None,
):
    t = MagicMock()
    t.table_id = table_id
    t.table_type = table_type
    t.description = description
    t.labels = labels or {}
    t.num_rows = num_rows
    t.num_bytes = num_bytes
    t.created = datetime(2026, 1, 1, tzinfo=UTC)
    t.modified = datetime(2026, 1, 2, tzinfo=UTC)
    t.time_partitioning = time_partitioning
    t.range_partitioning = range_partitioning
    t.clustering_fields = clustering_fields
    t.expires = expires
    t.schema = schema or []
    return t


def make_field(name="x", field_type="STRING", mode="NULLABLE", description=None):
    f = MagicMock()
    f.name = name
    f.field_type = field_type
    f.mode = mode
    f.description = description
    return f


def test_get_table_metadata_basic():
    client = MagicMock()
    client.get_table.return_value = make_table_obj()
    bq = BQClient(client=client, allowed_datasets=None)

    md = bq.get_table_metadata("d1", "t1")
    assert md.table_id == "t1"
    assert md.type == "TABLE"
    assert md.row_count == 42
    assert md.size_bytes == 4096
    assert md.partitioning is None
    assert md.clustering is None


def test_get_table_metadata_with_time_partitioning():
    client = MagicMock()
    tp = MagicMock()
    tp.type_ = "DAY"
    tp.field = "event_date"
    tp.expiration_ms = 86400000
    client.get_table.return_value = make_table_obj(time_partitioning=tp)
    bq = BQClient(client=client, allowed_datasets=None)

    md = bq.get_table_metadata("d1", "t1")
    assert md.partitioning is not None
    assert md.partitioning.type == "DAY"
    assert md.partitioning.column == "event_date"
    assert md.partitioning.expiration_ms == 86400000


def test_get_table_metadata_with_clustering():
    client = MagicMock()
    client.get_table.return_value = make_table_obj(clustering_fields=["col_a", "col_b"])
    bq = BQClient(client=client, allowed_datasets=None)

    md = bq.get_table_metadata("d1", "t1")
    assert md.clustering == ["col_a", "col_b"]


def test_describe_columns():
    client = MagicMock()
    client.get_table.return_value = make_table_obj(
        schema=[
            make_field("id", "INT64", "REQUIRED", "primary key"),
            make_field("name", "STRING", "NULLABLE"),
        ]
    )
    bq = BQClient(client=client, allowed_datasets=None)

    cols = bq.describe_columns("d1", "t1")
    assert len(cols) == 2
    assert cols[0].name == "id"
    assert cols[0].mode == "REQUIRED"
    assert cols[0].description == "primary key"


def test_get_table_metadata_rejects_disallowed_dataset():
    client = MagicMock()
    bq = BQClient(client=client, allowed_datasets=["a"])
    with pytest.raises(DatasetNotAllowedError):
        bq.get_table_metadata("b", "t1")
