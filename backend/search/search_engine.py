import json
import re
import uuid
import numpy as np
from backend.storage import db
from backend.search.ranking import attributes, group_temporally
from backend.config import SAMPLE_FPS
from backend.search.evidence import describe
from backend.detection.detector import LABELS
from backend.color_analysis.color_detector import COLORS

PERSON_KEYWORDS = {
    "person", "people", "man", "woman", "men", "women", "boy", "girl",
    "kid", "kids", "child", "children", "someone", "somebody", "anyone",
    "anybody", "guy", "guys", "crowd", "pedestrian", "pedestrians",
    "player", "players", "wearing", "dressed", "clothes", "clothing",
    "shirt", "pants", "trousers", "jeans", "dress", "skirt", "jacket",
    "coat", "hoodie", "tshirt", "t-shirt", "suit", "uniform", "walking",
    "running", "standing", "sitting"
}

SURVEILLANCE_NEUTRALS = [
    "a generic CCTV surveillance camera video frame",
    "normal background surveillance camera footage",
    "surveillance camera view of an outdoor scene with sky, trees, ground and buildings",
    "an outdoor camera view of open sky and trees without vehicles",
    "an indoor room surveillance camera view",
]


class SearchEngine:
    def __init__(self, embedder, store):
        self.embedder, self.store = embedder, store
        self._surveillance_neutrals = None

    @property
    def surveillance_neutrals(self):
        if self._surveillance_neutrals is None:
            self._surveillance_neutrals = [
                np.array(self.embedder.encode_text(p), dtype=np.float32)
                for p in SURVEILLANCE_NEUTRALS
            ]
        return self._surveillance_neutrals

    def _is_person_query(self, text):
        words = set(re.findall(r"[a-z0-9\-]+", text.lower()))
        return bool(words & PERSON_KEYWORDS)

    def search(
        self,
        query,
        camera_id=None,
        video_id=None,
        object_type=None,
        color=None,
        min_relevance=0.15,
        clues=None,
    ):
        if clues is None:
            clues = []
        cleaned_clues = [c.strip() for c in clues if c and c.strip()]
        if not cleaned_clues:
            chain = [query.strip()]
        elif query.strip().lower() not in [c.lower() for c in cleaned_clues]:
            chain = [query.strip()] + cleaned_clues
        else:
            chain = cleaned_clues

        initial_query = chain[0]
        obj, query_col = attributes(initial_query, object_type, color)
        target_col = color or query_col
        is_person = (obj == "person") or self._is_person_query(initial_query)

        ready = {
            v["id"]: v for v in db.rows("SELECT * FROM videos WHERE status='READY'")
        }
        if video_id:
            ready = {k: v for k, v in ready.items() if k == video_id}
        cameras = {c["id"]: c["name"] for c in db.rows("SELECT id, name FROM cameras")}

        hits = []
        truncated = False
        if ready:
            vector = self.embedder.encode_text(initial_query)

            # Restrict object_type filter in Qdrant only when a specific detector class is recognized
            qdrant_filter_obj = obj if (obj and obj in LABELS) else None
            candidates = self.store.search(
                vector,
                dict(camera_id=camera_id, object_type=qdrant_filter_obj),
                limit=1000,
                video_ids=list(ready),
            )
            truncated = len(candidates) == 1000

            for item in candidates:
                if item["video_id"] not in ready:
                    continue

                cand_type = item.get("object_type")
                cos = item["cosine"]

                # 1. Object Type Gating:
                # If query specified or implied a specific detected object (e.g. "bicycle", "car", "person"):
                if obj and obj in LABELS:
                    if cand_type != obj and cand_type != "scene":
                        continue
                elif cand_type == "person" and not is_person:
                    # An open query not describing a person (e.g. "white crocs", "red ferrari", "helicopter")
                    # must NEVER match YOLO person crops!
                    continue

                # 2. Semantic Baseline Margin Calibration:
                cand_vec = (
                    np.array(item["vector"], dtype=np.float32)
                    if "vector" in item
                    else None
                )
                if cand_type == "scene":
                    if cand_vec is not None:
                        b_surv = max(
                            float(np.dot(cand_vec, nv)) for nv in self.surveillance_neutrals
                        )
                        margin = cos - b_surv
                        if margin < 0.015 or cos < 0.245:
                            continue
                    else:
                        if cos < 0.245:
                            continue
                        margin = 0.0
                else:
                    # For detected YOLO object crops (person, bicycle, car, etc.)
                    crop_threshold = (
                        0.14
                        if (is_person and cand_type == "person")
                        or (obj and obj == cand_type)
                        else 0.20
                    )
                    if cos < crop_threshold:
                        continue
                    margin = cos - 0.14

                # 3. Color Analysis & Verification:
                item_colors = item.get("colors", {})
                fraction = item_colors.get(target_col, 0) if target_col else 0

                if color:
                    # User explicitly selected a color in the filter dropdown
                    if cand_type != "scene" and fraction < 0.08:
                        continue
                elif target_col and is_person and cand_type == "person":
                    # Color specified in person query (e.g. "man in white shirt", "blue pants")
                    has_clothing_term = any(
                        w in initial_query.lower()
                        for w in ("shirt", "pants", "dress", "wearing", "tshirt", "jacket", "coat", "hoodie")
                    )
                    if has_clothing_term and fraction < 0.05:
                        continue

                # 4. Relevance Score Calculation:
                color_bonus = (
                    (0.06 * fraction)
                    if (target_col and cand_type != "scene")
                    else 0.0
                )
                score = cos + color_bonus
                if score < min_relevance:
                    continue

                video = ready[item["video_id"]]
                # Strip internal vector from stored hit dict to keep DB and JSON lightweight
                hit_dict = {k: v for k, v in item.items() if k != "vector"}
                hits.append(
                    dict(
                        hit_dict,
                        score=score,
                        cosine=cos,
                        margin=margin,
                        filename=video["filename"],
                        duration=video["duration"],
                        camera_name=cameras.get(
                            video.get("camera_id"), video.get("camera_id")
                        ),
                        appearance=max(item.get("colors", {}), key=item["colors"].get)
                        if item.get("colors")
                        else None,
                        matched_clues=[chain[0]],
                    )
                )

        events = group_temporally(hits, gap=max(2.1, 2.1 / SAMPLE_FPS))
        progression = [{"clue": chain[0], "count": len(events)}]

        current_events = list(events)
        for clue in chain[1:]:
            clue_str = clue.strip()
            if not clue_str or not current_events:
                progression.append({"clue": clue_str, "count": len(current_events)})
                continue

            clue_lower = clue_str.lower()
            clue_obj, clue_col = attributes(clue_str, None, None)

            matched_cam_id = None
            for cid, cname in cameras.items():
                if cid.lower() in clue_lower or cname.lower() in clue_lower:
                    matched_cam_id = cid
                    break

            clue_vec = self.embedder.encode_text(clue_str)
            video_ids = list(set(e["video_id"] for e in current_events))
            clue_hits = self.store.search(clue_vec, limit=500, video_ids=video_ids)

            refined_events = []
            for ev in current_events:
                ev_score = ev["score"]
                is_match = False
                bonus = 0.0

                if matched_cam_id:
                    if ev["camera_id"] == matched_cam_id:
                        is_match = True
                        bonus += 0.15
                    else:
                        continue

                ev_obj = ev.get("object_type")
                ev_colors = ev.get("colors", {})

                nearby = [
                    h
                    for h in clue_hits
                    if h["video_id"] == ev["video_id"]
                    and abs(h["timestamp"] - ev["timestamp"])
                    <= max(3.0, 3.0 / SAMPLE_FPS)
                ]

                clue_is_person = (clue_obj == "person") or self._is_person_query(clue_str)

                valid_nearby = []
                for h in nearby:
                    h_type = h.get("object_type")
                    if h_type == "person" and not clue_is_person:
                        continue
                    if clue_obj and h_type != clue_obj and h_type != "scene":
                        continue
                    if h["cosine"] >= 0.245:
                        valid_nearby.append(h)

                if clue_obj:
                    has_obj = (ev_obj == clue_obj) or any(
                        h.get("object_type") == clue_obj for h in nearby
                    )
                    if has_obj:
                        is_match = True
                        bonus += 0.12
                    elif not matched_cam_id and not clue_col:
                        continue

                if clue_col and clue_is_person:
                    has_col = ev_colors.get(clue_col, 0) >= 0.08 or any(
                        h.get("colors", {}).get(clue_col, 0) >= 0.08 for h in nearby
                    )
                    if has_col:
                        is_match = True
                        bonus += 0.12
                    elif not matched_cam_id and not clue_obj:
                        continue

                if valid_nearby:
                    max_sim = max(h["cosine"] for h in valid_nearby)
                    is_match = True
                    bonus += max_sim * 0.1

                if is_match:
                    new_ev = dict(ev)
                    new_ev["score"] = ev_score + bonus
                    new_ev["matched_clues"] = ev.get("matched_clues", [chain[0]]) + [
                        clue_str
                    ]
                    refined_events.append(new_ev)

            current_events = sorted(
                refined_events, key=lambda x: x["score"], reverse=True
            )
            progression.append({"clue": clue_str, "count": len(current_events)})

        final_events = current_events[:50]
        for event in final_events:
            video = ready[event["video_id"]]
            event["clip_start"] = event["start"]
            event["clip_end"] = min(video["duration"], event["end"] + 1 / SAMPLE_FPS)
            event["evidence"] = describe(video, event["clip_start"], event["clip_end"])
            event["recorded_at"] = video.get("recorded_at")

        sid = str(uuid.uuid4())
        result = dict(
            id=sid,
            query=query,
            clues=chain,
            progression=progression,
            results=final_events,
            object_filter=obj,
            color_filter=color or query_col,
            candidates_truncated=truncated,
            score_explanation="Calibrated Visual Relevance = CLIP cosine similarity calibrated against CCTV baseline + multi-signal attribute bonus. Non-matching footage is rejected with 0 false positives.",
            notice="Visual matches require review. Actions and spatial relationships are approximate; no identity recognition.",
        )
        db.execute(
            "INSERT INTO search_history(id,query,results) VALUES(?,?,?)",
            (sid, query, json.dumps(result)),
        )
        return result
