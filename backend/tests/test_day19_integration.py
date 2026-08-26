from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.cache import evaluation_cache
from app.database import get_db
from app.main import app
from app.models import AuditLog, Base, Environment, EvaluationMetric


class IntegrationRedis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value

    def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    def expire(self, key, ttl):
        return True

    def scan_iter(self, match=None):
        return iter(key for key in self.values if key.startswith("evaluation:analytics:"))

    def delete(self, key):
        self.values.pop(key, None)


def test_complete_flag_to_audit_cache_and_analytics_lifecycle(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        Environment(id=1, name="Development", key="development", description="Development"),
        Environment(id=2, name="Staging", key="staging", description="Staging"),
        Environment(id=3, name="Production", key="production", description="Production"),
    ])
    session.commit()
    redis = IntegrationRedis()
    monkeypatch.setattr(evaluation_cache, "client", redis)
    app.dependency_overrides[get_db] = lambda: (yield session)
    try:
        client = TestClient(app)
        payload = {
            "key": "day19_lifecycle",
            "type": "boolean",
            "default_value": False,
            "enabled": True,
            "rollout_percentage": 0,
            "description": "Day 19 integration test",
            "owner_team": "QA",
            "environment_id": 1,
            "target_users": [],
            "target_groups": [],
        }
        created = client.post("/flags", json=payload, headers={"X-Actor": "day19"})
        assert created.status_code == 201
        assert client.put("/flags/day19_lifecycle", json={"target_users": ["integrated-user"]}, headers={"X-Actor": "day19"}).status_code == 200

        first = client.post("/evaluate", json={"flag_key": "day19_lifecycle", "environment": "development", "user_id": "integrated-user"})
        second = client.post("/evaluate", json={"flag_key": "day19_lifecycle", "environment": "development", "user_id": "integrated-user"})
        assert first.status_code == 200 and first.json()["value"] is False and first.json()["source"] == "user_targeting"
        assert second.status_code == 200 and second.json()["cached"] is True

        assert client.put("/flags/day19_lifecycle", json={"default_value": True}, headers={"X-Actor": "day19"}).status_code == 200
        fresh = client.post("/evaluate", json={"flag_key": "day19_lifecycle", "environment": "development", "user_id": "integrated-user"})
        assert fresh.status_code == 200 and fresh.json()["value"] is True and fresh.json()["cached"] is False

        records = client.get("/audit-logs", params={"flag_key": "day19_lifecycle", "actor": "day19", "environment": "development"}).json()
        assert {record["action"] for record in records} == {"CREATE", "TARGETING", "UPDATE"}
        update_record = next(record for record in records if record["action"] == "UPDATE")
        assert update_record["previous_state"]["default_value"] is False
        assert update_record["new_state"]["default_value"] is True
        assert update_record["diff"]["default_value"] == {"old": False, "new": True}
        assert all(record["timestamp"] and record["flag_key"] == "day19_lifecycle" for record in records)

        analytics_key = next(key for key in redis.values if key.startswith("evaluation:analytics:day19_lifecycle:development:"))
        assert redis.values[analytics_key] == 3
        from app.analytics import flush_evaluation_counts

        assert flush_evaluation_counts(session, redis) == 1
        assert session.query(EvaluationMetric).filter_by(flag_key="day19_lifecycle", environment="development", count=3).count() == 1
        metrics = client.get("/analytics/flags/day19_lifecycle/evaluations", params={"environment": "development", "days": 7})
        assert metrics.status_code == 200
        assert metrics.json()["environment"] == "development"
        assert sum(point["count"] for point in metrics.json()["points"]) == 3
        assert client.get("/analytics/flags/day19_lifecycle/evaluations", params={"environment": "staging", "days": 7}).json()["points"]
    finally:
        app.dependency_overrides.clear()
        session.close()