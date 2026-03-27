from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import ABSIndicator, PipelineRun, Property
from backend.app.ingestion.sources.abs_source import fetch_abs_snapshot
from backend.app.ingestion.sources.manual_listing_source import read_listing_csv


def run_abs_ingestion(db: Session) -> int:
    run = PipelineRun(pipeline_name="abs_ingestion", source_name="abs", status="running", started_at=datetime.utcnow())
    db.add(run)
    db.commit()
    db.refresh(run)

    rows = fetch_abs_snapshot()
    upserts = 0
    failures = 0

    for row in rows:
        if not row.postcode or row.census_year <= 0:
            failures += 1
            continue

        existing = db.scalars(
            select(ABSIndicator)
            .where(ABSIndicator.postcode == row.postcode)
            .where(ABSIndicator.census_year == row.census_year)
        ).first()

        if existing:
            existing.median_household_income = row.median_household_income
            existing.unemployment_rate_pct = row.unemployment_rate_pct
            existing.population = row.population
            existing.notes = row.notes
        else:
            db.add(
                ABSIndicator(
                    postcode=row.postcode,
                    census_year=row.census_year,
                    median_household_income=row.median_household_income,
                    unemployment_rate_pct=row.unemployment_rate_pct,
                    population=row.population,
                    notes=row.notes,
                )
            )
        upserts += 1

    run.status = "completed"
    run.records_processed = upserts
    run.records_failed = failures
    run.freshness_minutes = 0
    run.completed_at = datetime.utcnow()
    db.commit()
    return upserts


def run_manual_listing_ingestion(db: Session, csv_path: str) -> int:
    run = PipelineRun(
        pipeline_name="manual_listing_ingestion",
        source_name="manual_csv",
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    rows = read_listing_csv(csv_path)
    inserted = 0
    failed = 0
    for row in rows:
        if not str(row.get("address", "")).strip() or not str(row.get("postcode", "")).strip():
            failed += 1
            continue

        db.add(
            Property(
                address=str(row["address"]),
                suburb=str(row["suburb"]),
                state=str(row["state"]),
                postcode=str(row["postcode"]),
                property_type=str(row["property_type"]),
                bedrooms=int(row.get("bedrooms") or 0),
                bathrooms=int(row.get("bathrooms") or 0),
                carspaces=int(row.get("carspaces") or 0),
                land_area_sqm=float(row.get("land_area_sqm") or 0) or None,
                building_area_sqm=float(row.get("building_area_sqm") or 0) or None,
            )
        )
        inserted += 1

    run.status = "completed"
    run.records_processed = inserted
    run.records_failed = failed
    run.freshness_minutes = 0
    run.completed_at = datetime.utcnow()
    db.commit()
    return inserted
