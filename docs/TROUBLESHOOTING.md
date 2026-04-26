# Troubleshooting

Common errors and how to fix them.

---

## `DefaultCredentialsError` / "could not find default credentials"

**Cause:** Application Default Credentials are missing or expired.

**Fix:**

```bash
gcloud auth application-default login
```

After logging in, restart the MCP server (restart your editor or reload its MCP config).

---

## "permission denied" on a dataset or table

**Cause:** Your Google account doesn't have `roles/bigquery.dataViewer` (or equivalent) on the dataset or project.

**Fix:**

1. Ask your GCP project administrator to grant you `roles/bigquery.dataViewer` on the dataset or project.
2. If you are the administrator, grant access via the Cloud Console or:

```bash
gcloud projects add-iam-policy-binding your-project-id \
  --member="user:you@example.com" \
  --role="roles/bigquery.dataViewer"
```

3. Wait up to 60 seconds for IAM propagation, then retry.

---

## "exceeds bytes-billed cap" / `CostExceededError`

**Cause:** The query's estimated cost exceeds the configured `--max-bytes-billed` limit (default 1 GB).

**Fix — option A: narrow the query**

Add a `WHERE` clause, partition filter, or smaller `LIMIT` to reduce scanned data.

**Fix — option B: raise the cap**

Restart the server with a higher cap (5 GB example):

```bash
uvx bq-readonly-mcp --project your-project-id --max-bytes-billed 5368709120
```

Or set the env var:

```bash
export BIGQUERY_MAX_BYTES_BILLED=5368709120
```

---

## "no such dataset" / `DatasetNotAllowedError`

**Cause:** You started the server with `--datasets`, and the requested dataset is not in the allowlist.

**Fix:** Add the dataset to the `--datasets` list, or remove `--datasets` to allow all datasets.

```json
"args": [
  "bq-readonly-mcp",
  "--project", "your-project-id",
  "--datasets", "sales", "marketing", "the_new_dataset"
]
```

---

## ADC scope issues (tables backed by Google Drive sheets)

**Cause:** Some BigQuery tables are backed by Google Drive files (external tables). Querying them requires Drive read scope, which the standard ADC login does not include.

**Fix:** Re-authenticate with Drive scope:

```bash
gcloud auth application-default login --enable-gdrive-access
```

Restart the server after re-authenticating.

---

## Server starts but the editor shows "no tools available"

**Cause:** The MCP client may not have reloaded its config, or there is a path/command issue.

**Checklist:**

1. Verify the server binary is accessible: `uvx bq-readonly-mcp --help`
2. Confirm `--project` is set correctly.
3. Check editor logs for errors (e.g., in Cursor: **Output > MCP**).
4. Restart the editor fully (not just reload window) as a last resort.

---

## Slow first query / cold start

**Cause:** `uvx` downloads the package on first use. Subsequent runs use the cached version.

**Fix:** Run `uvx bq-readonly-mcp --help` once manually to pre-warm the cache.
