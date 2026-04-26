"""Tests for detection of multi-statement queries."""

from bq_readonly_mcp.safety import is_multistatement


def test_single_statement_no_semicolon():
    assert is_multistatement("SELECT 1") is False


def test_single_statement_trailing_semicolon():
    assert is_multistatement("SELECT 1;") is False


def test_single_statement_trailing_semicolon_whitespace():
    assert is_multistatement("SELECT 1;   \n  ") is False


def test_two_statements():
    assert is_multistatement("SELECT 1; SELECT 2") is True


def test_two_statements_both_terminated():
    assert is_multistatement("SELECT 1; SELECT 2;") is True


def test_semicolon_in_string_not_terminator():
    assert is_multistatement("SELECT 'a;b'") is False


def test_semicolon_in_comment_not_terminator():
    assert is_multistatement("SELECT 1 -- ; comment\n") is False
