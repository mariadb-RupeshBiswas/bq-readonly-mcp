# 🔌 Editor Setup

Step-by-step instructions for connecting `bq-readonly-mcp` to nine popular
MCP clients. Replace `your-project-id` with your actual GCP project ID throughout.

**Sections:** Claude Code · Claude Desktop · Cursor · Windsurf · GitHub Copilot (VS Code) · Cline · Continue.dev · Zed · Gemini CLI

---

## 🤖 Claude Code

Anthropic's official coding assistant for the terminal. The fastest way to
add the server is the `claude mcp add` command.

**Config file location:**
- All platforms: `~/.claude.json` (global) or `.mcp.json` in your project root (project-level)

**Steps:**

1. Run this one-liner to register the server globally:

   ```bash
   claude mcp add --transport stdio bq-readonly -- \
     uvx bq-readonly-mcp --project your-project-id --location US
   ```

2. Or manually edit `~/.claude.json`:

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

3. Reload with `/mcp` in the Claude Code REPL, or restart Claude Code.

4. ✅ Verify: `List all datasets in my BigQuery project.`

💡 **Project-level config:** Drop a `.mcp.json` in your repo root with the
same `mcpServers` shape. Claude Code picks it up automatically when you open
that directory, giving teammates the same server without touching their global config.

---

## 🖥️ Claude Desktop

The Claude desktop application for macOS and Windows. Supports MCP via a
JSON config file.

**Config file location:**
- 🍎 macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- 🪟 Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Steps:**

1. Open the config file (create it if it does not exist).

2. Paste this config:

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

3. Replace `your-project-id` with your GCP project ID.

4. Quit and relaunch Claude Desktop.

5. ✅ Verify: Ask Claude "List all datasets in my BigQuery project." — you
   should see datasets returned from BigQuery.

---

## ✏️ Cursor

A popular AI code editor with native MCP support.

**Config file location:**
- All platforms: `~/.cursor/mcp.json`

**Steps:**

1. Open (or create) `~/.cursor/mcp.json`.

2. Paste this config:

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

3. Replace `your-project-id` with your GCP project ID.

4. Open the Command Palette and run **Cursor: Reload Window**.

5. ✅ Verify by opening Cursor Chat and asking: `List my BigQuery datasets.`

---

## 🌊 Windsurf

Codeium's AI coding environment. Reads MCP config from a dedicated file.

**Config file location:**
- All platforms: `~/.codeium/windsurf/mcp_config.json`

**Steps:**

1. Open (or create) `~/.codeium/windsurf/mcp_config.json`.

2. Paste this config:

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

3. Replace `your-project-id` with your GCP project ID.

4. Open the Command Palette and run **Windsurf: Reload MCP Config**, or
   restart Windsurf.

5. ✅ Verify by asking Cascade: `List my BigQuery datasets.`

---

## 🐙 GitHub Copilot in VS Code

GitHub Copilot in VS Code supports MCP servers via a `mcp.json` config file.
Note the config key is `servers` (not `mcpServers`) and requires a `type` field.

**Config file location:**
- All platforms: `~/.vscode/mcp.json` (global, applies to all workspaces)
- Or scoped to a single project: `.vscode/mcp.json` in the project root

**Steps:**

1. Open (or create) `~/.vscode/mcp.json`.

2. Paste this config:

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

3. Replace `your-project-id` with your GCP project ID.

4. Open the Command Palette and run **Developer: Reload Window**.

5. ✅ Verify by opening GitHub Copilot Chat and asking: `List my BigQuery datasets.`

---

## 🧩 Cline

Cline is a VS Code extension for agentic AI coding tasks. It stores MCP
settings in a JSON file inside VS Code's extension storage folder.

**Config file location:**

The file lives in VS Code's extension storage. The folder name is the Cline
extension's VS Code marketplace ID (publisher dot name):

- 🍎 macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude‑dev/settings/cline_mcp_settings.json`
- 🪟 Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude‑dev\settings\cline_mcp_settings.json`
- 🐧 Linux: `~/.config/Code/User/globalStorage/saoudrizwan.claude‑dev/settings/cline_mcp_settings.json`

> ⚠️ The hyphen in `claude‑dev` above uses a Unicode non‑ASCII hyphen for display.
> Type a regular ASCII hyphen when navigating to this path in a terminal or file manager.

**Steps:**

1. Open the config file (create it if it does not exist).

2. Paste this config:

   ```json
   {
     "mcpServers": {
       "bq-readonly": {
         "command": "uvx",
         "args": [
           "bq-readonly-mcp",
           "--project", "your-project-id",
           "--location", "US"
         ],
         "disabled": false,
         "autoApprove": []
       }
     }
   }
   ```

3. Replace `your-project-id` with your GCP project ID.

4. Open Cline in VS Code and click the **MCP Servers** icon to reload
   servers, or restart VS Code.

5. ✅ Verify by asking Cline: `List my BigQuery datasets.`

---

## 🔄 Continue.dev

Continue.dev is an AI coding assistant for VS Code and JetBrains.
MCP servers are configured in `~/.continue/config.json`.

**Config file location:**
- All platforms: `~/.continue/config.json`

**Steps:**

1. Open `~/.continue/config.json` (create it if it does not exist).

2. Add the `mcpServers` block at the top level:

   ```json
   {
     "mcpServers": [
       {
         "name": "bq-readonly",
         "command": "uvx",
         "args": [
           "bq-readonly-mcp",
           "--project", "your-project-id",
           "--location", "US"
         ]
       }
     ]
   }
   ```

3. Replace `your-project-id` with your GCP project ID.

4. Reload the Continue extension (Command Palette → **Continue: Reload Config**),
   or restart VS Code / your JetBrains IDE.

5. ✅ Verify by asking Continue: `List my BigQuery datasets.`

---

## ⚡ Zed

Zed is a fast, GPU-accelerated code editor with native AI features. MCP
servers are configured in Zed's settings file under the `context_servers` key.

**Config file location:**
- 🍎 macOS: `~/.config/zed/settings.json`
- 🐧 Linux: `~/.config/zed/settings.json`
- 🪟 Windows: `%APPDATA%\Zed\settings.json`

**Steps:**

1. Open Zed settings (`Cmd+,` on macOS or via **Zed: Open Settings**).

2. Add the `context_servers` block:

   ```json
   {
     "context_servers": {
       "bq-readonly": {
         "command": {
           "path": "uvx",
           "args": [
             "bq-readonly-mcp",
             "--project", "your-project-id",
             "--location", "US"
           ]
         },
         "settings": {}
       }
     }
   }
   ```

3. Replace `your-project-id` with your GCP project ID.

4. Save the file. Zed picks up the change without a full restart.

5. ✅ Verify by opening the Zed assistant panel and asking: `List my BigQuery datasets.`

---

## 💎 Gemini CLI (Google)

Google's Gemini CLI is an AI assistant for the terminal that added MCP server
support in 2025. Servers are configured in a JSON settings file.

**Config file location:**
- All platforms: `~/.gemini/settings.json`

**Steps:**

1. Open (or create) `~/.gemini/settings.json`.

2. Paste this config:

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

3. Replace `your-project-id` with your GCP project ID.

4. Restart the Gemini CLI session.

5. ✅ Verify by asking: `List my BigQuery datasets.`

---

## 💡 Tips

### Lock down access with `--datasets`

Add `--datasets` to any config to restrict the server to specific datasets.
This reduces the surface area visible to the LLM and is recommended for
production or sensitive projects:

```json
"args": [
  "bq-readonly-mcp",
  "--project", "your-project-id",
  "--location", "US",
  "--datasets", "your_dataset", "another_dataset"
]
```

The server will refuse to list or query any dataset not in this list.

### Raise the cost cap for large tables

The default bytes-billed cap is 1 GB per query. Raise it when working with
large tables:

```json
"args": [
  "bq-readonly-mcp",
  "--project", "your-project-id",
  "--max-bytes-billed", "5368709120"
]
```

`5368709120` = 5 GB. Adjust to suit your workload.

### Use environment variables instead of args

You can pass all settings via env vars instead of `args`:

```json
{
  "mcpServers": {
    "bq-readonly": {
      "command": "uvx",
      "args": ["bq-readonly-mcp"],
      "env": {
        "GCP_PROJECT_ID": "your-project-id",
        "BIGQUERY_LOCATION": "US",
        "BIGQUERY_ALLOWED_DATASETS": "your_dataset,another_dataset",
        "BIGQUERY_MAX_BYTES_BILLED": "5368709120"
      }
    }
  }
}
```

This keeps the `args` array short and makes it easy to use different projects
in different environments.

### Project-level config for Claude Code

Drop a `.mcp.json` file in a project's root directory to give all contributors
the same server without touching their global `~/.claude.json`:

**.mcp.json:**
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

Claude Code automatically merges project-level and global servers.

---

## 🔍 Troubleshooting

See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for common errors and fixes.
