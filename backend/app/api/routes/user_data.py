from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.models import PortfolioItem, Property, SavedReport, User, WatchlistItem
from backend.app.db.session import get_db
from backend.app.schemas import (
    PortfolioCreateRequest,
    PortfolioItemOut,
    SaveReportRequest,
    SavedReportOut,
    WatchlistCreateRequest,
    WatchlistItemOut,
)

router = APIRouter(prefix="/user", tags=["user-workflows"])


@router.post("/watchlist", response_model=WatchlistItemOut)
def add_watchlist_item(
    payload: WatchlistCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WatchlistItemOut:
    property_exists = db.get(Property, payload.property_id)
    if not property_exists:
        raise HTTPException(status_code=404, detail="Property not found")

    existing = db.scalars(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == current_user.id)
        .where(WatchlistItem.property_id == payload.property_id)
    ).first()
    if existing:
        return WatchlistItemOut(id=existing.id, property_id=existing.property_id, note=existing.note)

    item = WatchlistItem(user_id=current_user.id, property_id=payload.property_id, note=payload.note)
    db.add(item)
    db.commit()
    db.refresh(item)
    return WatchlistItemOut(id=item.id, property_id=item.property_id, note=item.note)


@router.get("/watchlist", response_model=list[WatchlistItemOut])
def list_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WatchlistItemOut]:
    items = db.scalars(select(WatchlistItem).where(WatchlistItem.user_id == current_user.id)).all()
    return [WatchlistItemOut(id=item.id, property_id=item.property_id, note=item.note) for item in items]


@router.delete("/watchlist/{item_id}")
def remove_watchlist_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    db.execute(
        delete(WatchlistItem)
        .where(WatchlistItem.id == item_id)
        .where(WatchlistItem.user_id == current_user.id)
    )
    db.commit()
    return {"success": True}


@router.post("/reports", response_model=SavedReportOut)
def save_report(
    payload: SaveReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedReportOut:
    report = SavedReport(
        user_id=current_user.id,
        property_id=payload.property_id,
        title=payload.title,
        report_json=payload.report_json,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return SavedReportOut(id=report.id, property_id=report.property_id, title=report.title)


@router.get("/reports", response_model=list[SavedReportOut])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SavedReportOut]:
    reports = db.scalars(select(SavedReport).where(SavedReport.user_id == current_user.id)).all()
    return [SavedReportOut(id=report.id, property_id=report.property_id, title=report.title) for report in reports]


@router.post("/portfolio", response_model=PortfolioItemOut)
def add_portfolio_item(
    payload: PortfolioCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PortfolioItemOut:
    item = PortfolioItem(
        user_id=current_user.id,
        property_id=payload.property_id,
        purchase_price=payload.purchase_price,
        purchase_date=payload.purchase_date,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return PortfolioItemOut(
        id=item.id,
        property_id=item.property_id,
        purchase_price=item.purchase_price,
        purchase_date=item.purchase_date,
    )


@router.get("/portfolio", response_model=list[PortfolioItemOut])
def list_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PortfolioItemOut]:
    items = db.scalars(select(PortfolioItem).where(PortfolioItem.user_id == current_user.id)).all()
    return [
        PortfolioItemOut(
            id=item.id,
            property_id=item.property_id,
            purchase_price=item.purchase_price,
            purchase_date=item.purchase_date,
        )
        for item in items
    ]
