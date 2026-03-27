from pathlib import Path

import pandas as pd


def read_listing_csv(csv_path: str) -> list[dict]:
    path = Path(csv_path)
    if not path.exists():
        return []

    frame = pd.read_csv(path)
    required = {"address", "suburb", "state", "postcode", "property_type", "bedrooms", "bathrooms"}
    missing = required.difference(set(frame.columns))
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")

    records = frame.fillna("").to_dict(orient="records")
    return [dict(record) for record in records]
