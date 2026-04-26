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


def test_preserves_backtick_identifier():
    sql = "SELECT * FROM `bigquery-public-data.samples.shakespeare`"
    assert strip_comments(sql) == sql


def test_does_not_strip_inside_backtick():
    sql = "SELECT * FROM `tab--name`"
    assert strip_comments(sql) == sql


def test_does_not_strip_block_comment_inside_backtick():
    sql = "SELECT * FROM `tab/*x*/name`"
    assert strip_comments(sql) == sql


def test_handles_backslash_escape_inside_string():
    # 'foo\'bar' is one string with content foo'bar
    sql = r"SELECT 'foo\'bar' AS x"
    out = strip_comments(sql)
    assert out == sql  # comment stripper preserves the whole literal


def test_handles_backslash_escape_inside_double_quoted():
    sql = r'SELECT "foo\"bar" AS x'
    assert strip_comments(sql) == sql


def test_raw_string_does_not_honor_backslash_escape():
    # In a raw string, \" does NOT escape; the second " closes the string
    sql = r'SELECT r"foo\" FROM t'  # second " closes string -> ' FROM t' is outside
    out = strip_comments(sql)
    # The literal stays intact; outside content unchanged
    assert "FROM t" in out


def test_raw_string_lowercase_r():
    sql = r"SELECT r'foo\' FROM t"  # raw single-quoted; \ is literal, ' closes
    assert strip_comments(sql) == sql  # no comments, no change


def test_raw_string_uppercase_R():
    sql = r'SELECT R"hello" FROM t'
    assert strip_comments(sql) == sql
