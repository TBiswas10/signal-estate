from statistics import pstdev


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _safe_std_pct(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = sum(values) / len(values)
    if avg == 0:
        return 0.0
    return (pstdev(values) / avg) * 100


def build_deep_analysis(
    *,
    valuation_mid: float,
    valuation_low: float,
    valuation_high: float,
    confidence_pct: float,
    comparable_prices: list[float],
    annual_growth_pct: float,
    rental_yield_pct: float,
    days_on_market_avg: int,
    sales_count: int,
    unemployment_rate_pct: float | None,
) -> dict:
    dispersion_pct = _safe_std_pct(comparable_prices)
    downside_gap_pct = 0.0
    if valuation_mid > 0:
        downside_gap_pct = ((valuation_mid - valuation_low) / valuation_mid) * 100

    liquidity_risk = _clamp((days_on_market_avg / 60) * 10, 0, 10)
    volatility_risk = _clamp((dispersion_pct / 20) * 10, 0, 10)
    downside_risk = _clamp((downside_gap_pct / 12) * 10, 0, 10)
    macro_stress_base = unemployment_rate_pct if unemployment_rate_pct is not None else 5.0
    macro_stress_risk = _clamp((macro_stress_base / 10) * 10, 0, 10)

    fragility_score = round(
        _clamp((liquidity_risk + volatility_risk + downside_risk + macro_stress_risk) / 4, 0, 10),
        2,
    )

    data_depth_score = round(_clamp((len(comparable_prices) / 12) * 10 + min(2, sales_count / 150), 0, 10), 2)

    growth_score = _clamp((annual_growth_pct + 5) / 2.5, 0, 10)
    yield_score = _clamp(rental_yield_pct * 1.8, 0, 10)
    conviction_score = round(_clamp((growth_score * 0.35) + (yield_score * 0.35) + (confidence_pct / 10 * 0.30), 0, 10), 2)

    edge_score = round(
        _clamp(
            (yield_score * 0.45)
            + ((10 - liquidity_risk) * 0.20)
            + ((10 - volatility_risk) * 0.20)
            + (data_depth_score * 0.15),
            0,
            10,
        ),
        2,
    )

    moat_score = round(
        _clamp(
            (confidence_pct / 10 * 0.40)
            + ((10 - fragility_score) * 0.30)
            + (_clamp(sales_count / 40, 0, 10) * 0.30),
            0,
            10,
        ),
        2,
    )

    if annual_growth_pct >= 7 and days_on_market_avg <= 30:
        market_regime = "Momentum Expansion"
    elif annual_growth_pct <= 1 and days_on_market_avg > 45:
        market_regime = "Late-Cycle Cooling"
    else:
        market_regime = "Selective Accumulation"

    base_cashflow = valuation_mid * (rental_yield_pct / 100)
    scenario_matrix = [
        {
            "scenario": "Rates Down 100bps",
            "forecast_mid_value": round(valuation_mid * (1.06 + annual_growth_pct / 100 * 0.3), 2),
            "expected_cashflow_delta_annual": round(base_cashflow * 0.04, 2),
            "risk_shift": round(_clamp(fragility_score - 0.9, 0, 10), 2),
        },
        {
            "scenario": "Base Case",
            "forecast_mid_value": round(valuation_mid * (1.03 + annual_growth_pct / 100 * 0.2), 2),
            "expected_cashflow_delta_annual": round(base_cashflow * 0.015, 2),
            "risk_shift": fragility_score,
        },
        {
            "scenario": "Rates Up 150bps",
            "forecast_mid_value": round(valuation_mid * (0.95 + annual_growth_pct / 100 * 0.1), 2),
            "expected_cashflow_delta_annual": round(base_cashflow * -0.06, 2),
            "risk_shift": round(_clamp(fragility_score + 1.4, 0, 10), 2),
        },
    ]

    alpha_signals = [
        {
            "signal": "Yield-Growth Spread",
            "direction": "positive" if rental_yield_pct >= 4 and annual_growth_pct >= 4 else "neutral",
            "strength": round(_clamp((yield_score + growth_score) / 2, 0, 10), 2),
            "explanation": "Looks for suburbs where income return and capital growth are both resilient.",
        },
        {
            "signal": "Liquidity Compression",
            "direction": "positive" if days_on_market_avg < 30 else "negative",
            "strength": round(_clamp(10 - liquidity_risk, 0, 10), 2),
            "explanation": "Measures market depth by how quickly stock is absorbed.",
        },
        {
            "signal": "Dispersion Penalty",
            "direction": "negative" if volatility_risk > 6 else "positive",
            "strength": round(_clamp(10 - volatility_risk, 0, 10), 2),
            "explanation": "High comparable-sale dispersion can hide micro-market risk.",
        },
    ]

    strategy_fit: list[str] = []
    if rental_yield_pct >= 4.5:
        strategy_fit.append("Cashflow-first investors")
    if annual_growth_pct >= 6:
        strategy_fit.append("Growth-biased long hold")
    if fragility_score <= 4.5:
        strategy_fit.append("Conservative buy-and-hold")
    if not strategy_fit:
        strategy_fit.append("Opportunistic investors with active monitoring")

    return {
        "conviction_score": conviction_score,
        "edge_score": edge_score,
        "moat_score": moat_score,
        "fragility_score": fragility_score,
        "data_depth_score": data_depth_score,
        "market_regime": market_regime,
        "risk_breakdown": {
            "liquidity_risk": round(liquidity_risk, 2),
            "price_volatility_risk": round(volatility_risk, 2),
            "downside_gap_risk": round(downside_risk, 2),
            "macro_stress_risk": round(macro_stress_risk, 2),
        },
        "scenario_matrix": scenario_matrix,
        "alpha_signals": alpha_signals,
        "strategy_fit": strategy_fit,
    }
