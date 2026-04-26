"""Shared pytest fixtures."""

import os

import pytest

from bq_readonly_mcp.auth import AuthError, build_bigquery_client
from bq_readonly_mcp.bq import BQClient
from bq_readonly_mcp.config import Config


@pytest.fixture(scope="session")
def integration_bq() -> BQClient:
    project = os.environ.get("BQ_INTEGRATION_PROJECT")
    if not project:
        pytest.skip("BQ_INTEGRATION_PROJECT not set; skipping integration tests")
    cfg = Config(
        project=project,
        location="US",
        allowed_datasets=None,
        default_limit=50,
        max_limit=10_000,
        max_bytes_billed=1_073_741_824,
        sample_rows=3,
        key_file=None,
    )
    try:
        client = build_bigquery_client(cfg)
    except AuthError as exc:
        pytest.skip(f"ADC unavailable: {exc}")
    return BQClient(client=client, allowed_datasets=None)
