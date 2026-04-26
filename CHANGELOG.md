# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] — 2026-04-26

### Fixed
- Server startup no longer blocks the MCP handshake on projects with many datasets. The `_warn_if_no_allowlist` warning previously called `bq.list_datasets()`, which fetches per-dataset metadata via `client.get_dataset()` — one API roundtrip per dataset. With 100+ datasets this exceeded the 60-second MCP-client init timeout (Windsurf reported "MCP server timed out after 60 seconds"). Now uses `client.list_datasets()` directly: a single paginated API call returning names only.

## [0.1.1] — 2026-04-26

### Fixed
- `run_query` now correctly populates `column_schema` on the result. Previously the field returned an empty list because `job.schema` is not always populated after `job.result()`. The fix captures the `RowIterator` once and reads `schema` from it (with `job.schema` fallback).
- `Server` now reports the package version (`0.1.1`) in the MCP `serverInfo.version` field. Previously it returned the underlying `mcp` framework version, which was misleading.

### Changed
- Planning artifacts under `docs/superpowers/` and integration tests no longer ship in the PyPI sdist. They remain on GitHub for design transparency and contributor reference. This keeps `pip install` slim and avoids shipping AI-process-flavored documents to end users.
- Genericized one host-specific path (`/Users/...`) that had been quoted in `SECURITY_AUDIT.md`; resolves the P2-4 cosmetic finding from the v0.1.0 audit.

## [0.1.0] — 2026-04-26

### Added
- Initial release.
- 7 tools: `list_datasets`, `list_tables`, `get_table_metadata`, `describe_columns`, `get_table`, `run_query`, `estimate_query_cost`.
- Strict `SELECT`/`WITH`-only SQL validator with comment stripping, multi-statement rejection, DML/DDL keyword rejection, backslash and backtick awareness.
- Auto-LIMIT 50 with override (max 10,000 by default, raisable via `--max-limit`).
- Bytes-billed cap with dry-run guard (default 1 GB, configurable via `--max-bytes-billed`).
- Optional `--datasets` allowlist; warn at startup when unset.
- ADC default with optional `--key-file` for non-interactive use.
