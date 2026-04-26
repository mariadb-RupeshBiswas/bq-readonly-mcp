# bq-readonly-mcp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public, read-only BigQuery MCP server (PyPI: `bq-readonly-mcp`) with 7 tools, strict SQL safety validator, auto-LIMIT, dry-run cost guard, ADC auth, full test suite, CI/publish workflows, and protected `main` branch — ready for v0.1.0 release on PyPI.

**Architecture:** Single-process Python stdio MCP server. Modular layout: `safety.py` (SQL validator) and `bq.py` (BigQuery wrapper) are isolated for testability; one tool per file in `tools/`. All config flows from CLI/env into a typed `Config` object passed through dependency injection. Async at the MCP boundary, sync internals wrapped via `asyncio.to_thread`.

**Tech Stack:** Python 3.11+, `mcp[cli]>=1.9.0`, `google-cloud-bigquery`, `google-auth`, `pydantic>=2.10`, `hatchling` build, `uv` lockfile, `pytest` + `pytest-asyncio` + `pytest-mock`, `ruff`, `mypy`. CI on GitHub Actions; publish to PyPI via OIDC-style token in `pypi` environment. License: MIT.

---

## File Structure (created in this plan)

```
bq-readonly-mcp/
├── pyproject.toml                      # Task 1
├── README.md                           # Task 27
├── LICENSE                             # Task 1
├── CHANGELOG.md                        # Task 30
├── SECURITY.md                         # Task 30
├── CONTRIBUTING.md                     # Task 30
├── .gitignore                          # Task 1
├── .python-version                     # Task 1
├── CLAUDE.md                           # already exists
├── docs/
│   ├── superpowers/specs/...           # already exists
│   ├── superpowers/plans/...           # this file
│   ├── QUICKSTART.md                   # Task 28
│   ├── EDITOR_SETUP.md                 # Task 28
│   ├── PUBLISHING.md                   # Task 29
│   └── TROUBLESHOOTING.md              # Task 28
├── mcp-config-examples/
│   ├── claude-code.json                # Task 28
│   ├── claude-desktop.json             # Task 28
│   ├── cursor.json                     # Task 28
│   ├── windsurf.json                   # Task 28
│   └── copilot.json                    # Task 28
├── src/bq_readonly_mcp/
│   ├── __init__.py                     # Task 2  (version)
│   ├── __main__.py                     # Task 24 (python -m entry)
│   ├── config.py                       # Task 3
│   ├── safety.py                       # Tasks 4–10
│   ├── models.py                       # Task 11
│   ├── auth.py                         # Task 12
│   ├── bq.py                           # Tasks 13–15
│   ├── server.py                       # Task 23
│   └── tools/
│       ├── __init__.py                 # Task 16
│       ├── list_datasets.py            # Task 16
│       ├── list_tables.py              # Task 17
│       ├── get_table_metadata.py       # Task 18
│       ├── describe_columns.py         # Task 19
│       ├── get_table.py                # Task 20
│       ├── estimate_query_cost.py      # Task 21
│       └── run_query.py                # Task 22
├── tests/
│   ├── __init__.py                     # Task 2
│   ├── conftest.py                     # Task 2
│   ├── unit/
│   │   ├── __init__.py                 # Task 2
│   │   ├── test_config.py              # Task 3
│   │   ├── test_safety_*.py            # Tasks 4–10
│   │   ├── test_models.py              # Task 11
│   │   ├── test_auth.py                # Task 12
│   │   ├── test_bq_*.py                # Tasks 13–15
│   │   ├── test_tool_*.py              # Tasks 16–22
│   │   ├── test_server.py              # Task 23
│   │   └── test_no_pii.py              # Task 25
│   └── integration/
│       ├── __init__.py                 # Task 2
│       └── test_public_datasets.py     # Task 26
└── .github/workflows/
    ├── ci.yml                          # Task 31
    └── publish.yml                     # Task 32
```

**Out of this plan (separate operational tasks tracked in TaskList):**
- Creating the public GitHub repo + push
- Configuring branch protection on `main`
- Setting up the `pypi` GitHub environment secret
- Internal-data smoke testing
- Wiring Claude/Windsurf MCP configs to use the published `uvx` package
- Re-auditing the sister `google-sheets-mcp` project

---

## Conventions used by every task

- **Conventional commits** at the end of every task. Pattern: `type(scope): subject`. Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `ci`, `build`.
- **TDD** for every code-bearing task: failing test → run to confirm fail → minimal implementation → run to confirm pass → commit.
- **Run all tests** before any commit that adds/modifies production code (`uv run pytest tests/unit/ -q`).
- **Lint + type-check** before merging to `main` (covered by CI). Locally: `uv run ruff check src tests` and `uv run mypy src`.
- **Atomic commits.** One logical change per commit. The plan groups related steps so that each task ends with one commit.
- **No file edited in two consecutive tasks unless the second task depends on the first being committed first.** This keeps the diff per commit small and reviewable.

---

## Task 1: Project scaffold — `pyproject.toml`, license, gitignore

**Files:**
- Create: `pyproject.toml`
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `.python-version`

- [ ] **Step 1.1: Create `.python-version`**

```
3.11
```

- [ ] **Step 1.2: Create `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Build artifacts
dist/
build/
*.egg-info/
.eggs/

# Virtual envs
.venv/
venv/
env/

# Lockfile control: keep uv.lock tracked, ignore caches
.uv-cache/

# Test / coverage
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Editors / OS
.vscode/
.idea/
.DS_Store
*.swp

# Secrets / credentials — never commit
.env
.env.*
!.env.example
*.json.key
service-account*.json
application_default_credentials.json
```

- [ ] **Step 1.3: Create `LICENSE` (MIT)**

```
MIT License

Copyright (c) 2026 Rupesh Biswas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 1.4: Create `pyproject.toml`**

```toml
[project]
name = "bq-readonly-mcp"
version = "0.1.0"
description = "Read-only BigQuery MCP server with auto-LIMIT, dry-run cost guard, and ADC auth — for Claude, Cursor, Windsurf, Copilot, and other MCP clients."
readme = "README.md"
requires-python = ">=3.11"
authors = [{ name = "Rupesh Biswas", email = "rupesh.biswas@mariadb.com" }]
license = "MIT"
license-files = ["LICENSE"]
keywords = ["mcp", "bigquery", "google-cloud", "llm", "ai", "anthropic", "claude", "cursor", "windsurf", "readonly", "adc"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Database",
]
dependencies = [
    "mcp[cli]>=1.9.0",
    "google-cloud-bigquery>=3.20.0",
    "google-auth>=2.38.0",
    "pydantic>=2.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "pytest-mock>=3.14.0",
    "ruff>=0.11.0",
    "mypy>=1.15.0",
    "types-requests>=2.32.0",
]

[project.scripts]
bq-readonly-mcp = "bq_readonly_mcp.server:main"

[project.urls]
Homepage = "https://github.com/mariadb-RupeshBiswas/bq-readonly-mcp"
Repository = "https://github.com/mariadb-RupeshBiswas/bq-readonly-mcp"
Issues = "https://github.com/mariadb-RupeshBiswas/bq-readonly-mcp/issues"
Documentation = "https://github.com/mariadb-RupeshBiswas/bq-readonly-mcp#readme"
PyPI = "https://pypi.org/project/bq-readonly-mcp/"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/bq_readonly_mcp"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = [
    "integration: integration tests that hit real BigQuery (require ADC, skipped in CI by default)",
]
addopts = "-m 'not integration'"

[tool.ruff]
line-length = 100
target-version = "py311"
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = false
ignore_missing_imports = true
```

- [ ] **Step 1.5: Verify `uv sync` succeeds**

Run: `cd /Users/rupeshbiswas/projects/bq-readonly-mcp && uv sync --extra dev`
Expected: virtual env created at `.venv/`, dependencies resolved, `uv.lock` written.

- [ ] **Step 1.6: Commit**

```bash
git add pyproject.toml LICENSE .gitignore .python-version uv.lock
git commit -m "build: scaffold pyproject, MIT license, .gitignore"
```

---

## Task 2: Empty package skeleton + test harness

**Files:**
- Create: `src/bq_readonly_mcp/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 2.1: Create `src/bq_readonly_mcp/__init__.py`**

```python
"""bq-readonly-mcp — read-only BigQuery MCP server."""

__version__ = "0.1.0"
```

- [ ] **Step 2.2: Create empty `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`**

```python
```

(Three empty files, one per package.)

- [ ] **Step 2.3: Create `tests/conftest.py`**

```python
"""Shared pytest fixtures."""
```

(Will be expanded in later tasks as fixtures are needed.)

- [ ] **Step 2.4: Add a smoke test to confirm the package imports**

Create `tests/unit/test_package.py`:

```python
def test_package_imports():
    import bq_readonly_mcp

    assert bq_readonly_mcp.__version__ == "0.1.0"
```

- [ ] **Step 2.5: Run the test — expect PASS**

Run: `uv run pytest tests/unit/test_package.py -v`
Expected: 1 passed.

- [ ] **Step 2.6: Commit**

```bash
git add src/bq_readonly_mcp/ tests/
git commit -m "build: add package skeleton and pytest scaffolding"
```

---

## Task 3: `config.py` — typed config from CLI/env

**Files:**
- Create: `src/bq_readonly_mcp/config.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 3.1: Write the failing tests**

Create `tests/unit/test_config.py`:

```python
"""Tests for config resolution from CLI args and environment variables."""

import pytest

from bq_readonly_mcp.config import Config, build_config


def test_project_required():
    with pytest.raises(SystemExit):
        build_config(argv=[], env={})


def test_project_from_cli():
    cfg = build_config(argv=["--project", "my-proj"], env={})
    assert cfg.project == "my-proj"
    assert cfg.location == "US"  # default


def test_project_from_env():
    cfg = build_config(argv=[], env={"GCP_PROJECT_ID": "env-proj"})
    assert cfg.project == "env-proj"


def test_cli_overrides_env():
    cfg = build_config(
        argv=["--project", "cli-proj"],
        env={"GCP_PROJECT_ID": "env-proj"},
    )
    assert cfg.project == "cli-proj"


def test_defaults_match_spec():
    cfg = build_config(argv=["--project", "p"], env={})
    assert cfg.location == "US"
    assert cfg.default_limit == 50
    assert cfg.max_limit == 10_000
    assert cfg.max_bytes_billed == 1_073_741_824  # 1 GB
    assert cfg.sample_rows == 3
    assert cfg.allowed_datasets is None
    assert cfg.key_file is None


def test_datasets_allowlist_from_cli():
    cfg = build_config(argv=["--project", "p", "--datasets", "ds1", "ds2"], env={})
    assert cfg.allowed_datasets == ["ds1", "ds2"]


def test_datasets_allowlist_from_env_csv():
    cfg = build_config(
        argv=["--project", "p"],
        env={"BIGQUERY_ALLOWED_DATASETS": "ds1,ds2,ds3"},
    )
    assert cfg.allowed_datasets == ["ds1", "ds2", "ds3"]


def test_max_bytes_billed_override():
    cfg = build_config(argv=["--project", "p", "--max-bytes-billed", "5000"], env={})
    assert cfg.max_bytes_billed == 5000


def test_invalid_max_limit_rejected():
    with pytest.raises(SystemExit):
        build_config(argv=["--project", "p", "--max-limit", "0"], env={})
```

- [ ] **Step 3.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_config.py -v`
Expected: ImportError / ModuleNotFoundError on `Config` and `build_config`.

- [ ] **Step 3.3: Implement `config.py`**

```python
"""Configuration resolution: CLI args > env vars > defaults."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Config:
    project: str
    location: str
    allowed_datasets: list[str] | None
    default_limit: int
    max_limit: int
    max_bytes_billed: int
    sample_rows: int
    key_file: str | None


def _positive_int(s: str) -> int:
    n = int(s)
    if n <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {n}")
    return n


def build_config(argv: list[str], env: Mapping[str, str]) -> Config:
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
```

- [ ] **Step 3.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_config.py -v`
Expected: 9 passed.

- [ ] **Step 3.5: Commit**

```bash
git add src/bq_readonly_mcp/config.py tests/unit/test_config.py
git commit -m "feat(config): typed CLI/env config resolution with validation"
```

---

## Task 4: `safety.py` — comment stripping

**Files:**
- Create: `src/bq_readonly_mcp/safety.py`
- Create: `tests/unit/test_safety_comments.py`

- [ ] **Step 4.1: Write failing tests for comment stripping**

Create `tests/unit/test_safety_comments.py`:

```python
from bq_readonly_mcp.safety import strip_comments


def test_strips_line_comment():
    assert strip_comments("SELECT 1 -- comment").strip() == "SELECT 1"


def test_strips_multiple_line_comments():
    sql = "SELECT 1\n-- a\nFROM t -- b"
    assert strip_comments(sql).strip().split("\n") == ["SELECT 1", "", "FROM t "]


def test_strips_block_comment():
    assert strip_comments("SELECT /* hello */ 1").strip() == "SELECT  1"


def test_strips_multiline_block_comment():
    sql = "SELECT /*\nthis is\na comment\n*/ 1"
    assert strip_comments(sql).strip() == "SELECT  1"


def test_does_not_strip_inside_single_quoted_string():
    assert strip_comments("SELECT '-- not a comment'") == "SELECT '-- not a comment'"


def test_does_not_strip_inside_double_quoted_string():
    assert strip_comments('SELECT "/* not a comment */"') == 'SELECT "/* not a comment */"'


def test_handles_doubled_quote_escape():
    # BigQuery uses doubled '' to escape inside single-quoted strings
    sql = "SELECT 'it''s -- not a comment'"
    assert strip_comments(sql) == sql


def test_empty_string_returns_empty():
    assert strip_comments("") == ""
```

- [ ] **Step 4.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_safety_comments.py -v`
Expected: ModuleNotFoundError on `bq_readonly_mcp.safety`.

- [ ] **Step 4.3: Implement `strip_comments`**

Create `src/bq_readonly_mcp/safety.py`:

```python
"""SQL safety: comment stripping, validator, LIMIT injection.

This module is the highest-stakes part of the codebase. It must reject all
non-SELECT/WITH queries before they touch the BigQuery client. Tests live in
tests/unit/test_safety_*.py and are exhaustive on purpose.
"""

from __future__ import annotations


def strip_comments(sql: str) -> str:
    """Remove SQL line and block comments while preserving string literals.

    Walks character by character, tracking whether we're inside a single- or
    double-quoted string (with doubled-quote escape support). Outside strings,
    `--` runs to end-of-line and `/* ... */` is replaced with a single space.
    """
    out: list[str] = []
    i = 0
    n = len(sql)
    in_single = False
    in_double = False

    while i < n:
        c = sql[i]

        if in_single:
            out.append(c)
            if c == "'":
                # Doubled '' is an escape, not a closer
                if i + 1 < n and sql[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_single = False
            i += 1
            continue

        if in_double:
            out.append(c)
            if c == '"':
                if i + 1 < n and sql[i + 1] == '"':
                    out.append('"')
                    i += 2
                    continue
                in_double = False
            i += 1
            continue

        # Outside any string
        if c == "'":
            in_single = True
            out.append(c)
            i += 1
            continue
        if c == '"':
            in_double = True
            out.append(c)
            i += 1
            continue
        if c == "-" and i + 1 < n and sql[i + 1] == "-":
            # line comment, consume until newline
            while i < n and sql[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and sql[i + 1] == "*":
            # block comment, consume until */
            i += 2
            while i + 1 < n and not (sql[i] == "*" and sql[i + 1] == "/"):
                i += 1
            i += 2  # skip the closing */
            out.append(" ")
            continue

        out.append(c)
        i += 1

    return "".join(out)
```

- [ ] **Step 4.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_safety_comments.py -v`
Expected: 8 passed.

- [ ] **Step 4.5: Commit**

```bash
git add src/bq_readonly_mcp/safety.py tests/unit/test_safety_comments.py
git commit -m "feat(safety): SQL comment stripping with string-literal awareness"
```

---

## Task 5: `safety.py` — string-literal masking helper

**Files:**
- Modify: `src/bq_readonly_mcp/safety.py`
- Create: `tests/unit/test_safety_mask_strings.py`

We need a helper that replaces string-literal contents with placeholders so a later regex check for DML keywords doesn't false-positive on a column value like `'INSERT something'`.

- [ ] **Step 5.1: Write failing tests**

Create `tests/unit/test_safety_mask_strings.py`:

```python
from bq_readonly_mcp.safety import mask_string_literals


def test_masks_single_quoted():
    out = mask_string_literals("SELECT 'INSERT INTO bad'")
    assert "INSERT" not in out
    assert out.startswith("SELECT '")


def test_masks_double_quoted():
    out = mask_string_literals('SELECT "DROP TABLE"')
    assert "DROP" not in out
    assert "TABLE" not in out


def test_preserves_outer_structure():
    out = mask_string_literals("SELECT 'foo' FROM t WHERE c = 'bar'")
    assert out.startswith("SELECT '")
    assert " FROM t WHERE c = '" in out


def test_handles_doubled_quote_escape():
    out = mask_string_literals("SELECT 'it''s here'")
    # Whole literal should be masked; no INSERT/etc would trigger anyway, just check no error
    assert out.startswith("SELECT '")
    assert out.endswith("'")


def test_empty_input():
    assert mask_string_literals("") == ""


def test_no_strings_unchanged():
    sql = "SELECT 1 + 2 FROM dataset.table"
    assert mask_string_literals(sql) == sql
```

- [ ] **Step 5.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_safety_mask_strings.py -v`
Expected: ImportError on `mask_string_literals`.

- [ ] **Step 5.3: Add `mask_string_literals` to `safety.py`**

Append to `src/bq_readonly_mcp/safety.py`:

```python
def mask_string_literals(sql: str) -> str:
    """Replace contents of single- and double-quoted string literals with `X`.

    Used before keyword scanning so that a value like `'INSERT'` inside a
    string literal does not trigger the DML/DDL rejection. Preserves the
    surrounding quote characters and overall length structure.
    """
    out: list[str] = []
    i = 0
    n = len(sql)
    in_single = False
    in_double = False

    while i < n:
        c = sql[i]

        if in_single:
            if c == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    out.append("X")  # masked content
                    i += 2
                    continue
                out.append("'")
                in_single = False
                i += 1
                continue
            out.append("X")
            i += 1
            continue

        if in_double:
            if c == '"':
                if i + 1 < n and sql[i + 1] == '"':
                    out.append("X")
                    i += 2
                    continue
                out.append('"')
                in_double = False
                i += 1
                continue
            out.append("X")
            i += 1
            continue

        if c == "'":
            in_single = True
            out.append(c)
            i += 1
            continue
        if c == '"':
            in_double = True
            out.append(c)
            i += 1
            continue

        out.append(c)
        i += 1

    return "".join(out)
```

- [ ] **Step 5.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_safety_mask_strings.py -v`
Expected: 6 passed.

- [ ] **Step 5.5: Commit**

```bash
git add src/bq_readonly_mcp/safety.py tests/unit/test_safety_mask_strings.py
git commit -m "feat(safety): mask string literals to prevent keyword false positives"
```

---

## Task 6: `safety.py` — multi-statement detection

**Files:**
- Modify: `src/bq_readonly_mcp/safety.py`
- Create: `tests/unit/test_safety_multistatement.py`

- [ ] **Step 6.1: Write failing tests**

Create `tests/unit/test_safety_multistatement.py`:

```python
from bq_readonly_mcp.safety import is_multistatement


def test_single_statement_no_semicolon():
    assert is_multistatement("SELECT 1") is False


def test_single_statement_trailing_semicolon():
    assert is_multistatement("SELECT 1;") is False


def test_single_statement_trailing_semicolon_whitespace():
    assert is_multistatement("SELECT 1;   \n  ") is False


def test_two_statements():
    assert is_multistatement("SELECT 1; SELECT 2") is True


def test_two_statements_both_terminated():
    assert is_multistatement("SELECT 1; SELECT 2;") is True


def test_semicolon_in_string_not_terminator():
    assert is_multistatement("SELECT 'a;b'") is False


def test_semicolon_in_comment_not_terminator():
    assert is_multistatement("SELECT 1 -- ; comment\n") is False
```

- [ ] **Step 6.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_safety_multistatement.py -v`
Expected: ImportError on `is_multistatement`.

- [ ] **Step 6.3: Implement `is_multistatement`**

Append to `src/bq_readonly_mcp/safety.py`:

```python
def is_multistatement(sql: str) -> bool:
    """True if the query contains more than one statement.

    A statement is delimited by `;`. We strip comments and mask string
    literals first so semicolons inside strings/comments don't count.
    Trailing whitespace and a single optional terminating `;` do not
    count as a second statement.
    """
    stripped = strip_comments(sql)
    masked = mask_string_literals(stripped)
    # Remove trailing whitespace
    body = masked.rstrip()
    # Single trailing ; is fine; trim it
    if body.endswith(";"):
        body = body[:-1].rstrip()
    return ";" in body
```

- [ ] **Step 6.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_safety_multistatement.py -v`
Expected: 7 passed.

- [ ] **Step 6.5: Commit**

```bash
git add src/bq_readonly_mcp/safety.py tests/unit/test_safety_multistatement.py
git commit -m "feat(safety): reject multi-statement queries"
```

---

## Task 7: `safety.py` — SELECT/WITH start check + DML/DDL keyword check + main `validate_select_query`

**Files:**
- Modify: `src/bq_readonly_mcp/safety.py`
- Create: `tests/unit/test_safety_validate.py`

- [ ] **Step 7.1: Write failing tests**

Create `tests/unit/test_safety_validate.py`:

```python
import pytest

from bq_readonly_mcp.safety import SafetyError, validate_select_query


def test_select_allowed():
    validate_select_query("SELECT 1")


def test_select_with_leading_whitespace_allowed():
    validate_select_query("   \n  SELECT 1")


def test_with_cte_allowed():
    validate_select_query("WITH a AS (SELECT 1) SELECT * FROM a")


def test_select_lowercase_allowed():
    validate_select_query("select 1")


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO t VALUES (1)",
        "UPDATE t SET x = 1 WHERE y = 2",
        "DELETE FROM t WHERE x = 1",
        "MERGE t USING s ON ... WHEN MATCHED THEN UPDATE SET x = 1",
        "CREATE TABLE t (id INT)",
        "DROP TABLE t",
        "ALTER TABLE t ADD COLUMN c INT",
        "TRUNCATE TABLE t",
        "GRANT SELECT ON t TO user",
        "REVOKE SELECT ON t FROM user",
        "EXPORT DATA OPTIONS(...) AS SELECT 1",
    ],
)
def test_dml_ddl_rejected(sql):
    with pytest.raises(SafetyError, match=r"non-SELECT|DML|DDL|disallowed"):
        validate_select_query(sql)


def test_select_with_dml_word_in_string_allowed():
    validate_select_query("SELECT 'INSERT' AS label")


def test_select_with_dml_word_in_comment_allowed():
    validate_select_query("SELECT 1 /* INSERT something */ FROM t")


def test_column_named_delete_flag_allowed():
    # word boundaries should keep us safe — `delete_flag` is not `DELETE`
    validate_select_query("SELECT delete_flag FROM t")


def test_multistatement_rejected():
    with pytest.raises(SafetyError, match="multi-statement"):
        validate_select_query("SELECT 1; SELECT 2")


def test_empty_rejected():
    with pytest.raises(SafetyError):
        validate_select_query("")


def test_only_whitespace_rejected():
    with pytest.raises(SafetyError):
        validate_select_query("   \n  ")
```

- [ ] **Step 7.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_safety_validate.py -v`
Expected: ImportError on `SafetyError` and `validate_select_query`.

- [ ] **Step 7.3: Implement validator**

Append to `src/bq_readonly_mcp/safety.py`:

```python
import re

DISALLOWED_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "MERGE",
    "CREATE", "DROP", "ALTER", "TRUNCATE",
    "REPLACE", "GRANT", "REVOKE", "EXPORT",
)

_DISALLOWED_RE = re.compile(
    r"\b(" + "|".join(DISALLOWED_KEYWORDS) + r")\b",
    re.IGNORECASE,
)
_STARTS_WITH_SELECT_OR_WITH_RE = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


class SafetyError(ValueError):
    """Raised when a query fails safety validation."""


def validate_select_query(sql: str) -> None:
    """Validate that `sql` is a single read-only SELECT/WITH query.

    Pipeline (raises SafetyError on first failure):
      1. Strip comments.
      2. Reject if multi-statement.
      3. Reject if not starting with SELECT or WITH.
      4. Mask string literals, then reject if any DML/DDL keyword appears
         as a top-level token.
    """
    if not sql or not sql.strip():
        raise SafetyError("query is empty")

    stripped = strip_comments(sql)

    if is_multistatement(sql):
        raise SafetyError("multi-statement queries are not allowed")

    if not _STARTS_WITH_SELECT_OR_WITH_RE.match(stripped):
        raise SafetyError("only SELECT or WITH queries are allowed (non-SELECT detected)")

    masked = mask_string_literals(stripped)
    match = _DISALLOWED_RE.search(masked)
    if match:
        raise SafetyError(
            f"disallowed DML/DDL keyword detected: {match.group(1).upper()}"
        )
```

- [ ] **Step 7.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_safety_validate.py -v`
Expected: All passed (15 cases).

- [ ] **Step 7.5: Commit**

```bash
git add src/bq_readonly_mcp/safety.py tests/unit/test_safety_validate.py
git commit -m "feat(safety): validate SELECT/WITH-only queries with DML/DDL rejection"
```

---

## Task 8: `safety.py` — LIMIT detection

**Files:**
- Modify: `src/bq_readonly_mcp/safety.py`
- Create: `tests/unit/test_safety_limit_detect.py`

- [ ] **Step 8.1: Write failing tests**

Create `tests/unit/test_safety_limit_detect.py`:

```python
from bq_readonly_mcp.safety import has_outer_limit


def test_no_limit():
    assert has_outer_limit("SELECT * FROM t") is False


def test_limit_at_end():
    assert has_outer_limit("SELECT * FROM t LIMIT 10") is True


def test_limit_with_offset():
    assert has_outer_limit("SELECT * FROM t LIMIT 10 OFFSET 5") is True


def test_limit_lowercase():
    assert has_outer_limit("select * from t limit 10") is True


def test_limit_in_subquery_only_returns_false():
    # Outer query has no LIMIT — only inner does
    assert has_outer_limit("SELECT * FROM (SELECT * FROM t LIMIT 10) sub") is False


def test_limit_followed_by_semicolon():
    assert has_outer_limit("SELECT * FROM t LIMIT 10;") is True


def test_limit_followed_by_whitespace_and_semicolon():
    assert has_outer_limit("SELECT * FROM t LIMIT 10  ;  ") is True
```

- [ ] **Step 8.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_safety_limit_detect.py -v`
Expected: ImportError on `has_outer_limit`.

- [ ] **Step 8.3: Implement `has_outer_limit`**

Append to `src/bq_readonly_mcp/safety.py`:

```python
_TRAILING_LIMIT_RE = re.compile(
    r"\bLIMIT\s+\d+(\s+OFFSET\s+\d+)?\s*;?\s*$",
    re.IGNORECASE,
)


def has_outer_limit(sql: str) -> bool:
    """True if the outermost query already has a LIMIT clause.

    Heuristic: comments stripped, string literals masked, then check the
    trailing portion of the query for `LIMIT N` (optionally `OFFSET M`)
    followed by optional whitespace and semicolon.

    LIMIT clauses inside subqueries do not count — the trailing-anchor
    regex only matches at the very end of the (cleaned) query.
    """
    cleaned = mask_string_literals(strip_comments(sql)).rstrip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].rstrip()
    return bool(_TRAILING_LIMIT_RE.search(cleaned))
```

- [ ] **Step 8.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_safety_limit_detect.py -v`
Expected: 7 passed.

- [ ] **Step 8.5: Commit**

```bash
git add src/bq_readonly_mcp/safety.py tests/unit/test_safety_limit_detect.py
git commit -m "feat(safety): detect outer LIMIT clause to avoid double-injection"
```

---

## Task 9: `safety.py` — LIMIT injection

**Files:**
- Modify: `src/bq_readonly_mcp/safety.py`
- Create: `tests/unit/test_safety_inject_limit.py`

- [ ] **Step 9.1: Write failing tests**

Create `tests/unit/test_safety_inject_limit.py`:

```python
import pytest

from bq_readonly_mcp.safety import inject_limit


def test_injects_when_missing():
    out = inject_limit("SELECT * FROM t", limit=50)
    assert out.rstrip().rstrip(";").endswith("LIMIT 50")


def test_no_injection_when_present():
    sql = "SELECT * FROM t LIMIT 10"
    assert inject_limit(sql, limit=50) == sql


def test_strips_trailing_semicolon_before_injection():
    out = inject_limit("SELECT * FROM t;", limit=50)
    assert out == "SELECT * FROM t LIMIT 50"


def test_preserves_subquery_limit():
    sql = "SELECT * FROM (SELECT * FROM t LIMIT 10) sub"
    out = inject_limit(sql, limit=50)
    assert out.rstrip().rstrip(";").endswith("LIMIT 50")
    assert "LIMIT 10" in out  # inner preserved


def test_limit_zero_invalid():
    with pytest.raises(ValueError):
        inject_limit("SELECT * FROM t", limit=0)


def test_negative_limit_invalid():
    with pytest.raises(ValueError):
        inject_limit("SELECT * FROM t", limit=-5)
```

- [ ] **Step 9.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_safety_inject_limit.py -v`
Expected: ImportError on `inject_limit`.

- [ ] **Step 9.3: Implement `inject_limit`**

Append to `src/bq_readonly_mcp/safety.py`:

```python
def inject_limit(sql: str, limit: int) -> str:
    """Append `LIMIT <limit>` to the query if no outer LIMIT is already present."""
    if limit <= 0:
        raise ValueError(f"limit must be positive, got {limit}")
    if has_outer_limit(sql):
        return sql
    body = sql.rstrip()
    if body.endswith(";"):
        body = body[:-1].rstrip()
    return f"{body} LIMIT {limit}"
```

- [ ] **Step 9.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_safety_inject_limit.py -v`
Expected: 6 passed.

- [ ] **Step 9.5: Commit**

```bash
git add src/bq_readonly_mcp/safety.py tests/unit/test_safety_inject_limit.py
git commit -m "feat(safety): inject LIMIT clause when caller hasn't specified one"
```

---

## Task 10: `safety.py` — coverage check + freeze module

**Files:**
- No new code; this task is a quality gate.

- [ ] **Step 10.1: Run all safety tests with coverage**

Run: `uv run pytest tests/unit/test_safety_*.py --cov=src/bq_readonly_mcp/safety --cov-report=term-missing -q`

Expected: Coverage ≥ 95% on `safety.py`. Note any uncovered lines.

- [ ] **Step 10.2: If any uncovered branches, add targeted tests for them, then re-run.**

This is judgment-based — if coverage shows lines like an unreachable `else` branch, adding a test isn't useful. But missed branches in `strip_comments`, `mask_string_literals`, or the validator are mandatory to cover.

- [ ] **Step 10.3: Run linter and type checker**

```bash
uv run ruff check src/bq_readonly_mcp/safety.py tests/unit/test_safety_*.py
uv run mypy src/bq_readonly_mcp/safety.py
```

Expected: Zero warnings/errors.

- [ ] **Step 10.4: Commit only if changes were made**

```bash
git add tests/unit/test_safety_*.py
git commit -m "test(safety): close coverage gaps to ≥95%"
```

(Skip if no new tests added.)

---

## Task 11: `models.py` — Pydantic input/output schemas

**Files:**
- Create: `src/bq_readonly_mcp/models.py`
- Create: `tests/unit/test_models.py`

- [ ] **Step 11.1: Write failing tests**

Create `tests/unit/test_models.py`:

```python
import pytest
from pydantic import ValidationError

from bq_readonly_mcp.models import (
    ColumnSchema,
    DatasetInfo,
    DescribeColumnsInput,
    EstimateQueryCostInput,
    GetTableInput,
    GetTableMetadataInput,
    ListDatasetsInput,
    ListTablesInput,
    PartitioningInfo,
    QueryResult,
    RunQueryInput,
    TableInfo,
    TableMetadata,
)


def test_list_datasets_input_optional_filter():
    obj = ListDatasetsInput()
    assert obj.name_contains is None
    obj = ListDatasetsInput(name_contains="sales")
    assert obj.name_contains == "sales"


def test_list_tables_input_requires_dataset():
    with pytest.raises(ValidationError):
        ListTablesInput()
    obj = ListTablesInput(dataset_id="foo")
    assert obj.dataset_id == "foo"


def test_describe_columns_input_requires_both():
    with pytest.raises(ValidationError):
        DescribeColumnsInput(dataset_id="ds")
    DescribeColumnsInput(dataset_id="ds", table_id="t")


def test_get_table_input_sample_rows_default():
    obj = GetTableInput(dataset_id="ds", table_id="t")
    assert obj.sample_rows is None
    obj = GetTableInput(dataset_id="ds", table_id="t", sample_rows=5)
    assert obj.sample_rows == 5


def test_get_table_input_negative_sample_rows_rejected():
    with pytest.raises(ValidationError):
        GetTableInput(dataset_id="ds", table_id="t", sample_rows=-1)


def test_run_query_input_requires_query():
    with pytest.raises(ValidationError):
        RunQueryInput()
    RunQueryInput(query="SELECT 1")


def test_run_query_input_limit_must_be_positive():
    with pytest.raises(ValidationError):
        RunQueryInput(query="SELECT 1", limit=0)
    RunQueryInput(query="SELECT 1", limit=100)


def test_estimate_query_cost_input_requires_query():
    with pytest.raises(ValidationError):
        EstimateQueryCostInput()


def test_dataset_info_serializes():
    d = DatasetInfo(dataset_id="foo", location="US")
    assert d.model_dump()["dataset_id"] == "foo"


def test_column_schema_required_fields():
    c = ColumnSchema(name="x", type="STRING", mode="NULLABLE")
    assert c.description is None


def test_table_metadata_optional_partitioning():
    m = TableMetadata(
        table_id="t",
        type="TABLE",
        created="2026-01-01T00:00:00",
        modified="2026-01-01T00:00:00",
        row_count=0,
        size_bytes=0,
    )
    assert m.partitioning is None
    assert m.clustering is None


def test_partitioning_info_validates_type():
    p = PartitioningInfo(type="DAY", column="ts", expiration_ms=None)
    assert p.type == "DAY"


def test_query_result_round_trip():
    r = QueryResult(
        rows=[{"a": 1}],
        schema=[ColumnSchema(name="a", type="INT64", mode="NULLABLE")],
        total_bytes_processed=100,
        total_bytes_billed=10485760,
        cache_hit=False,
        job_id="abc",
        location="US",
    )
    dumped = r.model_dump()
    assert dumped["rows"] == [{"a": 1}]
```

- [ ] **Step 11.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: ModuleNotFoundError on `bq_readonly_mcp.models`.

- [ ] **Step 11.3: Implement `models.py`**

```python
"""Pydantic models for tool inputs and outputs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Tool inputs ---


class ListDatasetsInput(_StrictModel):
    name_contains: str | None = None


class ListTablesInput(_StrictModel):
    dataset_id: str = Field(min_length=1)
    name_contains: str | None = None


class GetTableMetadataInput(_StrictModel):
    dataset_id: str = Field(min_length=1)
    table_id: str = Field(min_length=1)


class DescribeColumnsInput(_StrictModel):
    dataset_id: str = Field(min_length=1)
    table_id: str = Field(min_length=1)


class GetTableInput(_StrictModel):
    dataset_id: str = Field(min_length=1)
    table_id: str = Field(min_length=1)
    sample_rows: PositiveInt | None = None


class RunQueryInput(_StrictModel):
    query: str = Field(min_length=1)
    limit: PositiveInt | None = None
    no_limit: bool = False
    dry_run: bool = False


class EstimateQueryCostInput(_StrictModel):
    query: str = Field(min_length=1)


# --- Outputs ---


class DatasetInfo(_StrictModel):
    dataset_id: str
    location: str
    friendly_name: str | None = None
    description: str | None = None


TableType = Literal["TABLE", "VIEW", "MATERIALIZED_VIEW", "EXTERNAL", "SNAPSHOT"]


class TableInfo(_StrictModel):
    table_id: str
    type: TableType
    created: str | None = None
    friendly_name: str | None = None


class ColumnSchema(_StrictModel):
    name: str
    type: str
    mode: Literal["NULLABLE", "REQUIRED", "REPEATED"]
    description: str | None = None


PartitioningType = Literal["DAY", "HOUR", "MONTH", "YEAR", "INTEGER_RANGE"]


class PartitioningInfo(_StrictModel):
    type: PartitioningType
    column: str | None = None
    expiration_ms: int | None = None


class TableMetadata(_StrictModel):
    table_id: str
    type: TableType
    description: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    created: str
    modified: str
    row_count: int
    size_bytes: int
    partitioning: PartitioningInfo | None = None
    clustering: list[str] | None = None
    expires: str | None = None
    time_travel_window_hours: int | None = None


class QueryResult(_StrictModel):
    rows: list[dict[str, Any]]
    schema: list[ColumnSchema]
    total_bytes_processed: int
    total_bytes_billed: int
    cache_hit: bool
    job_id: str
    location: str


class CostEstimate(_StrictModel):
    total_bytes_processed: int
    estimated_usd: float
    would_be_blocked: bool
```

- [ ] **Step 11.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: 13 passed.

- [ ] **Step 11.5: Commit**

```bash
git add src/bq_readonly_mcp/models.py tests/unit/test_models.py
git commit -m "feat(models): pydantic schemas for tool inputs and outputs"
```

---

## Task 12: `auth.py` — ADC + key file

**Files:**
- Create: `src/bq_readonly_mcp/auth.py`
- Create: `tests/unit/test_auth.py`

- [ ] **Step 12.1: Write failing tests**

Create `tests/unit/test_auth.py`:

```python
from unittest.mock import MagicMock, patch

import pytest

from bq_readonly_mcp.auth import AuthError, build_bigquery_client
from bq_readonly_mcp.config import Config


def make_config(**overrides) -> Config:
    base = dict(
        project="my-proj",
        location="US",
        allowed_datasets=None,
        default_limit=50,
        max_limit=10_000,
        max_bytes_billed=1_073_741_824,
        sample_rows=3,
        key_file=None,
    )
    base.update(overrides)
    return Config(**base)


@patch("bq_readonly_mcp.auth.bigquery.Client")
@patch("bq_readonly_mcp.auth.google_default")
def test_uses_adc_when_no_key_file(mock_default, mock_client):
    mock_default.return_value = (MagicMock(), "adc-detected-proj")
    cfg = make_config(key_file=None)

    client = build_bigquery_client(cfg)

    mock_default.assert_called_once()
    mock_client.assert_called_once()
    kwargs = mock_client.call_args.kwargs
    assert kwargs["project"] == "my-proj"
    assert kwargs["location"] == "US"
    assert client is mock_client.return_value


@patch("bq_readonly_mcp.auth.bigquery.Client")
@patch("bq_readonly_mcp.auth.service_account.Credentials.from_service_account_file")
def test_uses_key_file_when_provided(mock_from_file, mock_client, tmp_path):
    key = tmp_path / "key.json"
    key.write_text("{}")
    cfg = make_config(key_file=str(key))

    build_bigquery_client(cfg)

    mock_from_file.assert_called_once_with(str(key))
    mock_client.assert_called_once()
    assert mock_client.call_args.kwargs["credentials"] is mock_from_file.return_value


@patch("bq_readonly_mcp.auth.google_default")
def test_raises_clear_error_on_default_failure(mock_default):
    from google.auth.exceptions import DefaultCredentialsError
    mock_default.side_effect = DefaultCredentialsError("nope")
    cfg = make_config()

    with pytest.raises(AuthError, match="gcloud auth application-default login"):
        build_bigquery_client(cfg)


def test_raises_clear_error_on_missing_key_file(tmp_path):
    cfg = make_config(key_file=str(tmp_path / "does_not_exist.json"))
    with pytest.raises(AuthError, match="key file not found"):
        build_bigquery_client(cfg)
```

- [ ] **Step 12.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_auth.py -v`
Expected: ModuleNotFoundError on `bq_readonly_mcp.auth`.

- [ ] **Step 12.3: Implement `auth.py`**

```python
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
```

- [ ] **Step 12.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_auth.py -v`
Expected: 4 passed.

- [ ] **Step 12.5: Commit**

```bash
git add src/bq_readonly_mcp/auth.py tests/unit/test_auth.py
git commit -m "feat(auth): ADC + key-file BigQuery client construction"
```

---

## Task 13: `bq.py` — `BQClient` wrapper: list_datasets, list_tables

**Files:**
- Create: `src/bq_readonly_mcp/bq.py`
- Create: `tests/unit/test_bq_listing.py`

- [ ] **Step 13.1: Write failing tests**

Create `tests/unit/test_bq_listing.py`:

```python
from unittest.mock import MagicMock

from bq_readonly_mcp.bq import BQClient


def make_dataset(dataset_id="d1", location="US", friendly_name=None, description=None):
    ds = MagicMock()
    ds.dataset_id = dataset_id
    ds.location = location
    ds.friendly_name = friendly_name
    ds.description = description
    return ds


def make_table(table_id="t1", table_type="TABLE", created=None, friendly_name=None):
    t = MagicMock()
    t.table_id = table_id
    t.table_type = table_type
    t.created = created
    t.friendly_name = friendly_name
    return t


def test_list_datasets_returns_all_when_no_allowlist():
    client = MagicMock()
    client.list_datasets.return_value = [make_dataset("a"), make_dataset("b")]
    # bigquery's list_datasets returns DatasetListItem with dataset_id but not full attrs;
    # we simulate by also setting client.get_dataset to return a richer object.
    client.get_dataset.side_effect = lambda ref: make_dataset(
        dataset_id=ref.dataset_id, location="US"
    )

    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_datasets()

    ids = [d.dataset_id for d in out]
    assert ids == ["a", "b"]


def test_list_datasets_filters_by_allowlist():
    client = MagicMock()
    client.list_datasets.return_value = [
        make_dataset("a"), make_dataset("b"), make_dataset("c"),
    ]
    client.get_dataset.side_effect = lambda ref: make_dataset(
        dataset_id=ref.dataset_id, location="US"
    )

    bq = BQClient(client=client, allowed_datasets=["a", "c"])
    out = bq.list_datasets()

    assert [d.dataset_id for d in out] == ["a", "c"]


def test_list_datasets_filters_by_name_contains():
    client = MagicMock()
    client.list_datasets.return_value = [
        make_dataset("sales_2024"), make_dataset("hr_2024"), make_dataset("sales_2025"),
    ]
    client.get_dataset.side_effect = lambda ref: make_dataset(
        dataset_id=ref.dataset_id, location="US"
    )

    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_datasets(name_contains="sales")

    assert [d.dataset_id for d in out] == ["sales_2024", "sales_2025"]


def test_list_tables_basic():
    client = MagicMock()
    client.list_tables.return_value = [make_table("t1"), make_table("t2", "VIEW")]

    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_tables(dataset_id="d1")

    assert [t.table_id for t in out] == ["t1", "t2"]
    assert out[1].type == "VIEW"


def test_list_tables_filters_by_name_contains():
    client = MagicMock()
    client.list_tables.return_value = [
        make_table("orders"), make_table("customers"), make_table("order_items"),
    ]
    bq = BQClient(client=client, allowed_datasets=None)
    out = bq.list_tables(dataset_id="d1", name_contains="order")
    assert [t.table_id for t in out] == ["orders", "order_items"]


def test_list_tables_rejects_dataset_outside_allowlist():
    import pytest
    from bq_readonly_mcp.bq import DatasetNotAllowedError

    client = MagicMock()
    bq = BQClient(client=client, allowed_datasets=["allowed"])
    with pytest.raises(DatasetNotAllowedError):
        bq.list_tables(dataset_id="forbidden")
```

- [ ] **Step 13.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_bq_listing.py -v`
Expected: ModuleNotFoundError on `bq_readonly_mcp.bq`.

- [ ] **Step 13.3: Implement `bq.py` (listing portion)**

```python
"""Thin BigQuery client wrapper.

This is the only module that touches the `google.cloud.bigquery.Client`
directly. Everything else accepts a `BQClient` instance, making testing
trivial via mocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from google.cloud import bigquery

from .models import DatasetInfo, TableInfo


class DatasetNotAllowedError(PermissionError):
    """Raised when a request references a dataset outside the allowlist."""


@dataclass
class BQClient:
    client: bigquery.Client
    allowed_datasets: list[str] | None = None

    # ----- listing -----

    def _check_dataset(self, dataset_id: str) -> None:
        if self.allowed_datasets is not None and dataset_id not in self.allowed_datasets:
            raise DatasetNotAllowedError(
                f"dataset {dataset_id!r} is not in the configured allowlist"
            )

    def list_datasets(self, name_contains: str | None = None) -> list[DatasetInfo]:
        out: list[DatasetInfo] = []
        for ds_ref in self.client.list_datasets():
            if self.allowed_datasets is not None and ds_ref.dataset_id not in self.allowed_datasets:
                continue
            if name_contains and name_contains.lower() not in ds_ref.dataset_id.lower():
                continue
            ds = self.client.get_dataset(ds_ref)
            out.append(
                DatasetInfo(
                    dataset_id=ds.dataset_id,
                    location=ds.location,
                    friendly_name=getattr(ds, "friendly_name", None),
                    description=getattr(ds, "description", None),
                )
            )
        return out

    def list_tables(
        self, dataset_id: str, name_contains: str | None = None
    ) -> list[TableInfo]:
        self._check_dataset(dataset_id)
        out: list[TableInfo] = []
        for t in self.client.list_tables(dataset_id):
            if name_contains and name_contains.lower() not in t.table_id.lower():
                continue
            out.append(
                TableInfo(
                    table_id=t.table_id,
                    type=t.table_type,
                    created=t.created.isoformat() if t.created else None,
                    friendly_name=getattr(t, "friendly_name", None),
                )
            )
        return out
```

- [ ] **Step 13.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_bq_listing.py -v`
Expected: 6 passed.

- [ ] **Step 13.5: Commit**

```bash
git add src/bq_readonly_mcp/bq.py tests/unit/test_bq_listing.py
git commit -m "feat(bq): BQClient wrapper with allowlist-aware listing"
```

---

## Task 14: `bq.py` — table metadata + columns + sample rows

**Files:**
- Modify: `src/bq_readonly_mcp/bq.py`
- Create: `tests/unit/test_bq_tables.py`

- [ ] **Step 14.1: Write failing tests**

Create `tests/unit/test_bq_tables.py`:

```python
from unittest.mock import MagicMock
from datetime import datetime, timezone

import pytest

from bq_readonly_mcp.bq import BQClient, DatasetNotAllowedError


def make_table_obj(
    table_id="t1",
    table_type="TABLE",
    description=None,
    labels=None,
    num_rows=42,
    num_bytes=4096,
    time_partitioning=None,
    range_partitioning=None,
    clustering_fields=None,
    expires=None,
    schema=None,
):
    t = MagicMock()
    t.table_id = table_id
    t.table_type = table_type
    t.description = description
    t.labels = labels or {}
    t.num_rows = num_rows
    t.num_bytes = num_bytes
    t.created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t.modified = datetime(2026, 1, 2, tzinfo=timezone.utc)
    t.time_partitioning = time_partitioning
    t.range_partitioning = range_partitioning
    t.clustering_fields = clustering_fields
    t.expires = expires
    t.schema = schema or []
    return t


def make_field(name="x", field_type="STRING", mode="NULLABLE", description=None):
    f = MagicMock()
    f.name = name
    f.field_type = field_type
    f.mode = mode
    f.description = description
    return f


def test_get_table_metadata_basic():
    client = MagicMock()
    client.get_table.return_value = make_table_obj()
    bq = BQClient(client=client, allowed_datasets=None)

    md = bq.get_table_metadata("d1", "t1")
    assert md.table_id == "t1"
    assert md.type == "TABLE"
    assert md.row_count == 42
    assert md.size_bytes == 4096
    assert md.partitioning is None
    assert md.clustering is None


def test_get_table_metadata_with_time_partitioning():
    client = MagicMock()
    tp = MagicMock()
    tp.type_ = "DAY"
    tp.field = "event_date"
    tp.expiration_ms = 86400000
    client.get_table.return_value = make_table_obj(time_partitioning=tp)
    bq = BQClient(client=client, allowed_datasets=None)

    md = bq.get_table_metadata("d1", "t1")
    assert md.partitioning is not None
    assert md.partitioning.type == "DAY"
    assert md.partitioning.column == "event_date"
    assert md.partitioning.expiration_ms == 86400000


def test_get_table_metadata_with_clustering():
    client = MagicMock()
    client.get_table.return_value = make_table_obj(clustering_fields=["col_a", "col_b"])
    bq = BQClient(client=client, allowed_datasets=None)

    md = bq.get_table_metadata("d1", "t1")
    assert md.clustering == ["col_a", "col_b"]


def test_describe_columns():
    client = MagicMock()
    client.get_table.return_value = make_table_obj(
        schema=[
            make_field("id", "INT64", "REQUIRED", "primary key"),
            make_field("name", "STRING", "NULLABLE"),
        ]
    )
    bq = BQClient(client=client, allowed_datasets=None)

    cols = bq.describe_columns("d1", "t1")
    assert len(cols) == 2
    assert cols[0].name == "id"
    assert cols[0].mode == "REQUIRED"
    assert cols[0].description == "primary key"


def test_get_table_metadata_rejects_disallowed_dataset():
    client = MagicMock()
    bq = BQClient(client=client, allowed_datasets=["a"])
    with pytest.raises(DatasetNotAllowedError):
        bq.get_table_metadata("b", "t1")
```

- [ ] **Step 14.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_bq_tables.py -v`
Expected: AttributeError — `BQClient.get_table_metadata` not defined.

- [ ] **Step 14.3: Add table-metadata methods**

Append to `src/bq_readonly_mcp/bq.py`:

```python
    # ----- table-level introspection -----

    def get_table_metadata(self, dataset_id: str, table_id: str):
        from .models import PartitioningInfo, TableMetadata

        self._check_dataset(dataset_id)
        ref = f"{self.client.project}.{dataset_id}.{table_id}"
        t = self.client.get_table(ref)

        partitioning: PartitioningInfo | None = None
        if t.time_partitioning is not None:
            partitioning = PartitioningInfo(
                type=t.time_partitioning.type_,
                column=t.time_partitioning.field,
                expiration_ms=t.time_partitioning.expiration_ms,
            )
        elif t.range_partitioning is not None:
            partitioning = PartitioningInfo(
                type="INTEGER_RANGE",
                column=t.range_partitioning.field,
                expiration_ms=None,
            )

        return TableMetadata(
            table_id=t.table_id,
            type=t.table_type,
            description=t.description,
            labels=t.labels or {},
            created=t.created.isoformat(),
            modified=t.modified.isoformat(),
            row_count=t.num_rows or 0,
            size_bytes=t.num_bytes or 0,
            partitioning=partitioning,
            clustering=list(t.clustering_fields) if t.clustering_fields else None,
            expires=t.expires.isoformat() if t.expires else None,
        )

    def describe_columns(self, dataset_id: str, table_id: str):
        from .models import ColumnSchema

        self._check_dataset(dataset_id)
        ref = f"{self.client.project}.{dataset_id}.{table_id}"
        t = self.client.get_table(ref)
        return [
            ColumnSchema(
                name=f.name,
                type=f.field_type,
                mode=f.mode or "NULLABLE",
                description=f.description,
            )
            for f in t.schema
        ]
```

- [ ] **Step 14.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_bq_tables.py -v`
Expected: 5 passed.

- [ ] **Step 14.5: Commit**

```bash
git add src/bq_readonly_mcp/bq.py tests/unit/test_bq_tables.py
git commit -m "feat(bq): table metadata and column-schema introspection"
```

---

## Task 15: `bq.py` — query execution with dry-run guard

**Files:**
- Modify: `src/bq_readonly_mcp/bq.py`
- Create: `tests/unit/test_bq_query.py`

- [ ] **Step 15.1: Write failing tests**

Create `tests/unit/test_bq_query.py`:

```python
from unittest.mock import MagicMock

import pytest

from bq_readonly_mcp.bq import (
    BQClient,
    CostExceededError,
    DatasetNotAllowedError,
)


def make_dryrun_job(total_bytes_processed=1000, referenced_tables=None):
    job = MagicMock()
    job.total_bytes_processed = total_bytes_processed
    job.referenced_tables = referenced_tables or []
    return job


def make_real_job(rows=None, schema=None, total_bytes_processed=1000,
                  total_bytes_billed=10485760, cache_hit=False, job_id="abc",
                  location="US"):
    job = MagicMock()
    job.result.return_value = rows or []
    job.schema = schema or []
    job.total_bytes_processed = total_bytes_processed
    job.total_bytes_billed = total_bytes_billed
    job.cache_hit = cache_hit
    job.job_id = job_id
    job.location = location
    return job


def make_table_ref(project="p", dataset_id="d", table_id="t"):
    ref = MagicMock()
    ref.project = project
    ref.dataset_id = dataset_id
    ref.table_id = table_id
    return ref


def test_dry_run_returns_estimate():
    client = MagicMock()
    client.query.return_value = make_dryrun_job(total_bytes_processed=12345)

    bq = BQClient(client=client, allowed_datasets=None)
    est = bq.estimate_query_cost("SELECT 1", max_bytes_billed=1_000_000)

    assert est.total_bytes_processed == 12345
    assert est.would_be_blocked is False
    assert est.estimated_usd > 0


def test_dry_run_flags_block_when_over_cap():
    client = MagicMock()
    client.query.return_value = make_dryrun_job(total_bytes_processed=2_000_000_000)

    bq = BQClient(client=client, allowed_datasets=None)
    est = bq.estimate_query_cost("SELECT 1", max_bytes_billed=1_073_741_824)

    assert est.would_be_blocked is True


def test_run_query_refuses_when_dryrun_exceeds_cap():
    client = MagicMock()
    client.query.return_value = make_dryrun_job(total_bytes_processed=2_000_000_000)

    bq = BQClient(client=client, allowed_datasets=None)
    with pytest.raises(CostExceededError, match="exceeds"):
        bq.run_query("SELECT 1", max_bytes_billed=1_073_741_824)


def test_run_query_refuses_when_referenced_table_outside_allowlist():
    client = MagicMock()
    client.query.return_value = make_dryrun_job(
        referenced_tables=[make_table_ref(dataset_id="forbidden")]
    )

    bq = BQClient(client=client, allowed_datasets=["allowed"])
    with pytest.raises(DatasetNotAllowedError, match="forbidden"):
        bq.run_query("SELECT 1 FROM forbidden.t", max_bytes_billed=1_073_741_824)


def test_run_query_executes_when_under_cap():
    client = MagicMock()

    dryrun = make_dryrun_job(total_bytes_processed=500)
    real = make_real_job(rows=[MagicMock(__iter__=lambda self: iter([("a", 1)]))])
    client.query.side_effect = [dryrun, real]

    real.result.return_value = [{"x": 1}]

    bq = BQClient(client=client, allowed_datasets=None)
    result = bq.run_query("SELECT 1", max_bytes_billed=1_073_741_824)

    assert result.total_bytes_processed == 500


def test_run_query_passes_max_bytes_billed_to_real_job():
    client = MagicMock()
    dryrun = make_dryrun_job(total_bytes_processed=500)
    real = make_real_job()
    real.result.return_value = []
    client.query.side_effect = [dryrun, real]

    bq = BQClient(client=client, allowed_datasets=None)
    bq.run_query("SELECT 1", max_bytes_billed=999_999)

    # Second call (the real job) should have maximum_bytes_billed set
    real_call = client.query.call_args_list[1]
    job_config = real_call.kwargs.get("job_config") or real_call.args[1]
    assert job_config.maximum_bytes_billed == 999_999
```

- [ ] **Step 15.2: Run tests to confirm fail**

Run: `uv run pytest tests/unit/test_bq_query.py -v`
Expected: AttributeError on `run_query`/`estimate_query_cost`/`CostExceededError`.

- [ ] **Step 15.3: Add query methods to `bq.py`**

Append to `src/bq_readonly_mcp/bq.py`:

```python
# Pricing constant: $6.25 per TiB on-demand BigQuery query (US, approx).
# This is for human-readable estimates only — never billing-authoritative.
USD_PER_BYTE = 6.25 / (1024**4)


class CostExceededError(RuntimeError):
    """Raised when a query's estimated cost exceeds the configured cap."""
```

(Append the constant + exception class at module level — add them just below the `DatasetNotAllowedError` class, not inside `BQClient`.)

Then add these methods inside `BQClient`:

```python
    # ----- query execution -----

    def estimate_query_cost(self, query: str, *, max_bytes_billed: int):
        from .models import CostEstimate

        job = self._dry_run(query)
        bytes_proc = job.total_bytes_processed or 0
        return CostEstimate(
            total_bytes_processed=bytes_proc,
            estimated_usd=round(bytes_proc * USD_PER_BYTE, 6),
            would_be_blocked=bytes_proc > max_bytes_billed,
        )

    def run_query(self, query: str, *, max_bytes_billed: int):
        from google.cloud import bigquery as bq

        from .models import ColumnSchema, QueryResult

        dryrun_job = self._dry_run(query)

        # Allowlist enforcement on referenced tables
        if self.allowed_datasets is not None:
            for ref in dryrun_job.referenced_tables or []:
                if ref.dataset_id not in self.allowed_datasets:
                    raise DatasetNotAllowedError(
                        f"query references dataset {ref.dataset_id!r} which is "
                        "not in the configured allowlist"
                    )

        bytes_proc = dryrun_job.total_bytes_processed or 0
        if bytes_proc > max_bytes_billed:
            raise CostExceededError(
                f"query estimate {bytes_proc} bytes exceeds cap {max_bytes_billed}"
            )

        config = bq.QueryJobConfig(maximum_bytes_billed=max_bytes_billed)
        job = self.client.query(query, job_config=config)
        rows = [dict(row.items()) for row in job.result()]

        return QueryResult(
            rows=rows,
            schema=[
                ColumnSchema(
                    name=f.name,
                    type=f.field_type,
                    mode=f.mode or "NULLABLE",
                    description=getattr(f, "description", None),
                )
                for f in job.schema or []
            ],
            total_bytes_processed=job.total_bytes_processed or 0,
            total_bytes_billed=job.total_bytes_billed or 0,
            cache_hit=bool(job.cache_hit),
            job_id=job.job_id,
            location=job.location,
        )

    def _dry_run(self, query: str):
        from google.cloud import bigquery as bq

        config = bq.QueryJobConfig(dry_run=True, use_query_cache=False)
        return self.client.query(query, job_config=config)
```

- [ ] **Step 15.4: Run tests to confirm pass**

Run: `uv run pytest tests/unit/test_bq_query.py -v`
Expected: 6 passed.

- [ ] **Step 15.5: Run all unit tests**

Run: `uv run pytest tests/unit/ -q`
Expected: All passed; total ~70+ tests.

- [ ] **Step 15.6: Commit**

```bash
git add src/bq_readonly_mcp/bq.py tests/unit/test_bq_query.py
git commit -m "feat(bq): query execution with dry-run cost guard and allowlist check"
```

---

## Task 16: Tool — `list_datasets`

**Files:**
- Create: `src/bq_readonly_mcp/tools/__init__.py`
- Create: `src/bq_readonly_mcp/tools/list_datasets.py`
- Create: `tests/unit/test_tool_list_datasets.py`

- [ ] **Step 16.1: Write failing tests**

```python
# tests/unit/test_tool_list_datasets.py
from unittest.mock import MagicMock

from bq_readonly_mcp.models import DatasetInfo
from bq_readonly_mcp.tools.list_datasets import handle


def test_returns_all_datasets():
    bq = MagicMock()
    bq.list_datasets.return_value = [DatasetInfo(dataset_id="a", location="US")]
    out = handle({}, bq=bq)
    assert out == [{"dataset_id": "a", "location": "US", "friendly_name": None, "description": None}]
    bq.list_datasets.assert_called_once_with(name_contains=None)


def test_passes_name_contains():
    bq = MagicMock()
    bq.list_datasets.return_value = []
    handle({"name_contains": "sales"}, bq=bq)
    bq.list_datasets.assert_called_once_with(name_contains="sales")
```

- [ ] **Step 16.2: Run tests — expect fail**

`uv run pytest tests/unit/test_tool_list_datasets.py -v`

- [ ] **Step 16.3: Create `src/bq_readonly_mcp/tools/__init__.py`** (empty)

```python
```

- [ ] **Step 16.4: Implement `list_datasets.py`**

```python
"""Tool: list datasets."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import ListDatasetsInput

NAME = "list_datasets"
DESCRIPTION = (
    "List BigQuery datasets in the configured project. "
    "Returns dataset_id, location, friendly_name, and description for each. "
    "Optional `name_contains` does a case-insensitive substring filter."
)
INPUT_SCHEMA = ListDatasetsInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient) -> list[dict[str, Any]]:
    parsed = ListDatasetsInput(**args)
    return [d.model_dump() for d in bq.list_datasets(name_contains=parsed.name_contains)]
```

- [ ] **Step 16.5: Run tests to confirm pass**

Expected: 2 passed.

- [ ] **Step 16.6: Commit**

```bash
git add src/bq_readonly_mcp/tools/ tests/unit/test_tool_list_datasets.py
git commit -m "feat(tools): list_datasets"
```

---

## Task 17: Tool — `list_tables`

**Files:**
- Create: `src/bq_readonly_mcp/tools/list_tables.py`
- Create: `tests/unit/test_tool_list_tables.py`

- [ ] **Step 17.1: Write failing tests**

```python
# tests/unit/test_tool_list_tables.py
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from bq_readonly_mcp.models import TableInfo
from bq_readonly_mcp.tools.list_tables import handle


def test_returns_tables():
    bq = MagicMock()
    bq.list_tables.return_value = [TableInfo(table_id="t", type="TABLE")]
    out = handle({"dataset_id": "d"}, bq=bq)
    assert out[0]["table_id"] == "t"
    bq.list_tables.assert_called_once_with(dataset_id="d", name_contains=None)


def test_requires_dataset_id():
    with pytest.raises(ValidationError):
        handle({}, bq=MagicMock())
```

- [ ] **Step 17.2: Run tests — expect fail** (`uv run pytest tests/unit/test_tool_list_tables.py -v` → ModuleNotFoundError)
- [ ] **Step 17.3: Implement `list_tables.py`:**

```python
# src/bq_readonly_mcp/tools/list_tables.py
"""Tool: list tables in a dataset."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import ListTablesInput

NAME = "list_tables"
DESCRIPTION = (
    "List tables, views, materialized views, and external tables in a BigQuery dataset. "
    "Returns table_id and type for each. Optional `name_contains` filters by substring."
)
INPUT_SCHEMA = ListTablesInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient) -> list[dict[str, Any]]:
    parsed = ListTablesInput(**args)
    return [
        t.model_dump()
        for t in bq.list_tables(
            dataset_id=parsed.dataset_id, name_contains=parsed.name_contains
        )
    ]
```

- [ ] **Step 17.4: Run tests — expect pass** (`uv run pytest tests/unit/test_tool_list_tables.py -v` → 2 passed)
- [ ] **Step 17.5: Commit**

```bash
git add src/bq_readonly_mcp/tools/list_tables.py tests/unit/test_tool_list_tables.py
git commit -m "feat(tools): list_tables"
```

---

## Task 18: Tool — `get_table_metadata`

**Files:**
- Create: `src/bq_readonly_mcp/tools/get_table_metadata.py`
- Create: `tests/unit/test_tool_get_table_metadata.py`

Apply the same explicit 5-step TDD pattern (write failing test → run → implement → run pass → commit). Tests and implementation:

```python
# src/bq_readonly_mcp/tools/get_table_metadata.py
"""Tool: get table metadata (no schema, no samples)."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import GetTableMetadataInput

NAME = "get_table_metadata"
DESCRIPTION = (
    "Return metadata for a single table: type (TABLE/VIEW/MATERIALIZED_VIEW/EXTERNAL), "
    "description, labels, created/modified timestamps, row count, size in bytes, "
    "partitioning config, clustering columns, and expiration. Cheap — no query bytes consumed."
)
INPUT_SCHEMA = GetTableMetadataInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient) -> dict[str, Any]:
    parsed = GetTableMetadataInput(**args)
    md = bq.get_table_metadata(parsed.dataset_id, parsed.table_id)
    return md.model_dump()
```

Tests:

```python
# tests/unit/test_tool_get_table_metadata.py
from unittest.mock import MagicMock

from bq_readonly_mcp.models import TableMetadata
from bq_readonly_mcp.tools.get_table_metadata import handle


def test_returns_metadata_dict():
    bq = MagicMock()
    bq.get_table_metadata.return_value = TableMetadata(
        table_id="t", type="TABLE",
        created="2026-01-01T00:00:00", modified="2026-01-01T00:00:00",
        row_count=10, size_bytes=100,
    )
    out = handle({"dataset_id": "d", "table_id": "t"}, bq=bq)
    assert out["table_id"] == "t"
    assert out["row_count"] == 10
```

Commit:

```bash
git add src/bq_readonly_mcp/tools/get_table_metadata.py tests/unit/test_tool_get_table_metadata.py
git commit -m "feat(tools): get_table_metadata"
```

---

## Task 19: Tool — `describe_columns`

**Files:**
- Create: `src/bq_readonly_mcp/tools/describe_columns.py`
- Create: `tests/unit/test_tool_describe_columns.py`

```python
# src/bq_readonly_mcp/tools/describe_columns.py
"""Tool: describe columns of a table."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import DescribeColumnsInput

NAME = "describe_columns"
DESCRIPTION = (
    "Return the column schema (name, type, mode, description) of a single table. "
    "Lighter than `get_table` — no metadata, no samples. Use this when the LLM only "
    "needs schema to write a query. Cheap — no query bytes consumed."
)
INPUT_SCHEMA = DescribeColumnsInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient) -> list[dict[str, Any]]:
    parsed = DescribeColumnsInput(**args)
    return [c.model_dump() for c in bq.describe_columns(parsed.dataset_id, parsed.table_id)]
```

Apply the same explicit 5-step TDD pattern. Test verifies the tool calls the wrapper and serializes output:

```python
# tests/unit/test_tool_describe_columns.py
from unittest.mock import MagicMock

from bq_readonly_mcp.models import ColumnSchema
from bq_readonly_mcp.tools.describe_columns import handle


def test_returns_columns():
    bq = MagicMock()
    bq.describe_columns.return_value = [ColumnSchema(name="x", type="INT64", mode="NULLABLE")]
    out = handle({"dataset_id": "d", "table_id": "t"}, bq=bq)
    assert out == [{"name": "x", "type": "INT64", "mode": "NULLABLE", "description": None}]
```

Commit:

```bash
git add src/bq_readonly_mcp/tools/describe_columns.py tests/unit/test_tool_describe_columns.py
git commit -m "feat(tools): describe_columns"
```

---

## Task 20: Tool — `get_table` (metadata + columns + samples)

**Files:**
- Create: `src/bq_readonly_mcp/tools/get_table.py`
- Create: `tests/unit/test_tool_get_table.py`

```python
# src/bq_readonly_mcp/tools/get_table.py
"""Tool: get full table info — metadata, columns, and N sample rows."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import GetTableInput

NAME = "get_table"
DESCRIPTION = (
    "Return everything about a single table: metadata, column schema, and N sample rows "
    "(default 3). Combines `get_table_metadata` + `describe_columns` + a small SELECT * sample. "
    "The sample query is subject to the same dry-run cost guard as `run_query`."
)
INPUT_SCHEMA = GetTableInput.model_json_schema()


def handle(
    args: dict[str, Any],
    *,
    bq: BQClient,
    default_sample_rows: int,
    max_bytes_billed: int,
) -> dict[str, Any]:
    parsed = GetTableInput(**args)
    n = parsed.sample_rows if parsed.sample_rows is not None else default_sample_rows

    md = bq.get_table_metadata(parsed.dataset_id, parsed.table_id)
    cols = bq.describe_columns(parsed.dataset_id, parsed.table_id)
    samples = bq.run_query(
        f"SELECT * FROM `{bq.client.project}.{parsed.dataset_id}.{parsed.table_id}` LIMIT {n}",
        max_bytes_billed=max_bytes_billed,
    )

    return {
        "metadata": md.model_dump(),
        "columns": [c.model_dump() for c in cols],
        "sample_rows": samples.rows,
    }
```

Apply the same explicit 5-step TDD pattern. Test verifies the tool bundles all three sub-calls correctly:

```python
# tests/unit/test_tool_get_table.py
from unittest.mock import MagicMock

from bq_readonly_mcp.models import ColumnSchema, QueryResult, TableMetadata
from bq_readonly_mcp.tools.get_table import handle


def test_bundles_metadata_columns_and_samples():
    bq = MagicMock()
    bq.client.project = "p"
    bq.get_table_metadata.return_value = TableMetadata(
        table_id="t", type="TABLE", created="2026-01-01T00:00:00",
        modified="2026-01-01T00:00:00", row_count=10, size_bytes=100,
    )
    bq.describe_columns.return_value = [ColumnSchema(name="x", type="INT64", mode="NULLABLE")]
    bq.run_query.return_value = QueryResult(
        rows=[{"x": 1}], schema=[], total_bytes_processed=1, total_bytes_billed=0,
        cache_hit=False, job_id="j", location="US",
    )

    out = handle(
        {"dataset_id": "d", "table_id": "t"},
        bq=bq, default_sample_rows=3, max_bytes_billed=1_000_000_000,
    )
    assert out["metadata"]["table_id"] == "t"
    assert out["columns"][0]["name"] == "x"
    assert out["sample_rows"] == [{"x": 1}]
```

Commit:

```bash
git add src/bq_readonly_mcp/tools/get_table.py tests/unit/test_tool_get_table.py
git commit -m "feat(tools): get_table with metadata + columns + samples"
```

---

## Task 21: Tool — `estimate_query_cost`

**Files:**
- Create: `src/bq_readonly_mcp/tools/estimate_query_cost.py`
- Create: `tests/unit/test_tool_estimate_query_cost.py`

```python
# src/bq_readonly_mcp/tools/estimate_query_cost.py
"""Tool: estimate the cost of a query without executing it."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import EstimateQueryCostInput
from ..safety import validate_select_query

NAME = "estimate_query_cost"
DESCRIPTION = (
    "Run a free dry-run against BigQuery and return the estimated bytes processed and USD cost. "
    "Useful for the LLM to reason about query expense before deciding to execute. "
    "The query is validated as SELECT-only first; DML/DDL is rejected."
)
INPUT_SCHEMA = EstimateQueryCostInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient, max_bytes_billed: int) -> dict[str, Any]:
    parsed = EstimateQueryCostInput(**args)
    validate_select_query(parsed.query)
    est = bq.estimate_query_cost(parsed.query, max_bytes_billed=max_bytes_billed)
    return est.model_dump()
```

Apply the same explicit 5-step TDD pattern. Test verifies validation runs before estimation:

```python
# tests/unit/test_tool_estimate_query_cost.py
from unittest.mock import MagicMock

import pytest

from bq_readonly_mcp.safety import SafetyError
from bq_readonly_mcp.tools.estimate_query_cost import handle


def test_dml_rejected_before_estimate():
    bq = MagicMock()
    with pytest.raises(SafetyError):
        handle({"query": "DELETE FROM t"}, bq=bq, max_bytes_billed=1_000_000_000)
    bq.estimate_query_cost.assert_not_called()


def test_select_calls_estimate():
    bq = MagicMock()
    bq.estimate_query_cost.return_value.model_dump.return_value = {
        "total_bytes_processed": 100, "estimated_usd": 0.000001, "would_be_blocked": False,
    }
    out = handle({"query": "SELECT 1"}, bq=bq, max_bytes_billed=1_000_000_000)
    assert out["total_bytes_processed"] == 100
```

Commit:

```bash
git add src/bq_readonly_mcp/tools/estimate_query_cost.py tests/unit/test_tool_estimate_query_cost.py
git commit -m "feat(tools): estimate_query_cost"
```

---

## Task 22: Tool — `run_query`

**Files:**
- Create: `src/bq_readonly_mcp/tools/run_query.py`
- Create: `tests/unit/test_tool_run_query.py`

- [ ] **Step 22.1: Write failing tests**

```python
# tests/unit/test_tool_run_query.py
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from bq_readonly_mcp.models import QueryResult
from bq_readonly_mcp.tools.run_query import handle


def make_bq():
    bq = MagicMock()
    bq.run_query.return_value = QueryResult(
        rows=[{"x": 1}], schema=[],
        total_bytes_processed=100, total_bytes_billed=0,
        cache_hit=False, job_id="j1", location="US",
    )
    return bq


def test_select_query_executes_with_auto_limit():
    bq = make_bq()
    handle({"query": "SELECT * FROM t"}, bq=bq, default_limit=50, max_limit=10000, max_bytes_billed=1_000_000_000)
    sent = bq.run_query.call_args.args[0]
    assert sent.rstrip().rstrip(";").endswith("LIMIT 50")


def test_explicit_limit_used():
    bq = make_bq()
    handle({"query": "SELECT * FROM t", "limit": 200}, bq=bq, default_limit=50, max_limit=10000, max_bytes_billed=1_000_000_000)
    sent = bq.run_query.call_args.args[0]
    assert sent.endswith("LIMIT 200")


def test_no_limit_skips_injection():
    bq = make_bq()
    handle(
        {"query": "SELECT * FROM t", "no_limit": True},
        bq=bq, default_limit=50, max_limit=10000, max_bytes_billed=1_000_000_000,
    )
    sent = bq.run_query.call_args.args[0]
    assert "LIMIT" not in sent.upper()


def test_limit_above_cap_rejected():
    with pytest.raises(ValueError, match="exceeds max_limit"):
        handle(
            {"query": "SELECT * FROM t", "limit": 99999},
            bq=make_bq(), default_limit=50, max_limit=10000, max_bytes_billed=1_000_000_000,
        )


def test_dry_run_returns_estimate_only(monkeypatch):
    bq = make_bq()
    bq.estimate_query_cost.return_value.model_dump.return_value = {"total_bytes_processed": 999}
    out = handle(
        {"query": "SELECT * FROM t", "dry_run": True},
        bq=bq, default_limit=50, max_limit=10000, max_bytes_billed=1_000_000_000,
    )
    bq.run_query.assert_not_called()
    bq.estimate_query_cost.assert_called_once()


def test_dml_query_rejected_before_executing():
    from bq_readonly_mcp.safety import SafetyError
    bq = make_bq()
    with pytest.raises(SafetyError):
        handle(
            {"query": "DELETE FROM t WHERE 1=1"},
            bq=bq, default_limit=50, max_limit=10000, max_bytes_billed=1_000_000_000,
        )
    bq.run_query.assert_not_called()
```

- [ ] **Step 22.2: Run tests to confirm fail.**

- [ ] **Step 22.3: Implement `run_query.py`**

```python
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

    if parsed.no_limit:
        prepared = parsed.query
    else:
        prepared = inject_limit(parsed.query, effective_limit)

    result = bq.run_query(prepared, max_bytes_billed=max_bytes_billed)
    return result.model_dump()
```

- [ ] **Step 22.4: Run tests to confirm pass.**

- [ ] **Step 22.5: Commit**

```bash
git add src/bq_readonly_mcp/tools/run_query.py tests/unit/test_tool_run_query.py
git commit -m "feat(tools): run_query with auto-LIMIT, cap, and cost guard"
```

---

## Task 23: `server.py` — MCP wiring + CLI entry

**Files:**
- Create: `src/bq_readonly_mcp/server.py`
- Create: `tests/unit/test_server.py`

- [ ] **Step 23.1: Write failing tests**

```python
# tests/unit/test_server.py
from unittest.mock import patch

from bq_readonly_mcp.server import build_tool_registry


def test_registry_has_seven_tools():
    registry = build_tool_registry()
    names = [t["name"] for t in registry]
    assert set(names) == {
        "list_datasets",
        "list_tables",
        "get_table_metadata",
        "describe_columns",
        "get_table",
        "run_query",
        "estimate_query_cost",
    }


def test_each_tool_has_schema_and_description():
    registry = build_tool_registry()
    for t in registry:
        assert isinstance(t["description"], str) and t["description"]
        assert isinstance(t["input_schema"], dict)
```

- [ ] **Step 23.2: Run tests — fail.**

- [ ] **Step 23.3: Implement `server.py`**

```python
"""MCP server entry point.

Wires the 7 tools together, performs the startup checks (dataset enumeration
warning when no allowlist), and serves over stdio.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any

import mcp.server.stdio
from mcp.server import Server
from mcp.types import TextContent, Tool

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
    return [
        {
            "name": m.NAME,
            "description": m.DESCRIPTION,
            "input_schema": m.INPUT_SCHEMA,
        }
        for m in TOOL_MODULES
    ]


def _warn_if_no_allowlist(cfg: Config, bq: BQClient) -> None:
    if cfg.allowed_datasets is not None:
        return
    try:
        datasets = bq.list_datasets()
    except Exception as exc:
        LOG.warning("could not enumerate datasets at startup: %s", exc)
        return
    ids = sorted(d.dataset_id for d in datasets)
    print(
        "WARNING: no --datasets allowlist configured. "
        f"This server can read all {len(ids)} datasets visible to your ADC identity in "
        f"project {cfg.project!r}: {ids}\n"
        f"To restrict, restart with: --datasets " + " ".join(ids[:3]) + " ...",
        file=sys.stderr,
    )


async def _serve(cfg: Config, bq: BQClient) -> None:
    app = Server("bq-readonly-mcp")

    @app.list_tools()
    async def _list_tools() -> list[Tool]:
        return [
            Tool(name=t["name"], description=t["description"], inputSchema=t["input_schema"])
            for t in build_tool_registry()
        ]

    @app.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
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
                raise ValueError(f"unknown tool: {name}")
        except (SafetyError, CostExceededError, DatasetNotAllowedError, ValueError) as exc:
            return [TextContent(type="text", text=f"error: {exc}")]

        import json
        return [TextContent(type="text", text=json.dumps(result, default=str))]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        cfg = build_config(argv=sys.argv[1:], env=os.environ)
    except SystemExit as e:
        return int(e.code or 2)

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
```

- [ ] **Step 23.4: Run tests to confirm pass.**

- [ ] **Step 23.5: Commit**

```bash
git add src/bq_readonly_mcp/server.py tests/unit/test_server.py
git commit -m "feat(server): MCP stdio wiring with 7 tools and startup allowlist warning"
```

---

## Task 24: `__main__.py` — `python -m` entry

**Files:**
- Create: `src/bq_readonly_mcp/__main__.py`

- [ ] **Step 24.1: Add file**

```python
"""Allow `python -m bq_readonly_mcp` invocation."""

from .server import main

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 24.2: Smoke test**

```bash
uv run python -m bq_readonly_mcp --help
```

Expected: argparse help output with all flags, exit code 0.

- [ ] **Step 24.3: Commit**

```bash
git add src/bq_readonly_mcp/__main__.py
git commit -m "feat: support python -m bq_readonly_mcp invocation"
```

---

## Task 25: `test_no_pii.py` — public-repo hygiene scanner

**Files:**
- Create: `tests/unit/test_no_pii.py`

- [ ] **Step 25.1: Implement the test**

```python
"""Public-repo hygiene: positive allowlist scan for project-ID-shaped strings.

Walks every tracked file under the repo root and extracts any token matching
the GCP project ID regex. Asserts each match is one of:
  - placeholder (`your-project-id`)
  - Google's public-data projects (`bigquery-public-data`, `cloud-samples-data`,
    `bigquery-samples`)
  - the author's email domain literal (already part of pyproject metadata)

Any other project-ID-shaped string fails the test, signaling a leak.
"""

import re
import subprocess
from pathlib import Path

PROJECT_ID_RE = re.compile(r"\b[a-z][a-z0-9-]{4,28}[a-z0-9]\b")
ALLOWED = {
    "your-project-id",
    "bigquery-public-data",
    "cloud-samples-data",
    "bigquery-samples",
    # standard tooling/python-stdlib-ish strings that happen to match
    "google-cloud-bigquery",
    "google-auth-httplib2",
    "google-api-python-client",
    "google-cloud-sdk",
    "pytest-asyncio",
    "pytest-mock",
    "python-version",
    "license-files",
    "asyncio-default-fixture-loop-scope",
    "ignore-missing-imports",
    "use-query-cache",
    "set-quota-project",
    "test-driven-development",
    "verify-code-against-the-plan",
    "code-review-against-the-plan",
}

# Paths excluded from scanning
EXCLUDE_PREFIXES = (".git/", "dist/", ".venv/", "build/", "__pycache__/", ".ruff_cache/", ".mypy_cache/", ".pytest_cache/")
TEXT_EXTS = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".cfg", ".ini", ".txt"}


def _tracked_files(repo_root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"],
        check=True, capture_output=True, text=True,
    )
    return [repo_root / line for line in out.stdout.splitlines() if line]


def test_no_unknown_project_id_strings():
    repo_root = Path(__file__).resolve().parents[2]
    bad: dict[str, list[str]] = {}

    for path in _tracked_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        if any(rel.startswith(p) for p in EXCLUDE_PREFIXES):
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in PROJECT_ID_RE.findall(text):
            if match in ALLOWED:
                continue
            # The author's email domain is allowed via the pyproject author field;
            # we don't pattern-match the email here because it doesn't match the
            # project-ID regex anyway (contains '.' and '@').
            bad.setdefault(match, []).append(rel)

    # The point of this test is to fail loudly when a leak slips in.
    # We accept some false positives by extending ALLOWED above; the goal is
    # to never have an internal project-id-shaped token end up here.
    if bad:
        # Filter common english-word false positives that match the regex by accident.
        # These are tokens that appeared in the wild and are clearly not GCP project IDs.
        EXTRA_FALSE_POSITIVES = {
            "anthropic-ai", "claude-code", "claude-desktop",
            "google-sheets", "g-sheet-mcp", "bq-readonly-mcp",
            "modelcontextprotocol", "model-context-protocol",
        }
        bad = {k: v for k, v in bad.items() if k not in EXTRA_FALSE_POSITIVES}

    assert not bad, (
        "Possible leak: project-ID-shaped tokens found in tracked files. "
        "Add to ALLOWED in this test if they're legitimate, or scrub them: "
        + ", ".join(sorted(bad))
    )
```

- [ ] **Step 25.2: Run the test — expect PASS** (the repo currently has nothing leaky).

```bash
uv run pytest tests/unit/test_no_pii.py -v
```

If it fails, add the legitimate match to `ALLOWED` (or scrub the leak). Document in CLAUDE.md if the allowlist grows by more than 2 entries.

- [ ] **Step 25.3: Commit**

```bash
git add tests/unit/test_no_pii.py
git commit -m "test: positive-allowlist scanner for project-ID-shaped tokens"
```

---

## Task 26: Integration tests — public datasets

**Files:**
- Create: `tests/integration/test_public_datasets.py`
- Modify: `tests/conftest.py`

- [ ] **Step 26.1: Add ADC-required fixture to `conftest.py`**

Replace `tests/conftest.py` contents with:

```python
"""Shared pytest fixtures."""

import os
import pytest

from bq_readonly_mcp.auth import AuthError, build_bigquery_client
from bq_readonly_mcp.bq import BQClient
from bq_readonly_mcp.config import Config


@pytest.fixture(scope="session")
def integration_bq() -> BQClient:
    project = os.environ.get("BQ_INTEGRATION_PROJECT")
    if not project:
        pytest.skip("BQ_INTEGRATION_PROJECT not set; skipping integration tests")
    cfg = Config(
        project=project,
        location="US",
        allowed_datasets=None,
        default_limit=50,
        max_limit=10_000,
        max_bytes_billed=1_073_741_824,
        sample_rows=3,
        key_file=None,
    )
    try:
        client = build_bigquery_client(cfg)
    except AuthError as exc:
        pytest.skip(f"ADC unavailable: {exc}")
    return BQClient(client=client, allowed_datasets=None)
```

- [ ] **Step 26.2: Add integration tests**

```python
# tests/integration/test_public_datasets.py
"""Integration tests against Google's public datasets.

Require ADC + env var BQ_INTEGRATION_PROJECT pointing to a project that has
permission to query bigquery-public-data.* (which is essentially any project
with billing enabled). Skipped in CI by default.
"""

import pytest

from bq_readonly_mcp.bq import CostExceededError
from bq_readonly_mcp.safety import SafetyError
from bq_readonly_mcp.tools import (
    describe_columns,
    estimate_query_cost,
    get_table_metadata,
    list_tables,
    run_query,
)

pytestmark = pytest.mark.integration


def test_list_tables_in_public_samples(integration_bq):
    tables = list_tables.handle({"dataset_id": "samples"}, bq=integration_bq)
    # We list tables in the *configured project*, not in bigquery-public-data — so this
    # may be empty, that's fine. The point is the call succeeds without error.
    assert isinstance(tables, list)


def test_get_table_metadata_against_public_dataset(integration_bq):
    # Switch the BQClient's underlying client to query bigquery-public-data
    md = get_table_metadata.handle(
        {"dataset_id": "samples", "table_id": "shakespeare"},
        bq=_with_project(integration_bq, "bigquery-public-data"),
    )
    assert md["table_id"] == "shakespeare"
    assert md["row_count"] > 100_000


def test_describe_columns_against_public_dataset(integration_bq):
    cols = describe_columns.handle(
        {"dataset_id": "samples", "table_id": "shakespeare"},
        bq=_with_project(integration_bq, "bigquery-public-data"),
    )
    names = [c["name"] for c in cols]
    assert "word" in names
    assert "corpus" in names


def test_estimate_query_cost_returns_estimate(integration_bq):
    out = estimate_query_cost.handle(
        {"query": "SELECT word FROM `bigquery-public-data.samples.shakespeare` LIMIT 10"},
        bq=integration_bq,
        max_bytes_billed=1_073_741_824,
    )
    assert "total_bytes_processed" in out


def test_run_query_real(integration_bq):
    out = run_query.handle(
        {"query": "SELECT word FROM `bigquery-public-data.samples.shakespeare`"},
        bq=integration_bq,
        default_limit=5,
        max_limit=10_000,
        max_bytes_billed=1_073_741_824,
    )
    assert len(out["rows"]) == 5


def test_cost_guard_refuses_huge_query(integration_bq):
    # Wikipedia pageviews_2015 is hundreds of GB; with a tight cap this must refuse.
    with pytest.raises(CostExceededError):
        run_query.handle(
            {"query": "SELECT * FROM `bigquery-public-data.wikipedia.pageviews_2015`"},
            bq=integration_bq,
            default_limit=5,
            max_limit=10_000,
            max_bytes_billed=10_000_000,  # 10 MB — wikipedia pageviews scans way more
        )


def test_dml_rejected_before_query(integration_bq):
    with pytest.raises(SafetyError):
        run_query.handle(
            {"query": "DELETE FROM `bigquery-public-data.samples.shakespeare` WHERE 1=1"},
            bq=integration_bq,
            default_limit=5,
            max_limit=10_000,
            max_bytes_billed=1_073_741_824,
        )


def _with_project(bq, project: str):
    """Return a new BQClient whose underlying client targets a different project.

    bigquery-public-data tables are queried by anyone with a billing project,
    but `bq.client.project` controls the *billing* project. The dataset.table
    in the query string can reference any project the caller has IAM read on.
    For metadata calls (`get_table`, `list_tables`), the project is what's
    used as the lookup project — so we need a fresh client pointed at
    `bigquery-public-data` for those.
    """
    from google.cloud import bigquery
    new_client = bigquery.Client(
        project=project,
        location=bq.client.location,
        credentials=bq.client._credentials,
    )
    from bq_readonly_mcp.bq import BQClient
    return BQClient(client=new_client, allowed_datasets=None)
```

- [ ] **Step 26.3: Smoke test**

```bash
BQ_INTEGRATION_PROJECT=<your-project> uv run pytest -m integration tests/integration/ -v
```

(All should pass against ADC-authenticated user.)

- [ ] **Step 26.4: Commit**

```bash
git add tests/integration/ tests/conftest.py
git commit -m "test: integration tests against bigquery-public-data"
```

---

## Task 27: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 27.1: Write a README mirroring `g-sheet-mcp`'s structure**

Sections (in order):
1. Title + 1-line tagline
2. Badges: PyPI version, CI status, Python versions, license
3. **Why this exists** — 2-paragraph pitch on safety guarantees
4. **What it does** — bulleted list of the 7 tools
5. **Quick start** — three install paths:
   - **Recommended:** `uvx bq-readonly-mcp --project YOUR_PROJECT --location US`
   - From PyPI: `uv tool install bq-readonly-mcp`
   - From source: `git clone ... && uv run bq-readonly-mcp ...`
6. **Authentication** — `gcloud auth application-default login` plus the `--key-file` alternative
7. **MCP client setup** — link to `docs/EDITOR_SETUP.md` and copy/paste configs for Claude Code, Cursor, Windsurf
8. **Configuration reference** — full table of CLI args + env vars from §4 of the spec
9. **Safety model** — short summary of the validator + cost guard with a link to `SECURITY.md`
10. **What it does NOT do** — write operations, vector search, multi-project, job history
11. **Comparison to other BigQuery MCPs** — brief, honest table mentioning `pvoo/bigquery-mcp` and noting the differentiation (strict read-only + dry-run cost guard, no vector search)
12. **Development** — `uv sync --extra dev`, `pytest`, `ruff`, `mypy`
13. **License** — MIT

- [ ] **Step 27.2: Verify no PII**

```bash
uv run pytest tests/unit/test_no_pii.py -v
```

- [ ] **Step 27.3: Commit**

```bash
git add README.md
git commit -m "docs: README with quick start, config reference, and safety model"
```

---

## Task 28: User docs + MCP config examples

**Files:**
- Create: `docs/QUICKSTART.md`
- Create: `docs/EDITOR_SETUP.md`
- Create: `docs/TROUBLESHOOTING.md`
- Create: `mcp-config-examples/claude-code.json`
- Create: `mcp-config-examples/claude-desktop.json`
- Create: `mcp-config-examples/cursor.json`
- Create: `mcp-config-examples/windsurf.json`
- Create: `mcp-config-examples/copilot.json`

- [ ] **Step 28.1: `docs/QUICKSTART.md`** — five steps from zero (install gcloud, ADC login, install via uvx, configure MCP client, restart). Include exact commands.

- [ ] **Step 28.2: `docs/EDITOR_SETUP.md`** — per-editor walkthroughs with screenshots-replacement (paths to settings files, exact JSON to paste).

- [ ] **Step 28.3: `docs/TROUBLESHOOTING.md`** — common errors:
  - `DefaultCredentialsError` → run `gcloud auth application-default login`
  - "permission denied" on dataset → check IAM
  - "exceeds bytes-billed cap" → bump `--max-bytes-billed` or narrow query
  - "no such dataset" → verify `--datasets` allowlist if set

- [ ] **Step 28.4: Five MCP config examples**

`mcp-config-examples/claude-code.json`:

```json
{
  "mcpServers": {
    "bq-readonly": {
      "command": "uvx",
      "args": [
        "bq-readonly-mcp",
        "--project", "your-project-id",
        "--location", "US"
      ]
    }
  }
}
```

The other four (`claude-desktop.json`, `cursor.json`, `windsurf.json`, `copilot.json`) follow the format the respective client expects — same `uvx` command structure, just nested under whatever key each client uses.

- [ ] **Step 28.5: Verify no PII**

```bash
uv run pytest tests/unit/test_no_pii.py -v
```

- [ ] **Step 28.6: Commit (split into atomic commits)**

```bash
git add docs/QUICKSTART.md
git commit -m "docs: QUICKSTART walkthrough"

git add docs/EDITOR_SETUP.md
git commit -m "docs: EDITOR_SETUP for Claude/Cursor/Windsurf/Copilot"

git add docs/TROUBLESHOOTING.md
git commit -m "docs: TROUBLESHOOTING for common errors"

git add mcp-config-examples/
git commit -m "docs: ready-to-paste MCP config examples for 5 clients"
```

---

## Task 29: PUBLISHING.md

**Files:**
- Create: `docs/PUBLISHING.md`

- [ ] **Step 29.1: Write release runbook**

Sections:
1. **Prerequisites:** PyPI account, GitHub `pypi` environment with `PYPI__TOKEN__` secret.
2. **Steps:**
   - Bump `version` in `pyproject.toml` (semver)
   - Open PR with the bump + CHANGELOG entry
   - Merge to `main` after CI green + review
   - Publish workflow runs automatically on push to `main`
   - Verify on PyPI within ~3 minutes
   - Smoke test: `uvx bq-readonly-mcp@<new-version> --help`
3. **Rollback:** versions cannot be deleted from PyPI; bump version and re-publish.

- [ ] **Step 29.2: Commit**

```bash
git add docs/PUBLISHING.md
git commit -m "docs: PUBLISHING release runbook"
```

---

## Task 30: SECURITY.md, CONTRIBUTING.md, CHANGELOG.md

**Files:**
- Create: `SECURITY.md`
- Create: `CONTRIBUTING.md`
- Create: `CHANGELOG.md`

- [ ] **Step 30.1: `SECURITY.md`** — adapt sister-project's content. Cover:
  - Read-only model
  - ADC posture
  - Threats mitigated (table from spec §2)
  - Public-repo hygiene rules
  - Reporting a vulnerability via private GitHub security advisory

- [ ] **Step 30.2: `CONTRIBUTING.md`** — branch policy (PRs only, no direct pushes to `main`), conventional commits, TDD expectation, what to run before opening a PR, how to add a new tool (point to spec).

- [ ] **Step 30.3: `CHANGELOG.md`** — Keep-a-Changelog format, single entry for v0.1.0:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-26

### Added
- Initial release.
- 7 tools: `list_datasets`, `list_tables`, `get_table_metadata`, `describe_columns`, `get_table`, `run_query`, `estimate_query_cost`.
- Strict SELECT/WITH-only SQL validator with comment stripping, multi-statement rejection, DML/DDL keyword rejection.
- Auto-LIMIT 50 with override (max 10,000 by default, raisable via `--max-limit`).
- Bytes-billed cap with dry-run guard (default 1 GB, configurable via `--max-bytes-billed`).
- Optional `--datasets` allowlist; warn at startup when unset.
- ADC default with optional `--key-file` for non-interactive use.
```

- [ ] **Step 30.4: Commit each atomically**

```bash
git add SECURITY.md
git commit -m "docs: SECURITY policy and threat model"

git add CONTRIBUTING.md
git commit -m "docs: CONTRIBUTING guidelines"

git add CHANGELOG.md
git commit -m "docs: CHANGELOG for 0.1.0"
```

---

## Task 31: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 31.1: Mirror `g-sheet-mcp`'s `ci.yml`**

```yaml
name: CI

on:
  push:
    branches:
      - main
  pull_request:
  workflow_dispatch:

jobs:
  verify:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v5

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.11"

      - name: Set up uv
        uses: astral-sh/setup-uv@v7

      - name: Sync dependencies
        run: uv sync --extra dev --frozen

      - name: Lint
        run: uv run ruff check src tests

      - name: Type check
        run: uv run mypy src

      - name: Unit tests
        run: uv run pytest tests/unit/ -q
```

- [ ] **Step 31.2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions CI workflow (ruff, mypy, pytest)"
```

---

## Task 32: Publish workflow

**Files:**
- Create: `.github/workflows/publish.yml`

- [ ] **Step 32.1: Copy the idempotent publish workflow from `g-sheet-mcp`**

Copy `g-sheet-mcp`'s `publish.yml` verbatim, replacing only the package name reference if hardcoded (it isn't — the workflow reads from `pyproject.toml`). The workflow:
- Triggers on push to `main` and manual dispatch.
- Gates on `github.ref_protected == true`.
- Uses `pypi` GitHub environment with `PYPI__TOKEN__` secret.
- Compares built artifacts to PyPI; only publishes new versions; fails if version is partially published with mismatched artifacts.

- [ ] **Step 32.2: Commit**

```bash
git add .github/workflows/publish.yml
git commit -m "ci: idempotent PyPI publish workflow with branch-protection gate"
```

---

## Task 33: Final quality gate before PR

- [ ] **Step 33.1: Lint clean**

```bash
uv run ruff check src tests
```

Expected: no warnings.

- [ ] **Step 33.2: Types clean**

```bash
uv run mypy src
```

Expected: no errors.

- [ ] **Step 33.3: All unit tests pass**

```bash
uv run pytest tests/unit/ -q
```

Expected: all passed (~80+ tests).

- [ ] **Step 33.4: No-PII test passes**

```bash
uv run pytest tests/unit/test_no_pii.py -v
```

Expected: passed.

- [ ] **Step 33.5: Help works**

```bash
uv run bq-readonly-mcp --help
```

Expected: argparse help output, exit 0.

- [ ] **Step 33.6: Coverage report (informational)**

```bash
uv run pytest tests/unit/ --cov=src/bq_readonly_mcp --cov-report=term-missing
```

Expected: ≥90% on `safety.py` and `bq.py`; ≥80% overall.

---

## Spec coverage check

The following spec sections each have a corresponding task:

| Spec section | Implementing task |
|---|---|
| §1 Purpose / non-goals | Documented in README §10, CHANGELOG (Task 27, 30) |
| §2 Threat model | Implemented across Tasks 4–10, 15, 22; documented in SECURITY (Task 30) |
| §3 Architecture / file layout | Tasks 1–24 |
| §4 Configuration | Task 3 (`config.py`) + Task 23 (`server.py` startup warning) |
| §5.1 list_datasets | Task 16 |
| §5.2 list_tables | Task 17 |
| §5.3 get_table_metadata | Task 18 |
| §5.4 describe_columns | Task 19 |
| §5.5 get_table | Task 20 |
| §5.6 run_query (validator pipeline) | Tasks 4–9 (safety) + Task 15 (bq) + Task 22 (tool) |
| §5.7 estimate_query_cost | Task 21 |
| §6 Data flow | Task 23 |
| §7 Error handling | Task 23 (server-level handler) + each tool's exception path |
| §8 Testing strategy | Unit: Tasks 4–22; integration: Task 26; no-PII: Task 25 |
| §9 CI / publishing / branch protection | Tasks 31, 32; branch protection is operational (post-plan) |
| §10 Security posture | Implemented across; documented in SECURITY (Task 30) and test_no_pii (Task 25) |
| §11 Project metadata | Task 1 (`pyproject.toml`) |
| §13 Acceptance criteria | Task 33 |

---

## Operational follow-ups (after this plan completes)

These are tracked separately in the project's TaskList and are *not* part of this implementation plan:

1. **Create the public GitHub repo** `mariadb-RupeshBiswas/bq-readonly-mcp`, push `main`.
2. **Configure branch protection** on `main` (1 review, linear history, status check `verify`, no force-push).
3. **Set up `pypi` GitHub environment** with the `PYPI__TOKEN__` secret.
4. **Security audit** (self-audit per spec §10), produce `SECURITY_AUDIT.md`.
5. **Code review** via the `superpowers:code-reviewer` agent against this plan.
6. **Internal smoke test** against the user's working BigQuery project.
7. **Trigger publish workflow** to release v0.1.0 to PyPI.
8. **Wire Claude/Windsurf MCP configs** to use `uvx bq-readonly-mcp`.
9. **Re-audit `google-sheets-mcp`** sister project; fix and republish if needed.
