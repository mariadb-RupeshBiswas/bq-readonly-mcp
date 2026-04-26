from unittest.mock import MagicMock, patch

import pytest

from bq_readonly_mcp.auth import AuthError, build_bigquery_client
from bq_readonly_mcp.config import Config


def make_config(**overrides) -> Config:
    base = dict(
        project="my-proj",
        location="US",
        allowed_datasets=None,
        default_limit=50,
        max_limit=10_000,
        max_bytes_billed=1_073_741_824,
        sample_rows=3,
        key_file=None,
    )
    base.update(overrides)
    return Config(**base)


@patch("bq_readonly_mcp.auth.bigquery.Client")
@patch("bq_readonly_mcp.auth.google_default")
def test_uses_adc_when_no_key_file(mock_default, mock_client):
    mock_default.return_value = (MagicMock(), "adc-detected-proj")
    cfg = make_config(key_file=None)

    client = build_bigquery_client(cfg)

    mock_default.assert_called_once()
    mock_client.assert_called_once()
    kwargs = mock_client.call_args.kwargs
    assert kwargs["project"] == "my-proj"
    assert kwargs["location"] == "US"
    assert client is mock_client.return_value


@patch("bq_readonly_mcp.auth.bigquery.Client")
@patch("bq_readonly_mcp.auth.service_account.Credentials.from_service_account_file")
def test_uses_key_file_when_provided(mock_from_file, mock_client, tmp_path):
    key = tmp_path / "key.json"
    key.write_text("{}")
    cfg = make_config(key_file=str(key))

    build_bigquery_client(cfg)

    mock_from_file.assert_called_once_with(str(key))
    mock_client.assert_called_once()
    assert mock_client.call_args.kwargs["credentials"] is mock_from_file.return_value


@patch("bq_readonly_mcp.auth.google_default")
def test_raises_clear_error_on_default_failure(mock_default):
    from google.auth.exceptions import DefaultCredentialsError

    mock_default.side_effect = DefaultCredentialsError("nope")
    cfg = make_config()

    with pytest.raises(AuthError, match="gcloud auth application-default login"):
        build_bigquery_client(cfg)


def test_raises_clear_error_on_missing_key_file(tmp_path):
    cfg = make_config(key_file=str(tmp_path / "does_not_exist.json"))
    with pytest.raises(AuthError, match="key file not found"):
        build_bigquery_client(cfg)
