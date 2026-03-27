from datetime import date

from pydantic import BaseModel, Field


class PropertyOut(BaseModel):
    id: int
    address: str
    suburb: str
    state: str
    postcode: str
    property_type: str
    bedrooms: int
    bathrooms: int
    carspaces: int


class ComparableOut(BaseModel):
    property_id: int
    address: str
    sold_price: float
    sold_at: date
    similarity_score: float


class ValuationRequest(BaseModel):
    property_id: int = Field(ge=1)


class ValuationResponse(BaseModel):
    property_id: int
    low_estimate: float
    mid_estimate: float
    high_estimate: float
    confidence_pct: float
    score: float
    reasons: list[str]
    comparables: list[ComparableOut]


class ScenarioImpactOut(BaseModel):
    scenario: str
    forecast_mid_value: float
    expected_cashflow_delta_annual: float
    risk_shift: float


class RiskBreakdownOut(BaseModel):
    liquidity_risk: float
    price_volatility_risk: float
    downside_gap_risk: float
    macro_stress_risk: float


class AlphaSignalOut(BaseModel):
    signal: str
    direction: str
    strength: float
    explanation: str


class DeepAnalysisOut(BaseModel):
    conviction_score: float
    edge_score: float
    moat_score: float
    fragility_score: float
    data_depth_score: float
    market_regime: str
    risk_breakdown: RiskBreakdownOut
    scenario_matrix: list[ScenarioImpactOut]
    alpha_signals: list[AlphaSignalOut]
    strategy_fit: list[str]


class AdvancedValuationResponse(ValuationResponse):
    deep_analysis: DeepAnalysisOut


class ResearchAssumptionsIn(BaseModel):
    lvr_pct: float = Field(default=80, ge=30, le=95)
    interest_rate_pct: float = Field(default=6.2, ge=0.1, le=20)
    loan_years: int = Field(default=30, ge=5, le=40)
    expense_ratio_pct: float = Field(default=22, ge=5, le=70)
    vacancy_weeks: float = Field(default=2, ge=0, le=12)
    exit_cost_pct: float = Field(default=2.5, ge=0, le=10)
    gross_income_annual: float = Field(default=210000, ge=30000, le=2000000)
    other_debt_annual: float = Field(default=18000, ge=0, le=1000000)
    tax_rate_pct: float = Field(default=37, ge=0, le=55)
    depreciation_annual: float = Field(default=6000, ge=0, le=500000)
    hold_years: int = Field(default=5, ge=1, le=30)


class ResearchRequest(BaseModel):
    property_id: int = Field(ge=1)
    assumptions: ResearchAssumptionsIn | None = None


class InterestSensitivityOut(BaseModel):
    rate_pct: float
    annual_debt_service: float
    dscr: float
    annual_cashflow: float


class EquityProjectionOut(BaseModel):
    hold_years: int
    projected_value: float
    projected_loan_balance: float
    net_equity_after_costs: float


class ResearchPackOut(BaseModel):
    valuation_mid: float
    annual_growth_pct: float
    rental_yield_pct: float
    assumptions: ResearchAssumptionsIn
    underwriting: dict[str, float]
    acquisition_costs: dict[str, float]
    tax_position: dict[str, float]
    serviceability: dict[str, float]
    risk_overlays: dict[str, float | str]
    confidence_breakdown: dict[str, float]
    strategy_optimizer: dict[str, float | str]
    interest_sensitivity: list[InterestSensitivityOut]
    scenario_lab: list[ScenarioImpactOut]
    equity_projection: EquityProjectionOut


class PortfolioSimulationItemIn(BaseModel):
    purchase_price: float = Field(gt=0)
    lvr_pct: float = Field(default=80, ge=0, le=95)
    interest_rate_pct: float = Field(default=6.2, ge=0.1, le=20)
    loan_years: int = Field(default=30, ge=5, le=40)
    annual_rent: float = Field(gt=0)
    annual_expenses: float = Field(ge=0)


class PortfolioRiskRequest(BaseModel):
    items: list[PortfolioSimulationItemIn] = Field(min_length=1, max_length=200)


class PortfolioRiskResponse(BaseModel):
    holdings: int
    aggregate_value: float
    aggregate_debt: float
    aggregate_noi: float
    aggregate_cashflow: float
    weighted_dscr: float
    concentration_risk_score: float
    stress_test_rate_up_150bps_cashflow: float


class WaitlistRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    source: str = Field(default="landing", min_length=1, max_length=50)


class WaitlistResponse(BaseModel):
    success: bool
    already_exists: bool
    message: str


class SuburbRankingOut(BaseModel):
    suburb: str
    state: str
    postcode: str
    investment_score: float
    median_price: float
    annual_growth_pct: float
    rental_yield_pct: float


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    full_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=255)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    is_admin: bool


class WatchlistCreateRequest(BaseModel):
    property_id: int = Field(ge=1)
    note: str | None = None


class WatchlistItemOut(BaseModel):
    id: int
    property_id: int
    note: str | None


class SaveReportRequest(BaseModel):
    property_id: int = Field(ge=1)
    title: str = Field(min_length=3, max_length=255)
    report_json: str = Field(min_length=2)


class SavedReportOut(BaseModel):
    id: int
    property_id: int
    title: str


class PortfolioCreateRequest(BaseModel):
    property_id: int = Field(ge=1)
    purchase_price: float = Field(gt=0)
    purchase_date: date


class PortfolioItemOut(BaseModel):
    id: int
    property_id: int
    purchase_price: float
    purchase_date: date


class WaitlistNoteCreateRequest(BaseModel):
    signup_id: int = Field(ge=1)
    status: str = Field(min_length=2, max_length=30)
    note: str | None = None


class WaitlistNoteOut(BaseModel):
    id: int
    signup_id: int
    status: str
    note: str | None


class ModelEvaluationCreateRequest(BaseModel):
    model_name: str = Field(min_length=2, max_length=100)
    model_version: str = Field(min_length=1, max_length=50)
    split_name: str = Field(min_length=1, max_length=50)
    mae: float | None = None
    rmse: float | None = None
    mape: float | None = None
    drift_score: float | None = None


class ModelEvaluationOut(BaseModel):
    id: int
    model_name: str
    model_version: str
    split_name: str
    mae: float | None
    rmse: float | None
    mape: float | None
    drift_score: float | None
