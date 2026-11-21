"""Unit tests for SentinelAI Intelligence Engines."""

import numpy as np
from backend.intelligence.threat_engine import ThreatEngine
from backend.intelligence.risk_scoring import RiskScoringEngine
from backend.intelligence.reid_engine import ReidEngine
from backend.intelligence.copilot import InvestigationCopilot
from backend.intelligence.report_generator import ReportGenerator
from backend.storage.db import init_db


def test_threat_engine_anomaly_discovery():
    """Verify ThreatEngine discovers loitering, speed, and unattended payload anomalies."""
    engine = ThreatEngine(loiter_seconds=5.0, rapid_speed_threshold=0.20, unattended_seconds=5.0)

    # Frame 1: Person enters
    det_f1 = [{
        "track_id": 10,
        "label": "person",
        "confidence": 0.92,
        "bounding_box": [100, 100, 200, 400],
    }]
    events1 = engine.evaluate_frame(det_f1, timestamp=0.0, width=1000, height=1000)
    assert len(events1) == 0  # Initial observation

    # Frame 2: Person moves rapidly (sprint)
    det_f2 = [{
        "track_id": 10,
        "label": "person",
        "confidence": 0.92,
        "bounding_box": [600, 100, 700, 400],
    }]
    events2 = engine.evaluate_frame(det_f2, timestamp=1.0, width=1000, height=1000)
    assert any("Rapid Movement" in e["event_type"] for e in events2)

    # Frame 3: Unattended bag candidate
    det_f3 = [{
        "track_id": 25,
        "label": "backpack",
        "confidence": 0.88,
        "bounding_box": [100, 100, 150, 150],
    }]
    _ = engine.evaluate_frame(det_f3, timestamp=2.0, width=1000, height=1000)
    events4 = engine.evaluate_frame(det_f3, timestamp=8.0, width=1000, height=1000)
    assert any("Unattended Payload" in e["event_type"] for e in events4)


def test_risk_scoring_engine():
    """Verify composite risk score calculations and severity tiers."""
    alerts = [{"category": "PERIMETER_BREACH", "event_type": "Restricted Zone Incursion"}]
    score_data = RiskScoringEngine.compute_entity_score(
        track_id=1,
        alerts=alerts,
        dwell_seconds=45.0,
        max_speed=0.30,
        is_night_time=True,
    )
    assert score_data["composite_score"] >= 70.0
    assert score_data["severity_level"] in ("HIGH", "CRITICAL")
    assert len(score_data["factor_breakdown"]) >= 3


def test_reid_engine_affinity():
    """Verify feature affinity calculation between vectors and colors."""
    reid = ReidEngine()
    v1 = np.ones(512, dtype=np.float32)
    v2 = np.ones(512, dtype=np.float32)

    c1 = {"upper": "red", "lower": "black"}
    c2 = {"upper": "red", "lower": "black"}
    affinity_high = reid.compute_affinity(v1, v2, c1, c2)
    assert affinity_high > 0.85

    c3 = {"upper": "blue", "lower": "white"}
    affinity_low = reid.compute_affinity(v1, -v2, c1, c3)
    assert affinity_low < 0.50


def test_copilot_and_report_generator():
    """Verify AI Copilot synthesis and forensic report compilation."""
    init_db()
    copilot = InvestigationCopilot()
    briefing = copilot.query_intelligence("Summarize all security incursions")
    assert "response" in briefing
    assert "threat_level" in briefing
    assert len(briefing["recommendations"]) > 0

    reporter = ReportGenerator()
    report = reporter.generate_dossier(
        case_title="Automated Test Breach",
        investigator_id="INSP-001",
        summary="Unit test validation scenario",
    )
    assert "case_id" in report
    assert "sha256_hash" in report
    assert "download_url" in report
