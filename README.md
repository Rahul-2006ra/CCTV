# CCTV Intelligence

**Search hours of CCTV footage in seconds.** A local visual investigation prototype with real object detection, object tracking, semantic retrieval, source timestamps and verified context clips. Search latency and indexing time depend on hardware and library size; the tagline is a product goal, not a benchmark.

The repository also includes a full local workspace snapshot, uploaded at the owner's request: model weights, recordings, generated media, databases, installed dependencies, build output and test caches. Large files use Git LFS; run `git lfs install` and `git lfs pull` after cloning. The included virtual environment and native dependencies are specific to the original Apple Silicon machine. For a fresh installation, create a new virtual environment and reinstall dependencies rather than relying on the snapshot's absolute paths. Existing snapshot files are tracked even where `.gitignore` excludes newly generated files. Runtime media and metadata in this snapshot are shared with everyone who can access the repository.

## Run locally

Requirements: Windows 10/11, macOS Apple Silicon or Linux, Python 3.11–3.13, Node 20+, FFmpeg with `libx264`, and approximately 3 GB free for dependencies/models plus footage/index storage. Python 3.11 is the tested interpreter. No paid service, API key, Docker, CUDA, Kafka or Ollama is required.

### Quick Start on Windows

Double click `start.bat` or run in PowerShell:
```powershell
.\start.ps1
```

Or run manually in two terminals:
```powershell
# Terminal 1 (Backend):
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2 (Frontend):
npm run dev --prefix frontend
```

### Quick Start on macOS / Linux

```bash
# macOS prerequisites, if missing
brew install python@3.11 node ffmpeg

# From the project root
./start.sh
```

Open [the workstation](http://localhost:5173). Backend: [localhost:8000](http://localhost:8000/docs). Health: [localhost:8000/api/system/health](http://localhost:8000/api/system/health).

`start.sh`, `start.bat`, and `start.ps1` manage servers on loopback. The first run needs internet to install dependencies and download public model weights. Subsequent inference is local. The UI uses system fonts and no external assets or analytics. A browser-compatible H.264 clip can be generated even if the original MOV/AVI cannot play in the browser.

To download models before the first upload:

```powershell
# Windows
.venv\Scripts\python.exe scripts\download_models.py

# macOS / Linux
.venv/bin/python scripts/download_models.py
```

Run only one backend process. Embedded Qdrant locks its persistent directory; multiple workers are not supported.

## First investigation

1. In **Cameras**, create a virtual camera such as “Main entrance”. No cameras or footage are invented on a fresh installation.
2. Optionally enter a restricted-zone polygon using normalized `[x,y]` points, for example `[[0.1,0.1],[0.8,0.1],[0.8,0.9],[0.1,0.9]]`. Coordinates start at the top-left. The detected object's bottom-center is tested against the polygon.
3. In **Footage**, choose the camera and upload an MP4, MOV or AVI. The server validates metadata and queues real processing automatically.
4. Wait for **READY**. Stage, completed frames, detection count, vector count and progress come from the worker. Failed jobs can be re-indexed. A restart marks interrupted jobs failed rather than pretending they completed.
5. In **Investigation**, search “Find a person”, “Find a white car”, or “Find the person wearing a red shirt”. Filter by camera, supported object, color or minimum relevance.
6. Open an event. The application generates a verified MP4 with ten seconds of context on each side, clamped to source boundaries. Use native playback controls, the source-time seek bar, **Open Original**, and **Export Clip**.
7. Review rule-generated candidates in **Alerts**, change review status, and inspect runtime status and attribution in **System / Credits**.

## Architecture

```text
React + Vite + TypeScript workstation (5173)
                │ REST + 2.5-second polling
FastAPI (8000) ─┼─ SQLite: cameras, videos, jobs, samples, alerts, searches, clips
                ├─ one local background worker
                │    video → sampled frames → YOLOv8n + ByteTrack
                │          → scene / object crops → CLIP image embeddings
                │          → persistent Qdrant cosine collection
                │          → track geometry → candidate alerts
                ├─ query → CLIP text embedding → vector candidates
                │        → object/color evidence → ranking → temporal groups
                └─ selected event → FFmpeg → probe + full decode → playable MP4
```

`backend/processing` owns ingestion; `detection` wraps YOLO and the library's ByteTrack integration; `embeddings` loads one shared CLIP instance; `vector_store` serializes persistent local Qdrant operations; `search` ranks and groups evidence; `events` owns rules; `clips` verifies exports; `api` validates requests. The worker interface can later be replaced by a queue without changing the frontend API. This prototype deliberately uses no distributed infrastructure.

## AI and scoring

* **Detection:** Ultralytics YOLOv8n COCO weights (`yolov8n.pt`). Enabled classes: person, bicycle, car, motorcycle, bus, truck, backpack, handbag and suitcase. Confidence is the actual detector output.
* **Tracking:** Ultralytics ByteTrack with persistent tracks, reset per recording. IDs are local to a video, not identities. Sampling at 1 FPS can fragment tracks or miss fast movement.
* **Embeddings:** `openai/clip-vit-base-patch32` through Transformers `CLIPModel`/`CLIPProcessor`. Float32 features are L2 normalized. The dimension is read from `model.config.projection_dim` and checked against actual output and the Qdrant collection. Scene and supported-object crops are embedded in batches of up to 16.
* **Hardware:** MPS when available, otherwise CPU. Runtime MPS failures retry on CPU. `CCTV_DEVICE=cpu` forces CPU. System reports the actual embedding and detector device independently.
* **Search:** camera/object filters are applied to Qdrant candidates. Recognized English object/color words supply inferred filters unless explicit filters override them. Color is measured from the same object crop (upper torso for people), with a 12% matching-pixel floor. The score is **CLIP cosine + 0.08 × matching-color fraction** when color is requested; otherwise raw cosine. A cosine floor of 0.12 also applies. The default minimum relevance is 0.15; tune it against authorized footage. Values are uncalibrated retrieval scores, not probabilities or accuracy estimates.
* **Grouping:** adjacent matches are grouped per video, object category and track, with a gap of about two sampling intervals. The best sample represents each event; first/last matched sample offsets define the event. Results are capped at 50 groups after 1,000 nearest candidates; truncation is disclosed. These are matching intervals, not precisely inferred action boundaries.
* **Timestamps:** decoded presentation time is used when available, with frame index / FPS fallback. All times are source-relative, not wall-clock camera times. Sampling resolution limits temporal precision; variable-frame-rate footage needs further validation.

CLIP can retrieve visual similarities to actions or spatial phrases; it does not verify “running”, “carrying”, “near the entrance”, abandonment or entry direction. The interface states this limitation. The prototype does not provide VLM action reasoning. Thresholds require validation on authorized, representative footage. See the [model card](https://huggingface.co/openai/clip-vit-base-patch32) for intended use and limitations; this is a local research prototype, not a validated surveillance deployment.

## Rule-based events

* **Restricted zone intrusion:** tracked object's bottom-center lies in the camera's polygon.
* **Rapid movement:** displacement exceeds 0.25 normalized image units per second across observations no more than three seconds apart. Not a calibrated physical speed or proof of running.
* **Unattended object candidate:** a bag remains within 0.025 normalized distance for 15 seconds with no detected person within 0.2 normalized distance. Nearby people reset the timer. Occlusion and missing detections can cause false positives. Ownership is never inferred.

Events are deduplicated per rule and track within a processing run. No alerts exist unless processing produces rule evidence. Changing zones requires re-indexing. Re-indexing rebuilds that video's vectors, samples and alerts. Delete removes associated source files, clips, thumbnails, vector points, metadata and saved-search references.

## Persistent data and privacy

`data/metadata.sqlite3` stores metadata; `data/qdrant/` stores on-disk vectors; `data/uploads/`, `data/thumbnails/`, and `data/clips/` contain media. Model weights live under `data/models/`. Everything is ignored by Git. Back up the entire data directory only after shutting down the backend. No memory-only vector fallback exists.

The server binds to loopback by default and has no authentication, authorization, encryption-at-rest or multi-user isolation. Keep it local. Uploaded footage is not sent to model providers. No facial recognition, biometric matching, cross-camera identity matching, or sensitive-attribute inference is implemented. Dependencies/model downloads are the only required network activity.

## Configuration

Export environment variables before starting (the example file is not automatically sourced):

| Variable | Default | Meaning |
|---|---|---|
| `CCTV_SAMPLE_FPS` | `1` | Sampling target, greater than 0 and at most 10 |
| `CCTV_DEVICE` | `auto` | `auto`, `mps`, `cpu`; unavailable MPS falls back to CPU |
| `CCTV_DATA_DIR` | `./data` | Absolute persistent storage location |
| `CCTV_MODEL_DIR` | `$CCTV_DATA_DIR/models` | Optional shared local model directory |
| `CCTV_EMBEDDING_MODEL` | `openai/clip-vit-base-patch32` | Compatible CLIP checkpoint; re-index after changing |
| `CCTV_CLIP_BEFORE` / `CCTV_CLIP_AFTER` | `10` / `10` | Context seconds |
| `CCTV_MAX_UPLOAD_MB` | `2048` | Upload size limit |
| `CCTV_PYTHON` | Auto-detect | Interpreter for initial virtual environment |

Changing the model creates a separate model-specific Qdrant collection. Re-index videos before searching with it. Do not change the configured model against existing READY videos without rebuilding their index.

## Demo and datasets

```bash
.venv/bin/python demo/generate_sample_video.py
# Upload demo/photographic-test.mp4 in Footage.
```

This generates a 12-second panning video of NASA's public-domain astronaut photograph supplied by scikit-image. Actual visual objects are processed by the real models; no fake detections or vectors are injected. It is a diagnostic photographic video, not real CCTV, and does not establish performance on bags, cars or actions. A “car” query on this fixture should return no matches. A red-shirt query may correctly return no results: the image does not supply ground-truth red-shirt footage.

For real CCTV evaluation, obtain footage you are authorized to process. [Oxford Town Centre](https://www.robots.ox.ac.uk/ActiveVision/Research/Projects/2009bbenfold_headpose/project.html) and [PETS](https://www.cvg.reading.ac.uk/PETS2009/a.html) are potential research sources; review their current access, consent, attribution and use conditions before downloading. They are not bundled or represented as public domain. No third-party CCTV footage is redistributed here.

## Testing

```bash
# Real models must be downloaded; tests use temporary SQLite/Qdrant data.
.venv/bin/python -m pytest -q
npm run build --prefix frontend

# With both application servers running and the generated demo available:
cd frontend
npx playwright install chromium
npx playwright test
```

The tests exercise database/health, metadata, bad uploads, request validation, color analysis, temporal grouping, rule events, persistent vector insert/search/delete, actual image/text embeddings and normalization, real upload→YOLO/ByteTrack→index→search, clip verification, alert status and deletion cleanup. Browser tests create a clearly named verification camera, upload the diagnostic video, run the three required queries, open a match, play the clip, inspect the timeline, and visit Alerts and Credits. They leave that labeled fixture in the workstation for inspection. See `docs/VALIDATION.md` for actual recorded results.

## API

Interactive documentation: [FastAPI /docs](http://localhost:8000/docs).

| Method | Path | Purpose |
|---|---|---|
| GET / POST | `/api/cameras` | List / create virtual cameras |
| PATCH / DELETE | `/api/cameras/{id}` | Edit camera / Delete camera |
| GET | `/api/cameras/{id}/stream` | Continuous live MJPEG stream for browser viewing |
| GET | `/api/cameras/{id}/preview` | Single latest captured camera frame |
| POST | `/api/cameras/{id}/connect` | Start camera stream and automatic background recording |
| POST | `/api/cameras/{id}/stop` | Stop camera stream and finalize recordings |
| GET / POST | `/api/videos` | List / upload multipart `file`, `camera_id` |
| GET / DELETE | `/api/videos/{id}` | Metadata / remove source and derived data |
| GET | `/api/videos/{id}/status` | Actual processing state and counts |
| POST | `/api/videos/{id}/process` | Queue rebuild |
| GET | `/api/videos/{id}/source` | Original file with byte-range support |
| GET | `/api/videos/{id}/segments` | Stored sampled-frame evidence |
| POST | `/api/search` | Progressive multi-clue visual query with filters |
| GET | `/api/search/{id}` | Saved investigation |
| POST | `/api/clips` | Generate context around `video_id`, `start`, `end` |
| GET | `/api/clips/{id}` | Play clip; `?download=true` exports |
| GET / PATCH | `/api/alerts`, `/api/alerts/{id}` | List candidates / change review status |
| GET | `/api/system/health`, `/api/system/credits` | Runtime state / attribution |
| GET | `/api/dashboard` | Aggregate counts, live cameras, and vector stats |

## Troubleshooting and performance

* **Model loading fails:** run `scripts/download_models.py`, check the backend log and available storage. Internet is needed only if weights are missing. Avoid stopping a download mid-file. Models are lazy-loaded once, not for every search.
* **MPS error or memory pressure:** restart with `CCTV_DEVICE=cpu`; reduce sampling. The worker downsizes frames to at most 1280 pixels and YOLO inference uses 640-pixel input. CPU is slower. No production throughput claim is made.
* **Qdrant lock:** stop duplicate backends; do not launch `uvicorn --workers 2`. Embedded storage is persistent and single-process. For future scale, replace the store adapter with a local Qdrant server.
* **Port occupied:** stop the prior server; `start.sh` fails explicitly instead of attaching to an unrelated process.
* **Bad/corrupt video:** upload a playable video or transcode with FFmpeg. A mid-stream decoding failure marks the job failed and removes its partial vectors; failed videos are excluded from search.
* **Original won't play:** some AVI/MOV codecs lack browser support. Generated clips use H.264 MP4; original file remains available to download.
* **No matches:** ensure footage is READY, reduce threshold, inspect inferred filters, or use simpler English object descriptions. A query cannot find a class that YOLO missed. No fallback fabricates results.
* **Clip timing:** full browser-compatible sources may use stream copy. Partial intervals are re-encoded to avoid keyframe offsets. All outputs are probed and fully decoded before returning a URL; exported clips omit audio in this MVP.
* **Storage:** uploads have a 2 GB default cap and reserve 256 MB while writing. Model downloads, thumbnails and Qdrant also need space. Large archives and prolonged jobs require disk monitoring and retention planning.

## Licenses, credits and next steps

Project license: **AGPL-3.0-or-later**, selected for compatibility with Ultralytics. Full text is in `LICENSE`. Read `THIRD_PARTY_NOTICES.md`, `docs/credits.json`, `docs/DEPENDENCY_LICENSES.json`, and the visible **System / Credits** page. The reference audit is in `docs/REFERENCE_AUDIT.md`. Looking Glass and CCTV-Vision have no license grant found; Event-Driven Video Analytics reserves rights; SentrySearch is Apache-2.0. All four were references only; no source was copied.

Live camera capture is now available in **Cameras** with selectable RTSP, HTTP HLS/MJPEG, and local USB inputs. Investigation results open into an evidence report with adjustable clip boundaries and an MP4 download. See [Live cameras and evidence clips](docs/LIVE_CAMERAS.md) for setup, supported devices, API details, and limitations.

Next priorities: evaluate retrieval on consented CCTV with labeled positive/negative examples; validate variable-frame-rate timestamps; improve action understanding and track continuity; add visual zone editing, configurable rule thresholds, authentication, retention controls and a durable job queue before multiple users or unattended production recording.
