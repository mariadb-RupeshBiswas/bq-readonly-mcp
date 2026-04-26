"""Pydantic models for tool inputs and outputs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Tool inputs ---


class ListDatasetsInput(_StrictModel):
    name_contains: str | None = None


class ListTablesInput(_StrictModel):
    dataset_id: str = Field(min_length=1)
    name_contains: str | None = None


class GetTableMetadataInput(_StrictModel):
    dataset_id: str = Field(min_length=1)
    table_id: str = Field(min_length=1)


class DescribeColumnsInput(_StrictModel):
    dataset_id: str = Field(min_length=1)
    table_id: str = Field(min_length=1)


class GetTableInput(_StrictModel):
    dataset_id: str = Field(min_length=1)
    table_id: str = Field(min_length=1)
    sample_rows: PositiveInt | None = None


class RunQueryInput(_StrictModel):
    query: str = Field(min_length=1)
    limit: PositiveInt | None = None
    no_limit: bool = False
    dry_run: bool = False


class EstimateQueryCostInput(_StrictModel):
    query: str = Field(min_length=1)


# --- Outputs ---


class DatasetInfo(_StrictModel):
    dataset_id: str
    location: str
    friendly_name: str | None = None
    description: str | None = None


TableType = Literal["TABLE", "VIEW", "MATERIALIZED_VIEW", "EXTERNAL", "SNAPSHOT"]


class TableInfo(_StrictModel):
    table_id: str
    type: TableType
    created: str | None = None
    friendly_name: str | None = None


class ColumnSchema(_StrictModel):
    name: str
    type: str
    mode: Literal["NULLABLE", "REQUIRED", "REPEATED"]
    description: str | None = None


PartitioningType = Literal["DAY", "HOUR", "MONTH", "YEAR", "INTEGER_RANGE"]


class PartitioningInfo(_StrictModel):
    type: PartitioningType
    column: str | None = None
    expiration_ms: int | None = None


class TableMetadata(_StrictModel):
    table_id: str
    type: TableType
    description: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    created: str
    modified: str
    row_count: int
    size_bytes: int
    partitioning: PartitioningInfo | None = None
    clustering: list[str] | None = None
    expires: str | None = None
    time_travel_window_hours: int | None = None


class QueryResult(_StrictModel):
    rows: list[dict[str, Any]]
    schema: list[ColumnSchema]
    total_bytes_processed: int
    total_bytes_billed: int
    cache_hit: bool
    job_id: str
    location: str


class CostEstimate(_StrictModel):
    total_bytes_processed: int
    estimated_usd: float
    would_be_blocked: bool
