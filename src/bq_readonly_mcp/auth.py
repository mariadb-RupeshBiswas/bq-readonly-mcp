"""ADC and service-account-key auth for BigQuery client construction."""

from __future__ import annotations

import os

from google.auth import default as google_default
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery
from google.oauth2 import service_account

from .config import Config


class AuthError(RuntimeError):
    """Raised when BigQuery credentials cannot be acquired."""


def build_bigquery_client(config: Config) -> bigquery.Client:
    """Construct a BigQuery client using ADC or an explicit key file."""
    if config.key_file:
        if not os.path.isfile(config.key_file):
            raise AuthError(
                f"key file not found at {config.key_file!r}. "
                "Set --key-file or GOOGLE_APPLICATION_CREDENTIALS to a valid path."
            )
        creds = service_account.Credentials.from_service_account_file(config.key_file)
        return bigquery.Client(
            project=config.project,
            location=config.location,
            credentials=creds,
        )

    try:
        creds, _ = google_default()
    except DefaultCredentialsError as exc:
        raise AuthError(
            "Application Default Credentials not found. Run "
            "`gcloud auth application-default login` and try again. "
            f"(underlying error: {exc})"
        ) from exc

    return bigquery.Client(
        project=config.project,
        location=config.location,
        credentials=creds,
    )
