"""SentinelAI Composite Risk Scoring Engine."""

import math
from typing import Dict, List, Any, Optional
from backend.storage import db


class RiskScoringEngine:
    """Calculates granular, explainable 0-100 risk scores for entities, alerts,

    and overall facility operations.
    """

    WEIGHTS = {
        "zone_incursion": 35.0,
        "suspicious_velocity": 20.0,
        "loitering": 25.0,
        "unattended_payload": 30.0,
        "night_hours_penalty": 15.0,
        "repeated_visitation": 15.0,
    }

    @classmethod
    def compute_entity_score(
        cls,
        track_id: int,
        alerts: List[Dict[str, Any]],
        dwell_seconds: float = 0.0,
        max_speed: float = 0.0,
        is_night_time: bool = False,
    ) -> Dict[str, Any]:
        """Compute an explainable risk score (0-100) with contributing factors."""
        score = 10.0  # Baseline presence score
        factors = []

        has_zone_breach = any(a.get("category") == "PERIMETER_BREACH" or "Zone" in a.get("event_type", "") for a in alerts)
        if has_zone_breach:
            score += cls.WEIGHTS["zone_incursion"]
            factors.append({"factor": "Restricted Zone Incursion", "contribution": cls.WEIGHTS["zone_incursion"]})

        if max_speed > 0.22:
            velocity_pts = min(cls.WEIGHTS["suspicious_velocity"], (max_speed - 0.22) * 50)
            score += velocity_pts
            factors.append({"factor": "High Velocity / Flight Motion", "contribution": round(velocity_pts, 1)})

        if dwell_seconds > 30.0:
            dwell_pts = min(cls.WEIGHTS["loitering"], (dwell_seconds - 30.0) * 0.5)
            score += dwell_pts
            factors.append({"factor": "Extended Target Loitering", "contribution": round(dwell_pts, 1)})

        has_unattended = any("Unattended" in a.get("event_type", "") for a in alerts)
        if has_unattended:
            score += cls.WEIGHTS["unattended_payload"]
            factors.append({"factor": "Unattended Object Association", "contribution": cls.WEIGHTS["unattended_payload"]})

        if is_night_time:
            score += cls.WEIGHTS["night_hours_penalty"]
            factors.append({"factor": "Non-Operational Hours Activity", "contribution": cls.WEIGHTS["night_hours_penalty"]})

        normalized_score = min(100.0, max(5.0, score))
        severity = cls.get_severity_tier(normalized_score)

        return {
            "track_id": track_id,
            "composite_score": round(normalized_score, 1),
            "severity_level": severity,
            "factor_breakdown": factors,
        }

    @staticmethod
    def get_severity_tier(score: float) -> str:
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "ELEVATED"
        elif score >= 20:
            return "GUARDED"
        return "NORMAL"

    @classmethod
    def get_global_facility_threat(cls) -> Dict[str, Any]:
        """Aggregate global facility threat index from active alerts and camera events."""
        recent_alerts = db.rows(
            "SELECT * FROM alerts WHERE status != 'RESOLVED' ORDER BY created_at DESC LIMIT 50"
        )
        cameras = db.rows("SELECT id, name FROM cameras")

        if not recent_alerts:
            return {
                "global_risk_score": 12.0,
                "threat_level": "NORMAL",
                "status_code": "DEFCON 4",
                "active_threats": 0,
                "highest_risk_camera": cameras[0]["name"] if cameras else "Main Perimeter",
                "critical_incidents": 0,
            }

        severity_weights = {"CRITICAL": 35, "HIGH": 25, "MEDIUM": 15, "ELEVATED": 18, "GUARDED": 8, "LOW": 5}
        total_risk = 0.0
        critical_count = 0
        cam_risk: Dict[str, float] = {}

        for a in recent_alerts:
            sev = a.get("severity", "LOW").upper()
            w = severity_weights.get(sev, 10)
            total_risk += w
            if sev in ("CRITICAL", "HIGH"):
                critical_count += 1
            cid = a.get("camera_id") or "CAM-MAIN"
            cam_risk[cid] = cam_risk.get(cid, 0.0) + w

        highest_cam_id = max(cam_risk.items(), key=lambda x: x[1])[0] if cam_risk else "CAM-MAIN"
        cam_name_match = [c["name"] for c in cameras if c["id"] == highest_cam_id]
        highest_cam_name = cam_name_match[0] if cam_name_match else highest_cam_id

        # Scale non-linearly to 0-100
        composite_facility = min(100.0, 15.0 + math.sqrt(total_risk) * 6.5)
        threat_level = cls.get_severity_tier(composite_facility)

        status_codes = {
            "CRITICAL": "DEFCON 1 // IMMINENT BREACH",
            "HIGH": "DEFCON 2 // HIGH ALERT",
            "ELEVATED": "DEFCON 3 // ELEVATED MONITORING",
            "GUARDED": "DEFCON 4 // ACTIVE PATROL",
            "NORMAL": "DEFCON 5 // ROUTINE SURVEILLANCE",
        }

        return {
            "global_risk_score": round(composite_facility, 1),
            "threat_level": threat_level,
            "status_code": status_codes.get(threat_level, "DEFCON 4"),
            "active_threats": len(recent_alerts),
            "highest_risk_camera": highest_cam_name,
            "critical_incidents": critical_count,
        }
