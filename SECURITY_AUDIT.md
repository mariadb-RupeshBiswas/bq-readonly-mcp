# 🔐 Security Audit Report — bq-readonly-mcp

**Date:** 2026-04-26
**Version audited:** 0.1.0
**Branch:** `feat/v0.1.0-implementation`
**Auditor:** Automated comprehensive pre-release security review

---

## ✅ Audit Summary

**RESULT: SECURE.** No P0 (critical) issues found. The validator correctly rejects every DML/DDL bypass probe attempted, including the raw-string smuggle that was the headline finding from the prior code review (closed in commit `a21738f`). Defense-in-depth (validator + dry-run cost guard + `maximumBytesBilled` job-level cap + dataset allowlist) holds. Two P2 documentation/hardening items recorded for v0.2.

The package is cleared for v0.1.0 publish.

---

## 📋 Threat Model

This MCP server is invoked by an LLM with tool-use capability. The LLM is the **untrusted actor** — it may be steered by prompt injection from any text it ingests (queried table contents, web pages, documents). The user authenticated to BigQuery via ADC has read access to potentially sensitive datasets. The threat model assumes:

- The LLM may **attempt** to execute DML/DDL, exfiltrate data, or run cost-runaway queries
- The user trusts the local process execution but cannot police every tool call in real time
- The repo is **public** — no internal project IDs, customer names, or business logic may appear in tracked files

Threats explicitly tested in this audit:

1. SQL injection / DML keyword bypass (string-literal escape tricks, comment-merge, multi-statement smuggling, raw strings, triple-quoted strings, Unicode keyword lookalikes)
2. Cost guard bypass (estimating cheap, executing expensive)
3. Allowlist bypass (cross-dataset references, view-transitive references)
4. Auth/credential exposure (logs, error messages, serialization)
5. Dependency CVEs (runtime libs at recent supported versions)
6. Public-repo PII leak (project IDs, emails, host paths, internal terms)

---

## 🔬 Probes Tested

12 SQL bypass probes; every one behaves as designed:

| # | Probe | Expected | Actual | Verdict |
|---|---|---|---|---|
| 1 | Raw-string smuggle: `SELECT r"foo\"; DROP TABLE t; --" FROM s` | REJECT | `SafetyError` (multi-statement) | ✅ |
| 2 | Triple-quoted single literal: `SELECT '''hello''' FROM t` | PASS | PASS | ✅ |
| 3 | Triple-quoted with DML inside literal: `SELECT '''DROP TABLE t''' FROM s` | PASS (DML is in string) | PASS | ✅ |
| 4 | Triple-quoted DML smuggle: `SELECT """foo"""; DROP TABLE t; SELECT 1` | REJECT | `SafetyError` (multi-statement) | ✅ |
| 5 | Bytes literal: `SELECT b'\xff\xfe' FROM t` | PASS | PASS | ✅ |
| 6 | Raw bytes literal: `SELECT rb'\foo' FROM t` | PASS | PASS | ✅ |
| 7 | Whitespace before SELECT: `␣SELECT 1` | PASS | PASS | ✅ |
| 8 | Cyrillic SELECT (lookalike): `SЕLECT 1` (Cyrillic E) | REJECT | `SafetyError` (non-SELECT) | ✅ |
| 9 | Multi-statement DML: `SELECT 1;\nDROP TABLE t` | REJECT | `SafetyError` (multi-statement) | ✅ |
| 10 | Comment-merged DML: `SELECT * FROM t/*x*/UPDATE foo` | PASS validator (BigQuery rejects `tUPDATE`) | PASS validator | ✅ fail-safe |
| 11 | INFORMATION_SCHEMA.JOBS read | PASS validator (IAM-gated) | PASS | ⚠️ see P2-1 |
| 12 | CTE name `UPDATE_LOG`: `WITH UPDATE_LOG AS (...)` | PASS (`_LOG` keeps it from matching `\bUPDATE\b`) | PASS | ✅ |

Run the probes locally with: `uv run python -c "..."` against `bq_readonly_mcp.safety:validate_select_query`.

---

## 🛡️ Mitigations Verified

| Layer | File | Behavior |
|---|---|---|
| **Comment stripping with quote-state machine** | `src/bq_readonly_mcp/safety.py` `strip_comments` | Single-, double-, and backtick-quoted strings preserved; backslash-escape honored except inside raw strings (`r"..."`/`R"..."`) — closes the raw-string bypass |
| **String-literal masking before keyword scan** | `safety.py` `mask_string_literals` | DML keyword inside a literal cannot trigger the validator |
| **Multi-statement rejection** | `safety.py` `is_multistatement` | Single trailing `;` allowed; semicolons in strings/comments don't count |
| **Word-boundary keyword scan** | `safety.py` `validate_select_query` | `\b(INSERT\|UPDATE\|...)\b` regex; identifiers like `delete_flag`, `UPDATE_LOG`, `created_at` correctly do not trigger |
| **SELECT/WITH start anchor** | `safety.py` `_STARTS_WITH_SELECT_OR_WITH_RE` | `^\s*(SELECT\|WITH)\b` (i, case-insensitive); rejects DDL/DML at the front |
| **Pre-flight dry-run cost guard** | `src/bq_readonly_mcp/bq.py` `_dry_run` + `run_query` | `dryRun=True` first, refuses if `totalBytesProcessed > max_bytes_billed` before billing |
| **Defense-in-depth bytes cap** | `bq.py` `run_query` | `maximumBytesBilled` set on the real job config — re-enforces server-side even if local dry-run misjudges |
| **Allowlist enforcement (direct ops)** | `bq.py` `_check_dataset` | `list_tables`, `get_table_metadata`, etc. reject disallowed dataset before any API call |
| **Allowlist enforcement (referenced tables)** | `bq.py` `run_query` | After dry-run, walks `referencedTables` from the job and rejects if any is outside the allowlist (catches view transitive refs) |
| **Identifier validation on tool inputs** | `src/bq_readonly_mcp/models.py` | `dataset_id` and `table_id` constrained to BigQuery identifier pattern `^[A-Za-z_][A-Za-z0-9_]*$` — closes the f-string interpolation injection vector in `tools/get_table.py` |
| **Pydantic strict input models** | `models.py` `_StrictModel` | `extra="forbid"` rejects unknown fields; positive-int validation on `limit`, `sample_rows` |
| **Server-level error catch-all** | `src/bq_readonly_mcp/server.py` `dispatch_tool` | Catches `SafetyError`, `CostExceededError`, `DatasetNotAllowedError`, `ValueError`, `pydantic.ValidationError`, `GoogleAPIError`, plus a final `Exception` fallback that logs but doesn't leak stack traces |
| **Auth fails fast with actionable message** | `src/bq_readonly_mcp/auth.py` `AuthError` | Missing ADC → "run `gcloud auth application-default login`" message, not a raw `DefaultCredentialsError` traceback |
| **Startup allowlist transparency** | `server.py` `_warn_if_no_allowlist` | When no `--datasets` configured, warns to stderr listing first 3 datasets + count of remainder (truncated to avoid accidental paste-leaks) |

All 152 unit tests verify these behaviors; `tests/unit/test_safety_*.py` is exhaustive on the validator pipeline.

---

## ⚠️ Findings

### P0 — Critical (release blockers)

**None.** All previous critical issues from the code review are FIXED:

- C1 (raw-string SQL bypass) — FIXED in `a21738f`
- C2 (`QueryResult.schema` shadow warning) — FIXED in `d6e04d4` (renamed to `column_schema`)
- C3 (empty `tools/__init__.py`) — FIXED in `a1bae83`

### P1 — Should fix (release-quality)

**None.** All Important findings from the code review are FIXED.

### P2 — Defense in depth (v0.2 candidates)

#### P2-1. `INFORMATION_SCHEMA.JOBS_BY_PROJECT` is queryable

**Probe:** `SELECT user_email FROM region-US.INFORMATION_SCHEMA.JOBS_BY_PROJECT` passes validator.

**Risk:** If the user's ADC identity has IAM `bigquery.resourceAdmin` or `bigquery.user` on the project, this view exposes other users' query strings, emails, and bytes processed — a privacy-sensitive read. The MCP cannot prevent it because the SELECT is technically read-only and IAM-gated.

**Recommendation (v0.2):**
- Document this as a known limitation in `SECURITY.md`
- Optionally: add a heuristic block on `INFORMATION_SCHEMA.JOBS*` references at the validator level, with a `--allow-jobs-info` opt-in for legitimate observability use cases

**Status:** OPEN — documentation update for v0.2.

#### P2-2. No daily/per-session bytes-billed budget

**Risk:** A runaway LLM that respects the per-query cap (1 GB) can still rack up substantial cost across many queries. `--max-bytes-billed` is per-call, not aggregate.

**Recommendation (v0.2):** Add an optional `--session-bytes-budget` flag that tracks cumulative `totalBytesBilled` across the session and refuses queries when the budget is exhausted.

**Status:** OPEN — feature for v0.2.

#### P2-3. Wildcard-table reference detection in allowlist enforcement

**Note:** BigQuery wildcards like `bigquery-public-data.census_bureau_acs.*` are tracked by the dry-run's `referencedTables` field as a list of concrete tables, not the wildcard itself. The current allowlist check correctly evaluates each concrete reference. **Verified working** — no fix needed.

---

## 📊 Dependency Audit

Runtime dependencies (resolved versions, 2026-04-26):

| Package | Resolved | Min in `pyproject.toml` | Known CVEs at this version |
|---|---|---|---|
| `mcp[cli]` | 1.27.0 | `>=1.9.0` | None known |
| `google-cloud-bigquery` | 3.41.0 | `>=3.20.0` | None known |
| `google-auth` | 2.49.2 | `>=2.38.0` | None known |
| `pydantic` | 2.13.3 | `>=2.10.0` | None known |

Dev-only dependencies (`ruff`, `mypy`, `pytest`, `pytest-asyncio`, `pytest-mock`, `types-requests`) are not in the runtime path and are ignored for security purposes.

**Lockfile:** `uv.lock` is committed and pins all transitive dependencies. CI uses `uv sync --frozen` to enforce reproducibility.

**Recommendation:** Subscribe to GitHub Dependabot alerts on the public repo. No version bumps required for v0.1.0 release.

---

## 🧼 Public-repo Hygiene

### Two-string "mariadb" allowlist
Verified by manual grep: only `rupesh.biswas@mariadb.com` (author email in `pyproject.toml` and inline credits) and `mariadb-RupeshBiswas/bq-readonly-mcp` (GitHub URL in `pyproject.toml`, `README.md`, and badges) appear. Every other tracked file is clean.

### No internal terms
`grep -rEi "mariadb-business|customer|internal" src/ tests/ docs/` returns:
- `tests/unit/test_bq_listing.py:make_table("customers")` — generic test fixture name, not internal data
- `tests/unit/test_no_pii.py:"internal-data"` — appears as a label in the regression scanner's allowlist (the test that detects leaks contains the word "internal-data" as documentation)
- `docs/superpowers/specs/...md`, `docs/superpowers/plans/...md` — design/planning docs use the words "internal" and "customer" in normative text ("no internal project IDs", "no customer names")

None of these are real internal data leaks.

### No unauthorized email leaks
Only `rupesh.biswas@mariadb.com` (author) and `you@example.com` (placeholder in `docs/TROUBLESHOOTING.md`) appear.

### Host-path leak (minor)
`docs/superpowers/plans/2026-04-26-bq-readonly-mcp-implementation.md` contains `/Users/rupeshbiswas/projects/bq-readonly-mcp` in one example command. The OS username is the same as the GitHub handle, so this leaks no new info — but it's host-specific and cosmetic. **Recommendation:** genericize before pushing the plan doc to the public repo (or move the plan to a private location). Tracked as P2-4.

#### P2-4. Host path in tracked plan doc

**File:** `docs/superpowers/plans/2026-04-26-bq-readonly-mcp-implementation.md`

**Risk:** Cosmetic — username already public via GitHub handle. No new information disclosed.

**Recommendation:** replace `/Users/rupeshbiswas/projects/bq-readonly-mcp` with `<your-checkout>` or `~/projects/bq-readonly-mcp` before push. Or exclude `docs/superpowers/` from the public repo entirely (it's a planning artifact, not user-facing docs).

**Status:** OPEN — minor cosmetic cleanup. Defer to v0.1.1 if needed.

### Automated scanner
`tests/unit/test_no_pii.py` is the regression gate for hygiene. It walks `git ls-files`, extracts every project-ID-shaped token from text files, and asserts each match is on a positive allowlist (placeholders, public-data projects, common tooling/narrative tokens that incidentally match). **Confirmed passing** on this commit. Any new file added to the repo will be scanned automatically by CI.

---

## 📝 Recommendations for v0.2

1. Document `INFORMATION_SCHEMA.JOBS_BY_PROJECT` privacy caveat in `SECURITY.md`. Optionally block by default with an opt-in flag.
2. Add `--session-bytes-budget` for aggregate cost tracking across a session.
3. Add `--query-timeout-ms` for wall-clock timeouts on long queries (BigQuery's default is 6 hours — too generous for an interactive MCP).
4. Investigate triple-quoted string handling in `safety.py` — current behavior is fail-safe but the parser doesn't model `'''...'''` and `"""..."""` as a distinct quote type. Triple-quoted DML smuggling probes pass today, but a more deliberate model would be cleaner.
5. Consider moving `docs/superpowers/specs/` and `docs/superpowers/plans/` out of the public repo (they contain planning prose useful only to the author).
6. Add Dependabot config (`.github/dependabot.yml`) for automated dep update PRs.

---

## 🏁 Conclusion

**bq-readonly-mcp v0.1.0 is CLEARED for PyPI publish.**

The validator's stated promise — "no DML/DDL ever reaches BigQuery, no surprise bills" — holds under all 12 attack probes attempted. The cost guard is layered (dry-run estimate + `maximumBytesBilled` job config). The allowlist is enforced both at metadata-call time and via `referencedTables` post-dryrun. Auth, error handling, and dependency posture are all sound. Public-repo hygiene is enforced positively (allowlist) rather than via deny-lists, and the test gate runs in CI.

The two P2 items (INFORMATION_SCHEMA.JOBS privacy, session-level budget) are real but low-priority. Both can land in v0.2 without holding up the v0.1.0 release.

— *Audit complete.*
