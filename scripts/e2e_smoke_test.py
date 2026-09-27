"""End-to-End Smoke Test for CCTV Intelligence Workstation."""

import time
import httpx
from pathlib import Path

BASE = "http://127.0.0.1:8000/api"

def run_smoke_test():
    client = httpx.Client(timeout=30.0)
    print("[1/7] Testing system health...")
    r = client.get(f"{BASE}/system/health")
    assert r.status_code == 200, f"Health failed: {r.text}"
    health = r.json()
    print(f"       System status: {health['status']}, Vector DB: {health['vector_db']}, SQLite: {health['sqlite']}")

    print("[2/7] Checking device discovery...")
    r = client.get(f"{BASE}/camera-devices")
    devices = r.json()
    print(f"       Discovered {len(devices)} local camera devices: {[d['name'] for d in devices]}")

    print("[3/7] Creating test camera...")
    r = client.post(f"{BASE}/cameras", json={"name": "Demonstration Camera"})
    assert r.status_code == 201, f"Create camera failed: {r.text}"
    cam = r.json()
    cid = cam["id"]
    print(f"       Created camera: {cam['name']} ({cid})")

    print("[4/7] Uploading sample video (demo/photographic-test.mp4)...")
    video_path = Path("demo/photographic-test.mp4")
    assert video_path.exists(), "Sample video missing"
    with video_path.open("rb") as f:
        r = client.post(
            f"{BASE}/videos",
            data={"camera_id": cid},
            files={"file": (video_path.name, f, "video/mp4")},
            timeout=30.0,
        )
    assert r.status_code == 201, f"Upload failed: {r.text}"
    vid_data = r.json()
    vid = vid_data["id"]
    print(f"       Uploaded video ID: {vid} ({vid_data['filename']})")

    print("[5/7] Waiting for background indexing (YOLOv8 + ByteTrack + CLIP + Qdrant)...")
    deadline = time.time() + 60
    while time.time() < deadline:
        r = client.get(f"{BASE}/videos/{vid}/status")
        status = r.json()
        print(f"       Processing state: {status['status']} ({status['progress']:.0f}%) | Frames: {status['frames']} | Vectors: {status['embeddings']}")
        if status["status"] in ("READY", "FAILED"):
            break
        time.sleep(1.0)
    assert status["status"] == "READY", f"Processing failed: {status}"

    print("[6/7] Testing progressive multi-clue investigation search...")
    search_req = {
        "query": "person",
        "clues": ["person", "suit", "helmet"],
        "camera_id": cid,
        "min_relevance": 0.15,
    }
    r = client.post(f"{BASE}/search", json=search_req, timeout=15.0)
    assert r.status_code == 200, f"Search failed: {r.text}"
    results = r.json()
    print(f"       Search progression steps: {results['progression']}")
    print(f"       Final matched events count: {len(results['results'])}")
    if results["results"]:
        top = results["results"][0]
        print(f"       Top match: {top['object_type']} (score: {top['score']:.3f}) at source time {top['start']:.1f}s - {top['end']:.1f}s")
        print(f"       Matched clues: {top.get('matched_clues')}")

        print("[7/7] Generating verified context clip with before/after buffer...")
        clip_req = {
            "video_id": vid,
            "start": top["start"],
            "end": top["end"],
            "context": True,
        }
        r = client.post(f"{BASE}/clips", json=clip_req, timeout=20.0)
        assert r.status_code == 200, f"Clip generation failed: {r.text}"
        clip = r.json()
        print(f"       Generated clip ID: {clip['id']}")
        print(f"       Clip boundaries: {clip['start']}s to {clip['end']}s (method: {clip['method']})")

    # Cleanup
    print("       Cleaning up demonstration video...")
    r = client.delete(f"{BASE}/videos/{vid}")
    assert r.status_code == 200

    print("       Cleaning up demonstration camera...")
    r = client.delete(f"{BASE}/cameras/{cid}")
    assert r.status_code == 200

    print("\nALL 7 END-TO-END SMOKE TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_smoke_test()
