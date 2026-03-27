from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.property_repository import PropertyRepository
from backend.app.schemas import PropertyOut

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=list[PropertyOut])
def list_properties(
    suburb: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[PropertyOut]:
    repo = PropertyRepository(db)
    rows = repo.list_properties(suburb=suburb, limit=limit)
    return [
        PropertyOut(
            id=row.id,
            address=row.address,
            suburb=row.suburb,
            state=row.state,
            postcode=row.postcode,
            property_type=row.property_type,
            bedrooms=row.bedrooms,
            bathrooms=row.bathrooms,
            carspaces=row.carspaces,
        )
        for row in rows
    ]
