"""Thin BigQuery client wrapper.

This is the only module that touches the `google.cloud.bigquery.Client`
directly. Everything else accepts a `BQClient` instance, making testing
trivial via mocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from google.cloud import bigquery

from .models import DatasetInfo, TableInfo


class DatasetNotAllowedError(PermissionError):
    """Raised when a request references a dataset outside the allowlist."""


# Pricing constant: $6.25 per TiB on-demand BigQuery query (US, approx).
# This is for human-readable estimates only — never billing-authoritative.
USD_PER_BYTE = 6.25 / (1024**4)


class CostExceededError(RuntimeError):
    """Raised when a query's estimated cost exceeds the configured cap."""


@dataclass
class BQClient:
    client: bigquery.Client
    allowed_datasets: list[str] | None = None

    # ----- listing -----

    def _check_dataset(self, dataset_id: str) -> None:
        if self.allowed_datasets is not None and dataset_id not in self.allowed_datasets:
            raise DatasetNotAllowedError(
                f"dataset {dataset_id!r} is not in the configured allowlist"
            )

    def list_datasets(self, name_contains: str | None = None) -> list[DatasetInfo]:
        out: list[DatasetInfo] = []
        for ds_ref in self.client.list_datasets():
            if self.allowed_datasets is not None and ds_ref.dataset_id not in self.allowed_datasets:
                continue
            if name_contains and name_contains.lower() not in ds_ref.dataset_id.lower():
                continue
            ds = self.client.get_dataset(ds_ref)
            out.append(
                DatasetInfo(
                    dataset_id=ds.dataset_id,
                    location=ds.location,
                    friendly_name=getattr(ds, "friendly_name", None),
                    description=getattr(ds, "description", None),
                )
            )
        return out

    def list_tables(self, dataset_id: str, name_contains: str | None = None) -> list[TableInfo]:
        self._check_dataset(dataset_id)
        out: list[TableInfo] = []
        for t in self.client.list_tables(dataset_id):
            if name_contains and name_contains.lower() not in t.table_id.lower():
                continue
            out.append(
                TableInfo(
                    table_id=t.table_id,
                    type=t.table_type,
                    created=t.created.isoformat() if t.created else None,
                    friendly_name=getattr(t, "friendly_name", None),
                )
            )
        return out

    # ----- table-level introspection -----

    def get_table_metadata(self, dataset_id: str, table_id: str):
        from .models import PartitioningInfo, TableMetadata

        self._check_dataset(dataset_id)
        ref = f"{self.client.project}.{dataset_id}.{table_id}"
        t = self.client.get_table(ref)

        partitioning: PartitioningInfo | None = None
        if t.time_partitioning is not None:
            partitioning = PartitioningInfo(
                type=t.time_partitioning.type_,
                column=t.time_partitioning.field,
                expiration_ms=t.time_partitioning.expiration_ms,
            )
        elif t.range_partitioning is not None:
            partitioning = PartitioningInfo(
                type="INTEGER_RANGE",
                column=t.range_partitioning.field,
                expiration_ms=None,
            )

        return TableMetadata(
            table_id=t.table_id,
            type=t.table_type,
            description=t.description,
            labels=t.labels or {},
            created=t.created.isoformat(),
            modified=t.modified.isoformat(),
            row_count=t.num_rows or 0,
            size_bytes=t.num_bytes or 0,
            partitioning=partitioning,
            clustering=list(t.clustering_fields) if t.clustering_fields else None,
            expires=t.expires.isoformat() if t.expires else None,
        )

    def describe_columns(self, dataset_id: str, table_id: str):
        from .models import ColumnSchema

        self._check_dataset(dataset_id)
        ref = f"{self.client.project}.{dataset_id}.{table_id}"
        t = self.client.get_table(ref)
        return [
            ColumnSchema(
                name=f.name,
                type=f.field_type,
                mode=f.mode or "NULLABLE",
                description=f.description,
            )
            for f in t.schema
        ]

    # ----- query execution -----

    def estimate_query_cost(self, query: str, *, max_bytes_billed: int):
        from .models import CostEstimate

        job = self._dry_run(query)
        bytes_proc = job.total_bytes_processed or 0
        return CostEstimate(
            total_bytes_processed=bytes_proc,
            estimated_usd=round(bytes_proc * USD_PER_BYTE, 6),
            would_be_blocked=bytes_proc > max_bytes_billed,
        )

    def run_query(self, query: str, *, max_bytes_billed: int):
        from google.cloud import bigquery as bq

        from .models import ColumnSchema, QueryResult

        dryrun_job = self._dry_run(query)

        # Allowlist enforcement on referenced tables
        if self.allowed_datasets is not None:
            for ref in dryrun_job.referenced_tables or []:
                if ref.dataset_id not in self.allowed_datasets:
                    raise DatasetNotAllowedError(
                        f"query references dataset {ref.dataset_id!r} which is "
                        "not in the configured allowlist"
                    )

        bytes_proc = dryrun_job.total_bytes_processed or 0
        if bytes_proc > max_bytes_billed:
            raise CostExceededError(
                f"query estimate {bytes_proc} bytes exceeds cap {max_bytes_billed}"
            )

        config = bq.QueryJobConfig(maximum_bytes_billed=max_bytes_billed)
        job = self.client.query(query, job_config=config)
        rows = [dict(row.items()) for row in job.result()]

        return QueryResult(
            rows=rows,
            schema=[
                ColumnSchema(
                    name=f.name,
                    type=f.field_type,
                    mode=f.mode or "NULLABLE",
                    description=getattr(f, "description", None),
                )
                for f in job.schema or []
            ],
            total_bytes_processed=job.total_bytes_processed or 0,
            total_bytes_billed=job.total_bytes_billed or 0,
            cache_hit=bool(job.cache_hit),
            job_id=job.job_id,
            location=job.location,
        )

    def _dry_run(self, query: str) -> Any:
        from google.cloud import bigquery as bq

        config = bq.QueryJobConfig(dry_run=True, use_query_cache=False)
        return self.client.query(query, job_config=config)
