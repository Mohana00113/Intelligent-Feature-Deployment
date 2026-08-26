from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.cleanup import find_cleanup_suggestions, mark_cleanup_reviewed
from app.database import get_db

router = APIRouter(tags=["Cleanup"])


@router.get("/suggestions")
def cleanup_suggestions(days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)) -> list[dict]:
    return find_cleanup_suggestions(db, days)


@router.post("/suggestions/{flag_key}/review")
def review_cleanup_suggestion(flag_key: str, db: Session = Depends(get_db), x_actor: str | None = Header(default=None)) -> dict:
    review = mark_cleanup_reviewed(db, flag_key, x_actor or "system")
    return {"flag_key": review.flag_key, "reviewed": True, "reviewed_at": review.reviewed_at, "reviewed_by": review.reviewed_by}