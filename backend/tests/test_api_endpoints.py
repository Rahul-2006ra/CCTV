"""Comprehensive integration tests for SentinelAI API Endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storage.db import init_db
from scripts.generate_synthetic_threats import seed_demo_data


@pytest.fixture
def client():
    seed_demo_data()
    with TestClient(app) as test_client:
        yield test_client


def test_system_health(client):
    res = client.get("/api/system/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ok", "degraded")


def test_threat_status(client):
    res = client.get("/api/intelligence/threat-status")
    assert res.status_code == 200
    data = res.json()
    assert "global_risk_score" in data
    assert "threat_level" in data
    assert "status_code" in data
    assert data["global_risk_score"] >= 0


def test_evaluate_entity_risk(client):
    res = client.post(
        "/api/intelligence/evaluate-entity-risk",
        json={"track_id": 42, "dwell_seconds": 40.0, "max_speed": 0.35},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["composite_score"] >= 40.0
    assert data["severity_level"] in ("HIGH", "CRITICAL", "ELEVATED")
    assert len(data["factor_breakdown"]) > 0


def test_route_reconstruct(client):
    res = client.post(
        "/api/intelligence/route-reconstruct",
        json={"query": "person with backpack", "time_window_minutes": 60},
    )
    assert res.status_code == 200
    data = res.json()
    assert "entity_id" in data
    assert "route" in data
    assert "max_risk_score" in data


def test_copilot_query(client):
    res = client.post(
        "/api/intelligence/copilot/query",
        json={"query": "Summarize all high-risk perimeter breaches"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert "threat_level" in data
    assert len(data["recommendations"]) > 0


def test_copilot_explain(client):
    res = client.get("/api/intelligence/copilot/explain/ALT-001")
    assert res.status_code == 200
    data = res.json()
    assert "explanation" in data


def test_dossier_generation_and_download(client):
    # 1. Generate
    gen_res = client.post(
        "/api/intelligence/reports/generate",
        json={
            "case_title": "Automated Perimeter Penetration Audit",
            "investigator_id": "CHIEF-729",
            "summary": "Integration test forensic evaluation",
        },
    )
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    case_id = gen_data["case_id"]
    assert "sha256_hash" in gen_data

    # 2. Download
    down_res = client.get(f"/api/intelligence/reports/{case_id}/download")
    assert down_res.status_code == 200
    assert "SENTINELAI FORENSIC DOSSIER" in down_res.text


def test_analytics_endpoints(client):
    # Overview
    res1 = client.get("/api/analytics/overview")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "summary" in data1
    assert "camera_performance" in data1
    assert "temporal_trends" in data1

    # Heatmaps
    res2 = client.get("/api/analytics/heatmaps")
    assert res2.status_code == 200
    data2 = res2.json()
    assert "cameras" in data2
