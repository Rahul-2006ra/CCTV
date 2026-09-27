"""Test DirectShow live camera stream on Windows."""

import time
import httpx

BASE = "http://127.0.0.1:8000/api"

def test_live_camera():
    client = httpx.Client(timeout=15.0)
    print("Listing discovered devices...")
    r = client.get(f"{BASE}/camera-devices")
    devices = r.json()
    print("Discovered devices:", [d["name"] for d in devices])
    if not devices:
        print("No DirectShow devices found, skipping physical camera test.")
        return

    dev_name = devices[0]["name"]
    print(f"Creating camera for '{dev_name}'...")
    r = client.post(f"{BASE}/cameras", json={"name": f"Live - {dev_name}"})
    assert r.status_code == 201
    cam = r.json()
    cid = cam["id"]

    try:
        print(f"Connecting live stream to '{dev_name}'...")
        r = client.post(f"{BASE}/cameras/{cid}/connect", json={"url": dev_name, "source_type": "usb"})
        print("Connect response:", r.status_code, r.json())
        assert r.status_code == 200

        # Wait a few seconds for frames to arrive
        print("Reading frames and telemetry...")
        time.sleep(3.0)

        # Check camera telemetry
        r = client.get(f"{BASE}/cameras/{cid}")
        cam_info = r.json()
        print("Camera info:", cam_info)
        live_info = cam_info.get("live", {})
        print(f"Live telemetry: status={live_info.get('status')}, fps={live_info.get('fps')}, resolution={live_info.get('resolution')}, elapsed={live_info.get('elapsed_seconds')}s")

        # Test streaming endpoint (read the first 4KB of MJPEG multipart stream)
        print("Connecting to MJPEG streaming endpoint...")
        with client.stream("GET", f"{BASE}/cameras/{cid}/stream") as stream_res:
            assert stream_res.status_code == 200
            content_type = stream_res.headers.get("content-type")
            print("Stream Content-Type:", content_type)
            assert "multipart/x-mixed-replace" in content_type
            chunk = next(stream_res.iter_bytes(chunk_size=4096))
            print(f"Received initial stream chunk: {len(chunk)} bytes")
            assert len(chunk) > 0

        print("MJPEG stream verified successfully!")

    finally:
        print("Disconnecting live camera...")
        client.post(f"{BASE}/cameras/{cid}/disconnect")
        time.sleep(1.0)
        client.delete(f"{BASE}/cameras/{cid}")
        print("Live camera cleaned up successfully.")

if __name__ == "__main__":
    test_live_camera()
