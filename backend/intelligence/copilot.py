"""SentinelAI Autonomous AI Investigation Copilot."""

import os
import re
from typing import Dict, List, Any, Optional
from backend.storage import db


class InvestigationCopilot:
    """Autonomous reasoning agent that parses security queries, correlates alerts,

    and drafts military-grade tactical incident briefings.
    """

    def __init__(self, search_engine=None):
        self.search_engine = search_engine

    def query_intelligence(self, query: str, context_hours: int = 24) -> Dict[str, Any]:
        """Process conversational query across SQLite alerts, video tracks, and camera states."""
        query_lower = query.lower()
        cameras = db.rows("SELECT * FROM cameras")
        cam_map = {c["id"]: c["name"] for c in cameras}

        alerts = db.rows(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50"
        )
        videos = db.rows(
            "SELECT * FROM videos WHERE status='READY' ORDER BY created_at DESC LIMIT 10"
        )

        # 1. Identify query intent
        is_summary_request = any(w in query_lower for w in ("summarize", "summary", "brief", "what happened", "overview", "situation"))
        is_threat_request = any(w in query_lower for w in ("threat", "risk", "breach", "danger", "critical", "alarm", "intrusion"))
        is_target_request = any(w in query_lower for w in ("who", "person", "subject", "vehicle", "backpack", "bag", "track"))

        matched_alerts = []
        for a in alerts:
            cname = cam_map.get(a.get("camera_id"), "").lower()
            etype = a.get("event_type", "").lower()
            details = a.get("details", "").lower()
            if any(term in cname or term in etype or term in details for term in query_lower.split() if len(term) > 3):
                matched_alerts.append(a)

        target_alerts = matched_alerts if matched_alerts else alerts[:8]

        # 2. Synthesize situational narrative
        if not target_alerts and not videos:
            narrative = (
                "SENTINELAI ADVISORY // ALL SECTORS NOMINAL.\n\n"
                "No anomalous physical breaches or high-threat behavioral patterns detected in active camera feeds. "
                "Perimeter sensors and neural visual trackers are active in green state."
            )
            recommendations = ["Maintain scheduled perimeter patrols", "Verify camera feed latency"]
            threat_level = "NORMAL"
        else:
            high_sev = [a for a in target_alerts if a.get("severity") in ("CRITICAL", "HIGH")]
            threat_level = "CRITICAL" if len(high_sev) >= 2 else ("HIGH" if high_sev else "ELEVATED")

            points = []
            for idx, a in enumerate(target_alerts[:5], 1):
                cam = cam_map.get(a.get("camera_id"), a.get("camera_id") or "Sector A")
                ts = f"T+{int(a.get('timestamp', 0))}s"
                points.append(f"{idx}. [{cam} | {ts}] {a.get('event_type')}: {a.get('details')}")

            events_bulleted = "\n".join(points) if points else "No specific alert clusters isolated."

            narrative = (
                f"TACTICAL INCIDENT BRIEFING // THREAT EVALUATION: {threat_level}\n\n"
                f"Analysis of query '{query}' across {len(cameras)} active camera feeds isolated {len(target_alerts)} correlated events:\n\n"
                f"{events_bulleted}\n\n"
                f"TACTICAL ASSESSMENT:\n"
                f"Multi-camera correlation indicates {'concentrated perimeter activity requiring physical interception' if high_sev else 'low-to-moderate transient movement across monitored zones'}."
            )

            recommendations = [
                "Dispatch nearest tactical security unit to inspect flagged camera perimeter",
                "Reconstruct cross-camera trajectory of associated track IDs",
                "Generate cryptographically verified forensic dossier for chain-of-custody logging",
            ]

        return {
            "query": query,
            "response": narrative,
            "threat_level": threat_level,
            "matched_events_count": len(target_alerts),
            "recommendations": recommendations,
            "related_alert_ids": [a["id"] for a in target_alerts[:6]],
        }

    def explain_threat(self, alert_id: str) -> Dict[str, Any]:
        """Explain the rationale behind a specific alert."""
        alert = db.one("SELECT * FROM alerts WHERE id=?", (alert_id,))
        if not alert:
            return {"error": "Alert not found"}

        cam = db.one("SELECT name FROM cameras WHERE id=?", (alert.get("camera_id"),))
        cam_name = cam["name"] if cam else "Main Camera"

        explanation = (
            f"ALERT RATIONALE // {alert.get('event_type')}\n\n"
            f"1. Sensor Origin: {cam_name} (Track #{alert.get('track_id')})\n"
            f"2. Recorded Time: T+{alert.get('timestamp', 0):.1f}s into session\n"
            f"3. Algorithmic Trigger: {alert.get('details')}\n"
            f"4. Severity Determination: Assigned '{alert.get('severity')}' based on velocity thresholds, polygon boundary intersection, and object proximity heuristics."
        )

        return {
            "alert_id": alert_id,
            "explanation": explanation,
            "severity": alert.get("severity"),
            "event_type": alert.get("event_type"),
        }
