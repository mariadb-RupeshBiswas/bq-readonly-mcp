# CLAUDE.md — bq-readonly-mcp

This file is the at-a-glance briefing for any Claude session working on this repo.

## What this is

A public, read-only BigQuery MCP server. Lets MCP-aware LLMs (Claude, Cursor, Windsurf, Copilot) explore datasets, inspect schemas, and run SELECT-only queries against a Google Cloud project, with strict cost and safety guardrails.

- **PyPI:** `bq-readonly-mcp`
- **GitHub:** `mariadb-RupeshBiswas/bq-readonly-mcp` (public)
- **Author:** Rupesh Biswas <rupesh.biswas@mariadb.com>
- **License:** MIT
- **Python:** `>=3.11`
- **Auth:** ADC default; optional `--key-file`

The full design lives in `docs/superpowers/specs/2026-04-26-bq-readonly-mcp-design.md`. **Read that before making non-trivial changes.**

## Public-repo hygiene — DO NOT SKIP

This is a public repo. The author is fine with their email being public, but **nothing else internal** is allowed in tracked files:

- ❌ No real internal project IDs (e.g. company-specific GCP projects)
- ❌ No customer names, employee names, internal product names
- ❌ No internal hostnames, slack channels, Jira/Confluence URLs
- ❌ No real spreadsheet IDs or file paths that reveal internal structure
- ✅ All examples use `your-project-id`, `your_dataset`, or `bigquery-public-data.*`
- ✅ The author's email (`rupesh.biswas@mariadb.com`) is the only identifying string allowed

`tests/test_no_pii.py` enforces this with a positive allowlist. If you're tempted to add a "real" example, use a Google public-data project instead (`bigquery-public-data.samples.shakespeare`, `bigquery-public-data.usa_names.usa_1910_2013`, etc.).

## Tech stack

- **Build:** `uv` + `hatchling`
- **Lint:** `ruff` (line-length 100, target `py311`)
- **Types:** `mypy` (non-strict, ignore_missing_imports)
- **Tests:** `pytest` + `pytest-asyncio` + `pytest-mock`; `tests/integration/` skipped in CI (no GCP creds in CI)
- **MCP framework:** `mcp[cli]>=1.9.0`
- **BigQuery:** `google-cloud-bigquery`, `google-auth`

## Layout

```
src/bq_readonly_mcp/
  __init__.py     # version
  __main__.py     # python -m entry
  server.py       # MCP wiring, CLI parsing
  auth.py         # ADC + key-file
  config.py       # CLI/env → typed Config
  models.py       # Pydantic input/output models
  safety.py       # SQL validator, LIMIT injector — high-stakes module
  bq.py           # Thin BigQuery wrapper
  tools/          # One file per MCP tool
tests/
  unit/           # No network, runs in CI
  integration/    # Hits real BigQuery against bigquery-public-data, local-only
```

## The 7 tools

1. `list_datasets` — names + descriptions, optional name filter
2. `list_tables` — names + types in a dataset, optional name filter
3. `get_table_metadata` — table-level only (type, partitioning, clustering, row count, size)
4. `describe_columns` — column schema only (cheap)
5. `get_table` — full bundle (metadata + columns + 3 sample rows)
6. `run_query` — SELECT-only with auto-LIMIT, dry-run cost guard, bytes-billed cap
7. `estimate_query_cost` — standalone dry-run, returns bytes + USD

## Guardrail defaults (overridable via CLI/env)

| Setting | Default | Override |
|---|---|---|
| Auto-LIMIT | 50 | `limit` param per call, up to `--max-limit` |
| Max LIMIT cap | 10,000 | `--max-limit` |
| Max bytes billed/query | 1 GB | `--max-bytes-billed` |
| Dry-run guard | always on | `--no-dryrun-guard` |
| Dataset allowlist | none (warn at startup) | `--datasets ds1 ds2` |

## SQL validator pipeline (the high-stakes path)

1. Strip comments (`--`, `/* */`)
2. Reject multi-statement
3. Reject if not starting with `SELECT` or `WITH`
4. Reject if any DML/DDL keyword as a top-level token (word-boundary regex, string literals masked first)
5. Inject `LIMIT N` if absent and `no_limit != true`
6. `dryRun: true` first → use `referencedTables` for allowlist check, `totalBytesProcessed` for cost check
7. Refuse if outside allowlist or over cost cap
8. Real query with `maximumBytesBilled` set on the job (defense in depth)

## Workflow rules

- **Branch policy:** `main` is protected — PRs only, 1 approving review, linear history, CI must pass.
- **Commits:** Atomic, conventional (`feat(scope):`, `fix(scope):`, `docs:`, `test:`, `chore:`, `ci:`). Keep changes small enough to revert cleanly.
- **TDD-friendly:** `safety.py` and `bq.py` are easy to TDD. Write tests first when modifying validator logic.
- **No new tools without spec update.** If you add a tool, update the spec doc and `CLAUDE.md` before coding.
- **No customer/internal data in tests, fixtures, examples, agent files, or config samples.**

## Running locally

```bash
# One-time
gcloud auth application-default login
uv sync --extra dev

# Run the server (stdio) — usually invoked by an MCP client
uv run bq-readonly-mcp --project YOUR_PROJECT --location US

# Tests
uv run pytest tests/unit/ -q          # always-safe
uv run pytest -m integration -q       # hits BigQuery via ADC

# Quality checks
uv run ruff check src tests
uv run mypy src
```

## Releasing

1. Bump `version` in `pyproject.toml` (semver).
2. Open PR, get review, merge.
3. `Publish` workflow runs on push to `main`, idempotent: it'll skip if the version is already on PyPI.
4. Smoke test: `uvx bq-readonly-mcp --help` after the run completes.

## Related repos in the same author's ecosystem

- `mariadb-RupeshBiswas/google-sheets-mcp` (`g-sheet-mcp` on PyPI) — read-only Google Sheets MCP, similar shape, used as a structural reference for this project.
