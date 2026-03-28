from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from backend.app.db.models import Property, SuburbMetric, Transaction


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

    def latest_suburb_metrics(self, limit: int = 20) -> list[SuburbMetric]:
        query = (
            select(SuburbMetric)
            .order_by(desc(SuburbMetric.as_of_date), desc(SuburbMetric.annual_growth_pct))
            .limit(limit)
        )
        return list(self.db.scalars(query).all())

    def latest_metric_for_postcode(self, postcode: str) -> SuburbMetric | None:
        query = (
            select(SuburbMetric)
            .where(SuburbMetric.postcode == postcode)
            .order_by(desc(SuburbMetric.as_of_date))
            .limit(1)
        )
        return self.db.scalars(query).first()

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
