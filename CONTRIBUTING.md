# Contributing

Thank you for considering a contribution. This guide covers the rules and workflow for this project.

---

## Branch policy

- `main` is protected — no direct pushes.
- All changes go through a PR. At least 1 approving review is required before merge.
- CI (ruff, mypy, pytest) must pass.
- Prefer squash-merging to keep `main` history linear.

---

## Conventional commits

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).

**Format:** `type(scope): subject`

**Types:**

| Type | When to use |
|---|---|
| `feat` | New tool or user-visible feature |
| `fix` | Bug fix |
| `test` | Tests only |
| `docs` | Documentation only |
| `refactor` | Code change with no behavior change |
| `chore` | Maintenance (deps, config) |
| `ci` | CI/CD workflow changes |
| `build` | Build system changes |

**Scopes:** `safety`, `bq`, `config`, `server`, `auth`, `tools`, `docs`, `ci`

Examples:

```
feat(tools): add list_jobs tool
fix(safety): strip inline comments before DML check
test(bq): add coverage for CostExceededError path
docs: add QUICKSTART.md
```

---

## TDD expectation

`safety.py` and `bq.py` are the high-stakes modules. Any change to either
**must** be test-driven:

1. Write a failing test.
2. Run it — confirm it fails.
3. Implement the minimal fix.
4. Run tests — confirm they pass.
5. Commit.

New tools in `tools/` should have unit tests that mock `BQClient`.

---

## Before opening a PR

Run all three checks locally:

```bash
# Unit tests (fast, no BigQuery required)
uv run pytest tests/unit/ -q

# Lint
uv run ruff check src tests

# Type check
uv run mypy src
```

All three must be clean. The PII hygiene test (`tests/unit/test_no_pii.py`)
is part of the unit suite — make sure it passes if you added docs or config
files.

---

## Adding a new tool

1. Read the design spec at `docs/superpowers/specs/2026-04-26-bq-readonly-mcp-design.md` and update it with the new tool's contract.
2. Update `CLAUDE.md` (the 7 tools list → 8 tools list, etc.).
3. Create `src/bq_readonly_mcp/tools/<tool_name>.py` following the pattern of existing tools.
4. Register the tool in `src/bq_readonly_mcp/server.py`.
5. Add a unit test in `tests/unit/test_tool_<tool_name>.py`.
6. Update `README.md` (the tools table) and `CHANGELOG.md`.
7. Open a PR — do not merge without a review.

---

## Development setup

```bash
git clone https://github.com/mariadb-RupeshBiswas/bq-readonly-mcp.git
cd bq-readonly-mcp

# Install with dev extras
uv sync --extra dev

# Authenticate (needed for integration tests only)
gcloud auth application-default login
```

---

## Integration tests

Integration tests in `tests/integration/` hit real BigQuery and are skipped
in CI by default. To run them locally:

```bash
uv run pytest -m integration -q
```

They use `bigquery-public-data` and require a GCP project with billing
enabled. Set `GCP_PROJECT_ID` to your project before running.

---

## Public-repo hygiene

All examples, tests, and fixtures must use placeholder data. See `SECURITY.md`
for the full rules. The `tests/unit/test_no_pii.py` test enforces the positive
allowlist — if it fails after your change, either scrub the leak or add the
token to the allowlist with a comment explaining why it is safe.
