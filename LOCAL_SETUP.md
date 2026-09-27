# Local Setup & Verification Guide (Windows & Cross-Platform)

This guide provides exact, tested steps to run and verify the **CCTV Intelligence Workstation** locally on Windows 10/11 or macOS/Linux.

---

## 1. Prerequisites Check

Before starting, ensure the following are installed:
1. **Python 3.11** (`python --version` -> `Python 3.11.x`)
2. **Node.js 20+** (`node --version` -> `v20+` or `v22+`)
3. **FFmpeg Essentials with libx264** (`ffmpeg -version` -> Gyan.FFmpeg or equivalent)

> On Windows, FFmpeg binaries (`ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe`) are already placed directly into `.venv\Scripts\` so they are detected immediately by all Python subprocesses.

---

## 2. Quick One-Click Launch

### Option A: Windows Batch Launcher
Double-click `start.bat` in the project root.

### Option B: PowerShell
```powershell
.\start.ps1
```

### Option C: Manual Launch (Two Terminals)
```powershell
# Terminal 1 - FastAPI Backend
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2 - Vite React Frontend
npm run dev --prefix frontend
```

Once launched:
* **Workstation UI**: [http://localhost:5173](http://localhost:5173)
* **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/api/system/health](http://localhost:8000/api/system/health)

---

## 3. Physical USB & Built-in Camera (Windows DirectShow)

To stream and record directly from your laptop's built-in webcam or USB camera:
1. Go to **Cameras** in the sidebar.
2. Under **Live Monitoring Wall**, or in the **Camera Configuration** tab:
   - Select connection type: `USB / Built-in camera on this computer`.
   - Click `Scan for cameras`.
   - On Windows, your physical camera (e.g. `Integrated Camera`) is automatically discovered using FFmpeg DirectShow.
   - Click `Connect & Stream Live`.
3. In the **Live Monitoring Wall**, observe:
   - Continuous browser MJPEG stream playing at low latency.
   - Telemetry HUD showing `● LIVE`, `15 FPS`, `1280x720`, and elapsed recording time.
   - Every 30-second segment is automatically indexed by YOLOv8, ByteTrack, and CLIP into Qdrant!

---

## 4. Progressive Investigation Demonstration

1. Navigate to **Investigation**.
2. Type an initial visual description, e.g.:
   ```text
   Find a person wearing a red shirt
   ```
3. Observe the initial matches and the **Progressive Clues Funnel** bar:
   ```text
   [ Clue 1: "Find a person wearing a red shirt" | 20 matches ]
   ```
4. In the `+ Add next clue` input, type:
   ```text
   black pants
   ```
   and click **Refine**.
5. Observe the candidates shrink (e.g. `20 matches ➔ 8 matches`) with visual candidate tracking!
6. Add another clue:
   ```text
   backpack
   ```
   and click **Refine**.
7. Observe the candidates shrink further to only the relevant matching events! Each result card displays green checkmarks for all satisfied clues.
8. Click on any event card to open the **Evidence Review**:
   - Preview the playable clip with 10 seconds of surrounding context.
   - Inspect the frame-by-frame object detections, color measurements, and timeline.
   - Download the verified MP4 clip directly.

---

## 5. Running Automated Tests

To run the complete test suite (18 unit, integration, and real pipeline tests):
```powershell
.venv\Scripts\pytest backend\tests -v
```

All 18 tests will execute and pass:
```text
backend/tests/test_core.py::test_database_and_health PASSED
backend/tests/test_core.py::test_empty_and_invalid_search PASSED
backend/tests/test_core.py::test_camera_zone_validation PASSED
backend/tests/test_core.py::test_metadata_and_bad_video PASSED
backend/tests/test_core.py::test_invalid_upload_and_missing_camera PASSED
backend/tests/test_core.py::test_temporal_grouping_separates_videos_tracks_and_gaps PASSED
backend/tests/test_core.py::test_color_and_query_attributes PASSED
backend/tests/test_core.py::test_qdrant_persistence_insert_search_delete PASSED
backend/tests/test_core.py::test_rule_events_dedup_movement_and_stationarity PASSED
backend/tests/test_core.py::test_context_clip_boundaries_and_decode PASSED
backend/tests/test_core.py::test_clip_partial_interval_is_reencoded PASSED
backend/tests/test_core.py::test_progressive_search_chain PASSED
backend/tests/test_live_evidence.py::test_live_validation_does_not_expose_credentials PASSED
backend/tests/test_live_evidence.py::test_live_capture_finalizes_indexes_and_stops PASSED
backend/tests/test_live_evidence.py::test_network_failure_has_bounded_retries_and_no_url_leak PASSED
backend/tests/test_live_evidence.py::test_exact_clip_download_and_evidence PASSED
backend/tests/test_real_pipeline.py::test_real_embeddings_dimension_and_semantics PASSED
backend/tests/test_real_pipeline.py::test_upload_track_index_search_clip_alert_delete PASSED
================== 18 passed, 1 warning in 105s ==================
```

---

## 6. Building the Frontend

```powershell
npm run build --prefix frontend
```
Builds cleanly with zero errors in ~7 seconds to `frontend/dist/`.
