# bq-readonly-mcp — Design Spec

**Date:** 2026-04-26
**Author:** Rupesh Biswas
**Status:** Draft for review

---

## 1. Purpose

A public, read-only BigQuery MCP server that LLMs can safely point at a Google Cloud project to explore datasets, inspect schemas, and run SELECT queries — with strict guardrails so nobody runs up a surprise bill or executes an unintended write.

**Non-goals (v0.1):**
- Write operations (INSERT/UPDATE/DELETE/DDL) — never.
- Vector search / embeddings — deferred to a later release.
- Query history or job listing — privacy footgun, deferred indefinitely.
- Routine/UDF metadata — niche, deferred.
- Multi-project support inside a single server instance — one server, one project.

---

## 2. Audience and threat model

**Intended user:** A data engineer or analyst who wants to give an MCP-aware LLM (Claude, Cursor, Windsurf, Copilot) read access to BigQuery for exploration and ad-hoc analysis, without that LLM being able to mutate data or run cost-runaway queries.

**Threats explicitly mitigated:**

| Threat | Mitigation |
|---|---|
| LLM tries to run DML/DDL | SQL validator rejects everything except `SELECT` and `WITH` (after comment stripping). |
| Prompt injection causes LLM to run a wildly expensive query | Pre-flight dry-run estimates `totalBytesProcessed`; refused if over `--max-bytes-billed` (default 1 GB). The job itself also enforces the cap server-side. |
| LLM dumps a huge result into context | Auto-`LIMIT 50` appended to every query unless caller explicitly overrides; max overridable limit 10,000. |
| LLM crafts SQL with comments to hide dangerous statements | Comments stripped before validation; multi-statement queries rejected. |
| User accidentally exposes sensitive datasets | Optional `--datasets` allowlist restricts which datasets the server will surface or query. |
| Credential theft | No credentials stored or transmitted by this server. ADC is owned by the user's `gcloud` install with OS-level file permissions. |
| Supply-chain dependency CVEs | Pinned versions in `pyproject.toml`, committed `uv.lock`, dependabot alerts on the public GitHub repo. |

**Threats NOT mitigated (out of scope, documented as user responsibility):**
- Compromise of the user's local machine (process running as user gets ADC tokens).
- IAM over-permissioning at the GCP level — the server only restricts what its tools can do, not what the user's identity can do.
- The LLM exfiltrating data the user has legitimate access to (this is the inherent trade-off of giving an LLM tool use over BigQuery).

---

## 3. Architecture

A single-process Python MCP server speaking stdio. Modular layout so each unit is small and independently testable.

```
src/bq_readonly_mcp/
├── __init__.py        # version
├── __main__.py        # `python -m bq_readonly_mcp` entry
├── server.py          # MCP wiring: tool registry, request dispatch, CLI parsing
├── auth.py            # ADC resolution, BigQuery client construction
├── config.py          # CLI args + env var resolution → typed Config object
├── models.py          # Pydantic models for tool inputs/outputs
├── safety.py          # SQL validator, LIMIT injector, comment stripper
├── bq.py              # Thin BigQuery wrapper (list/get/query/dry-run)
└── tools/             # One file per MCP tool
    ├── list_datasets.py
    ├── list_tables.py
    ├── get_table_metadata.py
    ├── describe_columns.py
    ├── get_table.py
    ├── run_query.py
    └── estimate_query_cost.py
```

**Why this split:**
- `safety.py` is the highest-stakes module. Isolating it makes it trivially unit-testable with no BigQuery dependency.
- `bq.py` is the only module that touches the BigQuery client; everything else gets a typed wrapper. Lets us mock cleanly in tests.
- One tool per file keeps each tool small (~50 lines), with its own input/output model and one clear responsibility.

---

## 4. Configuration

All config resolves in this order (later overrides earlier): defaults → environment variables → CLI flags.

| CLI flag | Env var | Default | Required | Description |
|---|---|---|---|---|
| `--project` | `GCP_PROJECT_ID` | none | **yes** | GCP project ID to bill and query against. |
| `--location` | `BIGQUERY_LOCATION` | `US` | no | BigQuery location (`US`, `EU`, `asia-northeast1`, …). |
| `--datasets` | `BIGQUERY_ALLOWED_DATASETS` (comma-separated) | none (all readable) | no | Restrict listing/querying to these datasets. |
| `--default-limit` | `BIGQUERY_DEFAULT_LIMIT` | `50` | no | Auto-LIMIT appended when caller doesn't specify one. |
| `--max-limit` | `BIGQUERY_MAX_LIMIT` | `10000` | no | Hard ceiling on the LIMIT a caller can request. |
| `--max-bytes-billed` | `BIGQUERY_MAX_BYTES_BILLED` | `1073741824` (1 GB) | no | Per-query bytes-billed cap, enforced via dry-run + job config. |
| `--sample-rows` | `BIGQUERY_SAMPLE_ROWS` | `3` | no | Rows returned by `get_table` sample. |
| `--key-file` | `GOOGLE_APPLICATION_CREDENTIALS` | none (uses ADC) | no | Optional service-account key for non-interactive use. |

CLI args win over env vars; env vars win over defaults.

---

## 5. Tools (the public API)

Every tool returns structured JSON. Inputs are validated by Pydantic; invalid input returns a clear error message instead of a stack trace.

### 5.1 `list_datasets`

**Input:** `{ name_contains?: string }` — optional case-insensitive substring filter.
**Output:** `[{ dataset_id, location, friendly_name?, description? }]`
**Cost:** Metadata only, no query bytes.
**Behavior:** If `--datasets` allowlist is set, only those are returned (and `name_contains` filters within them).

### 5.2 `list_tables`

**Input:** `{ dataset_id: string, name_contains?: string }`
**Output:** `[{ table_id, type ("TABLE"|"VIEW"|"MATERIALIZED_VIEW"|"EXTERNAL"), created, friendly_name? }]`
**Cost:** Metadata only.

### 5.3 `get_table_metadata`

**Input:** `{ dataset_id: string, table_id: string }`
**Output:**
```json
{
  "table_id": "...",
  "type": "TABLE",
  "description": "...",
  "labels": {...},
  "created": "ISO-8601",
  "modified": "ISO-8601",
  "row_count": 12345,
  "size_bytes": 67890,
  "partitioning": { "type": "DAY"|"HOUR"|"MONTH"|"YEAR"|"INTEGER_RANGE"|null, "column": "...", "expiration_ms": 1234 } | null,
  "clustering": ["col1", "col2"] | null,
  "expires": "ISO-8601" | null,
  "time_travel_window_hours": 168
}
```
**Cost:** Metadata only.

### 5.4 `describe_columns`

**Input:** `{ dataset_id: string, table_id: string }`
**Output:** `[{ name, type, mode ("NULLABLE"|"REQUIRED"|"REPEATED"), description? }]`
**Cost:** Metadata only.

### 5.5 `get_table`

**Input:** `{ dataset_id: string, table_id: string, sample_rows?: int (default = config.sample_rows) }`
**Output:** Combination of `get_table_metadata` + `describe_columns` + sample rows.
**Cost:** One small `SELECT * FROM ds.table LIMIT N` query for samples.
**Safety:** Sample query goes through the same dry-run guard.

### 5.6 `run_query`

**Input:**
```json
{ "query": "SELECT ...", "limit"?: int, "no_limit"?: bool, "dry_run"?: bool }
```
**Output:** `{ rows: [...], schema: [...], total_bytes_processed: int, total_bytes_billed: int, cache_hit: bool, job_id: string, location: string }`

**Validation pipeline (in order):**
1. Strip comments (`--`, `/* */`).
2. Reject if multi-statement (more than one top-level `;`-terminated statement).
3. Reject if not starting with `SELECT` or `WITH` after stripping leading whitespace.
4. Reject if any DML/DDL keyword (`INSERT`, `UPDATE`, `DELETE`, `MERGE`, `CREATE`, `DROP`, `ALTER`, `TRUNCATE`, `REPLACE`, `GRANT`, `REVOKE`, `EXPORT`) appears as a top-level token. Token boundary is enforced via a regex of the form `\b(INSERT|UPDATE|...)\b` applied case-insensitively to the comment-stripped query, after first ensuring we're not inside a string literal. (Identifiers like `delete_flag` won't match because of the word boundary; quoted strings won't match because they're stripped/masked first.)
5. Inject `LIMIT N` if no `LIMIT` already present and `no_limit != true`. Honor `limit` parameter (capped at `--max-limit`).
6. Run `dryRun: true` first. This serves two purposes: (a) authoritative table-reference enumeration via the job's `referencedTables` field, and (b) cost estimate via `totalBytesProcessed`.
7. If `--datasets` allowlist is set and any entry in `referencedTables` is outside the allowlist, refuse with the offending table name.
8. If `totalBytesProcessed > --max-bytes-billed`, refuse with the estimate and the configured cap.
9. Run real query with `maximumBytesBilled = --max-bytes-billed` set on the job config (defense in depth — re-enforces the cap server-side even if our local dry-run misjudges).

If `dry_run=true` is passed, only step 7 runs and the estimate is returned without executing.

### 5.7 `estimate_query_cost`

**Input:** `{ query: string }`
**Output:** `{ total_bytes_processed: int, estimated_usd: float, would_be_blocked: bool }`
**Cost:** Free (dry-run only).
**Behavior:** Runs `run_query` steps 1–4 (comment strip, multi-statement reject, SELECT/WITH check, DML/DDL keyword check), skips LIMIT injection, runs the dry-run, applies the allowlist check on `referencedTables`. Returns the estimate without executing the real query. Useful for the LLM to reason about cost before deciding to run.

---

## 6. Data flow

```
Client (Claude/Windsurf/Cursor)
  │ stdio (JSON-RPC)
  ▼
server.py  ──► CLI/env config ──► auth.py ──► BigQuery client
  │
  │ tool call routed by name
  ▼
tools/<tool>.py
  │ Pydantic validates input
  │ For run_query/estimate_query_cost: safety.py validates SQL
  ▼
bq.py wrapper
  │ list_datasets / get_table / query (with dry-run guard)
  ▼
google-cloud-bigquery
  │ HTTPS
  ▼
BigQuery API
```

---

## 7. Error handling

- **Invalid input:** Pydantic validation error → return MCP error response with the field and reason. No stack trace.
- **Auth failure:** ADC missing/expired → return a clear message instructing the user to run `gcloud auth application-default login` (with `--enable-gdrive-access` callout if relevant). No raw `DefaultCredentialsError`.
- **SQL validation failure:** Return the specific reason (e.g., "DML keyword `UPDATE` detected", "multi-statement queries not allowed").
- **Cost guard refusal:** Return the estimated bytes + USD + the configured cap, so the LLM understands what to do (raise the cap with `--max-bytes-billed`, narrow the query, or add a `WHERE`).
- **BigQuery API errors:** Surface the `code` and `message` from the API response, but strip any internal job IDs that aren't useful to the LLM.

All errors are JSON, with `error_type` and `message` keys, so the LLM can act on them programmatically.

---

## 8. Testing strategy

**Unit tests (`tests/unit/`):** No network access required. Run on every PR.
- `test_safety.py` — exhaustive SQL validator cases: SELECT/WITH allowed, every DML/DDL rejected, comment-hidden DML rejected, multi-statement rejected, LIMIT injection correctness, override behavior, cap enforcement.
- `test_config.py` — CLI/env precedence, defaults, type coercion.
- `test_models.py` — Pydantic input validation for each tool.
- `test_bq_mocked.py` — `bq.py` wrapper with mocked `google.cloud.bigquery.Client`. Verify `maximumBytesBilled` ends up on job config, dry-run is called before real execution, etc.

**Integration tests (`tests/integration/`):** Hit the real BigQuery API against `bigquery-public-data.*` datasets. Require ADC. **Skipped in CI by default** (no GCP creds in CI runner); marked with `@pytest.mark.integration` and run locally with `pytest -m integration`.
- `test_public_datasets.py` — query `bigquery-public-data.samples.shakespeare`, `bigquery-public-data.usa_names.usa_1910_2013`. Verify all 7 tools work end-to-end. Verify dry-run guard refuses a deliberately huge query against `bigquery-public-data.wikipedia.pageviews_2015` (which is hundreds of GB).

**Coverage target:** 90%+ on `safety.py` and `bq.py`; the high-stakes modules.

---

## 9. CI / publishing / branch protection

Mirrors `google-sheets-mcp`'s proven pattern.

**`.github/workflows/ci.yml`** — runs on PRs and pushes to `main`:
- Lint: `ruff check`
- Types: `mypy src`
- Tests: `pytest tests/unit/ -q` (integration tests skipped, require GCP creds)

**`.github/workflows/publish.yml`** — runs on push to `main` (i.e., after PR merge):
- Gate: `github.ref_protected == true` (workflow refuses to publish if branch protection got disabled)
- Builds with `uv build`
- Idempotent publish check: compares built artifacts against PyPI; only publishes if missing, fails if version is partially published with mismatched files.
- Uses `pypi` GitHub environment + `PYPI__TOKEN__` secret.

**Branch protection on `main`:**
- Require PR with 1 approving review
- Require status check `verify` (CI) to pass
- Require branches up-to-date before merge
- Require linear history (no merge commits)
- Require conversation resolution
- No force pushes, no deletion
- Admin enforcement: off (owner can bypass for emergency fixes)

---

## 10. Security posture

- ADC-only by default; optional `--key-file` for non-interactive scenarios (warned in README).
- BigQuery API requested with default scopes (project-bound). No Drive scope.
- No outbound HTTP from this server other than to Google APIs via the official client library.
- No `eval`, no dynamic code execution, no shell-out except optional `gcloud auth application-default login` invocation when ADC is missing (and only if user is on an interactive TTY).
- All error messages reviewed to avoid echoing back user input verbatim into logs (prompt-injection-via-error-log defense).
- Public-repo hygiene: no real project IDs, no customer/employee names, no real spreadsheet IDs in tracked files. All examples use `your-project-id`, `bigquery-public-data.*`, etc. Enforced by a `tests/test_no_pii.py` that greps tracked files for known internal strings (`mariadb-business-analytics`, `mariadb.com` outside author email, etc.).
- `SECURITY.md` for vuln reporting; `SECURITY_AUDIT.md` after Phase 8 self-audit.
- `.gitignore` covers `.env`, ADC JSON, `__pycache__`, `.venv`, `dist/`, `*.egg-info`.

---

## 11. Project metadata

| Field | Value |
|---|---|
| PyPI package name | `bq-readonly-mcp` |
| Python module | `bq_readonly_mcp` |
| Script entry | `bq-readonly-mcp` |
| GitHub repo | `mariadb-RupeshBiswas/bq-readonly-mcp` (public) |
| License | MIT |
| Author | Rupesh Biswas <rupesh.biswas@mariadb.com> |
| Initial version | 0.1.0 |
| Python target | `>=3.11` |
| Build backend | `hatchling` |
| Lockfile | `uv.lock` (committed) |
| Linter | `ruff` |
| Type checker | `mypy` |
| Test runner | `pytest` + `pytest-asyncio` + `pytest-mock` |

---

## 12. Out of scope (deferred)

- Vector search via `ML.GENERATE_EMBEDDING` + `VECTOR_SEARCH` — needs Vertex AI external connection setup, larger surface, deferred to v0.2.
- Job history / `recent_jobs` — privacy footgun (exposes other users' queries), no current plan to add.
- INFORMATION_SCHEMA helpers (e.g. project-wide column search) — could be a useful v0.2 add.
- Materialized view refresh metadata, routine/UDF metadata — niche, on demand.
- Multi-project support — would require either re-auth per project or trust boundary changes; one server per project is the v0.1 stance.

---

## 13. Acceptance criteria

This spec is "done" when:
- All 7 tools implemented and unit-tested with ≥90% coverage on `safety.py`/`bq.py`.
- `pytest tests/unit/` green; `pytest -m integration` green locally against public datasets.
- `ruff` and `mypy` clean.
- CI pipeline green on a fresh PR.
- Publish workflow successfully publishes 0.1.0 to PyPI.
- `uvx bq-readonly-mcp --help` works on a fresh machine.
- Branch protection enforced on `main`.
- Security audit (Phase 8) signed off, no P0/P1 open.
- `mcp-config-examples/` contains working configs for Claude Code, Claude Desktop, Cursor, Windsurf, Copilot.
- `~/.codeium/windsurf/mcp_config.json` and `/Users/rupeshbiswas/projects/.mcp.json` updated to use `uvx bq-readonly-mcp`.
- `google-sheets-mcp` re-audit complete; any P0/P1 fixed and republished.
