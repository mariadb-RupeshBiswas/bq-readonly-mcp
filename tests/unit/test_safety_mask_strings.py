"""Tests for string-literal masking used before keyword scanning."""

from bq_readonly_mcp.safety import mask_string_literals


def test_masks_single_quoted():
    out = mask_string_literals("SELECT 'INSERT INTO bad'")
    assert "INSERT" not in out
    assert out.startswith("SELECT '")


def test_masks_double_quoted():
    out = mask_string_literals('SELECT "DROP TABLE"')
    assert "DROP" not in out
    assert "TABLE" not in out


def test_preserves_outer_structure():
    out = mask_string_literals("SELECT 'foo' FROM t WHERE c = 'bar'")
    assert out.startswith("SELECT '")
    assert " FROM t WHERE c = '" in out


def test_handles_doubled_quote_escape():
    out = mask_string_literals("SELECT 'it''s here'")
    assert out.startswith("SELECT '")
    assert out.endswith("'")


def test_empty_input():
    assert mask_string_literals("") == ""


def test_no_strings_unchanged():
    sql = "SELECT 1 + 2 FROM dataset.table"
    assert mask_string_literals(sql) == sql


def test_masks_backtick_content():
    out = mask_string_literals("SELECT * FROM `proj.ds.UPDATE_LOG`")
    assert "UPDATE" not in out
    assert out.startswith("SELECT * FROM `")
    assert out.endswith("`")


def test_backslash_escape_inside_string_does_not_close_early():
    # 'foo\'bar' is one string; outside-string content begins after the closing quote
    out = mask_string_literals(r"SELECT 'foo\'bar' AS x")
    # Whole literal masked; AS is outside, so it stays
    assert " AS x" in out


def test_raw_string_bypass_blocked():
    # The famous bypass query — must be detected as multi-statement
    out = mask_string_literals(r'SELECT r"foo\"; DROP TABLE t; --" FROM s')
    # The raw string ends at the second " (after foo\), then "; DROP TABLE t; --" is OUTSIDE
    # mask should leave outside content unmasked, so DROP, TABLE, ;, --, etc are visible
    assert "DROP" in out or ";" in out  # at least one keyword leaked outside the raw string
