"""Tool: run a SELECT/WITH query with auto-LIMIT and cost guard."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import RunQueryInput
from ..safety import inject_limit, validate_select_query

NAME = "run_query"
DESCRIPTION = (
    "Execute a read-only SELECT or WITH query against BigQuery. Behavior:\n"
    "- DML/DDL keywords are rejected (no INSERT/UPDATE/DELETE/MERGE/CREATE/DROP/ALTER/etc).\n"
    "- An auto-LIMIT is appended if the query has no LIMIT (default 50, configurable). "
    "Pass `limit` to override (up to the server-configured maximum), or `no_limit: true` "
    "to disable injection entirely.\n"
    "- A free dry-run runs first; if estimated bytes processed exceeds the configured cap, "
    "the query is refused.\n"
    "- The real job sets `maximumBytesBilled` as a defense-in-depth cap.\n"
    "- Pass `dry_run: true` to get cost estimate only without executing."
)
INPUT_SCHEMA = RunQueryInput.model_json_schema()


def handle(
    args: dict[str, Any],
    *,
    bq: BQClient,
    default_limit: int,
    max_limit: int,
    max_bytes_billed: int,
) -> dict[str, Any]:
    parsed = RunQueryInput(**args)
    validate_select_query(parsed.query)

    # Short-circuit: caller only wants a cost estimate, not real execution.
    if parsed.dry_run:
        est = bq.estimate_query_cost(parsed.query, max_bytes_billed=max_bytes_billed)
        return est.model_dump()

    if parsed.limit is not None:
        if parsed.limit > max_limit:
            raise ValueError(
                f"limit {parsed.limit} exceeds max_limit {max_limit} configured for this server"
            )
        effective_limit = parsed.limit
    else:
        effective_limit = default_limit

    # Respect no_limit flag — skip injection if caller explicitly opts out.
    prepared = parsed.query if parsed.no_limit else inject_limit(parsed.query, effective_limit)

    result = bq.run_query(prepared, max_bytes_billed=max_bytes_billed)
    return result.model_dump()
