from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.property_repository import PropertyRepository
from backend.app.schemas import SuburbRankingOut
from backend.app.services.investment_scoring import compute_investment_score

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/suburbs", response_model=list[SuburbRankingOut])
def suburb_rankings(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[SuburbRankingOut]:
    repo = PropertyRepository(db)
    metrics = repo.latest_suburb_metrics(limit=limit)
    rows: list[SuburbRankingOut] = []

    for metric in metrics:
        score, _ = compute_investment_score(
            annual_growth_pct=metric.annual_growth_pct if metric.annual_growth_pct is not None else 0.0,
            rental_yield_pct=metric.rental_yield_pct if metric.rental_yield_pct is not None else 0.0,
            days_on_market_avg=metric.days_on_market_avg if metric.days_on_market_avg is not None else 60,
        )
        rows.append(
            SuburbRankingOut(
                suburb=metric.suburb,
                state=metric.state,
                postcode=metric.postcode,
                investment_score=score,
                median_price=metric.median_price if metric.median_price is not None else 0.0,
                annual_growth_pct=metric.annual_growth_pct if metric.annual_growth_pct is not None else 0.0,
                rental_yield_pct=metric.rental_yield_pct if metric.rental_yield_pct is not None else 0.0,
            )
        )

    rows.sort(key=lambda row: row.investment_score, reverse=True)
    return rows
