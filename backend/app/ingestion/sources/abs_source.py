from dataclasses import dataclass
import time

import httpx

from backend.app.core.config import get_settings


@dataclass
class ABSRow:
    postcode: str
    census_year: int
    median_household_income: float | None
    unemployment_rate_pct: float | None
    population: int | None
    notes: str | None = None


def fetch_abs_snapshot() -> list[ABSRow]:
    settings = get_settings()
    if settings.abs_api_url:
        rows = _fetch_abs_from_api(settings.abs_api_url)
        if rows:
            return rows

    return [
        ABSRow(
            postcode="2000",
            census_year=2021,
            median_household_income=2530.0,
            unemployment_rate_pct=4.1,
            population=18300,
            notes="Seeded example row from initial scaffold.",
        )
    ]


def _fetch_abs_from_api(url: str) -> list[ABSRow]:
    # Simple bounded retry loop for transient upstream failures.
    for attempt in range(1, 4):
        try:
            with httpx.Client(timeout=15) as client:
                response = client.get(url)
                response.raise_for_status()
                payload = response.json()
            break
        except Exception:
            if attempt == 3:
                return []
            time.sleep(attempt)

    data = payload if isinstance(payload, list) else payload.get("data", [])
    rows: list[ABSRow] = []
    for item in data:
        try:
            rows.append(
                ABSRow(
                    postcode=str(item.get("postcode", "")).strip(),
                    census_year=int(item.get("census_year", 0)),
                    median_household_income=_to_float(item.get("median_household_income")),
                    unemployment_rate_pct=_to_float(item.get("unemployment_rate_pct")),
                    population=_to_int(item.get("population")),
                    notes=item.get("notes"),
                )
            )
        except Exception:
            continue
    return [row for row in rows if row.postcode and row.census_year > 0]


def _to_float(value) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _to_int(value) -> int | None:
    if value is None or value == "":
        return None
    return int(value)
