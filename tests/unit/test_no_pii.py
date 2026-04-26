"""Public-repo hygiene: positive allowlist scan for project-ID-shaped strings.

Walks every tracked file under the repo root and extracts any token matching
the GCP project ID regex. Asserts each match is in the ALLOWED set or the
EXTRA_FALSE_POSITIVES filter.

Any other project-ID-shaped string fails the test, signaling a potential leak.
"""

import re
import subprocess
from pathlib import Path

# Full GCP project-ID shape: lowercase letters, digits, hyphens, 6-30 chars total.
# We only flag tokens that contain at least one hyphen or digit, because pure
# lowercase words are ubiquitous English text; the risk of a real project ID leak
# is almost always a *hyphenated* or alphanumeric slug like `my-company-prod`.
PROJECT_ID_RE = re.compile(r"\b[a-z][a-z0-9-]{4,28}[a-z0-9]\b")
_HAS_HYPHEN_OR_DIGIT = re.compile(r"[-0-9]")

# Known-good tokens: placeholders, public-data projects, and tooling strings
# that happen to match the project-ID regex shape.
ALLOWED = {
    # Explicit placeholders
    "your-project-id",
    "your-project",
    # Literal regex character-class notation used in documentation
    "a-z0-9",
    # Google auth library module name (contains digit, matches the regex)
    "oauth2",
    # Google public-data projects
    "bigquery-public-data",
    "cloud-samples-data",
    "bigquery-samples",
    # Python/tooling package names
    "google-cloud-bigquery",
    "google-auth-httplib2",
    "google-api-python-client",
    "google-cloud-sdk",
    "google-cloud",
    "google-auth",
    "google-sheets",
    "pytest-asyncio",
    "pytest-mock",
    "types-requests",
    # pyproject / config keys
    "python-version",
    "license-files",
    "requires-python",
    "build-backend",
    "build-system",
    "target-version",
    "line-length",
    "optional-dependencies",
    "asyncio-default-fixture-loop",
    "ignore-missing-imports",
    "cov-report",
    # BigQuery / GCP-specific config strings
    "use-query-cache",
    "set-quota-project",
    "max-bytes-billed",
    "default-limit",
    "max-limit",
    "sample-rows",
    "key-file",
    "no-dryrun-guard",
    # CI / workflow strings
    "ubuntu-latest",
    "runs-on",
    "setup-python",
    "setup-uv",
    "enable-gdrive-access",
    # Superpowers skill names (appear in plan docs)
    "test-driven-development",
    "verify-code-against-the-plan",
    "code-review-against-the-plan",
    "subagent-driven-development",
    "executing-plans",
    # Plan/doc narrative tokens
    "application-default",
    "service-account",
    "service-account-key",
    "dry-run",
    "branch-protection",
    "end-to-end",
    "read-only",
    "non-trivial",
    "non-strict",
    "non-interactive",
    "non-obvious",
    "non-zero",
    "non-comment",
    "non-goals",
    "multi-statement",
    "multi-line",
    "multi-paragraph",
    "multi-project",
    "high-stakes",
    "highest-stakes",
    "copy-paste",
    "defense-in-depth",
    "human-readable",
    "word-boundary",
    "top-level",
    "table-level",
    "table-metadata",
    "table-reference",
    "column-schema",
    "positive-allowlist",
    "false-positive",
    "project-bound",
    "project-id-shaped",
    "project-level",
    "project-wide",
    "public-data",
    "public-repo",
    "ready-to-paste",
    "on-demand",
    "billing-authoritative",
    "bytes-billed",
    "cost-runaway",
    "string-literal",
    "double-quoted",
    "single-quoted",
    "backtick-quoted",
    "doubled-quote",
    "doubled-quote-escape",
    "backslash-escape",
    "comment-stripped",
    "comment-hidden",
    "anchor-match",
    "trailing-anchor",
    "semicolon-trimmed",
    "whitespace-only",
    "code-bearing",
    "plain-dict",
    "allowlist-aware",
    "unit-testable",
    "unit-tested",
    "up-to-date",
    "self-explanatory",
    "judgment-based",
    "well-named",
    "one-line",
    "one-liner",
    "per-editor",
    "local-only",
    "server-side",
    "server-level",
    "server-configured",
    "self-audit",
    "re-audit",
    "re-run",
    "re-auth",
    "re-publish",
    "re-enforces",
    "new-version",
    "follow-ups",
    "post-plan",
    "force-push",
    "shell-out",
    "pattern-match",
    "type-check",
    "over-permissioning",
    "prompt-injection-via-error-log",
    "case-insensitive",
    "case-insensitively",
    "comma-separated",
    "end-of-line",
    "end-of-string",
    "outside-string",
    "trade-off",
    "ad-hoc",
    "at-a-glance",
    "always-safe",
    "task-by-task",
    "sub-calls",
    "sister-project",
    "term-missing",
    "double-injection",
    "uv-cache",
    "egg-info",
    "single-process",
    "ls-files",
    "bigquery-mcp",
    "mcp-config-examples",
    "python-stdlib-ish",
    "english-word",
    "screenshots-replace",
    "screenshots-replacement",
    "company-specific",
    "astral-sh",
    "asia-northeast1",
    "model-context-protocol",
    # Test fixture project names (used only inside test functions, no leakage)
    "adc-detected-proj",
    "cli-proj",
    "env-proj",
    "my-proj",
    # Misc doc/narrative
    "re-inject",
    "code-reviewer",
    "tab--name",
}

# Tokens excluded from scanning by file prefix
EXCLUDE_PREFIXES = (
    ".git/",
    "dist/",
    ".venv/",
    "build/",
    "__pycache__/",
    ".ruff_cache/",
    ".mypy_cache/",
    ".pytest_cache/",
)
TEXT_EXTS = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".cfg", ".ini", ".txt"}

# Tokens that clearly match the regex shape but are obviously not GCP project IDs —
# these appear in narrative text, tool names, or package names in the repo.
EXTRA_FALSE_POSITIVES = {
    "anthropic-ai",
    "claude-code",
    "claude-desktop",
    "google-sheets-mcp",
    "g-sheet-mcp",
    "bq-readonly-mcp",
    "bq-readonly-mcp-design",
    "bq-readonly",
    "model-context-protocol",
    "modelcontextprotocol",
    "google-sheets",
    "enable-gdrive-access",
}


def _tracked_files(repo_root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
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
            # Pure alphabetic tokens are ordinary English words, not project IDs
            if not _HAS_HYPHEN_OR_DIGIT.search(match):
                continue
            if match in ALLOWED:
                continue
            if match in EXTRA_FALSE_POSITIVES:
                continue
            bad.setdefault(match, []).append(rel)

    # Fail loudly if any unrecognized project-ID-shaped token is found.
    # To fix: either add the token to ALLOWED (if safe) or scrub the source.
    assert not bad, (
        "Possible PII/internal-data leak: project-ID-shaped tokens found in tracked files. "
        "Add to ALLOWED in this test if they're legitimate, or scrub them: "
        + ", ".join(sorted(bad))
    )
