from unittest.mock import MagicMock

import pytest

from bq_readonly_mcp.bq import (
    BQClient,
    CostExceededError,
    DatasetNotAllowedError,
)


def make_dryrun_job(total_bytes_processed=1000, referenced_tables=None):
    job = MagicMock()
    job.total_bytes_processed = total_bytes_processed
    job.referenced_tables = referenced_tables or []
    return job


def make_real_job(
    rows=None,
    schema=None,
    total_bytes_processed=1000,
    total_bytes_billed=10485760,
    cache_hit=False,
    job_id="abc",
    location="US",
):
    job = MagicMock()
    job.result.return_value = rows or []
    job.schema = schema or []
    job.total_bytes_processed = total_bytes_processed
    job.total_bytes_billed = total_bytes_billed
    job.cache_hit = cache_hit
    job.job_id = job_id
    job.location = location
    return job


def make_table_ref(project="p", dataset_id="d", table_id="t"):
    ref = MagicMock()
    ref.project = project
    ref.dataset_id = dataset_id
    ref.table_id = table_id
    return ref


def test_dry_run_returns_estimate():
    client = MagicMock()
    client.query.return_value = make_dryrun_job(total_bytes_processed=12345)

    bq = BQClient(client=client, allowed_datasets=None)
    est = bq.estimate_query_cost("SELECT 1", max_bytes_billed=1_000_000)

    assert est.total_bytes_processed == 12345
    assert est.would_be_blocked is False
    assert est.estimated_usd > 0


def test_dry_run_flags_block_when_over_cap():
    client = MagicMock()
    client.query.return_value = make_dryrun_job(total_bytes_processed=2_000_000_000)

    bq = BQClient(client=client, allowed_datasets=None)
    est = bq.estimate_query_cost("SELECT 1", max_bytes_billed=1_073_741_824)

    assert est.would_be_blocked is True


def test_run_query_refuses_when_dryrun_exceeds_cap():
    client = MagicMock()
    client.query.return_value = make_dryrun_job(total_bytes_processed=2_000_000_000)

    bq = BQClient(client=client, allowed_datasets=None)
    with pytest.raises(CostExceededError, match="exceeds"):
        bq.run_query("SELECT 1", max_bytes_billed=1_073_741_824)


def test_run_query_refuses_when_referenced_table_outside_allowlist():
    client = MagicMock()
    client.query.return_value = make_dryrun_job(
        referenced_tables=[make_table_ref(dataset_id="forbidden")]
    )

    bq = BQClient(client=client, allowed_datasets=["allowed"])
    with pytest.raises(DatasetNotAllowedError, match="forbidden"):
        bq.run_query("SELECT 1 FROM forbidden.t", max_bytes_billed=1_073_741_824)


def test_run_query_executes_when_under_cap():
    client = MagicMock()

    dryrun = make_dryrun_job(total_bytes_processed=500)
    real = make_real_job(rows=[MagicMock(__iter__=lambda self: iter([("a", 1)]))])
    client.query.side_effect = [dryrun, real]

    real.result.return_value = [{"x": 1}]

    bq = BQClient(client=client, allowed_datasets=None)
    result = bq.run_query("SELECT 1", max_bytes_billed=1_073_741_824)

    assert result.total_bytes_processed == 500


def test_run_query_passes_max_bytes_billed_to_real_job():
    client = MagicMock()
    dryrun = make_dryrun_job(total_bytes_processed=500)
    real = make_real_job()
    real.result.return_value = []
    client.query.side_effect = [dryrun, real]

    bq = BQClient(client=client, allowed_datasets=None)
    bq.run_query("SELECT 1", max_bytes_billed=999_999)

    # Second call (the real job) should have maximum_bytes_billed set
    real_call = client.query.call_args_list[1]
    job_config = real_call.kwargs.get("job_config") or real_call.args[1]
    assert job_config.maximum_bytes_billed == 999_999
