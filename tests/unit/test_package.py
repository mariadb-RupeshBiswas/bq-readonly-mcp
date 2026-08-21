"""Smoke test that the package is installable and imports correctly."""


def test_package_imports():
    from importlib.metadata import version

    import bq_readonly_mcp

    # compare to installed metadata so a bump can't drift from pyproject
    assert bq_readonly_mcp.__version__ == version("bq-readonly-mcp")
