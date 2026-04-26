"""Tests for config resolution from CLI args and environment variables."""

import pytest

from bq_readonly_mcp.config import build_config


def test_project_required():
    with pytest.raises(SystemExit):
        build_config(argv=[], env={})


def test_project_from_cli():
    cfg = build_config(argv=["--project", "my-proj"], env={})
    assert cfg.project == "my-proj"
    assert cfg.location == "US"


def test_project_from_env():
    cfg = build_config(argv=[], env={"GCP_PROJECT_ID": "env-proj"})
    assert cfg.project == "env-proj"


def test_cli_overrides_env():
    cfg = build_config(
        argv=["--project", "cli-proj"],
        env={"GCP_PROJECT_ID": "env-proj"},
    )
    assert cfg.project == "cli-proj"


def test_defaults_match_spec():
    cfg = build_config(argv=["--project", "p"], env={})
    assert cfg.location == "US"
    assert cfg.default_limit == 50
    assert cfg.max_limit == 10_000
    assert cfg.max_bytes_billed == 1_073_741_824
    assert cfg.sample_rows == 3
    assert cfg.allowed_datasets is None
    assert cfg.key_file is None


def test_datasets_allowlist_from_cli():
    cfg = build_config(argv=["--project", "p", "--datasets", "ds1", "ds2"], env={})
    assert cfg.allowed_datasets == ["ds1", "ds2"]


def test_datasets_allowlist_from_env_csv():
    cfg = build_config(
        argv=["--project", "p"],
        env={"BIGQUERY_ALLOWED_DATASETS": "ds1,ds2,ds3"},
    )
    assert cfg.allowed_datasets == ["ds1", "ds2", "ds3"]


def test_max_bytes_billed_override():
    cfg = build_config(argv=["--project", "p", "--max-bytes-billed", "5000"], env={})
    assert cfg.max_bytes_billed == 5000


def test_invalid_max_limit_rejected():
    with pytest.raises(SystemExit):
        build_config(argv=["--project", "p", "--max-limit", "0"], env={})


def test_invalid_env_int_rejected():
    with pytest.raises(SystemExit):
        build_config(argv=["--project", "p"], env={"BIGQUERY_DEFAULT_LIMIT": "abc"})
    with pytest.raises(SystemExit):
        build_config(argv=["--project", "p"], env={"BIGQUERY_DEFAULT_LIMIT": "-5"})


def test_empty_env_allowlist_treated_as_unset():
    cfg = build_config(argv=["--project", "p"], env={"BIGQUERY_ALLOWED_DATASETS": ""})
    assert cfg.allowed_datasets is None


def test_whitespace_only_env_allowlist_treated_as_unset():
    cfg = build_config(argv=["--project", "p"], env={"BIGQUERY_ALLOWED_DATASETS": "   "})
    assert cfg.allowed_datasets is None
