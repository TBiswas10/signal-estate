from dataclasses import dataclass
from statistics import mean

from backend.app.db.models import Property, Transaction


@dataclass
class ComparableResult:
    property_id: int
    address: str
    sold_price: float
    sold_at: str
    similarity_score: float


def _similarity_score(target: Property, comp: Property) -> float:
    bed_gap = abs(target.bedrooms - comp.bedrooms)
    bath_gap = abs(target.bathrooms - comp.bathrooms)
    car_gap = abs(target.carspaces - comp.carspaces)
    raw_score = 1 - ((bed_gap * 0.15) + (bath_gap * 0.15) + (car_gap * 0.05))
    return max(0.0, round(raw_score, 2))


def build_valuation(target: Property, comparable_pairs: list[tuple[Property, Transaction]]) -> dict:
    if not comparable_pairs:
        return {
            "low": 0.0,
            "mid": 0.0,
            "high": 0.0,
            "confidence": 0.0,
            "comparables": [],
            "reason_codes": ["No comparable sales available yet."],
        }

    scored: list[tuple[float, float, Property, Transaction]] = []
    for comp_property, tx in comparable_pairs:
        score = _similarity_score(target, comp_property)
        scored.append((score, tx.sale_price, comp_property, tx))

    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:8]
    weighted_prices = [sale_price * (0.5 + similarity) for similarity, sale_price, _, _ in top]
    center_estimate = round(mean(weighted_prices), 2)

    return {
        "low": round(center_estimate * 0.93, 2),
        "mid": center_estimate,
        "high": round(center_estimate * 1.07, 2),
        "confidence": round(min(95.0, 55.0 + (len(top) * 4.5)), 2),
        "comparables": [
            {
                "property_id": comp_property.id,
                "address": comp_property.address,
                "sold_price": sale_price,
                "sold_at": tx.sold_at,
                "similarity_score": similarity,
            }
            for similarity, sale_price, comp_property, tx in top
        ],
        "reason_codes": [
            f"{len(top)} nearby comparable sales included.",
            "Estimation weighted toward bedroom/bathroom/carspace similarity.",
        ],
    }
