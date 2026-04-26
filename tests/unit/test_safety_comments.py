"""Tests for SQL comment stripping that respects string literals."""

from bq_readonly_mcp.safety import strip_comments


def test_strips_line_comment():
    assert strip_comments("SELECT 1 -- comment").strip() == "SELECT 1"


def test_strips_multiple_line_comments():
    sql = "SELECT 1\n-- a\nFROM t -- b"
    assert strip_comments(sql).strip().split("\n") == ["SELECT 1", "", "FROM t"]


def test_strips_block_comment():
    assert strip_comments("SELECT /* hello */ 1").strip() == "SELECT  1"


def test_strips_multiline_block_comment():
    sql = "SELECT /*\nthis is\na comment\n*/ 1"
    assert strip_comments(sql).strip() == "SELECT  1"


def test_does_not_strip_inside_single_quoted_string():
    assert strip_comments("SELECT '-- not a comment'") == "SELECT '-- not a comment'"


def test_does_not_strip_inside_double_quoted_string():
    assert strip_comments('SELECT "/* not a comment */"') == 'SELECT "/* not a comment */"'


def test_handles_doubled_quote_escape():
    sql = "SELECT 'it''s -- not a comment'"
    assert strip_comments(sql) == sql


def test_empty_string_returns_empty():
    assert strip_comments("") == ""
