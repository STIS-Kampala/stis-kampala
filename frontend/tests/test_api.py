import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "stis-dev-key"}


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["service"] == "STIS API"


def test_health():
    res = client.get("/health")
    assert res.status_code == 200


def test_unauthorized():
    res = client.get("/roads")
    assert res.status_code == 401


def test_roads():
    res = client.get("/roads", headers=HEADERS)
    assert res.status_code == 200
    assert len(res.json()) > 0


def test_models():
    res = client.get("/models", headers=HEADERS)
    assert res.status_code == 200


def test_predict_now():
    res = client.get("/predict/now/kampala_rd", headers=HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "label" in data
    assert "delay_ratio" in data
    assert data["label"] in ("low", "medium", "high")


def test_predict_post():
    res = client.post("/predict", headers=HEADERS, json={
        "road_id": "jinja_rd",
        "hour": 8,
        "rain_mm": 5.0,
        "model": "gradient_boosting"
    })
    assert res.status_code == 200
    assert res.json()["road_id"] == "jinja_rd"


def test_data_summary():
    res = client.get("/data/summary", headers=HEADERS)
    assert res.status_code == 200
