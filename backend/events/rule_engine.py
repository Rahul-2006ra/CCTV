import math
import cv2
import numpy as np


class RuleEngine:
    """Geometric candidates, not confirmed intent or ownership. Coordinates are normalized."""

    def __init__(self, zone=None, stationary_seconds=15, rapid_speed=0.25):
        self.zone = np.array(zone, dtype=np.float32) if zone else None
        self.stationary_seconds = stationary_seconds
        self.rapid_speed = rapid_speed
        self.tracks = {}
        self.emitted = set()

    def evaluate(self, detections, timestamp, width, height):
        events = []
        people = [
            (
                (d["bounding_box"][0] + d["bounding_box"][2]) / 2 / width,
                d["bounding_box"][3] / height,
            )
            for d in detections
            if d["label"] == "person"
        ]
        for d in detections:
            tid = d["track_id"]
            if tid is None:
                continue
            x1, y1, x2, y2 = d["bounding_box"]
            point = ((x1 + x2) / 2 / width, y2 / height)
            prev = self.tracks.get(tid)
            stationary = timestamp
            types = []
            if (
                self.zone is not None
                and cv2.pointPolygonTest(self.zone, point, False) >= 0
            ):
                types.append(
                    (
                        "Restricted zone intrusion",
                        "HIGH",
                        "Track entered configured polygon.",
                    )
                )
            if prev and 0 < timestamp - prev["time"] <= 3:
                speed = math.dist(point, prev["point"]) / (timestamp - prev["time"])
                if (
                    d["label"]
                    in ("person", "car", "truck", "bus", "motorcycle", "bicycle")
                    and speed > self.rapid_speed
                ):
                    types.append(
                        (
                            "Rapid movement",
                            "MEDIUM",
                            f"Image-plane speed {speed:.3f} normalized units/s; not a real-world speed estimate.",
                        )
                    )
                if math.dist(point, prev["anchor"]) < 0.025:
                    stationary = prev["stationary"]
                unattended = not any(math.dist(point, p) < 0.2 for p in people)
                if (
                    d["label"] in ("backpack", "handbag", "suitcase")
                    and unattended
                    and timestamp - stationary >= self.stationary_seconds
                ):
                    types.append(
                        (
                            "Unattended object candidate",
                            "MEDIUM",
                            "Stationary bag with no nearby detected person; ownership is unknown.",
                        )
                    )
                if not unattended and d["label"] in ("backpack", "handbag", "suitcase"):
                    stationary = timestamp
            self.tracks[tid] = dict(
                point=point,
                time=timestamp,
                stationary=stationary,
                anchor=prev["anchor"]
                if prev and stationary == prev["stationary"]
                else point,
            )
            for event, severity, details in types:
                if (tid, event) not in self.emitted:
                    events.append(
                        dict(
                            timestamp=timestamp,
                            event_type=event,
                            severity=severity,
                            track_id=tid,
                            details=details,
                        )
                    )
                    self.emitted.add((tid, event))
        self.tracks = {
            k: v for k, v in self.tracks.items() if timestamp - v["time"] <= 30
        }
        return events
