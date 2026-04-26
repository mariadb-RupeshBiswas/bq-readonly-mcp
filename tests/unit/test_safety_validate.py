"""Tests for the SELECT/WITH-only validator with DML/DDL rejection."""

import pytest

from bq_readonly_mcp.safety import SafetyError, validate_select_query


def test_select_allowed():
    validate_select_query("SELECT 1")


def test_select_with_leading_whitespace_allowed():
    validate_select_query("   \n  SELECT 1")


def test_with_cte_allowed():
    validate_select_query("WITH a AS (SELECT 1) SELECT * FROM a")


def test_select_lowercase_allowed():
    validate_select_query("select 1")


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO t VALUES (1)",
        "UPDATE t SET x = 1 WHERE y = 2",
        "DELETE FROM t WHERE x = 1",
        "MERGE t USING s ON x=y WHEN MATCHED THEN UPDATE SET x = 1",
        "CREATE TABLE t (id INT)",
        "DROP TABLE t",
        "ALTER TABLE t ADD COLUMN c INT",
        "TRUNCATE TABLE t",
        "GRANT SELECT ON t TO user",
        "REVOKE SELECT ON t FROM user",
        "EXPORT DATA OPTIONS(uri='gs://x') AS SELECT 1",
    ],
)
def test_dml_ddl_rejected(sql):
    with pytest.raises(SafetyError, match=r"non-SELECT|DML|DDL|disallowed"):
        validate_select_query(sql)


def test_select_with_dml_word_in_string_allowed():
    validate_select_query("SELECT 'INSERT' AS label")


def test_select_with_dml_word_in_comment_allowed():
    validate_select_query("SELECT 1 /* INSERT something */ FROM t")


def test_column_named_delete_flag_allowed():
    validate_select_query("SELECT delete_flag FROM t")


def test_multistatement_rejected():
    with pytest.raises(SafetyError, match="multi-statement"):
        validate_select_query("SELECT 1; SELECT 2")


def test_empty_rejected():
    with pytest.raises(SafetyError):
        validate_select_query("")


def test_only_whitespace_rejected():
    with pytest.raises(SafetyError):
        validate_select_query("   \n  ")


def test_backticked_path_with_reserved_word_allowed():
    # The backticked identifier should NOT trigger DML/DDL keyword check
    validate_select_query("SELECT * FROM `proj.ds.UPDATE_LOG`")


def test_real_bigquery_public_data_query_allowed():
    # The canonical "every real BigQuery query" shape with backticked path
    validate_select_query("SELECT word FROM `bigquery-public-data.samples.shakespeare`")
