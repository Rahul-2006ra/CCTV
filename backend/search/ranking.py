import re
from backend.detection.detector import LABELS
from backend.color_analysis.color_detector import COLORS


def attributes(query, object_type=None, color=None):
    words = set(re.findall(r"[a-z]+", query.lower()))
    aliases = {
        "someone": "person",
        "somebody": "person",
        "people": "person",
        "wearing": "person",
        "man": "person",
        "men": "person",
        "woman": "person",
        "women": "person",
        "boy": "person",
        "girl": "person",
        "kid": "person",
        "child": "person",
        "guy": "person",
        "pedestrian": "person",
        "runner": "person",
        "intruder": "person",
        "thief": "person",
        "suspect": "person",
        "driver": "person",
        "officer": "person",
        "guard": "person",
        "worker": "person",
        "individual": "person",
        "human": "person",
        "cars": "car",
        "vehicle": "car",
        "automobile": "car",
        "trucks": "truck",
        "pickup": "truck",
        "lorry": "truck",
        "van": "truck",
        "buses": "bus",
        "coach": "bus",
        "bike": "bicycle",
        "bikes": "bicycle",
        "bicycles": "bicycle",
        "cyclist": "bicycle",
        "cycling": "bicycle",
        "motorbikes": "motorcycle",
        "motorbike": "motorcycle",
        "scooter": "motorcycle",
        "moped": "motorcycle",
        "backpacks": "backpack",
        "pack": "backpack",
        "bag": "handbag",
        "bags": "handbag",
        "purse": "handbag",
        "handbags": "handbag",
        "suitcases": "suitcase",
        "luggage": "suitcase",
        "baggage": "suitcase",
    }
    words.update(aliases[w] for w in list(words) if w in aliases)
    return object_type or next((x for x in LABELS if x in words), None), color or next(
        (c for c in COLORS if c in words), None
    )


def group_temporally(hits, gap=2.1):
    # Keep distinct objects/tracks separate and collapse frame/crop duplication.
    buckets = {}
    for hit in hits:
        key = (hit["video_id"], hit.get("track_id"), hit["object_type"])
        buckets.setdefault(key, []).append(hit)
    groups = []
    for values in buckets.values():
        values.sort(key=lambda x: x["timestamp"])
        current = []
        for hit in values:
            if current and hit["timestamp"] - current[-1]["timestamp"] > gap:
                groups.append(current)
                current = []
            current.append(hit)
        if current:
            groups.append(current)
    events = []
    for group in groups:
        best = max(group, key=lambda x: x["score"])
        events.append(
            dict(
                best,
                start=group[0]["timestamp"],
                end=group[-1]["timestamp"],
                matched_frames=len(set(x["timestamp"] for x in group)),
            )
        )
    return sorted(events, key=lambda x: x["score"], reverse=True)
