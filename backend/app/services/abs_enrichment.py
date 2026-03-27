from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from backend.app.db.models import ABSIndicator


def describe_abs_context(db: Session, postcode: str) -> list[str]:
    query: Select[tuple[ABSIndicator]] = (
        select(ABSIndicator)
        .where(ABSIndicator.postcode == postcode)
        .order_by(desc(ABSIndicator.census_year))
        .limit(1)
    )
    row = db.scalars(query).first()
    if not row:
        return ["No ABS context available for this postcode yet."]

    notes: list[str] = []
    if row.unemployment_rate_pct is not None:
        notes.append(f"ABS unemployment rate: {row.unemployment_rate_pct:.1f}%")
    if row.median_household_income is not None:
        notes.append(f"ABS median household income: ${row.median_household_income:,.0f}")
    if row.population is not None:
        notes.append(f"ABS population baseline: {row.population:,}")

    if row.notes:
        notes.append(row.notes)

    return notes or ["ABS row exists but has no populated analytics fields."]
