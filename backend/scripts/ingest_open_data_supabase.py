"""Free-tier ingestion runner for Supabase Postgres.

Pipelines:
- abs: pulls ABS-like JSON rows from ABS_API_URL (or fallback sample)
- metrics: pulls suburb metrics CSV from OPEN_METRICS_CSV_URL (or fallback sample)

This script writes ingestion telemetry to pipeline_runs.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime

import httpx
import psycopg2
from psycopg2.extensions import connection as PGConnection


@dataclass
class ABSRow:
    postcode: str
    census_year: int
    median_household_income: float | None
    unemployment_rate_pct: float | None
    population: int | None
    notes: str | None = None


@dataclass
class MetricRow:
    suburb: str
    state: str
    postcode: str
    median_price: float | None
    annual_growth_pct: float | None
    rental_yield_pct: float | None
    days_on_market_avg: int | None
    source: str
    as_of_date: date


def _get_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def _to_int(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return int(float(text))


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def fetch_abs_rows(abs_api_url: str) -> list[ABSRow]:
    if not abs_api_url:
        return [
            ABSRow(
                postcode="2000",
                census_year=2021,
                median_household_income=2530.0,
                unemployment_rate_pct=4.1,
                population=18300,
                notes="Fallback seed ABS row",
            )
        ]

    with httpx.Client(timeout=30) as client:
        response = client.get(abs_api_url)
        response.raise_for_status()
        payload = response.json()

    data = payload if isinstance(payload, list) else payload.get("data", [])
    rows: list[ABSRow] = []
    for item in data:
        try:
            row = ABSRow(
                postcode=str(item.get("postcode", "")).strip(),
                census_year=int(item.get("census_year", 0)),
                median_household_income=_to_float(item.get("median_household_income")),
                unemployment_rate_pct=_to_float(item.get("unemployment_rate_pct")),
                population=_to_int(item.get("population")),
                notes=str(item.get("notes", "")).strip() or None,
            )
        except Exception:
            continue

        if row.postcode and row.census_year > 0:
            rows.append(row)

    return rows


def fetch_metric_rows(metrics_csv_url: str, as_of_date: date) -> list[MetricRow]:
    if not metrics_csv_url:
        return [
            MetricRow(
                suburb="Sydney",
                state="NSW",
                postcode="2000",
                median_price=1450000,
                annual_growth_pct=7.2,
                rental_yield_pct=3.8,
                days_on_market_avg=29,
                source="open_data",
                as_of_date=as_of_date,
            )
        ]

    with httpx.Client(timeout=45) as client:
        response = client.get(metrics_csv_url)
        response.raise_for_status()
        content = response.text

    rows: list[MetricRow] = []
    reader = csv.DictReader(io.StringIO(content))
    for item in reader:
        suburb = str(item.get("suburb", "")).strip()
        state = str(item.get("state", "")).strip()
        postcode = str(item.get("postcode", "")).strip()
        if not suburb or not state or not postcode:
            continue

        rows.append(
            MetricRow(
                suburb=suburb,
                state=state,
                postcode=postcode,
                median_price=_to_float(item.get("median_price")),
                annual_growth_pct=_to_float(item.get("annual_growth_pct")),
                rental_yield_pct=_to_float(item.get("rental_yield_pct")),
                days_on_market_avg=_to_int(item.get("days_on_market_avg")),
                source=str(item.get("source", "open_data")).strip() or "open_data",
                as_of_date=_parse_date(str(item.get("as_of_date", as_of_date.isoformat())).strip()),
            )
        )

    return rows


def create_pipeline_run(conn: PGConnection, pipeline_name: str, source_name: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into public.pipeline_runs (pipeline_name, source_name, status, records_processed, records_failed, started_at)
            values (%s, %s, 'running', 0, 0, now())
            returning id::text
            """,
            (pipeline_name, source_name),
        )
        run_id = cur.fetchone()[0]
    conn.commit()
    return run_id


def complete_pipeline_run(
    conn: PGConnection,
    run_id: str,
    *,
    status: str,
    records_processed: int,
    records_failed: int,
    message: str | None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            update public.pipeline_runs
            set status = %s,
                records_processed = %s,
                records_failed = %s,
                error_message = %s,
                freshness_minutes = 0,
                completed_at = now()
            where id::text = %s
            """,
            (status, records_processed, records_failed, message, run_id),
        )
    conn.commit()


def ingest_abs(conn: PGConnection, abs_api_url: str) -> tuple[int, int]:
    rows = fetch_abs_rows(abs_api_url)
    processed = 0
    failed = 0

    with conn.cursor() as cur:
        for row in rows:
            if not row.postcode or row.census_year <= 0:
                failed += 1
                continue

            cur.execute(
                """
                insert into public.abs_indicators
                (postcode, census_year, median_household_income, unemployment_rate_pct, population, notes)
                values (%s, %s, %s, %s, %s, %s)
                on conflict (postcode, census_year)
                do update
                  set median_household_income = excluded.median_household_income,
                      unemployment_rate_pct = excluded.unemployment_rate_pct,
                      population = excluded.population,
                      notes = excluded.notes
                """,
                (
                    row.postcode,
                    row.census_year,
                    row.median_household_income,
                    row.unemployment_rate_pct,
                    row.population,
                    row.notes,
                ),
            )
            processed += 1

    conn.commit()
    return processed, failed


def ingest_metrics(conn: PGConnection, metrics_csv_url: str, as_of_date: date) -> tuple[int, int]:
    rows = fetch_metric_rows(metrics_csv_url, as_of_date)
    processed = 0
    failed = 0

    with conn.cursor() as cur:
        for row in rows:
            if not row.suburb or not row.state or not row.postcode:
                failed += 1
                continue

            cur.execute(
                """
                insert into public.suburb_metrics
                (suburb, state, postcode, median_price, annual_growth_pct, rental_yield_pct, days_on_market_avg, source, as_of_date)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                on conflict (postcode, as_of_date, source)
                do update
                  set suburb = excluded.suburb,
                      state = excluded.state,
                      median_price = excluded.median_price,
                      annual_growth_pct = excluded.annual_growth_pct,
                      rental_yield_pct = excluded.rental_yield_pct,
                      days_on_market_avg = excluded.days_on_market_avg
                """,
                (
                    row.suburb,
                    row.state,
                    row.postcode,
                    row.median_price,
                    row.annual_growth_pct,
                    row.rental_yield_pct,
                    row.days_on_market_avg,
                    row.source,
                    row.as_of_date,
                ),
            )
            processed += 1

    conn.commit()
    return processed, failed


def run_pipeline(conn: PGConnection, pipeline: str, abs_api_url: str, metrics_csv_url: str, as_of_date: date) -> None:
    if pipeline in {"abs", "all"}:
        run_id = create_pipeline_run(conn, "abs_ingestion", "abs")
        try:
            processed, failed = ingest_abs(conn, abs_api_url)
            complete_pipeline_run(
                conn,
                run_id,
                status="completed",
                records_processed=processed,
                records_failed=failed,
                message=None,
            )
            print(f"ABS ingestion complete: processed={processed}, failed={failed}")
        except Exception as exc:
            conn.rollback()
            complete_pipeline_run(
                conn,
                run_id,
                status="failed",
                records_processed=0,
                records_failed=0,
                message=str(exc),
            )
            raise

    if pipeline in {"metrics", "all"}:
        run_id = create_pipeline_run(conn, "suburb_metrics_ingestion", "open_metrics")
        try:
            processed, failed = ingest_metrics(conn, metrics_csv_url, as_of_date)
            complete_pipeline_run(
                conn,
                run_id,
                status="completed",
                records_processed=processed,
                records_failed=failed,
                message=None,
            )
            print(f"Metrics ingestion complete: processed={processed}, failed={failed}")
        except Exception as exc:
            conn.rollback()
            complete_pipeline_run(
                conn,
                run_id,
                status="failed",
                records_processed=0,
                records_failed=0,
                message=str(exc),
            )
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest open data into Supabase Postgres")
    parser.add_argument("--pipeline", choices=["abs", "metrics", "all"], default="all")
    parser.add_argument("--as-of-date", default=date.today().isoformat(), help="Date for metric rows (YYYY-MM-DD)")
    args = parser.parse_args()

    database_url = _get_env("DATABASE_URL")
    # Allow DATABASE_URL to be either SQLAlchemy style or native psycopg2 DSN.
    if database_url.startswith("postgresql+psycopg2://"):
        database_url = "postgresql://" + database_url.split("postgresql+psycopg2://", 1)[1]
    elif database_url.startswith("postgres+psycopg2://"):
        database_url = "postgres://" + database_url.split("postgres+psycopg2://", 1)[1]
    abs_api_url = os.getenv("ABS_API_URL", "").strip()
    metrics_csv_url = os.getenv("OPEN_METRICS_CSV_URL", "").strip()
    as_of_date = _parse_date(args.as_of_date)

    print(f"Starting pipeline={args.pipeline} at {datetime.now(UTC).isoformat()}")
    with psycopg2.connect(database_url) as conn:
        run_pipeline(conn, args.pipeline, abs_api_url, metrics_csv_url, as_of_date)
    print("Ingestion finished")


if __name__ == "__main__":
    main()
