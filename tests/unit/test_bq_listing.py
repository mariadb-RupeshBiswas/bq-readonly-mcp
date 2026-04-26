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


def _list_item(dataset_id: str):
    """A DatasetListItem-shaped mock with a `.reference` (real-API contract)."""
    item = MagicMock()
    item.dataset_id = dataset_id
    ref = MagicMock(name=f"ref({dataset_id})")
    ref.dataset_id = dataset_id
    item.reference = ref
    return item


def _resolve_via_reference(ref):
    """Mirrors `client.get_dataset(reference) -> Dataset` for the test path."""
    return make_dataset(dataset_id=ref.dataset_id, location="US")


def test_list_datasets_returns_all_when_no_allowlist():
    client = MagicMock()
    client.list_datasets.return_value = [_list_item("a"), _list_item("b")]
    client.get_dataset.side_effect = _resolve_via_reference

    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_datasets()

    assert [d.dataset_id for d in out] == ["a", "b"]


def test_list_datasets_filters_by_allowlist():
    client = MagicMock()
    client.list_datasets.return_value = [_list_item("a"), _list_item("b"), _list_item("c")]
    client.get_dataset.side_effect = _resolve_via_reference

    bq = BQClient(client=client, allowed_datasets=["a", "c"])
    out = bq.list_datasets()

    assert [d.dataset_id for d in out] == ["a", "c"]


def test_list_datasets_filters_by_name_contains():
    client = MagicMock()
    client.list_datasets.return_value = [
        _list_item("sales_2024"),
        _list_item("hr_2024"),
        _list_item("sales_2025"),
    ]
    client.get_dataset.side_effect = _resolve_via_reference

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


def test_list_datasets_uses_reference_for_get_dataset():
    """Regression: get_dataset() needs a DatasetReference, not a DatasetListItem.

    Real BigQuery raises AttributeError ('DatasetListItem has no attribute path')
    when you pass the list-item directly. We must pass `.reference`.
    """
    client = MagicMock()

    list_item = MagicMock()
    list_item.dataset_id = "demo"
    list_item.reference = MagicMock(name="dataset_ref")  # the thing get_dataset wants

    client.list_datasets.return_value = [list_item]
    client.get_dataset.return_value = make_dataset("demo", location="US")

    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_datasets()

    # get_dataset must have been called with the .reference, not the list_item itself
    args, _ = client.get_dataset.call_args
    assert args[0] is list_item.reference
    assert len(out) == 1
    assert out[0].dataset_id == "demo"
