import argparse

from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.ingestion.pipeline import run_abs_ingestion, run_manual_listing_ingestion


def main() -> None:
    parser = argparse.ArgumentParser(description="Run initial ingestion tasks")
    parser.add_argument("--csv", type=str, default="", help="Optional property CSV path")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        abs_count = run_abs_ingestion(db)
        csv_count = run_manual_listing_ingestion(db, args.csv) if args.csv else 0
        print(f"ABS rows loaded: {abs_count}")
        print(f"CSV properties loaded: {csv_count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
