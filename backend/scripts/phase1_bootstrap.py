"""Phase 1 data bootstrap for open-data baseline.

This script runs the open-data ingestion pipeline and prints quick table counts
for the app-critical datasets.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from datetime import UTC, date, datetime

import psycopg2
from dotenv import load_dotenv

from backend.scripts.ingest_open_data_supabase import _parse_date, run_pipeline


def _normalize_database_url(database_url: str) -> str:
    value = database_url.strip()
    if value.startswith("postgresql+psycopg2://"):
        return "postgresql://" + value.split("postgresql+psycopg2://", 1)[1]
    if value.startswith("postgres+psycopg2://"):
        return "postgres://" + value.split("postgres+psycopg2://", 1)[1]
    return value


def _table_count(conn: psycopg2.extensions.connection, table_name: str) -> int:
    with conn.cursor() as cur:
        cur.execute(f"select count(*) from public.{table_name}")
        return int(cur.fetchone()[0])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 1 open-data bootstrap")
    parser.add_argument("--as-of-date", default=date.today().isoformat(), help="Date for metric rows (YYYY-MM-DD)")
    parser.add_argument("--pipeline", choices=["abs", "metrics", "all"], default="all")
    args = parser.parse_args()

    # Load workspace .env so local runs work without shell exports.
    workspace_root = Path(__file__).resolve().parents[2]
    load_dotenv(workspace_root / ".env")

    database_url = _normalize_database_url(os.getenv("DATABASE_URL", ""))
    if not database_url:
        raise RuntimeError("Missing required environment variable: DATABASE_URL")

    abs_api_url = os.getenv("ABS_API_URL", "").strip()
    metrics_csv_url = os.getenv("OPEN_METRICS_CSV_URL", "").strip()
    as_of_date = _parse_date(args.as_of_date)

    print(f"Phase 1 bootstrap start: pipeline={args.pipeline} at {datetime.now(UTC).isoformat()}")

    with psycopg2.connect(database_url) as conn:
        run_pipeline(
            conn=conn,
            pipeline=args.pipeline,
            abs_api_url=abs_api_url,
            metrics_csv_url=metrics_csv_url,
            as_of_date=as_of_date,
        )

        counts = {
            "abs_indicators": _table_count(conn, "abs_indicators"),
            "suburb_metrics": _table_count(conn, "suburb_metrics"),
            "pipeline_runs": _table_count(conn, "pipeline_runs"),
        }

    print("Phase 1 bootstrap complete")
    for table_name, count in counts.items():
        print(f"  {table_name}: {count}")


if __name__ == "__main__":
    main()
