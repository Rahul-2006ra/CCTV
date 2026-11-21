"""SentinelAI Multi-Camera Route Reconstruction & Trajectory Graph Engine."""

import math
import uuid
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from backend.storage import db
from backend.intelligence.reid_engine import ReidEngine
from backend.intelligence.risk_scoring import RiskScoringEngine


class RouteReconstructor:
    """Reconstructs spatio-temporal trajectories across disjoint camera views."""

    def __init__(self, store, embedder):
        self.store = store
        self.embedder = embedder
        self.reid = ReidEngine()

    def reconstruct_from_vector(
        self,
        target_vector: np.ndarray,
        time_window_minutes: int = 60,
        min_affinity: float = 0.65,
        target_label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query Qdrant across all camera collections and synthesize an ordered route graph."""
        # Query top candidate vectors
        candidates = self.store.search(
            target_vector,
            filters={"object_type": target_label} if target_label else None,
            limit=300,
        )

        if not candidates:
            return {
                "entity_id": f"TARGET-{uuid.uuid4().hex[:6].upper()}",
                "route": [],
                "total_cameras": 0,
                "first_seen": None,
                "last_seen": None,
                "max_risk_score": 10.0,
            }

        cameras = {c["id"]: c["name"] for c in db.rows("SELECT id, name FROM cameras")}

        # Filter by affinity and sort by timestamp
        matched_hits = []
        for hit in candidates:
            hit_vec = np.array(hit.get("vector") or target_vector, dtype=np.float32)
            affinity = self.reid.compute_affinity(target_vector, hit_vec, hit.get("colors"))
            if affinity >= min_affinity or hit.get("cosine", 0) >= 0.70:
                matched_hits.append({
                    "camera_id": hit.get("camera_id", "CAM-MAIN"),
                    "video_id": hit.get("video_id"),
                    "timestamp": float(hit.get("timestamp", 0.0)),
                    "track_id": hit.get("track_id"),
                    "label": hit.get("label", "person"),
                    "box": hit.get("bounding_box", [0, 0, 0, 0]),
                    "thumbnail": hit.get("thumbnail") or hit.get("crop_path"),
                    "affinity": round(affinity, 2),
                })

        # Sort chronologically
        matched_hits.sort(key=lambda x: (x["timestamp"]))

        # Group temporally into camera hops (steps)
        grouped_steps = []
        current_step = None

        for hit in matched_hits:
            cid = hit["camera_id"]
            ts = hit["timestamp"]

            if current_step is None:
                current_step = {
                    "camera_id": cid,
                    "camera_name": cameras.get(cid, cid),
                    "video_id": hit["video_id"],
                    "track_id": hit["track_id"],
                    "label": hit["label"],
                    "entry_time": ts,
                    "exit_time": ts,
                    "hits": [hit],
                    "thumbnail": hit["thumbnail"],
                    "max_affinity": hit["affinity"],
                }
            elif current_step["camera_id"] == cid and (ts - current_step["exit_time"]) <= 15.0:
                # Same camera contiguous dwell
                current_step["exit_time"] = ts
                current_step["hits"].append(hit)
                if hit["affinity"] > current_step["max_affinity"]:
                    current_step["max_affinity"] = hit["affinity"]
                    current_step["thumbnail"] = hit["thumbnail"]
            else:
                # Camera transition
                grouped_steps.append(current_step)
                current_step = {
                    "camera_id": cid,
                    "camera_name": cameras.get(cid, cid),
                    "video_id": hit["video_id"],
                    "track_id": hit["track_id"],
                    "label": hit["label"],
                    "entry_time": ts,
                    "exit_time": ts,
                    "hits": [hit],
                    "thumbnail": hit["thumbnail"],
                    "max_affinity": hit["affinity"],
                }

        if current_step:
            grouped_steps.append(current_step)

        # Synthesize trajectory node records with actions & risk scores
        entity_id = f"ENT-{uuid.uuid4().hex[:6].upper()}"
        route_nodes = []
        global_max_risk = 15.0

        for idx, step in enumerate(grouped_steps, 1):
            dwell = max(1.0, round(step["exit_time"] - step["entry_time"], 1))
            
            # Infer plausible tactical action
            if dwell > 45.0:
                action = f"Static Dwell / Loitering ({int(dwell)}s)"
                step_risk = 72.0
            elif idx == len(grouped_steps) and idx > 1:
                action = "Transit to Perimeter / Exit"
                step_risk = 55.0
            elif idx == 1:
                action = "Initial Sector Breach / Ingress"
                step_risk = 60.0
            else:
                action = f"Monitored Corridor Transit ({int(dwell)}s)"
                step_risk = 40.0

            if step_risk > global_max_risk:
                global_max_risk = step_risk

            node = {
                "step_order": idx,
                "camera_id": step["camera_id"],
                "camera_name": step["camera_name"],
                "video_id": step["video_id"],
                "track_id": step["track_id"],
                "entry_time": round(step["entry_time"], 1),
                "exit_time": round(step["exit_time"], 1),
                "dwell_seconds": dwell,
                "action": action,
                "confidence": round(step["max_affinity"] * 100, 1),
                "risk_score": step_risk,
                "thumbnail_url": step["thumbnail"],
            }
            route_nodes.append(node)

        # Persist into database for case management
        try:
            db.execute(
                """
                INSERT OR REPLACE INTO threat_entities(id, composite_score, severity_level, object_type, first_seen, last_seen, primary_crop_path, status)
                VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, 'TRACKED')
                """,
                (
                    entity_id,
                    global_max_risk,
                    RiskScoringEngine.get_severity_tier(global_max_risk),
                    route_nodes[0]["label"] if route_nodes else "person",
                    route_nodes[0]["thumbnail_url"] if route_nodes else None,
                ),
            )
        except Exception:
            pass

        return {
            "entity_id": entity_id,
            "route": route_nodes,
            "total_cameras": len(set(n["camera_id"] for n in route_nodes)),
            "first_seen": route_nodes[0]["entry_time"] if route_nodes else 0.0,
            "last_seen": route_nodes[-1]["exit_time"] if route_nodes else 0.0,
            "max_risk_score": global_max_risk,
            "severity_level": RiskScoringEngine.get_severity_tier(global_max_risk),
        }
