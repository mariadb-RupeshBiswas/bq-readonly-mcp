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
