from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analytics import flush_evaluation_counts, get_evaluation_metrics, hour_key, record_evaluation
from app.models import Base, EvaluationMetric


class FakeRedis:
    def __init__(self):
        self.values = {}

    def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    def expire(self, key, ttl):
        return True

    def scan_iter(self, match=None):
        return iter(self.values)

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        self.values.pop(key, None)


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_hourly_counter_flushes_to_database():
    redis = FakeRedis()
    timestamp = datetime(2026, 8, 26, 14, 30)
    record_evaluation(redis, "checkout", timestamp)
    record_evaluation(redis, "checkout", timestamp)
    assert redis.values[hour_key("checkout", timestamp)] == 2

    session = make_session()
    try:
        assert flush_evaluation_counts(session, redis) == 1
        metric = session.query(EvaluationMetric).one()
        assert metric.flag_key == "checkout"
        assert metric.hour == datetime(2026, 8, 26, 14)
        assert metric.count == 2
        assert redis.values == {}
    finally:
        session.close()


def test_metrics_are_zero_filled_for_requested_range():
    session = make_session()
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    session.add(EvaluationMetric(flag_key="checkout", hour=now, count=4))
    session.commit()
    try:
        points = get_evaluation_metrics(session, "checkout", days=7)
        assert len(points) == 168
        assert points[-1]["count"] == 4
        assert sum(point["count"] for point in points) == 4
        assert len(get_evaluation_metrics(session, "checkout", days=30)) == 720
    finally:
        session.close()