# bq-readonly-mcp

> 🔍 Read-only BigQuery MCP server with auto-LIMIT, dry-run cost guard, and ADC auth. Safe for LLMs to query your BigQuery — no DML, no surprises, no runaway bills.

[![PyPI](https://img.shields.io/pypi/v/bq-readonly-mcp.svg?cacheSeconds=300)](https://pypi.org/project/bq-readonly-mcp/)
[![CI](https://github.com/mariadb-RupeshBiswas/bq-readonly-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/mariadb-RupeshBiswas/bq-readonly-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/bq-readonly-mcp.svg?cacheSeconds=300)](https://pypi.org/project/bq-readonly-mcp/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## ✨ Why this exists

LLMs connected to BigQuery can accidentally scan terabytes if the MCP layer lets them run arbitrary SQL. `bq-readonly-mcp` prevents that by design: every query goes through a strict `SELECT`/`WITH`-only validator, gets an automatic `LIMIT` injected before it runs, and is priced via a dry-run before any bytes are billed. If the estimated cost exceeds the cap (default 1 GB), the query is refused outright — before a single byte hits your bill.

The server runs as a local stdio process under your OS account, uses [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials), and exposes zero write operations. There is no INSERT, no UPDATE, no DELETE, no DDL — anywhere in the codebase. The only thing it can do is read, and it does that safely.

---

## 🛠️ The 7 tools

| Tool | What it does | Use when… |
|---|---|---|
| `list_datasets` | List datasets in the project, with optional name filter | Starting exploration, finding what exists |
| `list_tables` | List tables in a dataset, with optional name filter | Drilling into a specific dataset |
| `get_table_metadata` | Table type, partitioning, clustering, row count, size | Checking if a table is large before querying |
| `describe_columns` | Column schema for a table (no data scan) | Understanding the shape of a table cheaply |
| `get_table` | Full bundle: metadata + columns + 3 sample rows | Onboarding to an unfamiliar table |
| `run_query` | `SELECT`-only with auto-LIMIT, dry-run cost guard, and bytes-billed cap | Running ad-hoc SQL |
| `estimate_query_cost` | Standalone dry-run — returns estimated bytes and USD cost | Checking query cost before running it |

---

## 🚀 Quick start

**Recommended — run directly via `uvx` (no install needed):**

```bash
uvx bq-readonly-mcp --project your-project-id --location US
```

**From PyPI (persistent install):**

```bash
uv tool install bq-readonly-mcp
bq-readonly-mcp --project your-project-id --location US
```

**From source:**

```bash
git clone https://github.com/mariadb-RupeshBiswas/bq-readonly-mcp.git
cd bq-readonly-mcp
uv run bq-readonly-mcp --project your-project-id --location US
```

For a full walkthrough (five steps from zero), see **[docs/QUICKSTART.md](docs/QUICKSTART.md)**.

---

## 🔐 Authentication

The server uses [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials). Run this once:

```bash
gcloud auth application-default login
```

For non-interactive environments (CI, containers, service accounts), pass a key file:

```bash
bq-readonly-mcp --project your-project-id --key-file /path/to/service-account.json
```

Or set `GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json`.

---

## 🔌 Plug it into your editor

Full walkthroughs for each client — config file paths, JSON snippets, restart steps — are in **[docs/EDITOR_SETUP.md](docs/EDITOR_SETUP.md)**.

Covered clients: Claude Code, Claude Desktop, Cursor, Windsurf, GitHub Copilot (VS Code), Cline, Continue.dev, Zed, Gemini CLI.

**Claude Code — quick example:**

```bash
claude mcp add --transport stdio bq-readonly -- \
  uvx bq-readonly-mcp --project your-project-id --location US
```

Or add to `~/.claude.json` (global) or `.mcp.json` (project-level):

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

Ready-to-paste configs for all supported clients are in [`mcp-config-examples/`](mcp-config-examples/).

---

## ⚙️ Configuration reference

All flags can also be set via environment variables. CLI flags take precedence over env vars; env vars take precedence over defaults.

| CLI flag | Env var | Default | Description |
|---|---|---|---|
| `--project` | `GCP_PROJECT_ID` | _(required)_ | GCP project to query |
| `--location` | `BIGQUERY_LOCATION` | `US` | BigQuery processing location |
| `--datasets` | `BIGQUERY_ALLOWED_DATASETS` | _(none — all allowed)_ | Space-separated dataset allowlist; comma-separated in env var |
| `--default-limit` | `BIGQUERY_DEFAULT_LIMIT` | `50` | Rows injected by auto-LIMIT |
| `--max-limit` | `BIGQUERY_MAX_LIMIT` | `10000` | Hard cap on per-query LIMIT |
| `--max-bytes-billed` | `BIGQUERY_MAX_BYTES_BILLED` | `1073741824` (1 GB) | Per-query bytes-billed cap |
| `--sample-rows` | `BIGQUERY_SAMPLE_ROWS` | `3` | Rows returned by `get_table` preview |
| `--key-file` | `GOOGLE_APPLICATION_CREDENTIALS` | _(uses ADC)_ | Path to service-account JSON |

---

## 🛡️ Safety model

1. **SELECT/WITH only** — The SQL validator strips comments, then rejects any statement that doesn't start with `SELECT` or `WITH`, or that contains DML/DDL keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `MERGE`, …).
2. **Auto-LIMIT** — `LIMIT N` is injected if absent. The caller can raise it up to `--max-limit` (default 10,000).
3. **Dry-run cost guard** — Every `run_query` call first runs a dry-run to estimate cost. Queries exceeding `--max-bytes-billed` are refused before any bytes are billed.
4. **Dataset allowlist** — Optional `--datasets` flag restricts access to named datasets. A startup warning is logged when unset.
5. **Defense in depth** — `maximumBytesBilled` is also set on the real job as a server-side backstop.

Full details and threat model → [SECURITY.md](SECURITY.md)

---

## 🚫 What it does NOT do

- Write operations of any kind (INSERT, UPDATE, DELETE, DDL) — by design, forever
- Vector / embedding search — deferred to a future release
- Multi-project queries — one server, one GCP project
- Job history / audit log access — privacy footgun, intentionally omitted
- Storage API (export, streaming reads)

These are intentional omissions. v0.1 focuses on safe, read-only schema exploration and SQL queries.

---

## 🤔 vs other BigQuery MCPs

| Feature | bq-readonly-mcp | pvoo/bigquery-mcp ecosystem |
|---|---|---|
| Read-only enforced | ✅ validator + zero write tools | Varies by fork |
| Dry-run cost guard | ✅ refuses over-budget queries | Not standard |
| Auto-LIMIT injection | ✅ default 50, cap 10,000 | Not standard |
| Dataset allowlist | ✅ optional `--datasets` | Not standard |
| ADC auth | ✅ | ✅ |
| Vector / embedding search | No (v0.1) | Some forks |
| PyPI package | ✅ `bq-readonly-mcp` | Varies |

---

## 💻 Development

```bash
# Install with dev deps
uv sync --extra dev

# Run unit tests (fast, no BigQuery required)
uv run pytest tests/unit/ -q

# Run integration tests (requires ADC + BigQuery access)
uv run pytest -m integration -q

# Lint
uv run ruff check src tests

# Type check
uv run mypy src
```

---

## 📜 License

MIT — see [LICENSE](LICENSE)
