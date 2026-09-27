import json
import threading
import time
from unittest.mock import Mock

import pytest
from backend.config import DATA
from backend.storage import db
from backend.processing.media import probe, verify_decode
from backend.live import LiveManager


def wait_for(predicate, timeout=20):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if predicate():
            return
        time.sleep(0.1)
    raise AssertionError("Timed out waiting for capture")


def test_live_validation_does_not_expose_credentials(client):
    cid = client.post("/api/cameras", json={"name": "Live test"}).json()["id"]
    for url in (
        "file:///etc/passwd",
        "rtsp://user:SECRET@host:bad/live",
        "rtsp://user:SECRET@host/has space",
    ):
        response = client.post(f"/api/cameras/{cid}/connect", json={"url": url})
        assert response.status_code == 422
        assert "SECRET" not in response.text
        assert "input" not in response.text
    response = client.post(
        f"/api/cameras/{cid}/connect",
        json={"url": "http://user:SECRET@host/live", "source_type": "rtsp"},
    )
    assert response.status_code == 409
    assert "SECRET" not in response.text
    assert client.get(f"/api/cameras/{cid}/preview").status_code == 404
    assert client.post(f"/api/cameras/{cid}/stop").json()["status"] == "STOPPED"


def test_live_capture_finalizes_indexes_and_stops(sample_video, monkeypatch):
    # Real FFmpeg muxing/preview; use paced fixture frames instead of requiring a physical camera.
    from backend import live

    original = live.capture_command

    def fixture_command(url, folder, segment_seconds, source_type):
        cmd = original(url, folder, segment_seconds, source_type)
        input_end = cmd.index("-map")
        return (
            cmd[: cmd.index("-y") + 1]
            + ["-re", "-stream_loop", "-1", "-i", str(sample_video)]
            + cmd[input_end:]
        )

    monkeypatch.setattr(live, "capture_command", fixture_command)
    pipeline = Mock(lock=threading.RLock(), active=set())
    manager = LiveManager(pipeline, segment_seconds=2)
    db.execute("INSERT INTO cameras(id,name) VALUES('LIVE','Fixture source')")
    try:
        manager.start("LIVE", "rtsp://camera.example/live", 1)
        with pytest.raises(ValueError, match="already"):
            manager.start("LIVE", "rtsp://camera.example/live", 1)
        wait_for(lambda: manager.status("LIVE")["segments"] >= 1)
        assert manager.status("LIVE")["status"] == "RECORDING"
        assert manager.preview("LIVE").startswith(b"\xff\xd8")
        manager.stop("LIVE")
        wait_for(lambda: manager.status("LIVE")["status"] == "STOPPED")
        videos = db.rows("SELECT * FROM videos WHERE camera_id='LIVE'")
        assert len(videos) >= 2  # completed segment plus final partial segment
        assert pipeline.enqueue.call_count == len(videos)
        for video in videos:
            assert video["source_kind"] == "live"
            assert video["recorded_at"]
            assert probe(video["path"])["duration"] > 0
            verify_decode(video["path"])
        assert not list((DATA / "live" / "LIVE").rglob("*.mp4"))
    finally:
        manager.close()


def test_network_failure_has_bounded_retries_and_no_url_leak(monkeypatch):
    from backend import live

    import sys
    failing_cmd = ["cmd.exe", "/c", "exit 1"] if sys.platform == "win32" else ["false"]
    monkeypatch.setattr(live, "capture_command", lambda *args: failing_cmd)
    pipeline = Mock(lock=threading.RLock(), active=set())
    manager = LiveManager(pipeline)
    manager.start("FAILED", "rtsp://user:SECRET@invalid/live", 1)
    try:
        wait_for(lambda: manager.status("FAILED")["status"] == "FAILED", timeout=15)
        assert "SECRET" not in json.dumps(manager.status("FAILED"))
        assert pipeline.enqueue.call_count == 0
    finally:
        manager.close()


def test_exact_clip_download_and_evidence(client, sample_video):
    meta = probe(sample_video)
    keys = ["id", "filename", "path", *meta]
    db.execute(
        f"INSERT INTO videos({','.join(keys)}) VALUES({','.join('?' for _ in keys)})",
        ("evidence", "fixture.mp4", str(sample_video), *meta.values()),
    )
    for stamp, box in ((0, [10, 20, 30, 40]), (1, [40, 20, 60, 40])):
        payload = dict(
            timestamp=stamp,
            frame_width=100,
            detected_objects=[
                dict(label="person", track_id=1, bounding_box=box, colors={"red": 0.8})
            ],
        )
        db.execute(
            "INSERT INTO video_segments(id,video_id,timestamp,payload) VALUES(?,?,?,?)",
            (str(stamp), "evidence", stamp, json.dumps(payload)),
        )
    for aid, stamp in (("inside", 1), ("outside", 1.5)):
        db.execute(
            "INSERT INTO alerts(id,video_id,timestamp,event_type,details) VALUES(?,?,?,?,?)",
            (aid, "evidence", stamp, "Rapid movement", aid),
        )
    report = client.get("/api/videos/evidence/evidence?start=0&end=1.5").json()
    assert [event["details"] for event in report["events"]] == ["inside"]
    assert report["sample_count"] == 2
    assert "red" in report["observations"][0]
    assert "right" in report["observations"][0]
    assert "does not verify a crime" in report["limitation"]
    response = client.post(
        "/api/clips", json=dict(video_id="evidence", start=0.5, end=1.5, context=False)
    )
    assert response.status_code == 200
    clip = response.json()
    assert (clip["start"], clip["end"]) == (0.5, 1.5)
    assert clip["method"] == "h264 re-encode"
    assert probe(DATA / "clips" / f"{clip['id']}.mp4")["duration"] == pytest.approx(
        1, abs=0.1
    )
    download = client.get(clip["download_url"])
    assert download.status_code == 200
    assert "attachment" in download.headers["content-disposition"]
    assert download.headers["content-type"] == "video/mp4"
    assert len(download.content) > 1000
    assert (
        client.post(
            "/api/clips", json=dict(video_id="evidence", start=0, end=3, context=False)
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/clips", json=dict(video_id="evidence", start=1, end=1, context=False)
        ).status_code
        == 422
    )
    assert (
        client.get("/api/videos/evidence/evidence?start=0&end=999").status_code == 422
    )
