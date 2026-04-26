# Quick Start

Get from zero to a working BigQuery MCP server in five steps.

---

## Step 1 — Install the Google Cloud SDK

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

Verify:

```bash
gcloud --version
```

---

## Step 2 — Authenticate with Application Default Credentials

```bash
gcloud auth application-default login
```

This opens a browser window. After you approve, credentials are written to
`~/.config/gcloud/application_default_credentials.json`. The server picks
them up automatically on every subsequent run.

---

## Step 3 — Install `bq-readonly-mcp` via uvx

The recommended approach requires no separate install step — `uvx` fetches
the package on demand:

```bash
uvx bq-readonly-mcp --project your-project-id --location US --help
```

You should see the CLI help output. If you prefer a persistent install:

```bash
uv tool install bq-readonly-mcp
```

---

## Step 4 — Configure your MCP client

Add the server to your editor's MCP config. Example for Claude Code:

```bash
claude mcp add --transport stdio bq-readonly -- \
  uvx bq-readonly-mcp --project your-project-id --location US
```

For other editors, see **[EDITOR_SETUP.md](EDITOR_SETUP.md)** or copy a config
from [`../mcp-config-examples/`](../mcp-config-examples/).

---

## Step 5 — Restart your editor and verify

Restart the editor (or reload its MCP config). Then ask the AI:

```
List all datasets in my BigQuery project.
```

If the server is connected, the AI will call `list_datasets` and return
the dataset names.

---

## Troubleshooting

If something doesn't work, see **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**.
The most common issue is missing ADC credentials — re-run Step 2.
