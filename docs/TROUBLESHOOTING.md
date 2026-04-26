# 🔍 Troubleshooting

Common symptoms, causes, and fixes. Jump to the section that matches your error.

**Sections:** Auth errors · Cost errors · Permission errors · MCP/connection errors · Drive-backed tables

---

## 🔑 Auth Errors

### `DefaultCredentialsError` / "could not find default credentials"

**Symptom:** The server fails to start, or the first tool call returns an error
mentioning `DefaultCredentialsError` or "could not find default credentials".

**Cause:** Application Default Credentials (ADC) are missing or have not been
initialized on this machine.

**Fix:**

```bash
gcloud auth application-default login
```

This opens a browser, logs you in, and writes credentials to
`~/.config/gcloud/application_default_credentials.json`. After authenticating,
restart your editor (or reload its MCP config) so the server picks up the new
credentials.

---

### Stale / expired ADC token

**Symptom:** The server worked before but now returns auth errors after a period
of inactivity, or after your browser session expired.

**Cause:** ADC tokens have a limited lifetime. The token may have expired.

**Fix:** Re-authenticate:

```bash
gcloud auth application-default login
```

Then restart the MCP server (restart your editor or reload the MCP config).

---

### Service account key rejected

**Symptom:** The server fails when `--key-file` is set, with an error like
"invalid_grant" or "could not deserialize key data".

**Cause:** The service account JSON file is malformed, belongs to the wrong
project, or the key has been revoked.

**Fix:**

1. Verify the key file is valid JSON and was downloaded from the correct GCP project.
2. Check that the service account exists and has not been disabled:
   Open the GCP Console → **IAM & Admin → Service account** and confirm the account is active and not deleted.
3. If the key was revoked, create a new key in the GCP Console under
   **IAM & Admin → Service account → Keys**.

---

## 💸 Cost Errors

### "exceeds bytes-billed cap" / `CostExceededError`

**Symptom:** A `run_query` call returns an error about the query exceeding the
bytes-billed cap.

**Cause:** The query's estimated cost from the dry-run exceeds `--max-bytes-billed`
(default 1 GB = 1,073,741,824 bytes).

**Fix — option A: narrow the query**

Add a `WHERE` clause, partition filter, or a smaller `LIMIT` to reduce the data
scanned. For partitioned tables, include a filter on the partition column:

```sql
SELECT * FROM your_dataset.your_table
WHERE _PARTITIONDATE = '2024-01-01'
LIMIT 100
```

**Fix — option B: raise the cap**

Restart the server with a higher limit (5 GB example):

```bash
uvx bq-readonly-mcp --project your-project-id --max-bytes-billed 5368709120
```

Or set the env var in your editor's MCP config:

```json
"env": {
  "BIGQUERY_MAX_BYTES_BILLED": "5368709120"
}
```

5 GB = 5,368,709,120 bytes. Adjust to suit your workload.

---

## 🔍 Permission Errors

### "permission denied" on a dataset or table

**Symptom:** A tool call returns "permission denied" for a specific dataset
or table.

**Cause:** Your Google account (or service account) does not have
`roles/bigquery.dataViewer` (or equivalent) on the dataset or project.

**Fix:**

1. Ask your GCP project administrator to grant the role:

   ```bash
   gcloud projects add-iam-policy-binding your-project-id \
     --member="user:you@example.com" \
     --role="roles/bigquery.dataViewer"
   ```

   Or grant it at the dataset level in the BigQuery Console.

2. Wait up to 60 seconds for IAM propagation, then retry.

3. Verify your current identity:
   ```bash
   gcloud auth list
   gcloud config get project
   ```

---

### "no such dataset" / `DatasetNotAllowedError`

**Symptom:** The server returns a "dataset not allowed" or "no such dataset" error
even though the dataset exists in BigQuery.

**Cause:** The server was started with `--datasets`, and the requested dataset
is not in the allowlist.

**Fix:** Add the dataset to `--datasets`, or remove `--datasets` to allow all
datasets:

```json
"args": [
  "bq-readonly-mcp",
  "--project", "your-project-id",
  "--datasets", "sales", "marketing", "the_new_dataset"
]
```

---

## 🐛 MCP / Connection Errors

### "tool not found" / server not appearing in the editor

**Symptom:** The AI says it doesn't have BigQuery tools, or the MCP panel shows
no servers connected.

**Checklist:**

1. Verify the command works outside the editor:
   ```bash
   uvx bq-readonly-mcp --project your-project-id --help
   ```
   If this fails, `uvx` is not installed or the package name is wrong.

2. Confirm `--project` is set correctly in the config.

3. Check the editor's MCP logs for the real error message:
   - **Cursor:** Output panel → MCP
   - **Windsurf:** Output panel → Cascade MCP
   - **VS Code (Copilot):** Output panel → GitHub Copilot Chat
   - **Claude Code:** run `claude` with `--verbose`

4. Try restarting the editor fully (not just "Reload Window"), as some editors
   only start MCP servers on a full launch.

5. On macOS, confirm `uvx` is on the PATH used by the editor's process:
   ```bash
   which uvx
   ```
   Some editors launch with a restricted PATH. If needed, use the full path to
   `uvx` in the config (e.g., `/Users/you/.local/bin/uvx`).

---

### Slow first query / cold start delay

**Symptom:** The first tool call takes 10–30 seconds, then subsequent calls are
fast.

**Cause:** `uvx` downloads and extracts the package on first use. Subsequent
runs use the cached version.

**Fix:** Pre-warm the cache by running once manually:

```bash
uvx bq-readonly-mcp --help
```

After that, starts are very fast.

---

### Server starts but returns errors on every query

**Symptom:** The server connects, tools appear, but every `run_query` call
fails with a BigQuery API error.

**Checklist:**

1. The BigQuery API must be enabled in your GCP project:
   ```bash
   gcloud services enable bigquery.googleapis.com --project your-project-id
   ```

2. Confirm the project ID is correct (not a project name — BigQuery uses the
   project ID, which typically looks like a hyphenated slug with digits).

3. Check your quota in the GCP Console under **BigQuery → Quotas**.

---

## 🔗 Drive-backed Table Errors

### "Access denied: BigQuery BigQuery: Drive credentials are required"

**Symptom:** Querying a table returns an error mentioning Drive credentials.

**Cause:** The table is an external BigQuery table backed by a Google Drive
spreadsheet. Querying it requires Drive read scope, which the standard ADC
login does not include.

**Fix:** Re-authenticate with Drive scope:

```bash
gcloud auth application-default login --enable-gdrive-access
```

Restart the MCP server after re-authenticating. You only need to do this once;
the scope persists in your ADC credentials until you revoke or refresh them.

---

## 💡 Still stuck?

Check the BigQuery job history in the GCP Console (**BigQuery → Job history**)
to see whether your query reached BigQuery and what error it returned there.

For bugs or unexpected behavior, open an issue on GitHub:
<https://github.com/mariadb-RupeshBiswas/bq-readonly-mcp/issues>
