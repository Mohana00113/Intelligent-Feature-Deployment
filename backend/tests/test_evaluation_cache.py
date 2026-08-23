from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.cache import evaluation_cache
from app.crud import update_flag
from app.database import get_db
from app.main import app
import app.main as main_module
from app.models import Base, FeatureFlag
from app.schemas import FlagUpdate


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.ttl_calls = []

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value
        self.ttl_calls.append((key, ttl))

    def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]


class BrokenRedis:
    def get(self, key):
        raise ConnectionError("Redis is unavailable")

    def setex(self, key, ttl, value):
        raise ConnectionError("Redis is unavailable")

    def incr(self, key):
        raise ConnectionError("Redis is unavailable")


def make_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_cache_hit_and_flag_invalidation(monkeypatch):
    session = make_session()
    session.add(
        FeatureFlag(
            key="cached-flag",
            type="boolean",
            default_value=False,
            enabled=True,
            owner_team="QA",
            environment_id=1,
        )
    )
    session.commit()

    fake_redis = FakeRedis()
    monkeypatch.setattr(evaluation_cache, "client", fake_redis)
    evaluation_calls = []
    original_evaluator = main_module.evaluate_feature_flag_request

    def counted_evaluator(*args, **kwargs):
        evaluation_calls.append(True)
        return original_evaluator(*args, **kwargs)

    monkeypatch.setattr(main_module, "evaluate_feature_flag_request", counted_evaluator)
    app.dependency_overrides[get_db] = lambda: (yield session)
    try:
        client = TestClient(app)
        payload = {"flag_key": "cached-flag", "environment": "staging", "user_id": "user-1", "group": None}

        first = client.post("/evaluate", json=payload)
        second = client.post("/evaluate", json=payload)

        assert first.json()["cached"] is False
        assert second.json()["cached"] is True
        assert len(evaluation_calls) == 1
        assert first.json()["value"] is False
        assert fake_redis.ttl_calls
        assert fake_redis.ttl_calls[0][1] == evaluation_cache.ttl

        update_flag(session, "cached-flag", FlagUpdate(default_value=True))
        fresh = client.post("/evaluate", json=payload)
        assert fresh.json()["cached"] is False
        assert fresh.json()["value"] is True

        update_flag(session, "cached-flag", FlagUpdate(default_value=False, target_users=["user-1"]))
        targeted = client.post("/evaluate", json=payload)
        assert targeted.json()["cached"] is False
        assert targeted.json()["source"] == "user_targeting"
        assert len(evaluation_calls) == 3
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_redis_failure_falls_back_to_database(monkeypatch):
    session = make_session()
    session.add(
        FeatureFlag(
            key="redis-down-flag",
            type="boolean",
            default_value=True,
            enabled=True,
            owner_team="QA",
            environment_id=1,
        )
    )
    session.commit()

    monkeypatch.setattr(evaluation_cache, "client", BrokenRedis())
    app.dependency_overrides[get_db] = lambda: (yield session)
    try:
        response = TestClient(app).post(
            "/evaluate",
            json={"flag_key": "redis-down-flag", "environment": "staging", "user_id": "user-1", "group": None},
        )
        assert response.status_code == 200
        assert response.json()["value"] is True
        assert response.json()["cached"] is False
    finally:
        app.dependency_overrides.clear()
        session.close()