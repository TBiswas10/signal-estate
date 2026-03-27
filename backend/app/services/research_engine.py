from math import pow


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _monthly_payment(principal: float, annual_rate_pct: float, years: int) -> float:
    months = years * 12
    if months <= 0:
        return 0.0
    monthly_rate = annual_rate_pct / 100 / 12
    if monthly_rate <= 0:
        return principal / months
    growth = pow(1 + monthly_rate, months)
    return principal * monthly_rate * growth / (growth - 1)


def _remaining_balance(principal: float, annual_rate_pct: float, years: int, paid_months: int) -> float:
    total_months = years * 12
    paid_months = max(0, min(total_months, paid_months))
    if total_months == 0:
        return 0.0
    monthly_rate = annual_rate_pct / 100 / 12
    if monthly_rate <= 0:
        return principal * max(0.0, (total_months - paid_months) / total_months)
    growth_total = pow(1 + monthly_rate, total_months)
    growth_paid = pow(1 + monthly_rate, paid_months)
    return principal * (growth_total - growth_paid) / (growth_total - 1)


def _estimate_stamp_duty(state: str, purchase_price: float) -> float:
    s = (state or "").upper()
    if s == "NSW":
        return purchase_price * 0.040 + 1800
    if s == "VIC":
        return purchase_price * 0.050 + 1300
    if s == "QLD":
        return purchase_price * 0.036 + 1100
    if s == "WA":
        return purchase_price * 0.044 + 1000
    if s == "SA":
        return purchase_price * 0.045 + 1000
    return purchase_price * 0.042 + 1200


def build_research_pack(
    *,
    valuation_mid: float,
    annual_growth_pct: float,
    rental_yield_pct: float,
    state: str,
    confidence_pct: float,
    comparable_count: int,
    assumptions: dict,
) -> dict:
    lvr_pct = _clamp(float(assumptions.get("lvr_pct", 80)), 30, 95)
    interest_rate_pct = _clamp(float(assumptions.get("interest_rate_pct", 6.2)), 0.1, 20)
    loan_years = int(_clamp(float(assumptions.get("loan_years", 30)), 5, 40))
    expense_ratio_pct = _clamp(float(assumptions.get("expense_ratio_pct", 22)), 5, 70)
    vacancy_weeks = _clamp(float(assumptions.get("vacancy_weeks", 2)), 0, 12)
    exit_cost_pct = _clamp(float(assumptions.get("exit_cost_pct", 2.5)), 0, 10)
    gross_income_annual = _clamp(float(assumptions.get("gross_income_annual", 210000)), 30000, 2000000)
    other_debt_annual = _clamp(float(assumptions.get("other_debt_annual", 18000)), 0, 1000000)
    tax_rate_pct = _clamp(float(assumptions.get("tax_rate_pct", 37)), 0, 55)
    depreciation_annual = _clamp(float(assumptions.get("depreciation_annual", 6000)), 0, 500000)
    hold_years = int(_clamp(float(assumptions.get("hold_years", 5)), 1, 30))

    purchase_price = max(float(valuation_mid), 0.0)
    loan_amount = purchase_price * (lvr_pct / 100)
    monthly_payment = _monthly_payment(loan_amount, interest_rate_pct, loan_years)
    annual_debt_service = monthly_payment * 12

    annual_gross_rent = purchase_price * (rental_yield_pct / 100)
    occupied_ratio = max(0.0, 1 - (vacancy_weeks / 52))
    effective_rent = annual_gross_rent * occupied_ratio
    operating_expenses = effective_rent * (expense_ratio_pct / 100)
    noi = effective_rent - operating_expenses

    dscr = noi / annual_debt_service if annual_debt_service > 0 else 0.0
    annual_cashflow = noi - annual_debt_service
    monthly_cashflow = annual_cashflow / 12

    denominator = occupied_ratio * (1 - (expense_ratio_pct / 100))
    break_even_rent_annual = (annual_debt_service / denominator) if denominator > 0 else 0.0
    break_even_rent_weekly = break_even_rent_annual / 52 if break_even_rent_annual > 0 else 0.0

    cap_rate_pct = (noi / purchase_price * 100) if purchase_price > 0 else 0.0
    net_yield_pct = (annual_cashflow / purchase_price * 100) if purchase_price > 0 else 0.0

    stamp_duty = _estimate_stamp_duty(state=state, purchase_price=purchase_price)
    acquisition_costs = {
        "stamp_duty": round(stamp_duty, 2),
        "transfer_and_reg": round(purchase_price * 0.0022, 2),
        "conveyancing": 1800.0,
        "building_and_pest": 780.0,
        "loan_setup": 650.0,
        "buyers_agent_fee": round(purchase_price * 0.012, 2),
    }
    total_acquisition_cost = sum(acquisition_costs.values())
    acquisition_costs["total"] = round(total_acquisition_cost, 2)

    taxable_profit = annual_cashflow - depreciation_annual
    tax_shield = 0.0
    if taxable_profit < 0:
        tax_shield = abs(taxable_profit) * (tax_rate_pct / 100)
    after_tax_cashflow = annual_cashflow + tax_shield

    projected_value = purchase_price * pow(1 + annual_growth_pct / 100, hold_years)
    projected_balance = _remaining_balance(loan_amount, interest_rate_pct, loan_years, hold_years * 12)
    net_sale_after_costs = projected_value * (1 - exit_cost_pct / 100)
    net_equity_after_costs = max(0.0, net_sale_after_costs - projected_balance)
    gross_capital_gain = max(0.0, projected_value - purchase_price)
    discounted_gain = gross_capital_gain * 0.5 if hold_years >= 1 else gross_capital_gain
    estimated_cgt = discounted_gain * (tax_rate_pct / 100)

    serviceability_buffer_rate = interest_rate_pct + 3.0
    stress_debt_service = _monthly_payment(loan_amount, serviceability_buffer_rate, loan_years) * 12
    net_surplus_income = gross_income_annual - other_debt_annual - stress_debt_service
    serviceability_ratio = net_surplus_income / gross_income_annual if gross_income_annual > 0 else 0.0

    sensitivity_rows = []
    for delta in (-1.0, -0.5, 0.0, 0.5, 1.5):
        rate = _clamp(interest_rate_pct + delta, 0.1, 20)
        debt_service = _monthly_payment(loan_amount, rate, loan_years) * 12
        row_dscr = noi / debt_service if debt_service > 0 else 0.0
        row_cashflow = noi - debt_service
        sensitivity_rows.append(
            {
                "rate_pct": round(rate, 2),
                "annual_debt_service": round(debt_service, 2),
                "dscr": round(row_dscr, 3),
                "annual_cashflow": round(row_cashflow, 2),
            }
        )

    scenario_lab = [
        {
            "scenario": "Base Case",
            "forecast_mid_value": round(projected_value, 2),
            "expected_cashflow_delta_annual": round(annual_cashflow * 0.05, 2),
            "risk_shift": round(_clamp((10 - dscr * 2), 0, 10), 2),
        },
        {
            "scenario": "Rent +5% / Rate +50bps",
            "forecast_mid_value": round(projected_value * 1.01, 2),
            "expected_cashflow_delta_annual": round((annual_cashflow * 1.05) - (annual_debt_service * 0.06), 2),
            "risk_shift": round(_clamp((10 - dscr * 2) + 0.5, 0, 10), 2),
        },
        {
            "scenario": "Rent -5% / Rate +150bps",
            "forecast_mid_value": round(projected_value * 0.965, 2),
            "expected_cashflow_delta_annual": round((annual_cashflow * 0.85) - (annual_debt_service * 0.15), 2),
            "risk_shift": round(_clamp((10 - dscr * 2) + 2.2, 0, 10), 2),
        },
    ]

    risk_overlays = {
        "liquidity_risk_score": round(_clamp(10 - (annual_growth_pct + rental_yield_pct), 1, 9.5), 2),
        "vacancy_risk_score": round(_clamp(vacancy_weeks / 1.4, 1, 9.5), 2),
        "insurance_stress_score": round(_clamp((purchase_price / 1000000) * 4.5, 1, 9.5), 2),
        "climate_exposure_flag": "review-required" if state.upper() in {"QLD", "NT", "WA"} else "normal",
    }

    confidence_breakdown = {
        "comp_coverage": round(_clamp(comparable_count / 8 * 100, 0, 100), 2),
        "data_freshness": 88.0,
        "market_stability": round(_clamp(100 - risk_overlays["liquidity_risk_score"] * 7.5, 10, 95), 2),
        "model_confidence": round(_clamp(confidence_pct, 0, 100), 2),
    }

    growth_mode_score = round(_clamp((annual_growth_pct * 0.8) + (100 - risk_overlays["liquidity_risk_score"] * 4), 0, 100), 2)
    cashflow_mode_score = round(_clamp((dscr * 40) + (net_yield_pct * 6), 0, 100), 2)
    balanced_score = round((growth_mode_score + cashflow_mode_score) / 2, 2)
    recommended_mode = "growth" if growth_mode_score > cashflow_mode_score + 5 else "cashflow" if cashflow_mode_score > growth_mode_score + 5 else "balanced"

    return {
        "valuation_mid": round(purchase_price, 2),
        "annual_growth_pct": round(annual_growth_pct, 2),
        "rental_yield_pct": round(rental_yield_pct, 2),
        "assumptions": {
            "lvr_pct": round(lvr_pct, 2),
            "interest_rate_pct": round(interest_rate_pct, 2),
            "loan_years": loan_years,
            "expense_ratio_pct": round(expense_ratio_pct, 2),
            "vacancy_weeks": round(vacancy_weeks, 2),
            "exit_cost_pct": round(exit_cost_pct, 2),
            "gross_income_annual": round(gross_income_annual, 2),
            "other_debt_annual": round(other_debt_annual, 2),
            "tax_rate_pct": round(tax_rate_pct, 2),
            "depreciation_annual": round(depreciation_annual, 2),
            "hold_years": hold_years,
        },
        "underwriting": {
            "gross_rent_annual": round(annual_gross_rent, 2),
            "noi_annual": round(noi, 2),
            "annual_debt_service": round(annual_debt_service, 2),
            "dscr": round(dscr, 3),
            "annual_cashflow": round(annual_cashflow, 2),
            "monthly_cashflow": round(monthly_cashflow, 2),
            "break_even_rent_weekly": round(break_even_rent_weekly, 2),
            "cap_rate_pct": round(cap_rate_pct, 2),
            "net_yield_pct": round(net_yield_pct, 2),
        },
        "acquisition_costs": acquisition_costs,
        "tax_position": {
            "taxable_profit_before_shield": round(taxable_profit, 2),
            "tax_shield": round(tax_shield, 2),
            "after_tax_cashflow": round(after_tax_cashflow, 2),
            "estimated_cgt_on_exit": round(estimated_cgt, 2),
        },
        "serviceability": {
            "assessment_rate_pct": round(serviceability_buffer_rate, 2),
            "assessment_debt_service": round(stress_debt_service, 2),
            "net_surplus_income": round(net_surplus_income, 2),
            "serviceability_ratio": round(serviceability_ratio, 3),
        },
        "risk_overlays": risk_overlays,
        "confidence_breakdown": confidence_breakdown,
        "strategy_optimizer": {
            "recommended_mode": recommended_mode,
            "growth_score": growth_mode_score,
            "cashflow_score": cashflow_mode_score,
            "balanced_score": balanced_score,
        },
        "interest_sensitivity": sensitivity_rows,
        "scenario_lab": scenario_lab,
        "equity_projection": {
            "hold_years": hold_years,
            "projected_value": round(projected_value, 2),
            "projected_loan_balance": round(projected_balance, 2),
            "net_equity_after_costs": round(net_equity_after_costs, 2),
        },
    }


def simulate_portfolio_risk(items: list[dict]) -> dict:
    if not items:
        return {
            "holdings": 0,
            "aggregate_value": 0.0,
            "aggregate_debt": 0.0,
            "aggregate_noi": 0.0,
            "aggregate_cashflow": 0.0,
            "weighted_dscr": 0.0,
            "concentration_risk_score": 0.0,
            "stress_test_rate_up_150bps_cashflow": 0.0,
        }

    total_value = 0.0
    total_debt = 0.0
    total_noi = 0.0
    total_debt_service = 0.0
    total_cashflow = 0.0
    stress_cashflow = 0.0
    largest_asset = 0.0

    for item in items:
        purchase_price = float(item.get("purchase_price", 0))
        lvr_pct = _clamp(float(item.get("lvr_pct", 80)), 0, 95)
        rate = _clamp(float(item.get("interest_rate_pct", 6.2)), 0.1, 20)
        years = int(_clamp(float(item.get("loan_years", 30)), 5, 40))
        annual_rent = float(item.get("annual_rent", 0))
        annual_expenses = float(item.get("annual_expenses", 0))

        debt = purchase_price * (lvr_pct / 100)
        debt_service = _monthly_payment(debt, rate, years) * 12
        stressed_debt_service = _monthly_payment(debt, rate + 1.5, years) * 12
        noi = annual_rent - annual_expenses
        cashflow = noi - debt_service

        total_value += purchase_price
        total_debt += debt
        total_noi += noi
        total_debt_service += debt_service
        total_cashflow += cashflow
        stress_cashflow += noi - stressed_debt_service
        largest_asset = max(largest_asset, purchase_price)

    weighted_dscr = total_noi / total_debt_service if total_debt_service > 0 else 0.0
    concentration_ratio = (largest_asset / total_value) if total_value > 0 else 0.0
    concentration_risk_score = _clamp(concentration_ratio * 10, 0, 10)

    return {
        "holdings": len(items),
        "aggregate_value": round(total_value, 2),
        "aggregate_debt": round(total_debt, 2),
        "aggregate_noi": round(total_noi, 2),
        "aggregate_cashflow": round(total_cashflow, 2),
        "weighted_dscr": round(weighted_dscr, 3),
        "concentration_risk_score": round(concentration_risk_score, 2),
        "stress_test_rate_up_150bps_cashflow": round(stress_cashflow, 2),
    }
