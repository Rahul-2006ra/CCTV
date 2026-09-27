"""Integration tests execute real YOLO/ByteTrack, CLIP, Qdrant and FFmpeg. No mocks."""

import time
import numpy as np
from PIL import Image
from skimage import data
from backend.embeddings.clip_engine import ClipEngine


def test_real_embeddings_dimension_and_semantics():
    engine = ClipEngine()
    image = engine.encode_image(Image.fromarray(data.astronaut()))
    text = engine.encode_text("a photograph of an astronaut")
    negative = engine.encode_text("a photograph of a green forest")
    assert len(image) == len(text) == engine.get_embedding_dimension()
    assert np.isclose(np.linalg.norm(image), 1, atol=1e-5)
    assert np.isclose(np.linalg.norm(text), 1, atol=1e-5)
    assert image @ text > image @ negative
    batch = engine.encode_images([Image.fromarray(data.astronaut())] * 2)
    assert batch.shape == (2, engine.get_embedding_dimension())
    assert np.allclose(batch[0], batch[1], atol=1e-4)


def test_upload_track_index_search_clip_alert_delete(client, sample_video):
    camera = client.post(
        "/api/cameras",
        json={"name": "Integration camera", "zone": [[0, 0], [1, 0], [1, 1], [0, 1]]},
    ).json()
    with sample_video.open("rb") as file:
        response = client.post(
            "/api/videos",
            data={"camera_id": camera["id"]},
            files={"file": ("sample.mp4", file, "video/mp4")},
        )
    assert response.status_code == 201, response.text
    video = response.json()
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        status = client.get(f"/api/videos/{video['id']}/status").json()
        if status["status"] in ("READY", "FAILED"):
            break
        time.sleep(0.25)
    assert status["status"] == "READY", status
    assert status["frames"] == 3 and status["objects"] >= 3
    assert status["embeddings"] > status["frames"]
    segments = client.get(f"/api/videos/{video['id']}/segments").json()
    assert any(
        d["track_id"] is not None for s in segments for d in s["detected_objects"]
    )
    assert client.get("/api/system/health").json()["vectors"] == status["embeddings"]
    result = client.post("/api/search", json={"query": "Find a person"}).json()
    assert result["results"], result
    event = result["results"][0]
    assert 0 <= event["timestamp"] < status["duration"]
    assert event["matched_frames"] == 3
    assert event["score"] == event["cosine"]
    assert event["evidence"]["sample_count"] == 3
    assert event["evidence"]["observations"]
    assert event["clip_start"] < event["clip_end"] <= status["duration"]
    assert (
        client.post("/api/search", json={"query": "Find a car"}).json()["results"] == []
    )
    red = client.post(
        "/api/search", json={"query": "Find the person wearing a red shirt"}
    )
    assert red.status_code == 200
    for hit in red.json()["results"]:
        assert hit["colors"]["red"] >= 0.12
    clip = client.post(
        "/api/clips",
        json={"video_id": video["id"], "start": event["start"], "end": event["end"]},
    )
    assert clip.status_code == 200, clip.text
    assert (
        client.get(clip.json()["url"], headers={"Range": "bytes=0-1023"}).status_code
        == 206
    )
    alerts = client.get("/api/alerts").json()
    assert alerts and alerts[0]["event_type"] == "Restricted zone intrusion"
    assert (
        client.patch(
            "/api/alerts/" + alerts[0]["id"], json={"status": "REVIEWED"}
        ).json()["status"]
        == "REVIEWED"
    )
    assert client.delete("/api/videos/" + video["id"]).status_code == 200
    assert client.get("/api/system/health").json()["vectors"] == 0
    assert client.get("/api/alerts").json() == []
    assert client.get("/api/search/" + result["id"]).json()["results"] == []
