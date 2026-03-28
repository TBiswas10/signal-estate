from datetime import date, timedelta
import random

from backend.app.db.base import Base
from backend.app.db.models import ABSIndicator, Property, SuburbMetric, Transaction
from backend.app.db.session import SessionLocal, engine


def run() -> None:
    random.seed(42)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    suburb_specs = [
        ("Parramatta", "NSW", "2150", 1120000, 5.8, 4.2, 29, 220),
        ("Newtown", "NSW", "2042", 1510000, 4.4, 3.6, 31, 190),
        ("Fortitude Valley", "QLD", "4006", 815000, 6.9, 5.1, 24, 250),
        ("South Brisbane", "QLD", "4101", 902000, 7.4, 4.8, 22, 280),
        ("Richmond", "VIC", "3121", 1380000, 3.9, 3.4, 33, 205),
        ("Footscray", "VIC", "3011", 842000, 6.3, 4.6, 28, 230),
        ("West End", "QLD", "4101", 1035000, 6.1, 4.4, 27, 210),
        ("Leederville", "WA", "6007", 955000, 5.3, 4.0, 30, 175),
        ("North Adelaide", "SA", "5006", 980000, 4.8, 4.1, 32, 165),
        ("Hobart CBD", "TAS", "7000", 760000, 5.6, 4.7, 26, 140),
    ]

    streets = [
        "King St",
        "High St",
        "River Rd",
        "Park Ave",
        "Market Ln",
        "Victoria St",
        "Oxford St",
        "Boundary St",
        "Harbour View",
        "Union Rd",
    ]

    db = SessionLocal()
    try:
        properties: list[Property] = []
        for suburb, state, postcode, median, growth, _, _, _ in suburb_specs:
            for i in range(18):
                prop_type = "apartment" if i % 4 == 0 else "house"
                bedrooms = random.choice([2, 3, 3, 4, 4, 5])
                bathrooms = 1 if bedrooms <= 2 else random.choice([2, 2, 3])
                carspaces = random.choice([0, 1, 1, 2, 2, 3])
                land_area = random.randint(120, 700) if prop_type == "house" else random.randint(55, 180)
                building_area = max(45, int(land_area * random.uniform(0.55, 0.9)))

                growth_factor = 1 + (growth / 100) * random.uniform(0.3, 1.2)
                address = f"{10 + i} {random.choice(streets)}"
                properties.append(
                    Property(
                        address=address,
                        suburb=suburb,
                        state=state,
                        postcode=postcode,
                        property_type=prop_type,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        carspaces=carspaces,
                        land_area_sqm=float(land_area),
                        building_area_sqm=float(building_area),
                    )
                )

        db.add_all(properties)
        db.flush()

        transactions: list[Transaction] = []
        today = date(2026, 3, 1)
        for prop in properties:
            suburb_spec = next((row for row in suburb_specs if row[0] == prop.suburb), None)
            if not suburb_spec:
                continue
            median = suburb_spec[3]
            for j in range(3):
                jitter = random.uniform(0.74, 1.29)
                bedrooms_uplift = 1 + max(0, prop.bedrooms - 2) * 0.07
                base_price = median * jitter * bedrooms_uplift
                sold_price = round(base_price, 2)
                sold_at = today - timedelta(days=random.randint(30 + j * 80, 680 + j * 120))
                transactions.append(Transaction(property_id=prop.id, sale_price=sold_price, sold_at=sold_at))
        db.add_all(transactions)

        metrics: list[SuburbMetric] = []
        for suburb, state, postcode, median, growth, yield_pct, dom, sales in suburb_specs:
            for month_offset in range(0, 7):
                metric_date = date(2025, 9, 1) + timedelta(days=30 * month_offset)
                trend = 1 + (growth / 100) * (month_offset / 12)
                metrics.append(
                    SuburbMetric(
                        suburb=suburb,
                        state=state,
                        postcode=postcode,
                        as_of_date=metric_date,
                        median_price=round(median * trend * random.uniform(0.97, 1.03), 2),
                        annual_growth_pct=round(growth + random.uniform(-1.4, 1.5), 2),
                        rental_yield_pct=round(yield_pct + random.uniform(-0.4, 0.5), 2),
                        days_on_market_avg=max(14, int(dom + random.randint(-8, 8))),
                    )
                )
        db.add_all(metrics)

        abs_rows: list[ABSIndicator] = []
        for _, _, postcode, _, _, _, _, _ in suburb_specs:
            abs_rows.append(
                ABSIndicator(
                    postcode=postcode,
                    census_year=2021,
                    median_household_income=round(random.uniform(1800, 2950), 2),
                    unemployment_rate_pct=round(random.uniform(2.7, 6.9), 2),
                    population=random.randint(16000, 56000),
                    notes="Synthetic ABS profile for full-demo mode.",
                )
            )
        db.add_all(abs_rows)

        db.commit()
        print(
            f"Seed complete: properties={len(properties)}, transactions={len(transactions)}, suburb_metrics={len(metrics)}, abs_rows={len(abs_rows)}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
