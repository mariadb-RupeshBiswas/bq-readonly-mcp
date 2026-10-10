"""Atheris fuzz target for the SQL safety guard: any exception except SafetyError is a bug.

Linux, Python 3.12+:
    pip install atheris==3.1.0
    PYTHONPATH=src python fuzz/fuzz_safety.py -max_len=4096 -max_total_time=120
"""

import sys

import atheris

with atheris.instrument_imports():
    from bq_readonly_mcp import safety


def test_one_input(data: bytes) -> None:
    sql = atheris.FuzzedDataProvider(data).ConsumeUnicodeNoSurrogates(4096)
    safety.is_multistatement(sql)
    try:
        safety.validate_select_query(sql)
    except safety.SafetyError:
        return
    safety.inject_limit(sql, 100)


if __name__ == "__main__":
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()
