"""Tool: list datasets."""

from __future__ import annotations

from typing import Any

from ..bq import BQClient
from ..models import ListDatasetsInput

NAME = "list_datasets"
DESCRIPTION = (
    "List BigQuery datasets in the configured project. "
    "Returns dataset_id, location, friendly_name, and description for each. "
    "Optional `name_contains` does a case-insensitive substring filter."
)
INPUT_SCHEMA = ListDatasetsInput.model_json_schema()


def handle(args: dict[str, Any], *, bq: BQClient) -> list[dict[str, Any]]:
    parsed = ListDatasetsInput(**args)
    return [d.model_dump() for d in bq.list_datasets(name_contains=parsed.name_contains)]
