from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Event
from time import monotonic

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import AuditLog, Base, Environment


def test_flag_mutations_create_filterable_audit_records():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(Environment(id=1, name="Development", key="development", description="Development"))
    session.commit()
    app.dependency_overrides[get_db] = lambda: (yield session)
    try:
        client = TestClient(app)
        payload = {
            "key": "audit-test",
            "type": "boolean",
            "default_value": False,
            "enabled": False,
            "owner_team": "Platform",
            "environment_id": 1,
            "target_users": [],
            "target_groups": [],
        }
        assert client.post("/flags", json=payload, headers={"X-Actor": "alice"}).status_code == 201
        assert client.put("/flags/audit-test", json={"enabled": True, "rollout_percentage": 50}, headers={"X-Actor": "alice"}).status_code == 200

        response = client.get("/audit-logs", params={"actor": "alice", "flag_key": "audit-test"})
        assert response.status_code == 200
        records = response.json()
        assert [record["action"] for record in records] == ["ENABLE", "CREATE"]
        assert records[0]["environment"] == "development"
        assert records[0]["diff"]["enabled"] == {"old": False, "new": True}
        assert records[0]["diff"]["rollout_percentage"] == {"old": 0, "new": 50}
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_feature_flag_client_keeps_last_snapshot_on_refresh_failure(monkeypatch):
    from app.feature_flag_client import FeatureFlagClient

    client = FeatureFlagClient("http://flags.test")
    responses = [{"checkout": {"key": "checkout", "enabled": True}}, OSError("offline")]
    monkeypatch.setattr(client, "_fetch_flags", lambda: responses.pop(0))

    assert client.refresh() is True
    assert client.is_enabled("checkout") is True
    assert client.refresh() is False
    assert client.get_flag("checkout")["enabled"] is True


def test_audit_records_all_flag_actions_and_supports_date_filters():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(Environment(id=1, name="Development", key="development", description="Development"))
    session.commit()
    app.dependency_overrides[get_db] = lambda: (yield session)
    try:
        client = TestClient(app)
        payload = {
            "key": "all-actions",
            "type": "boolean",
            "default_value": False,
            "enabled": False,
            "owner_team": "Platform",
            "environment_id": 1,
            "target_users": [],
            "target_groups": [],
        }
        assert client.post("/flags", json=payload).status_code == 201
        assert client.put("/flags/all-actions", json={"default_value": True}, headers={"X-Actor": "bob"}).status_code == 200
        assert client.put("/flags/all-actions", json={"enabled": True}, headers={"X-Actor": "bob"}).status_code == 200
        assert client.put("/flags/all-actions", json={"enabled": False}, headers={"X-Actor": "bob"}).status_code == 200
        assert client.put("/flags/all-actions", json={"target_users": ["user-1"]}, headers={"X-Actor": "bob"}).status_code == 200
        assert client.put("/flags/all-actions/environments/1", json={"enabled": True}, headers={"X-Actor": "bob"}).status_code == 200

        records = client.get("/audit-logs", params={"flag_key": "all-actions", "actor": "bob"}).json()
        actions = [record["action"] for record in records]
        assert {"ENABLE", "TARGETING", "DISABLE", "UPDATE"}.issubset(actions)
        enable_record = next(record for record in records if record["action"] == "ENABLE")
        assert enable_record["environment"] == "development"
        assert enable_record["previous_state"]["enabled"] is False
        assert enable_record["new_state"]["enabled"] is True
        assert enable_record["diff"]["enabled"] == {"old": False, "new": True}
        assert all(record["timestamp"] for record in records)

        create_records = client.get("/audit-logs", params={"actor": "system", "flag_key": "all-actions"}).json()
        assert [record["action"] for record in create_records] == ["CREATE"]
        today = datetime.utcnow().date().isoformat()
        assert len(client.get("/audit-logs", params={"from_date": today, "to_date": today}).json()) >= 6
        tomorrow = (datetime.utcnow() + timedelta(days=1)).date().isoformat()
        assert client.get("/audit-logs", params={"from_date": tomorrow}).json() == []
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_feature_flag_client_refreshes_periodically_and_stops_cleanly(monkeypatch):
    from app.feature_flag_client import FeatureFlagClient

    refresh_seen = Event()
    calls = []

    def fetch_flags():
        calls.append(len(calls))
        refresh_seen.set()
        return {"checkout": {"key": "checkout", "enabled": bool(len(calls) % 2)}}

    client = FeatureFlagClient("http://flags.test", refresh_interval=0.02)
    monkeypatch.setattr(client, "_fetch_flags", fetch_flags)
    client.start()
    try:
        assert refresh_seen.wait(1)
        initial_calls = len(calls)
        deadline = monotonic() + 1
        while len(calls) <= initial_calls and monotonic() < deadline:
            refresh_seen.wait(0.05)
            refresh_seen.clear()
        assert len(calls) > initial_calls
        with ThreadPoolExecutor(max_workers=4) as executor:
            assert all(executor.map(client.is_enabled, ["checkout"] * 20)) in (True, False)
    finally:
        client.stop()
    assert client._thread is None