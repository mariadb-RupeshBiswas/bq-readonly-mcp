# Security Policy

## Read-only model

`bq-readonly-mcp` is designed to be safe by construction:

- It exposes **zero write tools**. There are no INSERT, UPDATE, DELETE, DDL, or storage-write operations anywhere in the codebase.
- The SQL validator rejects any statement that is not `SELECT` or `WITH` — after stripping comments that could hide dangerous keywords.
- All code paths that touch BigQuery are wrapped in the `BQClient` class, which enforces the dataset allowlist before every operation.

## ADC posture

Authentication uses [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials).

- No credentials are stored or transmitted by this server.
- The ADC file (`~/.config/gcloud/application_default_credentials.json`) is owned by the user's `gcloud` install with OS-level file permissions.
- An optional `--key-file` path (or `GOOGLE_APPLICATION_CREDENTIALS`) can point to a service-account JSON file for non-interactive use. Never commit that file.

## Threat model

Threats explicitly mitigated:

| Threat | Mitigation |
|---|---|
| LLM tries to run DML/DDL | SQL validator rejects everything except `SELECT` and `WITH` after comment stripping |
| Prompt injection causes a cost-runaway query | Pre-flight dry-run estimates `totalBytesProcessed`; query refused if over `--max-bytes-billed` (default 1 GB). The job itself also enforces the cap server-side. |
| LLM dumps a huge result into context | Auto-`LIMIT 50` injected on every query unless the caller explicitly overrides; maximum overridable limit 10,000 |
| SQL with comments hiding dangerous statements | Comments stripped before validation; multi-statement queries rejected |
| LLM accesses sensitive datasets | Optional `--datasets` allowlist restricts which datasets the server will surface or query |
| Credential theft | No credentials stored or transmitted by this server; ADC is owned by `gcloud` with OS-level file permissions |
| Supply-chain dependency CVEs | Pinned versions in `pyproject.toml`, committed `uv.lock`, Dependabot alerts on the public GitHub repo |

Threats **not** mitigated (out of scope, user responsibility):

- Compromise of the user's local machine (the process runs as the user and inherits their ADC tokens).
- IAM over-permissioning at the GCP level — this server restricts what its tools can do, not what the user's identity can do in GCP.
- The LLM exfiltrating data the user has legitimate access to (inherent trade-off of giving an LLM tool use over BigQuery).

## Public-repo hygiene

This is a public repository. The following rules apply to all tracked files:

- No real GCP project IDs (only `your-project-id`, `your-project`, or `bigquery-public-data.*`).
- No customer names, employee names, or internal product names.
- No internal hostnames, Slack channels, or Jira/Confluence URLs.
- No real service-account JSON files or credential paths.

Two strings are allowed to contain "mariadb":
1. The author's email (`rupesh.biswas@mariadb.com`)
2. The GitHub repository URL (`github.com/mariadb-RupeshBiswas/bq-readonly-mcp`)

The automated hygiene gate is `tests/unit/test_no_pii.py`, which scans every tracked file for project-ID-shaped tokens not in the allowlist.

## Reporting a vulnerability

If you discover a security vulnerability, please open a **private** GitHub security advisory:

1. Go to the repository on GitHub.
2. Click **Security** → **Advisories** → **New draft security advisory**.
3. Fill in the details and submit.

Do **not** open a public issue for security vulnerabilities.

If private advisories are unavailable, email the maintainer via the address in `pyproject.toml`.

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x (current) | Yes |

## Best practices for users

- Treat `~/.config/gcloud/application_default_credentials.json` as a secret.
- Run `gcloud auth revoke` when you no longer need the server.
- Use a dedicated service account with `roles/bigquery.dataViewer` in CI/CD rather than personal credentials.
- Scope the service account to the minimum datasets it needs.
- Monitor BigQuery job history in the Cloud Console for unexpected queries.
