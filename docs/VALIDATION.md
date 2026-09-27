# Validation record — 2026-09-25

## Live camera and evidence update — 2026-09-26

- Backend: **17 passed**, including real YOLO/CLIP integration, migration-compatible storage, input redaction, bounded reconnect failure, real FFmpeg segment finalization/preview, and exact-interval downloadable MP4 validation. The four new live/evidence tests were rerun after hardening preview reads against concurrent shutdown; all passed.
- Browser: **2 passed**. Camera type choices, brand presets, invalid URL handling, automatic evidence view, playback, a 1.0–2.5 second trim, actual browser download, and camera-scoped positive/negative queries were verified. The browser fixture uses a unique camera so existing user footage cannot affect negative searches.
- Network integration: a temporary **MediaMTX v1.21.1** server on loopback published the labeled photographic fixture. Both actual RTSP/TCP and HTTP/HLS connections produced JPEG previews and finalized recordings, stopped cleanly, completed real detection/indexing, returned evidence descriptions, and exported nonempty MP4 attachments. This used the real running backend without a mocked capture command.
- Frontend production build and `ruff check backend` passed.
- No physical camera credentials were supplied. Physical camera compatibility, USB capture, proprietary cloud cameras, and arbitrary crime/action recognition have not been validated. Reports describe stored detections rather than inventing a crime narrative; users review and trim event boundaries.
- Test cameras and recordings remain clearly labeled in the local workspace. Temporary stream publisher/server processes were stopped after verification.

The following sections retain the original MVP validation record.

Pre-push review additionally corrected evidence-event filtering to exclude the exact end boundary, cleared stale descriptions when a replacement report fails, and tied browser acceptance to the exact newly uploaded video ID. Regression checks cover the end-boundary alert and a failed evidence response after an earlier successful clip.

Validation was run locally on Apple Silicon with Python 3.11.15, MPS available, FFmpeg installed, the downloaded YOLOv8n weights, and the local CLIP ViT-B/32 checkpoint.

## Automated checks

```text
13 passed, 1 warning in 4.66s
```

The warning is Starlette's upstream deprecation notice for its TestClient/httpx integration. It does not affect the application or test result.

```text
frontend: npm run build
vite v6.4.3 ... ✓ built
ruff check backend demo scripts
All checks passed!
```

The backend tests cover health and SQLite initialization, validation failures, metadata extraction, temporal grouping, color analysis, persistent Qdrant insert/search/delete, actual normalized CLIP image/text embeddings and dimension, actual YOLO/ByteTrack processing, vector counts, semantic search, red-color filtering, alert rules/status, clip generation/decode, and deletion cleanup.

## Browser acceptance

```text
1 passed (2.9s)
```

The Playwright workflow created a virtual camera, uploaded `demo/photographic-test.mp4`, waited for actual READY state, asserted non-zero detections and vectors, searched “Find a person”, opened a match, generated and played the verified MP4 context clip, moved the source timeline, checked metadata and export, searched the red-shirt and car queries, opened Alerts, and opened System / Credits. No page errors were reported. Screenshots from the latest run are [investigation-results.png](investigation-results.png), [investigation-review.png](investigation-review.png), and [system-credits.png](system-credits.png).

## Runtime health after acceptance

```json
{
  "status": "ok",
  "python": "3.11.15",
  "device": "Apple Silicon",
  "acceleration": "mps",
  "detector_acceleration": "mps",
  "model_status": "Loaded",
  "detector_status": "Loaded",
  "vector_db": "Connected",
  "sqlite": "Connected",
  "ffmpeg": "Available",
  "sample_fps": 1.0
}
```

The running workspace contains the diagnostic fixture created by browser acceptance: two virtual cameras, two READY recordings, actual detections, vectors, alerts and saved investigations. These are local test artifacts and can be removed from Footage in the UI. The demo video itself is intentionally retained under `demo/` as a repeatable test input.

## What this validates and what it does not

The checks prove the local pipeline runs end to end on the included photographic fixture. They do not establish retrieval accuracy for authorized CCTV footage, action recognition accuracy, calibrated confidence, or suitability for high-impact decisions. The fixture contains a real astronaut photograph and is not a CCTV scene; car and red-shirt searches correctly return no match on it. Use consented, labeled footage to evaluate retrieval thresholds before any operational use.
