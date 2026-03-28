from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.models import ABSIndicator, Property, Transaction
from backend.app.db.session import get_db
from backend.app.repositories.property_repository import PropertyRepository
from backend.app.schemas import (
    AdvancedValuationResponse,
    ComparableOut,
    PortfolioRiskRequest,
    PortfolioRiskResponse,
    ResearchPackOut,
    ResearchRequest,
    ValuationRequest,
)
from backend.app.services.abs_enrichment import describe_abs_context
from backend.app.services.cma_service import build_valuation
from backend.app.services.deep_analysis import build_deep_analysis
from backend.app.services.investment_scoring import compute_investment_score
from backend.app.services.research_engine import build_research_pack, simulate_portfolio_risk

router = APIRouter(prefix="/valuation", tags=["valuation"])


@router.post("", response_model=AdvancedValuationResponse)
def value_property(payload: ValuationRequest, db: Session = Depends(get_db)) -> AdvancedValuationResponse:
    repo = PropertyRepository(db)
    target = repo.get_property(payload.property_id)
    if not target:
        raise HTTPException(status_code=404, detail="Property not found")

    recent_transactions = repo.recent_transactions(suburb=target.suburb, property_type=target.property_type)
    comparable_pairs: list[tuple[Property, Transaction]] = []

    for tx in recent_transactions:
        comp_property = db.get(Property, tx.property_id)
        if not comp_property:
            continue
        if comp_property.id == target.id:
            continue
        comparable_pairs.append((comp_property, tx))

    valuation = build_valuation(target=target, comparable_pairs=comparable_pairs)

    suburb_metric = repo.latest_metric_for_postcode(target.postcode)
    abs_row = (
        db.query(ABSIndicator)
        .filter(ABSIndicator.postcode == target.postcode)
        .order_by(ABSIndicator.census_year.desc())
        .first()
    )

    growth = suburb_metric.annual_growth_pct if suburb_metric and suburb_metric.annual_growth_pct is not None else 2.5
    yield_pct = suburb_metric.rental_yield_pct if suburb_metric and suburb_metric.rental_yield_pct is not None else 3.6
    dom = suburb_metric.days_on_market_avg if suburb_metric and suburb_metric.days_on_market_avg is not None else 40
    sales_count = max(len(comparable_pairs), 1)
    if suburb_metric and getattr(suburb_metric, "sales_count", None) is not None:
        sales_count = max(int(suburb_metric.sales_count), 1)

    score, score_reasons = compute_investment_score(
        annual_growth_pct=growth,
        rental_yield_pct=yield_pct,
        days_on_market_avg=dom,
    )

    deep_analysis = build_deep_analysis(
        valuation_mid=valuation["mid"],
        valuation_low=valuation["low"],
        valuation_high=valuation["high"],
        confidence_pct=valuation["confidence"],
        comparable_prices=[item["sold_price"] for item in valuation["comparables"]],
        annual_growth_pct=growth,
        rental_yield_pct=yield_pct,
        days_on_market_avg=dom,
        sales_count=sales_count,
        unemployment_rate_pct=abs_row.unemployment_rate_pct if abs_row else None,
    )

    reasons = valuation["reason_codes"] + score_reasons + describe_abs_context(db, target.postcode)

    return AdvancedValuationResponse(
        property_id=target.id,
        low_estimate=valuation["low"],
        mid_estimate=valuation["mid"],
        high_estimate=valuation["high"],
        confidence_pct=valuation["confidence"],
        score=score,
        reasons=reasons,
        comparables=[ComparableOut(**item) for item in valuation["comparables"]],
        deep_analysis=deep_analysis,
    )


@router.post("/research", response_model=ResearchPackOut)
def valuation_research(payload: ResearchRequest, db: Session = Depends(get_db)) -> ResearchPackOut:
    repo = PropertyRepository(db)
    target = repo.get_property(payload.property_id)
    if not target:
        raise HTTPException(status_code=404, detail="Property not found")

    recent_transactions = repo.recent_transactions(suburb=target.suburb, property_type=target.property_type)
    comparable_pairs: list[tuple[Property, Transaction]] = []
    for tx in recent_transactions:
        comp_property = db.get(Property, tx.property_id)
        if not comp_property or comp_property.id == target.id:
            continue
        comparable_pairs.append((comp_property, tx))

    valuation = build_valuation(target=target, comparable_pairs=comparable_pairs)
    suburb_metric = repo.latest_metric_for_postcode(target.postcode)
    annual_growth_pct = suburb_metric.annual_growth_pct if suburb_metric and suburb_metric.annual_growth_pct is not None else 2.5
    rental_yield_pct = suburb_metric.rental_yield_pct if suburb_metric and suburb_metric.rental_yield_pct is not None else 3.6

    if payload.assumptions:
        assumptions = payload.assumptions.model_dump() if hasattr(payload.assumptions, "model_dump") else payload.assumptions.dict()
    else:
        assumptions = {}
    pack = build_research_pack(
        valuation_mid=valuation["mid"],
        annual_growth_pct=annual_growth_pct,
        rental_yield_pct=rental_yield_pct,
        state=target.state,
        confidence_pct=valuation["confidence"],
        comparable_count=len(valuation["comparables"]),
        assumptions=assumptions,
    )
    return ResearchPackOut(**pack)


@router.post("/portfolio-risk", response_model=PortfolioRiskResponse)
def portfolio_risk(payload: PortfolioRiskRequest) -> PortfolioRiskResponse:
    rows = [
        {
            "purchase_price": item.purchase_price,
            "lvr_pct": item.lvr_pct,
            "interest_rate_pct": item.interest_rate_pct,
            "loan_years": item.loan_years,
            "annual_rent": item.annual_rent,
            "annual_expenses": item.annual_expenses,
        }
        for item in payload.items
    ]
    result = simulate_portfolio_risk(rows)
    return PortfolioRiskResponse(**result)
