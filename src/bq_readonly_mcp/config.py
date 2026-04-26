"""Configuration resolution: CLI args > env vars > defaults."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Server configuration, resolved from CLI args, env vars, and defaults."""

    project: str
    location: str
    allowed_datasets: list[str] | None
    default_limit: int
    max_limit: int
    max_bytes_billed: int
    sample_rows: int
    key_file: str | None


def _positive_int(s: str) -> int:
    """argparse type validator: only accept positive integers."""
    n = int(s)
    if n <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {n}")
    return n


def build_config(argv: list[str], env: Mapping[str, str]) -> Config:
    """Parse CLI args plus env vars into a typed Config object.

    Precedence (later wins): defaults < env vars < CLI args.
    Calls parser.error() (which exits) if --project / GCP_PROJECT_ID is missing.
    """
    parser = argparse.ArgumentParser(
        prog="bq-readonly-mcp",
        description="Read-only BigQuery MCP server with auto-LIMIT and cost guards.",
    )
    parser.add_argument("--project", default=env.get("GCP_PROJECT_ID"))
    parser.add_argument("--location", default=env.get("BIGQUERY_LOCATION", "US"))
    parser.add_argument("--datasets", nargs="+", default=None)
    parser.add_argument(
        "--default-limit",
        type=_positive_int,
        default=int(env.get("BIGQUERY_DEFAULT_LIMIT", "50")),
    )
    parser.add_argument(
        "--max-limit",
        type=_positive_int,
        default=int(env.get("BIGQUERY_MAX_LIMIT", "10000")),
    )
    parser.add_argument(
        "--max-bytes-billed",
        type=_positive_int,
        default=int(env.get("BIGQUERY_MAX_BYTES_BILLED", str(1_073_741_824))),
    )
    parser.add_argument(
        "--sample-rows",
        type=_positive_int,
        default=int(env.get("BIGQUERY_SAMPLE_ROWS", "3")),
    )
    parser.add_argument(
        "--key-file",
        default=env.get("GOOGLE_APPLICATION_CREDENTIALS"),
    )

    ns = parser.parse_args(argv)

    if not ns.project:
        parser.error("--project (or GCP_PROJECT_ID env var) is required")

    # CLI flag wins; otherwise check env var and parse comma-separated list
    allowed = ns.datasets
    if allowed is None and "BIGQUERY_ALLOWED_DATASETS" in env:
        allowed = [d.strip() for d in env["BIGQUERY_ALLOWED_DATASETS"].split(",") if d.strip()]

    return Config(
        project=ns.project,
        location=ns.location,
        allowed_datasets=allowed,
        default_limit=ns.default_limit,
        max_limit=ns.max_limit,
        max_bytes_billed=ns.max_bytes_billed,
        sample_rows=ns.sample_rows,
        key_file=ns.key_file,
    )
