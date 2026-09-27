"""Readable reports grounded in stored detections; no invented action narration."""

import json
from collections import Counter
from backend.storage import db
from backend.config import SAMPLE_FPS


def timestamp(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(int(minutes), 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:04.1f}"


def describe(video, start, end):
    samples = [
        json.loads(row["payload"])
        for row in db.rows(
            "SELECT payload FROM video_segments WHERE video_id=? AND timestamp>=? AND timestamp<? ORDER BY timestamp",
            (video["id"], start, end),
        )
    ]
    maxima = Counter()
    tracks = {}
    timeline = []
    for sample in samples:
        detections = sample.get("detected_objects", [])
        counts = Counter(d["label"] for d in detections)
        maxima |= counts
        for d in detections:
            if d.get("track_id") is not None:
                tracks.setdefault((d["label"], d["track_id"]), []).append((sample, d))
        timeline.append(
            dict(
                timestamp=sample["timestamp"],
                description=", ".join(
                    f"{n} {label}{'s' if n != 1 else ''}"
                    for label, n in sorted(counts.items())
                )
                or "No supported objects detected in this sampled frame.",
            )
        )
    observations = []
    for (label, track), points in list(tracks.items())[:20]:
        first, last = points[0], points[-1]
        text = f"{label.capitalize()} track {track}: detected at {timestamp(first[0]['timestamp'])}–{timestamp(last[0]['timestamp'])} in {len(points)} sampled frames."
        colors = first[1].get("colors", {})
        if colors:
            color = max(colors, key=colors.get)
            text += f" Dominant measured crop color at first sample: {color}."
        if len(points) > 1:
            a, b = first[1].get("bounding_box"), last[1].get("bounding_box")
            width = first[0].get("frame_width", 0)
            if a and b and width:
                dx = ((b[0] + b[2]) - (a[0] + a[2])) / (2 * width)
                if abs(dx) > 0.05:
                    text += f" Box center shifts {abs(dx) * 100:.0f}% of image width toward the {'right' if dx > 0 else 'left'} (image motion, not physical speed)."
        observations.append(text)
    events = db.rows(
        "SELECT timestamp,event_type,details FROM alerts WHERE video_id=? AND timestamp>=? AND timestamp<? ORDER BY timestamp",
        (video["id"], start, end),
    )
    objects = ", ".join(
        f"up to {n} {label}{'s' if n != 1 else ''} per sampled frame"
        for label, n in sorted(maxima.items())
    )
    summary = f"In {video['filename']}, the interval {timestamp(start)}–{timestamp(end)} contains {len(samples)} indexed samples. "
    summary += (
        f"The detector records {objects}."
        if objects
        else "No supported objects were detected in these samples."
    )
    if events:
        summary += (
            " Rule signals in this interval: "
            + ", ".join(sorted({e["event_type"] for e in events}))
            + "."
        )
    return dict(
        summary=summary,
        observations=observations,
        timeline=timeline,
        events=events,
        sample_count=len(samples),
        source="Stored object detections, tracked boxes, color measurements, and event rules",
        limitation=f"This report describes sampled visual evidence at {SAMPLE_FPS:g} FPS. It does not verify a crime, intent, or the exact beginning/end of an action. Review the clip and adjust its boundaries. Tracks reset for each recording segment.",
    )
