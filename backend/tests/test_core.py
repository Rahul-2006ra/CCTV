import json
import numpy as np
import pytest
from backend.storage import db
from backend.processing.media import probe
from backend.search.ranking import group_temporally, attributes
from backend.events.rule_engine import RuleEngine
from backend.vector_store.qdrant_store import VectorStore
from backend.color_analysis.color_detector import analyze


def test_database_and_health(client):
    assert db.one("SELECT COUNT(*) AS n FROM videos")["n"] == 0
    h = client.get("/api/system/health").json()
    assert h["vector_db"] == "Connected"
    assert h["ffmpeg"] == "Available"
    assert h["vectors"] == 0
    assert h["acceleration"] in ("mps", "cpu")
    assert client.get("/api/system/credits").status_code == 200


def test_empty_and_invalid_search(client):
    assert client.post("/api/search", json={"query": "   "}).status_code == 422
    response = client.post("/api/search", json={"query": "Find a person"})
    assert response.status_code == 200
    assert response.json()["results"] == []
    assert client.get("/api/search/" + response.json()["id"]).json() == response.json()
    assert (
        client.post(
            "/api/search", json={"query": "car", "min_relevance": -1}
        ).status_code
        == 422
    )


def test_camera_zone_validation(client):
    assert (
        client.post(
            "/api/cameras", json={"name": "x", "zone": [[0, 0], [1, 1]]}
        ).status_code
        == 422
    )
    assert client.post("/api/cameras", json={"name": " "}).status_code == 422
    c = client.post(
        "/api/cameras",
        json={"name": "Test zone", "zone": [[0, 0], [1, 0], [1, 1], [0, 1]]},
    )
    assert c.status_code == 201
    assert len(json.loads(c.json()["zone"])) == 4


def test_metadata_and_bad_video(sample_video, tmp_path):
    meta = probe(sample_video)
    assert meta["duration"] == pytest.approx(3, abs=0.1)
    assert meta["fps"] == 12
    assert meta["width"] == 768
    assert meta["frame_count"] == 36
    bad = tmp_path / "bad.mp4"
    bad.write_text("invalid")
    with pytest.raises(ValueError, match="Cannot read video"):
        probe(bad)


def test_invalid_upload_and_missing_camera(client):
    c = client.post("/api/cameras", json={"name": "Test"}).json()
    assert (
        client.post(
            "/api/videos",
            data={"camera_id": c["id"]},
            files={"file": ("bad.mp4", b"invalid", "video/mp4")},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/videos",
            data={"camera_id": c["id"]},
            files={"file": ("bad.txt", b"invalid", "text/plain")},
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/api/videos",
            data={"camera_id": "missing"},
            files={"file": ("bad.mp4", b"invalid", "video/mp4")},
        ).status_code
        == 404
    )
    assert client.get("/api/videos").json() == []
    assert client.get("/api/videos/missing/status").status_code == 404


def test_temporal_grouping_separates_videos_tracks_and_gaps():
    hits = [
        dict(
            video_id=v,
            track_id=track,
            object_type="person",
            timestamp=t,
            score=0.3 + t / 100,
        )
        for v, track, t in [
            ("a", 1, 0),
            ("a", 1, 1),
            ("a", 1, 2),
            ("a", 1, 8),
            ("a", 2, 1),
            ("b", 1, 1),
        ]
    ]
    groups = group_temporally(hits)
    assert len(groups) == 4
    first = next(
        x
        for x in groups
        if x["video_id"] == "a" and x["track_id"] == 1 and x["start"] == 0
    )
    assert (
        first["end"] == 2 and first["matched_frames"] == 3 and first["timestamp"] == 2
    )


def test_color_and_query_attributes():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, :, 0] = 255
    assert analyze(image, person=True)["red"] == 1
    assert attributes("Find someone wearing a red shirt") == ("person", "red")
    assert attributes("Find a white car") == ("car", "white")


def test_qdrant_persistence_insert_search_delete(tmp_path):
    store = VectorStore(tmp_path / "vectors")
    store.ensure(3)
    store.upsert(
        np.array([[1.0, 0, 0], [0, 1.0, 0]]),
        [
            dict(video_id="a", camera_id="A", object_type="person"),
            dict(video_id="b", camera_id="B", object_type="car"),
        ],
    )
    assert store.count() == 2
    assert store.search(np.array([1.0, 0, 0]))[0]["video_id"] == "a"
    assert len(store.search(np.array([1.0, 0, 0]), {"camera_id": "B"})) == 1
    store.close()
    store = VectorStore(tmp_path / "vectors")
    assert store.count() == 2
    store.delete_video("a")
    assert store.count() == 1
    store.close()


def detection(label="person", track=1, box=None):
    return dict(
        label=label,
        track_id=track,
        bounding_box=box or [10, 10, 30, 30],
        confidence=0.9,
    )


def test_rule_events_dedup_movement_and_stationarity():
    rules = RuleEngine([[0, 0], [1, 0], [1, 1], [0, 1]])
    events = rules.evaluate([detection()], 0, 100, 100)
    assert events[0]["event_type"] == "Restricted zone intrusion"
    assert rules.evaluate([detection()], 1, 100, 100) == []
    events = rules.evaluate([detection(box=[70, 10, 90, 30])], 2, 100, 100)
    assert events[0]["event_type"] == "Rapid movement"
    rules = RuleEngine(stationary_seconds=3)
    for t in range(3):
        assert not rules.evaluate([detection("backpack")], t, 100, 100)
    assert (
        rules.evaluate([detection("backpack")], 3, 100, 100)[0]["event_type"]
        == "Unattended object candidate"
    )
    rules = RuleEngine(stationary_seconds=2)
    for t in range(5):
        assert not rules.evaluate(
            [detection("backpack"), detection(track=2)], t, 100, 100
        )


def test_context_clip_boundaries_and_decode(sample_video):
    from backend.clips.clip_generator import generate
    from backend.processing.media import verify_decode
    from backend.config import DATA

    db.execute(
        "INSERT INTO videos(id,filename,path,duration) VALUES(?,?,?,?)",
        ("cliptest", "source.mp4", str(sample_video), 3),
    )
    result = generate(
        dict(id="cliptest", path=str(sample_video), duration=3, fps=12), 1, 2
    )
    assert result["start"] == 0 and result["end"] == 3
    output = DATA / "clips" / f"{result['id']}.mp4"
    assert probe(output)["codec"] == "h264"
    verify_decode(output)


def test_clip_partial_interval_is_reencoded(sample_video, tmp_path):
    import subprocess
    from backend.clips.clip_generator import generate
    from backend.config import DATA

    longer = tmp_path / "long.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-stream_loop",
            "9",
            "-i",
            str(sample_video),
            "-c",
            "copy",
            str(longer),
        ],
        check=True,
    )
    meta = probe(longer)
    db.execute(
        "INSERT INTO videos(id,filename,path,duration) VALUES(?,?,?,?)",
        ("partial", "long.mp4", str(longer), meta["duration"]),
    )
    result = generate(
        dict(id="partial", path=str(longer), duration=meta["duration"], fps=12), 15, 16
    )
    assert result["start"] == 5 and result["end"] == 26
    assert result["method"] == "h264 re-encode"
    assert probe(DATA / "clips" / f"{result['id']}.mp4")["duration"] == pytest.approx(
        21, abs=0.15
    )


def test_progressive_search_chain(client):
    response = client.post(
        "/api/search",
        json={"query": "person", "clues": ["red shirt", "black pants", "backpack"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "progression" in data
    assert len(data["progression"]) == 4
    assert data["clues"] == ["person", "red shirt", "black pants", "backpack"]
    assert all("clue" in p and "count" in p for p in data["progression"])

