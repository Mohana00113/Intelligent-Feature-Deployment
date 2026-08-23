from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.cache import evaluation_cache
from app.database import get_db
from app.main import app
from app.models import Base, Environment, FeatureFlag, FlagEnvironmentOverride


class MemoryRedis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value

    def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]


def make_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        Environment(id=1, name="Development", key="development", description="Development"),
        Environment(id=2, name="Staging", key="staging", description="Staging"),
        Environment(id=3, name="Production", key="production", description="Production"),
    ])
    session.commit()
    return session


def test_day13_priority_conflicts_and_api_cache_invalidation(monkeypatch):
    session = make_session()
    session.add_all([
        FeatureFlag(
            key="priority-user",
            type="boolean",
            default_value=True,
            enabled=True,
            target_users=["priority-user"],
            target_groups=["demo-group"],
            rollout_percentage=100,
            owner_team="QA",
            environment_id=1,
        ),
        FeatureFlag(
            key="priority-group",
            type="boolean",
            default_value=True,
            enabled=True,
            target_groups=["demo-group"],
            rollout_percentage=100,
            owner_team="QA",
            environment_id=1,
        ),
        FeatureFlag(
            key="priority-rollout",
            type="boolean",
            default_value=True,
            enabled=True,
            rollout_percentage=100,
            owner_team="QA",
            environment_id=1,
        ),
        FeatureFlag(
            key="priority-default",
            type="boolean",
            default_value=True,
            enabled=True,
            owner_team="QA",
            environment_id=1,
        ),
        FeatureFlag(
            key="mutation-flow",
            type="boolean",
            default_value=False,
            enabled=True,
            owner_team="QA",
            environment_id=1,
        ),
    ])
    session.commit()
    override_flag = session.query(FeatureFlag).filter_by(key="priority-rollout").one()
    session.add(FlagEnvironmentOverride(
        flag_id=override_flag.id,
        environment_id=2,
        enabled=True,
        default_value=False,
        rollout_percentage=100,
        target_users=[],
        target_groups=[],
    ))
    session.commit()

    monkeypatch.setattr(evaluation_cache, "client", MemoryRedis())
    app.dependency_overrides[get_db] = lambda: (yield session)
    try:
        client = TestClient(app)

        def evaluate(flag_key, environment="staging", user_id="demo-user", group=None):
            response = client.post("/evaluate", json={
                "flag_key": flag_key,
                "environment": environment,
                "user_id": user_id,
                "group": group,
            })
            assert response.status_code == 200, response.text
            return response.json()

        assert evaluate("priority-user", user_id="priority-user", group="demo-group")["source"] == "user_targeting"
        assert evaluate("priority-group", group="demo-group")["source"] == "group_targeting"
        assert evaluate("priority-rollout")["source"] == "percentage_rollout"
        assert evaluate("priority-default", environment="development")["source"] == "default"
        assert evaluate("priority-rollout")["cached"] is True

        created = client.post("/flags", json={
            "key": "api-mutation-flow",
            "type": "boolean",
            "default_value": False,
            "enabled": True,
            "rollout_percentage": 0,
            "description": "Day 13 mutation flow",
            "owner_team": "QA",
            "environment_id": 1,
            "target_users": [],
            "target_groups": [],
        })
        assert created.status_code == 201
        assert evaluate("api-mutation-flow", environment="development")["value"] is False
        assert evaluate("api-mutation-flow", environment="development")["cached"] is True

        updated = client.put("/flags/api-mutation-flow", json={"default_value": True})
        assert updated.status_code == 200
        changed = evaluate("api-mutation-flow", environment="development")
        assert changed["value"] is True
        assert changed["cached"] is False

        updated = client.put("/flags/api-mutation-flow", json={"target_groups": ["demo-group"]})
        assert updated.status_code == 200
        targeted = evaluate("api-mutation-flow", environment="development", group="demo-group")
        assert targeted["source"] == "group_targeting"
        assert targeted["cached"] is False

        updated = client.put("/flags/api-mutation-flow", json={"rollout_percentage": 100})
        assert updated.status_code == 200
        rolled = evaluate("api-mutation-flow", environment="development", group="other")
        assert rolled["source"] == "percentage_rollout"
        assert rolled["cached"] is False

        updated = client.put("/flags/api-mutation-flow", json={"rollout_percentage": 0, "target_groups": []})
        assert updated.status_code == 200
        override = client.put("/flags/api-mutation-flow/environments/2", json={"default_value": False})
        assert override.status_code == 200
        overridden = evaluate("api-mutation-flow", group="other")
        assert overridden["source"] == "environment_override"
        assert overridden["cached"] is False
    finally:
        app.dependency_overrides.clear()
        session.close()