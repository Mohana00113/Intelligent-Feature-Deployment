from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog, CleanupReview, Environment, FeatureFlag, FlagEnvironmentOverride


def _effective_state(db: Session, flag: FeatureFlag, environment: Environment) -> dict[str, Any]:
    override = db.query(FlagEnvironmentOverride).filter(
        FlagEnvironmentOverride.flag_id == flag.id,
        FlagEnvironmentOverride.environment_id == environment.id,
    ).first()
    if override is not None:
        return {"enabled": bool(override.enabled), "rollout_percentage": int(override.rollout_percentage or 0)}
    return {"enabled": bool(flag.enabled), "rollout_percentage": int(flag.rollout_percentage or 0)}


def find_cleanup_suggestions(db: Session, days: int = 30) -> list[dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    environments = db.query(Environment).order_by(Environment.id).all()
    flags = db.query(FeatureFlag).order_by(FeatureFlag.key).all()
    suggestions = []
    for key in sorted({flag.key for flag in flags}):
        variants = [flag for flag in flags if flag.key == key]
        baseline = next((flag for flag in variants if flag.environment_id == 1), variants[0])
        states = []
        for environment in environments:
            variant = next((flag for flag in variants if flag.environment_id == environment.id), baseline)
            states.append(_effective_state(db, variant, environment))
        if not states:
            continue
        fully_rolled_out = all(state["enabled"] and state["rollout_percentage"] == 100 for state in states)
        fully_disabled = all(not state["enabled"] for state in states)
        if not (fully_rolled_out or fully_disabled):
            continue
        latest_event = db.query(AuditLog).filter(AuditLog.flag_key == key).order_by(AuditLog.timestamp.desc()).first()
        if latest_event is None or latest_event.timestamp > cutoff:
            continue
        review = db.query(CleanupReview).filter(CleanupReview.flag_key == key).first()
        suggestions.append({
            "flag_key": key,
            "state": "fully_rolled_out" if fully_rolled_out else "fully_disabled",
            "stale_since": latest_event.timestamp,
            "stale_days": max(0, (datetime.utcnow() - latest_event.timestamp).days),
            "reviewed": review is not None,
            "reviewed_at": review.reviewed_at if review else None,
            "reviewed_by": review.reviewed_by if review else None,
        })
    return suggestions


def mark_cleanup_reviewed(db: Session, flag_key: str, actor: str = "system") -> CleanupReview:
    review = db.query(CleanupReview).filter(CleanupReview.flag_key == flag_key).first()
    if review is None:
        review = CleanupReview(flag_key=flag_key, reviewed_by=actor or "system")
        db.add(review)
    else:
        review.reviewed_at = datetime.utcnow()
        review.reviewed_by = actor or "system"
    db.commit()
    db.refresh(review)
    return review