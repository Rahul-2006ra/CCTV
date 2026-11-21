"""SentinelAI Threat Intelligence & Autonomous Anomaly Discovery Engine."""

import math
try:
    import cv2
except ImportError:
    cv2 = None
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any


def is_point_in_zone(zone, point):
    """Point in polygon check using OpenCV when available, with ray-casting fallback."""
    if zone is None or len(zone) < 3:
        return False
    if cv2 is not None:
        try:
            poly = np.array(zone, dtype=np.float32)
            return cv2.pointPolygonTest(poly, (float(point[0]), float(point[1])), False) >= 0
        except Exception:
            pass
    # Ray casting fallback
    x, y = float(point[0]), float(point[1])
    poly = list(zone)
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


class ThreatEngine:
    """Evaluates multi-signal behavioral and spatial anomalies, outputting

    structured threat alerts with composite risk scores (0-100).
    """

    SEVERITY_LEVELS = {
        "CRITICAL": (80, 100),
        "HIGH": (60, 79),
        "ELEVATED": (40, 59),
        "GUARDED": (20, 39),
        "LOW": (0, 19),
    }

    def __init__(
        self,
        zone: Optional[List[List[float]]] = None,
        loiter_seconds: float = 25.0,
        rapid_speed_threshold: float = 0.22,
        unattended_seconds: float = 15.0,
    ):
        self.zone = np.array(zone, dtype=np.float32) if zone else None
        self.loiter_seconds = loiter_seconds
        self.rapid_speed_threshold = rapid_speed_threshold
        self.unattended_seconds = unattended_seconds

        # Persistent track state: track_id -> dict
        self.tracks: Dict[int, Dict[str, Any]] = {}
        # Emitted alert cache to avoid duplicate spamming: (track_id, event_type)
        self.emitted_alerts = set()
        # Track visitation counts: track_id -> list of visit timestamps
        self.visitation_history: Dict[int, List[float]] = {}

    @staticmethod
    def classify_severity(score: float) -> str:
        """Classify numeric threat score into standard defense tier."""
        for level, (low, high) in ThreatEngine.SEVERITY_LEVELS.items():
            if low <= score <= high:
                return level
        return "CRITICAL" if score > 100 else "LOW"

    def evaluate_frame(
        self,
        detections: List[Dict[str, Any]],
        timestamp: float,
        width: int,
        height: int,
        camera_id: str = "CAM-01",
    ) -> List[Dict[str, Any]]:
        """Perform autonomous anomaly discovery on detections for a given frame."""
        anomalies = []
        people_positions = []

        # 1. Map person coordinates
        for d in detections:
            if d.get("label") == "person":
                box = d["bounding_box"]
                cx = (box[0] + box[2]) / 2 / width
                cy = box[3] / height
                people_positions.append((cx, cy))

        for d in detections:
            tid = d.get("track_id")
            if tid is None:
                continue

            x1, y1, x2, y2 = d["bounding_box"]
            cx = (x1 + x2) / 2 / width
            cy = y2 / height
            point = (cx, cy)
            label = d.get("label", "unknown")
            conf = d.get("confidence", 0.5)

            prev = self.tracks.get(tid)
            now_stationary = timestamp

            # Log visitation
            if tid not in self.visitation_history:
                self.visitation_history[tid] = []
            if not self.visitation_history[tid] or (timestamp - self.visitation_history[tid][-1] > 60):
                self.visitation_history[tid].append(timestamp)

            candidate_events = []

            # -------------------------------------------------------------
            # ANOMALY 1: Restricted Zone Intrusion
            # -------------------------------------------------------------
            in_zone = False
            if self.zone is not None:
                in_zone = is_point_in_zone(self.zone, point)
                if in_zone:
                    candidate_events.append({
                        "event_type": "Restricted Zone Incursion",
                        "category": "PERIMETER_BREACH",
                        "base_score": 85.0,
                        "details": f"Track #{tid} ({label}) entered restricted polygon boundary.",
                    })

            # -------------------------------------------------------------
            # ANOMALY 2: Speed / Sudden Acceleration / Sprints
            # -------------------------------------------------------------
            speed = 0.0
            if prev:
                dt = timestamp - prev["time"]
                if 0 < dt <= 3.0:
                    dist = math.dist(point, prev["point"])
                    speed = dist / dt
                    if label in ("person", "car", "motorcycle", "bicycle") and speed > self.rapid_speed_threshold:
                        candidate_events.append({
                            "event_type": "Suspicious Rapid Movement",
                            "category": "DYNAMIC_ANOMALY",
                            "base_score": 68.0 + min(20.0, (speed - self.rapid_speed_threshold) * 50),
                            "details": f"High image-plane velocity ({speed:.3f} units/s) indicating sudden flight or sprint.",
                        })

                # Maintain stationary anchor
                if math.dist(point, prev["anchor"]) < 0.05:
                    now_stationary = prev["stationary"]

                # ---------------------------------------------------------
                # ANOMALY 3: Loitering Detection
                # ---------------------------------------------------------
                dwell_time = timestamp - prev["first_seen"]
                stationary_time = timestamp - now_stationary

                if label == "person" and (dwell_time >= self.loiter_seconds or stationary_time >= self.loiter_seconds):
                    loiter_score = 65.0 + min(25.0, (dwell_time - self.loiter_seconds) * 0.5)
                    if in_zone:
                        loiter_score = min(100.0, loiter_score + 15.0)

                    candidate_events.append({
                        "event_type": "Extended Loitering Pattern",
                        "category": "BEHAVIORAL_ANOMALY",
                        "base_score": loiter_score,
                        "details": f"Subject #{tid} dwelling in monitored zone for {int(dwell_time)}s without transition.",
                    })

                # ---------------------------------------------------------
                # ANOMALY 4: Unattended Object / Abandonment
                # ---------------------------------------------------------
                if label in ("backpack", "handbag", "suitcase"):
                    is_unattended = not any(math.dist(point, p) < 0.18 for p in people_positions)
                    if is_unattended and (timestamp - now_stationary) >= self.unattended_seconds:
                        candidate_events.append({
                            "event_type": "Unattended Payload Deposited",
                            "category": "TACTICAL_ANOMALY",
                            "base_score": 78.0 + min(15.0, (timestamp - now_stationary) * 0.3),
                            "details": f"Stationary {label} abandoned with no associated handler in proximity for {int(timestamp - now_stationary)}s.",
                        })

            # -------------------------------------------------------------
            # ANOMALY 5: Repeated Visitation Patterns
            # -------------------------------------------------------------
            visits = len(self.visitation_history[tid])
            if visits >= 3:
                candidate_events.append({
                    "event_type": "Repeated Area Recurrence",
                    "category": "RECONNAISSANCE_PATTERN",
                    "base_score": 60.0 + min(20.0, visits * 5),
                    "details": f"Target #{tid} has repeatedly re-entered surveillance sector ({visits} distinct encounters).",
                })

            # Update track state
            self.tracks[tid] = {
                "point": point,
                "time": timestamp,
                "first_seen": prev["first_seen"] if prev else timestamp,
                "stationary": now_stationary,
                "anchor": prev["anchor"] if prev and now_stationary == prev["stationary"] else point,
                "label": label,
                "confidence": conf,
                "speed": speed,
            }

            # Emit new anomalies
            for ev in candidate_events:
                event_key = (tid, ev["event_type"])
                if event_key not in self.emitted_alerts:
                    score = min(100.0, max(10.0, ev["base_score"]))
                    severity = self.classify_severity(score)
                    anomalies.append({
                        "timestamp": timestamp,
                        "camera_id": camera_id,
                        "event_type": ev["event_type"],
                        "category": ev["category"],
                        "severity": severity,
                        "threat_score": round(score, 1),
                        "track_id": tid,
                        "details": ev["details"],
                    })
                    self.emitted_alerts.add(event_key)

        # Cleanup stale tracks (> 45 seconds unseen)
        self.tracks = {k: v for k, v in self.tracks.items() if timestamp - v["time"] <= 45}
        return anomalies
