# 🚀 Quick Start

Get from zero to a working BigQuery MCP server in five steps.

---

## 📦 Step 1 — Install the Google Cloud SDK

If you don't have `gcloud` yet:

```bash
# macOS (Homebrew)
brew install google-cloud-sdk

# Linux / WSL
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
tar -xf google-cloud-cli-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh
```

Or follow the official guide: <https://cloud.google.com/sdk/docs/install>

Verify the install:

```bash
gcloud --version
```

---

## 🔐 Step 2 — Authenticate with Application Default Credentials

```bash
gcloud auth application-default login
```

This opens a browser window. After you approve, credentials are written to
`~/.config/gcloud/application_default_credentials.json`. The server reads
them automatically on every subsequent run — you only need to do this once
(or when the token expires).

💡 **Tip:** If you need access to Google Drive-backed tables (external tables), use:

```bash
gcloud auth application-default login --enable-gdrive-access
```

---

## 🛠️ Step 3 — Install `bq-readonly-mcp`

The recommended approach uses `uvx` — no separate install step needed, it
fetches the package on demand:

```bash
# Verify it works before wiring it into your editor
uvx bq-readonly-mcp --project your-project-id --location US --help
```

You should see the CLI help output. That means the package downloaded and
ADC is accessible.

If you prefer a persistent install:

```bash
uv tool install bq-readonly-mcp
```

Or install it into a specific virtual environment:

```bash
pip install bq-readonly-mcp
```

---

## 🔌 Step 4 — Add the server to your MCP client

Pick your editor below and add the config. Replace `your-project-id` with
your actual GCP project ID.

**Claude Code (CLI) — one-liner:**

```bash
claude mcp add --transport stdio bq-readonly -- \
  uvx bq-readonly-mcp --project your-project-id --location US
```

**Claude Code — manual config (`~/.claude.json`):**

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

**Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):**

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

**Cursor (`~/.cursor/mcp.json`)**, **Windsurf (`~/.codeium/windsurf/mcp_config.json`)**: same `mcpServers` shape as above.

**GitHub Copilot in VS Code (`~/.vscode/mcp.json`):**

```json
{
  "servers": {
    "bq-readonly": {
      "type": "stdio",
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

For complete instructions for all supported editors, see **[EDITOR_SETUP.md](EDITOR_SETUP.md)**.
Ready-to-paste JSON files are in [`../mcp-config-examples/`](../mcp-config-examples/).

---

## ▶️ Step 5 — Restart your editor and verify

Restart the editor (or reload its MCP config). Then open a chat and ask:

```
List all datasets in my BigQuery project.
```

If the server is connected, the AI calls `list_datasets` and returns the
dataset names from your project.

You can also try with Google's public data to avoid needing your own project:

```
List the tables in bigquery-public-data.samples
```

---

## 🎉 You're done!

The server is running. Here are a few things to try next:

```
# Explore a dataset
List the tables in your_dataset

# Understand a table
Describe the columns in your_dataset.your_table

# Check query cost before running
How much would it cost to run: SELECT * FROM your_dataset.your_table?

# Run a safe, bounded query
SELECT name, age FROM your_dataset.users WHERE active = true LIMIT 20
```

💡 **Tip:** To lock down access to specific datasets and reduce surface area,
add `--datasets` to your config:

```json
"args": [
  "bq-readonly-mcp",
  "--project", "your-project-id",
  "--datasets", "your_dataset", "another_dataset"
]
```

---

## 🔍 Troubleshooting

If something doesn't work, see **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**.

The most common issue is missing ADC credentials — re-run Step 2. The
second most common is a `uvx` cold start: run
`uvx bq-readonly-mcp --help` once to pre-warm the package cache.
