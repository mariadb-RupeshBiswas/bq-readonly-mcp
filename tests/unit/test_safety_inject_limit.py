"""Tests for safe LIMIT injection on queries that lack an outer LIMIT."""

import pytest

from bq_readonly_mcp.safety import has_outer_limit, inject_limit


def test_injects_when_missing():
    out = inject_limit("SELECT * FROM t", limit=50)
    assert out.rstrip().rstrip(";").endswith("LIMIT 50")


def test_no_injection_when_present():
    sql = "SELECT * FROM t LIMIT 10"
    assert inject_limit(sql, limit=50) == sql


def test_strips_trailing_semicolon_before_injection():
    out = inject_limit("SELECT * FROM t;", limit=50)
    assert out == "SELECT * FROM t\nLIMIT 50"


def test_trailing_line_comment_does_not_swallow_limit():
    out = inject_limit("SELECT * FROM t -- note", limit=50)
    assert has_outer_limit(out)


def test_trailing_block_comment_keeps_limit():
    out = inject_limit("SELECT * FROM t /* note */", limit=50)
    assert has_outer_limit(out)


def test_preserves_subquery_limit():
    sql = "SELECT * FROM (SELECT * FROM t LIMIT 10) sub"
    out = inject_limit(sql, limit=50)
    assert out.rstrip().rstrip(";").endswith("LIMIT 50")
    assert "LIMIT 10" in out


def test_limit_zero_invalid():
    with pytest.raises(ValueError):
        inject_limit("SELECT * FROM t", limit=0)


def test_negative_limit_invalid():
    with pytest.raises(ValueError):
        inject_limit("SELECT * FROM t", limit=-5)
