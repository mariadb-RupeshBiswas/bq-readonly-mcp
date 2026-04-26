# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-26

### Added
- Initial release.
- 7 tools: `list_datasets`, `list_tables`, `get_table_metadata`, `describe_columns`, `get_table`, `run_query`, `estimate_query_cost`.
- Strict `SELECT`/`WITH`-only SQL validator with comment stripping, multi-statement rejection, DML/DDL keyword rejection, backslash and backtick awareness.
- Auto-LIMIT 50 with override (max 10,000 by default, raisable via `--max-limit`).
- Bytes-billed cap with dry-run guard (default 1 GB, configurable via `--max-bytes-billed`).
- Optional `--datasets` allowlist; warn at startup when unset.
- ADC default with optional `--key-file` for non-interactive use.
