# bq-readonly-mcp

Read-only BigQuery MCP server with auto-LIMIT, dry-run cost guard, and ADC auth — for Claude, Cursor, Windsurf, Copilot, and other MCP clients.

## Installation

```bash
uvx bq-readonly-mcp --project your-project-id
```

## Configuration

Set `GCP_PROJECT_ID` or pass `--project your-project-id`.

## License

MIT
