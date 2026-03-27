from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_admin_user
from backend.app.db.models import User, WaitlistNote, WaitlistSignup
from backend.app.db.session import get_db
from backend.app.schemas import WaitlistNoteCreateRequest, WaitlistNoteOut, WaitlistResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/waitlist", response_model=list[WaitlistResponse])
def list_waitlist(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> list[WaitlistResponse]:
    rows = db.scalars(select(WaitlistSignup)).all()
    return [
        WaitlistResponse(
            success=True,
            already_exists=False,
            message=f"{row.email} ({row.source})",
        )
        for row in rows
    ]


@router.post("/waitlist/notes", response_model=WaitlistNoteOut)
def upsert_waitlist_note(
    payload: WaitlistNoteCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> WaitlistNoteOut:
    note = db.scalars(select(WaitlistNote).where(WaitlistNote.signup_id == payload.signup_id)).first()
    if note:
        note.status = payload.status
        note.note = payload.note
    else:
        note = WaitlistNote(signup_id=payload.signup_id, status=payload.status, note=payload.note)
        db.add(note)

    db.commit()
    db.refresh(note)
    return WaitlistNoteOut(id=note.id, signup_id=note.signup_id, status=note.status, note=note.note)
