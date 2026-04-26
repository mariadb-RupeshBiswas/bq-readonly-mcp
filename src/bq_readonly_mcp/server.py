"""MCP server entry point.

Wires the 7 tools together, performs the startup checks (dataset enumeration
warning when no allowlist), and serves over stdio.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any

import mcp.server.stdio
from google.api_core.exceptions import GoogleAPIError, Unauthenticated
from google.auth.exceptions import RefreshError
from mcp.server import Server
from mcp.types import TextContent, Tool
from pydantic import ValidationError

from . import __version__
from .auth import AuthError, build_bigquery_client
from .bq import BQClient, CostExceededError, DatasetNotAllowedError
from .config import Config, build_config
from .safety import SafetyError
from .tools import (
    describe_columns,
    estimate_query_cost,
    get_table,
    get_table_metadata,
    list_datasets,
    list_tables,
    run_query,
)

LOG = logging.getLogger("bq_readonly_mcp")

# Ordered list of all tool modules — order determines `list_tools` output
TOOL_MODULES = (
    list_datasets,
    list_tables,
    get_table_metadata,
    describe_columns,
    get_table,
    run_query,
    estimate_query_cost,
)


def build_tool_registry() -> list[dict[str, Any]]:
    """Return a plain-dict registry of all tools (name, description, input_schema)."""
    return [
        {
            "name": m.NAME,
            "description": m.DESCRIPTION,
            "input_schema": m.INPUT_SCHEMA,
        }
        for m in TOOL_MODULES
    ]


_WARN_PREVIEW_COUNT = 3  # show at most this many dataset IDs in the warning


def _warn_if_no_allowlist(cfg: Config, bq: BQClient) -> None:
    """Print a clear stderr warning when no dataset allowlist is configured.

    Truncates the dataset list to the first _WARN_PREVIEW_COUNT IDs to avoid
    accidentally pasting a full dataset inventory into chat logs or tickets.
    """
    if cfg.allowed_datasets is not None:
        return
    try:
        datasets = bq.list_datasets()
    except Exception as exc:
        LOG.warning("could not enumerate datasets at startup: %s", exc)
        return
    ids = sorted(d.dataset_id for d in datasets)

    # Truncate the preview; log the full list at DEBUG for diagnostics
    preview = ids[:_WARN_PREVIEW_COUNT]
    remainder = len(ids) - _WARN_PREVIEW_COUNT
    ids_display = " ".join(preview) + (f" ... (and {remainder} more)" if remainder > 0 else "")
    LOG.debug("all visible datasets: %s", ids)

    print(
        f"WARNING: no --datasets allowlist configured. "
        f"This server can read all {len(ids)} datasets visible to your ADC identity in "
        f"project {cfg.project!r}: {ids_display}\n"
        f"To restrict, restart with: --datasets {ids_display.split(' ...')[0]}",
        file=sys.stderr,
    )


async def dispatch_tool(
    name: str, arguments: dict[str, Any], cfg: Config, bq: BQClient
) -> list[TextContent]:
    """Dispatch a named tool call to its handler and return TextContent results.

    Extracted as a module-level function so it can be unit-tested without
    spinning up the full MCP stdio server.
    """
    result: Any
    try:
        if name == list_datasets.NAME:
            result = await asyncio.to_thread(list_datasets.handle, arguments, bq=bq)
        elif name == list_tables.NAME:
            result = await asyncio.to_thread(list_tables.handle, arguments, bq=bq)
        elif name == get_table_metadata.NAME:
            result = await asyncio.to_thread(get_table_metadata.handle, arguments, bq=bq)
        elif name == describe_columns.NAME:
            result = await asyncio.to_thread(describe_columns.handle, arguments, bq=bq)
        elif name == get_table.NAME:
            result = await asyncio.to_thread(
                get_table.handle,
                arguments,
                bq=bq,
                default_sample_rows=cfg.sample_rows,
                max_bytes_billed=cfg.max_bytes_billed,
            )
        elif name == run_query.NAME:
            result = await asyncio.to_thread(
                run_query.handle,
                arguments,
                bq=bq,
                default_limit=cfg.default_limit,
                max_limit=cfg.max_limit,
                max_bytes_billed=cfg.max_bytes_billed,
            )
        elif name == estimate_query_cost.NAME:
            result = await asyncio.to_thread(
                estimate_query_cost.handle,
                arguments,
                bq=bq,
                max_bytes_billed=cfg.max_bytes_billed,
            )
        else:
            raise ValueError(f"unknown tool: {name!r}")
    except ValidationError as exc:
        # ValidationError is a subclass of ValueError; must be checked first
        return [TextContent(type="text", text=f"error: invalid input: {exc}")]
    except (SafetyError, CostExceededError, DatasetNotAllowedError, ValueError) as exc:
        # Return structured errors as text so the MCP client sees them
        return [TextContent(type="text", text=f"error: {exc}")]
    except (RefreshError, Unauthenticated) as exc:
        # ADC tokens can expire mid-session (gcloud reauth required).
        # Return an actionable message so the LLM/user knows the next step
        # rather than a raw stack trace.
        LOG.warning("auth refresh failure: %s", exc)
        return [
            TextContent(
                type="text",
                text=(
                    "error: authentication has expired. Run "
                    "`gcloud auth application-default login` and retry. "
                    f"(underlying: {exc})"
                ),
            )
        ]
    except GoogleAPIError as exc:
        # Detect HTTP 401 even when the API library wraps it as a generic GoogleAPIError
        if getattr(exc, "code", None) == 401 or "401" in str(exc):
            return [
                TextContent(
                    type="text",
                    text=(
                        "error: BigQuery rejected the request as unauthenticated. "
                        "Try `gcloud auth application-default login` to refresh ADC."
                    ),
                )
            ]
        return [TextContent(type="text", text=f"error: BigQuery API error: {exc}")]
    except Exception as exc:
        # Last-resort catch: keeps the MCP loop alive; logs full traceback for debugging
        LOG.exception("unexpected error in tool %s", name)
        return [TextContent(type="text", text=f"error: unexpected error ({type(exc).__name__})")]

    return [TextContent(type="text", text=json.dumps(result, default=str))]


async def _serve(cfg: Config, bq: BQClient) -> None:
    """Async MCP server loop: register tools and serve over stdio."""
    # Pass our package version so MCP clients see "bq-readonly-mcp 0.1.x" in
    # serverInfo, not the version of the underlying mcp framework
    app = Server("bq-readonly-mcp", version=__version__)

    @app.list_tools()
    async def _list_tools() -> list[Tool]:
        return [
            Tool(name=t["name"], description=t["description"], inputSchema=t["input_schema"])
            for t in build_tool_registry()
        ]

    @app.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        return await dispatch_tool(name, arguments, cfg, bq)

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main() -> int:
    """CLI entry point. Returns process exit code (0 = clean, 2 = error)."""
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Build config from argv + env; build_config calls parser.error() on bad input
    try:
        cfg = build_config(argv=sys.argv[1:], env=os.environ)
    except SystemExit as e:
        # argparse uses exit(0) for --help and exit(2) for usage errors
        return 0 if e.code == 0 else int(e.code or 2)

    # Authenticate; fail fast with a clear message on bad credentials
    try:
        client = build_bigquery_client(cfg)
    except AuthError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return 2

    bq = BQClient(client=client, allowed_datasets=cfg.allowed_datasets)
    _warn_if_no_allowlist(cfg, bq)

    asyncio.run(_serve(cfg, bq))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
