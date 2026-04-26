from unittest.mock import MagicMock

from bq_readonly_mcp.bq import BQClient


def make_dataset(dataset_id="d1", location="US", friendly_name=None, description=None):
    ds = MagicMock()
    ds.dataset_id = dataset_id
    ds.location = location
    ds.friendly_name = friendly_name
    ds.description = description
    return ds


def make_table(table_id="t1", table_type="TABLE", created=None, friendly_name=None):
    t = MagicMock()
    t.table_id = table_id
    t.table_type = table_type
    t.created = created
    t.friendly_name = friendly_name
    return t


def test_list_datasets_returns_all_when_no_allowlist():
    client = MagicMock()
    client.list_datasets.return_value = [make_dataset("a"), make_dataset("b")]
    # bigquery's list_datasets returns DatasetListItem with dataset_id but not full attrs;
    # we simulate by also setting client.get_dataset to return a richer object.
    client.get_dataset.side_effect = lambda ref: make_dataset(
        dataset_id=ref.dataset_id, location="US"
    )

    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_datasets()

    ids = [d.dataset_id for d in out]
    assert ids == ["a", "b"]


def test_list_datasets_filters_by_allowlist():
    client = MagicMock()
    client.list_datasets.return_value = [
        make_dataset("a"),
        make_dataset("b"),
        make_dataset("c"),
    ]
    client.get_dataset.side_effect = lambda ref: make_dataset(
        dataset_id=ref.dataset_id, location="US"
    )

    bq = BQClient(client=client, allowed_datasets=["a", "c"])
    out = bq.list_datasets()

    assert [d.dataset_id for d in out] == ["a", "c"]


def test_list_datasets_filters_by_name_contains():
    client = MagicMock()
    client.list_datasets.return_value = [
        make_dataset("sales_2024"),
        make_dataset("hr_2024"),
        make_dataset("sales_2025"),
    ]
    client.get_dataset.side_effect = lambda ref: make_dataset(
        dataset_id=ref.dataset_id, location="US"
    )

    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_datasets(name_contains="sales")

    assert [d.dataset_id for d in out] == ["sales_2024", "sales_2025"]


def test_list_tables_basic():
    client = MagicMock()
    client.list_tables.return_value = [make_table("t1"), make_table("t2", "VIEW")]

    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_tables(dataset_id="d1")

    assert [t.table_id for t in out] == ["t1", "t2"]
    assert out[1].type == "VIEW"


def test_list_tables_filters_by_name_contains():
    client = MagicMock()
    client.list_tables.return_value = [
        make_table("orders"),
        make_table("customers"),
        make_table("order_items"),
    ]
    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_tables(dataset_id="d1", name_contains="order")
    assert [t.table_id for t in out] == ["orders", "order_items"]


def test_list_tables_rejects_dataset_outside_allowlist():
    import pytest

    from bq_readonly_mcp.bq import DatasetNotAllowedError

    client = MagicMock()
    bq = BQClient(client=client, allowed_datasets=["allowed"])
    with pytest.raises(DatasetNotAllowedError):
        bq.list_tables(dataset_id="forbidden")
