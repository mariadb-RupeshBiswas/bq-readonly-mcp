"""Allow `python -m bq_readonly_mcp` invocation."""

from .server import main

if __name__ == "__main__":
    raise SystemExit(main())
