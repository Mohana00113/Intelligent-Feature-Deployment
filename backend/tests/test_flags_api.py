from fastapi.testclient import TestClient

from app.main import app


def test_list_flags_returns_empty_array_when_database_is_empty():
    client = TestClient(app)

    response = client.get('/flags')

    assert response.status_code == 200
    assert response.json() == []
