from __future__ import annotations

from datetime import datetime, timedelta
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import EvaluationMetric

logger = logging.getLogger(__name__)
_KEY_PATTERN = re.compile(r"^evaluation:analytics:(?P<flag>.+):(?P<environment>[^:]+):(?P<hour>\d{10})$")


def hour_key(flag_key: str, timestamp: datetime | None = None, environment: str = "development") -> str:
    current = timestamp or datetime.utcnow()
    return f"evaluation:analytics:{flag_key}:{environment}:{current:%Y%m%d%H}"


def record_evaluation(redis_client: Any, flag_key: str, environment: str = "development", timestamp: datetime | None = None) -> None:
    """Increment the current hourly counter, failing open if Redis is unavailable."""

    try:
        if isinstance(environment, datetime):
            timestamp, environment = environment, "development"
        key = hour_key(flag_key, timestamp, environment)
        redis_client.incr(key)
        redis_client.expire(key, 60 * 60 * 24 * 8)
    except Exception as exc:
        logger.warning("Unable to record evaluation metric for %s: %s", flag_key, exc)


def flush_evaluation_counts(db: Session, redis_client: Any) -> int:
    """Persist Redis hourly counters and remove them after the DB commit succeeds."""

    pending: list[tuple[str, str, str, datetime, int]] = []
    try:
        for raw_key in redis_client.scan_iter(match="evaluation:analytics:*"):
            key = raw_key.decode() if isinstance(raw_key, bytes) else raw_key
            match = _KEY_PATTERN.match(key)
            if not match:
                continue
            pending.append((raw_key, match.group("flag"), match.group("environment"), datetime.strptime(match.group("hour"), "%Y%m%d%H"), int(redis_client.get(raw_key) or 0)))
    except Exception as exc:
        logger.warning("Unable to read evaluation metrics from Redis: %s", exc)
        return 0

    for _, flag_key, environment, hour, count in pending:
        metric = db.query(EvaluationMetric).filter(EvaluationMetric.flag_key == flag_key, EvaluationMetric.environment == environment, EvaluationMetric.hour == hour).first()
        if metric is None:
            db.add(EvaluationMetric(flag_key=flag_key, environment=environment, hour=hour, count=count))
        else:
            metric.count = count
    if not pending:
        return 0
    db.commit()
    for raw_key, _, _, _, _ in pending:
        try:
            redis_client.delete(raw_key)
        except Exception as exc:
            logger.warning("Unable to remove flushed evaluation metric: %s", exc)
    return len(pending)


def get_evaluation_metrics(db: Session, flag_key: str, days: int = 7, environment: str = "development") -> list[dict[str, Any]]:
    """Return one zero-filled point per hour for the requested recent period."""

    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(hours=days * 24 - 1)
    rows = db.query(EvaluationMetric).filter(EvaluationMetric.flag_key == flag_key, EvaluationMetric.environment == environment, EvaluationMetric.hour >= start, EvaluationMetric.hour <= now).all()
    counts = {row.hour: row.count for row in rows}
    return [{"timestamp": hour.isoformat(), "count": counts.get(hour, 0)} for hour in (start + timedelta(hours=index) for index in range(days * 24))]