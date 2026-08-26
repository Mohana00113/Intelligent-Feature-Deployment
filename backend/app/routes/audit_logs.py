from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog
from app.schemas import AuditLogResponse

router = APIRouter(tags=["Audit Logs"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    actor: str | None = Query(default=None, max_length=100),
    flag_key: str | None = Query(default=None, max_length=100),
    environment: str | None = Query(default=None, max_length=100),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AuditLog]:
    query = db.query(AuditLog)
    if actor:
        query = query.filter(AuditLog.actor.ilike(f"%{actor}%"))
    if flag_key:
        query = query.filter(AuditLog.flag_key == flag_key)
    if environment:
        query = query.filter(AuditLog.environment == environment.strip().lower())
    if from_date:
        query = query.filter(AuditLog.timestamp >= from_date)
    if to_date:
        # Date-only UI values represent the whole selected calendar day.
        end = to_date + timedelta(days=1) if to_date.time() == datetime.min.time() else to_date
        query = query.filter(AuditLog.timestamp < end)
    return query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).all()