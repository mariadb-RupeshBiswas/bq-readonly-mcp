"""Smoke test that the package is installable and imports correctly."""


def test_package_imports():
    import bq_readonly_mcp

    assert bq_readonly_mcp.__version__ == "0.1.0"
