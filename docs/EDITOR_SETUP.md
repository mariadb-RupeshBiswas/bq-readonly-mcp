# Editor Setup

Step-by-step instructions for connecting `bq-readonly-mcp` to five MCP clients.

Replace `your-project-id` with your actual GCP project ID throughout.

---

## Claude Code (CLI)

**Config file:** `~/.claude/mcp_config.json`

Add via the CLI:

```bash
claude mcp add --transport stdio bq-readonly -- \
  uvx bq-readonly-mcp --project your-project-id --location US
```

Or edit `~/.claude/mcp_config.json` directly:

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

Reload with `/mcp` in the Claude Code REPL, or restart Claude Code.

---

## Claude Desktop

**Config file (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Config file (Windows):** `%APPDATA%\Claude\claude_desktop_config.json`

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

Quit and relaunch Claude Desktop for the change to take effect.

---

## Cursor

**Config file:** `~/.cursor/mcp.json`

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

Open the Command Palette and run **Cursor: Reload Window** to pick up the change.

---

## Windsurf

**Config file:** `~/.codeium/windsurf/mcp_config.json`

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

Reload via **Windsurf: Reload MCP Config** in the Command Palette, or restart Windsurf.

---

## VS Code + GitHub Copilot

**Config file:** `~/.vscode/mcp.json`

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

Open the Command Palette and run **Developer: Reload Window**.

---

## Optional: restrict to specific datasets

Add `--datasets` to any config to limit the server to named datasets:

```json
"args": [
  "bq-readonly-mcp",
  "--project", "your-project-id",
  "--location", "US",
  "--datasets", "your_dataset", "another_dataset"
]
```

---

## Optional: increase cost cap

The default bytes-billed cap is 1 GB per query. Raise it if needed:

```json
"args": [
  "bq-readonly-mcp",
  "--project", "your-project-id",
  "--max-bytes-billed", "5368709120"
]
```

(5 GB = 5 × 1024³ bytes)

---

## Troubleshooting

See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for common errors and fixes.
