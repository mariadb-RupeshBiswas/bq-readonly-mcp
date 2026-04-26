"""Tests for detecting an existing LIMIT on the outermost query."""

from bq_readonly_mcp.safety import has_outer_limit


def test_no_limit():
    assert has_outer_limit("SELECT * FROM t") is False


def test_limit_at_end():
    assert has_outer_limit("SELECT * FROM t LIMIT 10") is True


def test_limit_with_offset():
    assert has_outer_limit("SELECT * FROM t LIMIT 10 OFFSET 5") is True


def test_limit_lowercase():
    assert has_outer_limit("select * from t limit 10") is True


def test_limit_in_subquery_only_returns_false():
    assert has_outer_limit("SELECT * FROM (SELECT * FROM t LIMIT 10) sub") is False


def test_limit_followed_by_semicolon():
    assert has_outer_limit("SELECT * FROM t LIMIT 10;") is True


def test_limit_followed_by_whitespace_and_semicolon():
    assert has_outer_limit("SELECT * FROM t LIMIT 10  ;  ") is True


def test_limit_with_named_parameter():
    assert has_outer_limit("SELECT * FROM t LIMIT @max") is True


def test_limit_with_positional_parameter():
    assert has_outer_limit("SELECT * FROM t LIMIT ?") is True


def test_limit_param_with_offset():
    assert has_outer_limit("SELECT * FROM t LIMIT @max OFFSET @off") is True
