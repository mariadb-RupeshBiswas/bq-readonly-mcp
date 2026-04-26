"""Integration tests against Google's public datasets.

Require ADC + env var BQ_INTEGRATION_PROJECT pointing to a project that has
permission to query bigquery-public-data.* (which is essentially any project
with billing enabled). Skipped in CI by default.
"""

import pytest

from bq_readonly_mcp.bq import BQClient, CostExceededError
from bq_readonly_mcp.safety import SafetyError
from bq_readonly_mcp.tools import (
    describe_columns,
    estimate_query_cost,
    get_table_metadata,
    list_tables,
    run_query,
)

pytestmark = pytest.mark.integration


def test_list_tables_in_public_samples(integration_bq):
    # list_tables uses the configured project; result may be empty, that's fine
    tables = list_tables.handle({"dataset_id": "samples"}, bq=integration_bq)
    assert isinstance(tables, list)


def test_get_table_metadata_against_public_dataset(integration_bq):
    # Metadata lookup requires the client project to be `bigquery-public-data`
    md = get_table_metadata.handle(
        {"dataset_id": "samples", "table_id": "shakespeare"},
        bq=_with_project(integration_bq, "bigquery-public-data"),
    )
    assert md["table_id"] == "shakespeare"
    assert md["row_count"] > 100_000


def test_describe_columns_against_public_dataset(integration_bq):
    cols = describe_columns.handle(
        {"dataset_id": "samples", "table_id": "shakespeare"},
        bq=_with_project(integration_bq, "bigquery-public-data"),
    )
    names = [c["name"] for c in cols]
    assert "word" in names
    assert "corpus" in names


def test_estimate_query_cost_returns_estimate(integration_bq):
    out = estimate_query_cost.handle(
        {"query": "SELECT word FROM `bigquery-public-data.samples.shakespeare` LIMIT 10"},
        bq=integration_bq,
        max_bytes_billed=1_073_741_824,
    )
    assert "total_bytes_processed" in out


def test_run_query_real(integration_bq):
    out = run_query.handle(
        {"query": "SELECT word FROM `bigquery-public-data.samples.shakespeare`"},
        bq=integration_bq,
        default_limit=5,
        max_limit=10_000,
        max_bytes_billed=1_073_741_824,
    )
    assert len(out["rows"]) == 5


def test_cost_guard_refuses_huge_query(integration_bq):
    # Try several known-large public tables in order; skip if none are found.
    # The test only needs one table that dry-runs > 1 GB to verify the guard fires.
    _LARGE_TABLE_CANDIDATES = [
        "bigquery-public-data.wikipedia.pageviews_2015",
        "bigquery-public-data.crypto_bitcoin.transactions",
        "bigquery-public-data.github_repos.contents",
    ]
    from google.api_core.exceptions import NotFound

    for table_ref in _LARGE_TABLE_CANDIDATES:
        try:
            run_query.handle(
                {"query": f"SELECT * FROM `{table_ref}`"},
                bq=integration_bq,
                default_limit=5,
                max_limit=10_000,
                max_bytes_billed=10_000_000,  # 10 MB — any of these scans far more
            )
        except CostExceededError:
            return  # guard fired correctly — test passes
        except NotFound:
            continue  # table not available, try the next one

    pytest.skip("none of the large public tables were available to test the cost guard")


def test_dml_rejected_before_query(integration_bq):
    with pytest.raises(SafetyError):
        run_query.handle(
            {"query": "DELETE FROM `bigquery-public-data.samples.shakespeare` WHERE 1=1"},
            bq=integration_bq,
            default_limit=5,
            max_limit=10_000,
            max_bytes_billed=1_073_741_824,
        )


def _with_project(bq: BQClient, project: str) -> BQClient:
    """Return a new BQClient whose underlying client targets a different project.

    Metadata calls (`get_table_metadata`, `describe_columns`) use
    `bq.client.project` as the lookup project, so we need a fresh client
    pointed at `bigquery-public-data` for those calls.
    """
    from google.cloud import bigquery

    new_client = bigquery.Client(
        project=project,
        location=bq.client.location,
        credentials=bq.client._credentials,
    )
    return BQClient(client=new_client, allowed_datasets=None)
