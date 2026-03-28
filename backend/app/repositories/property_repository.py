from dataclasses import dataclass

from sqlalchemy import MetaData, Select, Table, desc, func, select
from sqlalchemy.orm import Session

from backend.app.db.models import Property, Transaction


@dataclass
class SuburbMetricSnapshot:
    suburb: str
    state: str
    postcode: str
    as_of_date: object | None
    median_price: float | None
    annual_growth_pct: float | None
    rental_yield_pct: float | None
    days_on_market_avg: int | None
    sales_count: int | None


class PropertyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_properties(self, suburb: str | None, limit: int = 50) -> list[Property]:
        query: Select[tuple[Property]] = select(Property).order_by(Property.id.desc()).limit(limit)
        if suburb:
            query = (
                select(Property)
                .where(Property.suburb.ilike(f"%{suburb}%"))
                .order_by(Property.id.desc())
                .limit(limit)
            )
        return list(self.db.scalars(query).all())

    def get_property(self, property_id: int) -> Property | None:
        return self.db.get(Property, property_id)

    def _suburb_metrics_table(self) -> Table:
        metadata = MetaData()
        return Table("suburb_metrics", metadata, autoload_with=self.db.get_bind())

    @staticmethod
    def _metric_column(table: Table, name: str, fallback_name: str | None = None):
        if name in table.c:
            return table.c[name]
        if fallback_name and fallback_name in table.c:
            return table.c[fallback_name]
        return None

    @staticmethod
    def _to_float(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: object) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _snapshot_from_row(self, row: object) -> SuburbMetricSnapshot:
        mapping = row._mapping
        return SuburbMetricSnapshot(
            suburb=str(mapping.get("suburb", "") or ""),
            state=str(mapping.get("state", "") or ""),
            postcode=str(mapping.get("postcode", "") or ""),
            as_of_date=mapping.get("as_of_date"),
            median_price=self._to_float(mapping.get("median_price")),
            annual_growth_pct=self._to_float(mapping.get("annual_growth_pct")),
            rental_yield_pct=self._to_float(mapping.get("rental_yield_pct")),
            days_on_market_avg=self._to_int(mapping.get("days_on_market_avg")),
            sales_count=self._to_int(mapping.get("sales_count")),
        )

    def latest_suburb_metrics(self, limit: int = 20) -> list[SuburbMetricSnapshot]:
        table = self._suburb_metrics_table()
        as_of_col = self._metric_column(table, "as_of_date", "metric_month")
        growth_col = self._metric_column(table, "annual_growth_pct")
        dom_col = self._metric_column(table, "days_on_market_avg")
        sales_col = self._metric_column(table, "sales_count")

        if as_of_col is None:
            # No date column means we cannot rank by freshness reliably.
            return []

        query = (
            select(
                table.c.suburb.label("suburb"),
                table.c.state.label("state"),
                table.c.postcode.label("postcode"),
                as_of_col.label("as_of_date"),
                table.c.median_price.label("median_price"),
                func.coalesce(growth_col, 0).label("annual_growth_pct") if growth_col is not None else func.cast(0, table.c.median_price.type).label("annual_growth_pct"),
                table.c.rental_yield_pct.label("rental_yield_pct"),
                dom_col.label("days_on_market_avg") if dom_col is not None else func.cast(None, table.c.postcode.type).label("days_on_market_avg"),
                sales_col.label("sales_count") if sales_col is not None else func.cast(None, table.c.postcode.type).label("sales_count"),
            )
            .order_by(desc(as_of_col), desc(func.coalesce(growth_col, 0)) if growth_col is not None else desc(as_of_col))
            .limit(limit)
        )
        rows = self.db.execute(query).all()
        return [self._snapshot_from_row(row) for row in rows]

    def latest_metric_for_postcode(self, postcode: str) -> SuburbMetricSnapshot | None:
        table = self._suburb_metrics_table()
        as_of_col = self._metric_column(table, "as_of_date", "metric_month")
        growth_col = self._metric_column(table, "annual_growth_pct")
        dom_col = self._metric_column(table, "days_on_market_avg")
        sales_col = self._metric_column(table, "sales_count")

        if as_of_col is None:
            return None

        query = (
            select(
                table.c.suburb.label("suburb"),
                table.c.state.label("state"),
                table.c.postcode.label("postcode"),
                as_of_col.label("as_of_date"),
                table.c.median_price.label("median_price"),
                func.coalesce(growth_col, 0).label("annual_growth_pct") if growth_col is not None else func.cast(0, table.c.median_price.type).label("annual_growth_pct"),
                table.c.rental_yield_pct.label("rental_yield_pct"),
                dom_col.label("days_on_market_avg") if dom_col is not None else func.cast(None, table.c.postcode.type).label("days_on_market_avg"),
                sales_col.label("sales_count") if sales_col is not None else func.cast(None, table.c.postcode.type).label("sales_count"),
            )
            .where(table.c.postcode == postcode)
            .order_by(desc(as_of_col))
            .limit(1)
        )
        row = self.db.execute(query).first()
        return self._snapshot_from_row(row) if row else None

    def recent_transactions(self, suburb: str, property_type: str, limit: int = 40) -> list[Transaction]:
        query = (
            select(Transaction)
            .join(Property, Property.id == Transaction.property_id)
            .where(Property.suburb == suburb)
            .where(Property.property_type == property_type)
            .order_by(Transaction.sold_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(query).all())
