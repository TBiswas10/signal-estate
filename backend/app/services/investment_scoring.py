def compute_investment_score(
    annual_growth_pct: float,
    rental_yield_pct: float,
    days_on_market_avg: int,
) -> tuple[float, list[str]]:
    growth_component = min(max(annual_growth_pct, -5), 20) * 0.3
    yield_component = min(max(rental_yield_pct, 0), 10) * 0.5
    liquidity_component = max(0, 60 - min(days_on_market_avg, 60)) * 0.05

    score = round(min(10.0, max(0.0, growth_component + yield_component + liquidity_component)), 2)

    reasons: list[str] = []
    if annual_growth_pct > 5:
        reasons.append("Suburb has strong recent capital growth momentum.")
    if rental_yield_pct > 4:
        reasons.append("Rental yield is above common metro-market averages.")
    if days_on_market_avg < 30:
        reasons.append("Properties move quickly, indicating good demand depth.")
    if not reasons:
        reasons.append("Balanced profile with no extreme positive or negative signals yet.")

    return score, reasons
