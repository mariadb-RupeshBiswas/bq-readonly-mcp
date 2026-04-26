"""SQL safety: comment stripping, validator, LIMIT injection.

This module is the highest-stakes part of the codebase. It must reject all
non-SELECT/WITH queries before they touch the BigQuery client. Tests live in
tests/unit/test_safety_*.py and are exhaustive on purpose.
"""

from __future__ import annotations

import re


def strip_comments(sql: str) -> str:
    """Remove SQL line and block comments while preserving string literals.

    Walks character by character, tracking whether we're inside a single- or
    double-quoted string (with doubled-quote escape support). Outside strings,
    `--` runs to end-of-line and `/* ... */` is replaced with a single space.
    """
    out: list[str] = []
    i = 0
    n = len(sql)
    in_single = False
    in_double = False

    while i < n:
        c = sql[i]

        # Inside a single-quoted string: pass through, watch for closer or doubled-quote escape
        if in_single:
            out.append(c)
            if c == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_single = False
            i += 1
            continue

        # Inside a double-quoted string: same logic mirrored
        if in_double:
            out.append(c)
            if c == '"':
                if i + 1 < n and sql[i + 1] == '"':
                    out.append('"')
                    i += 2
                    continue
                in_double = False
            i += 1
            continue

        # Outside any string: detect string openers, line comments, block comments
        if c == "'":
            in_single = True
            out.append(c)
            i += 1
            continue
        if c == '"':
            in_double = True
            out.append(c)
            i += 1
            continue
        if c == "-" and i + 1 < n and sql[i + 1] == "-":
            # Line comment: consume until newline (newline itself is dropped here, but the
            # next non-comment iteration will preserve newlines naturally)
            while i < n and sql[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and sql[i + 1] == "*":
            # Block comment: skip past closing */; no replacement space needed because
            # surrounding whitespace in the original SQL provides separation
            i += 2
            while i + 1 < n and not (sql[i] == "*" and sql[i + 1] == "/"):
                i += 1
            i += 2
            continue

        out.append(c)
        i += 1

    return "".join(out)


def mask_string_literals(sql: str) -> str:
    """Replace contents of single- and double-quoted string literals with `X`.

    Used before keyword scanning so that a value like `'INSERT'` inside a
    string literal does not trigger DML/DDL rejection. Preserves the
    surrounding quote characters and overall length structure.
    """
    out: list[str] = []
    i = 0
    n = len(sql)
    in_single = False
    in_double = False

    while i < n:
        c = sql[i]

        # Inside single-quoted string: replace contents with X, watch for closer/escape
        if in_single:
            if c == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    out.append("X")
                    i += 2
                    continue
                out.append("'")
                in_single = False
                i += 1
                continue
            out.append("X")
            i += 1
            continue

        # Inside double-quoted string: same logic mirrored
        if in_double:
            if c == '"':
                if i + 1 < n and sql[i + 1] == '"':
                    out.append("X")
                    i += 2
                    continue
                out.append('"')
                in_double = False
                i += 1
                continue
            out.append("X")
            i += 1
            continue

        # Outside any string: detect openers and pass through
        if c == "'":
            in_single = True
            out.append(c)
            i += 1
            continue
        if c == '"':
            in_double = True
            out.append(c)
            i += 1
            continue

        out.append(c)
        i += 1

    return "".join(out)


def is_multistatement(sql: str) -> bool:
    """True if the query contains more than one statement.

    Strips comments and masks string literals so semicolons inside strings
    or comments are not counted. A single trailing `;` is allowed.
    """
    stripped = strip_comments(sql)
    masked = mask_string_literals(stripped)
    body = masked.rstrip()
    if body.endswith(";"):
        body = body[:-1].rstrip()
    return ";" in body


# Keywords that signal DML/DDL/permission changes — never allowed in this server
DISALLOWED_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "CREATE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "REPLACE",
    "GRANT",
    "REVOKE",
    "EXPORT",
)

# Word-boundary regex; identifiers like `delete_flag` won't match because of \b
_DISALLOWED_RE = re.compile(
    r"\b(" + "|".join(DISALLOWED_KEYWORDS) + r")\b",
    re.IGNORECASE,
)
_STARTS_WITH_SELECT_OR_WITH_RE = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


class SafetyError(ValueError):
    """Raised when a query fails safety validation."""


def validate_select_query(sql: str) -> None:
    """Validate that `sql` is a single read-only SELECT/WITH query.

    Pipeline (raises SafetyError on first failure):
      1. Reject empty/whitespace-only.
      2. Strip comments.
      3. Reject if multi-statement.
      4. Reject if not starting with SELECT or WITH.
      5. Mask string literals, then reject if any DML/DDL keyword appears
         as a top-level token.
    """
    if not sql or not sql.strip():
        raise SafetyError("query is empty")

    stripped = strip_comments(sql)

    if is_multistatement(sql):
        raise SafetyError("multi-statement queries are not allowed")

    if not _STARTS_WITH_SELECT_OR_WITH_RE.match(stripped):
        raise SafetyError("only SELECT or WITH queries are allowed (non-SELECT detected)")

    # Mask string contents so a DML keyword inside a literal does not trigger
    masked = mask_string_literals(stripped)
    match = _DISALLOWED_RE.search(masked)
    if match:
        raise SafetyError(f"disallowed DML/DDL keyword detected: {match.group(1).upper()}")


# Trailing-anchor LIMIT regex: matches `LIMIT N [OFFSET M]` only at end-of-string,
# so LIMIT clauses inside subqueries do not register as outer LIMITs
_TRAILING_LIMIT_RE = re.compile(
    r"\bLIMIT\s+\d+(\s+OFFSET\s+\d+)?\s*;?\s*$",
    re.IGNORECASE,
)


def has_outer_limit(sql: str) -> bool:
    """True if the outermost query already has a LIMIT clause.

    Heuristic: strip comments, mask string literals, drop optional trailing
    semicolon, then anchor-match `LIMIT N [OFFSET M]` at end-of-string.
    LIMIT clauses inside subqueries do not match because the regex is
    anchored at $ on the cleaned, semicolon-trimmed body.
    """
    cleaned = mask_string_literals(strip_comments(sql)).rstrip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].rstrip()
    return bool(_TRAILING_LIMIT_RE.search(cleaned))


def inject_limit(sql: str, limit: int) -> str:
    """Append `LIMIT <limit>` to the outermost query if no outer LIMIT exists.

    Strips an optional trailing semicolon before appending. Raises ValueError
    if `limit` is not positive.
    """
    if limit <= 0:
        raise ValueError(f"limit must be positive, got {limit}")
    if has_outer_limit(sql):
        return sql
    body = sql.rstrip()
    if body.endswith(";"):
        body = body[:-1].rstrip()
    return f"{body} LIMIT {limit}"
