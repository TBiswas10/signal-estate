from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import WaitlistSignup
from backend.app.db.session import get_db
from backend.app.schemas import WaitlistRequest, WaitlistResponse

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


@router.post("", response_model=WaitlistResponse)
def join_waitlist(payload: WaitlistRequest, db: Session = Depends(get_db)) -> WaitlistResponse:
    email = payload.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Invalid email format")

    existing = db.scalars(select(WaitlistSignup).where(WaitlistSignup.email == email)).first()
    if existing:
        return WaitlistResponse(
            success=True,
            already_exists=True,
            message="You are already on the waitlist.",
        )

    db.add(WaitlistSignup(email=email, source=payload.source.strip().lower()))
    db.commit()

    return WaitlistResponse(
        success=True,
        already_exists=False,
        message="You are in. Private beta invitations roll out in waves.",
    )
