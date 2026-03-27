from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String(255), index=True)
    suburb: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(10), index=True)
    postcode: Mapped[str] = mapped_column(String(10), index=True)
    property_type: Mapped[str] = mapped_column(String(30), index=True)
    bedrooms: Mapped[int] = mapped_column(Integer)
    bathrooms: Mapped[int] = mapped_column(Integer)
    carspaces: Mapped[int] = mapped_column(Integer, default=0)
    land_area_sqm: Mapped[float | None] = mapped_column(Float, nullable=True)
    building_area_sqm: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    listings: Mapped[list["Listing"]] = relationship(back_populates="property")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="property")


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    listing_status: Mapped[str] = mapped_column(String(20), index=True)
    price_ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    listed_at: Mapped[date] = mapped_column(Date)
    days_on_market: Mapped[int | None] = mapped_column(Integer, nullable=True)

    property: Mapped[Property] = relationship(back_populates="listings")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    sale_price: Mapped[float] = mapped_column(Float, index=True)
    sold_at: Mapped[date] = mapped_column(Date, index=True)

    property: Mapped[Property] = relationship(back_populates="transactions")


class SuburbMetric(Base):
    __tablename__ = "suburb_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    suburb: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(10), index=True)
    postcode: Mapped[str] = mapped_column(String(10), index=True)
    metric_month: Mapped[date] = mapped_column(Date, index=True)
    median_price: Mapped[float] = mapped_column(Float)
    annual_growth_pct: Mapped[float] = mapped_column(Float)
    rental_yield_pct: Mapped[float] = mapped_column(Float)
    days_on_market_avg: Mapped[int] = mapped_column(Integer)
    sales_count: Mapped[int] = mapped_column(Integer)


class ABSIndicator(Base):
    __tablename__ = "abs_indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    postcode: Mapped[str] = mapped_column(String(10), index=True)
    census_year: Mapped[int] = mapped_column(Integer, index=True)
    median_household_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    unemployment_rate_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class WaitlistSignup(Base):
    __tablename__ = "waitlist_signups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(50), default="landing")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SavedReport(Base):
    __tablename__ = "saved_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    report_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    purchase_price: Mapped[float] = mapped_column(Float)
    purchase_date: Mapped[date] = mapped_column(Date)
    current_estimated_value: Mapped[float | None] = mapped_column(Float, nullable=True)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pipeline_name: Mapped[str] = mapped_column(String(100), index=True)
    source_name: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    freshness_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String(100), index=True)
    model_version: Mapped[str] = mapped_column(String(50), index=True)
    split_name: Mapped[str] = mapped_column(String(50), index=True)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    drift_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WaitlistNote(Base):
    __tablename__ = "waitlist_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    signup_id: Mapped[int] = mapped_column(ForeignKey("waitlist_signups.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
