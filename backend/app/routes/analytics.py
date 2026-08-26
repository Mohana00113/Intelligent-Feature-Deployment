from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics import get_evaluation_metrics
from app.database import get_db

router = APIRouter(tags=["Evaluation Analytics"])


@router.get("/flags/{flag_key}/evaluations")
def evaluation_metrics(
    flag_key: str,
    environment: str = Query(default="development", min_length=1, max_length=100),
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return {"flag_key": flag_key, "environment": environment, "days": days, "points": get_evaluation_metrics(db, flag_key, days, environment)}