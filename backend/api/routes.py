import json
import platform
import shutil
import sys
import uuid
from pathlib import Path
import fastapi
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response, StreamingResponse
from backend.config import DATA, ROOT, MODEL, MAX_UPLOAD, SAMPLE_FPS
from backend.storage import db
from backend.api.schemas import (
    CameraCreate,
    SearchRequest,
    ClipRequest,
    AlertUpdate,
    LiveConnect,
)
from backend.processing.media import probe
from backend.clips.clip_generator import generate

router = APIRouter(prefix="/api")


def get_video(vid):
    row = db.one("SELECT * FROM videos WHERE id=?", (vid,))
    if not row:
        raise HTTPException(404, "Video not found")
    return row


def public_video(v):
    return {k: x for k, x in v.items() if k != "path"} | {
        "source_url": f"/api/videos/{v['id']}/source"
    }


@router.get("/system/health")
def health(request: Request):
    state = request.app.state
    try:
        vectors = state.store.count()
        vector_state = "Connected"
    except Exception:
        vectors = None
        vector_state = "Disconnected"
    return dict(
        status="ok" if vector_state == "Connected" else "degraded",
        python=platform.python_version(),
        fastapi=fastapi.__version__,
        device="Apple Silicon"
        if sys.platform == "darwin" and platform.machine() == "arm64"
        else platform.machine(),
        acceleration=state.embedder.device,
        detector_acceleration=state.detector.device,
        model=MODEL,
        model_status=state.embedder.status,
        model_error=state.embedder.error,
        detector_status=state.detector.status,
        vector_db=vector_state,
        vectors=vectors,
        sqlite="Connected" if db.one("SELECT 1 AS ok") else "Disconnected",
        ffmpeg="Available"
        if shutil.which("ffmpeg") and shutil.which("ffprobe")
        else "Unavailable",
        storage_free_bytes=shutil.disk_usage(DATA).free,
        sample_fps=SAMPLE_FPS,
    )


@router.get("/system/credits")
def credits():
    return json.loads((ROOT / "docs" / "credits.json").read_text())


@router.get("/dashboard")
def dashboard(request: Request):
    state = request.app.state
    try:
        vectors = state.store.count()
    except Exception:
        vectors = 0
    live_count = sum(
        1
        for s in state.live.sessions.values()
        if s.get("status") in ("RECORDING", "CONNECTING")
    )
    total_cameras = db.one("SELECT COUNT(*) AS n FROM cameras")["n"]
    return dict(
        cameras=total_cameras,
        live_cameras=live_count,
        offline_cameras=max(0, total_cameras - live_count),
        vectors=vectors,
        indexed=db.one("SELECT COUNT(*) AS n FROM videos WHERE status='READY'")["n"],
        jobs=db.one(
            "SELECT COUNT(*) AS n FROM videos WHERE status NOT IN ('READY','FAILED','UPLOADED')"
        )["n"],
        duration=db.one(
            "SELECT COALESCE(SUM(duration),0) AS n FROM videos WHERE status='READY'"
        )["n"],
        searches=db.rows(
            "SELECT id,query,created_at FROM search_history ORDER BY created_at DESC LIMIT 8"
        ),
        alerts=db.rows("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 8"),
    )


@router.get("/cameras")
def cameras(request: Request):
    return [
        dict(c, live=request.app.state.live.status(c["id"]))
        for c in db.rows(
            "SELECT c.*,COUNT(v.id) AS footage_count,MAX(v.created_at) AS last_activity FROM cameras c LEFT JOIN videos v ON c.id=v.camera_id GROUP BY c.id ORDER BY c.created_at"
        )
    ]


@router.get("/cameras/{cid}")
def camera_detail(cid: str, request: Request):
    row = db.one("SELECT * FROM cameras WHERE id=?", (cid,))
    if not row:
        raise HTTPException(404, "Camera not found")
    return dict(row, live=request.app.state.live.status(cid))


@router.get("/camera-devices")
def camera_devices():
    from backend.live import local_devices

    return local_devices()


@router.post("/cameras/{cid}/connect")
def connect_camera(cid: str, body: LiveConnect, request: Request):
    if not db.one("SELECT id FROM cameras WHERE id=?", (cid,)):
        raise HTTPException(404, "Camera not found")
    try:
        return request.app.state.live.start(
            cid, body.url.get_secret_value(), body.duration_minutes, body.source_type
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/cameras/{cid}/stop")
def stop_camera(cid: str, request: Request):
    if not db.one("SELECT id FROM cameras WHERE id=?", (cid,)):
        raise HTTPException(404, "Camera not found")
    return request.app.state.live.stop(cid)


@router.get("/cameras/{cid}/preview")
def camera_preview(cid: str, request: Request):
    frame = request.app.state.live.preview(cid)
    if not frame:
        raise HTTPException(404, "Waiting for a current camera frame")
    return Response(
        frame, media_type="image/jpeg", headers={"Cache-Control": "no-store"}
    )


@router.get("/cameras/{cid}/stream")
async def camera_stream(cid: str, request: Request):
    if not db.one("SELECT id FROM cameras WHERE id=?", (cid,)):
        raise HTTPException(404, "Camera not found")

    async def frame_stream():
        import asyncio
        while True:
            if await request.is_disconnected():
                break
            status = request.app.state.live.status(cid)
            frame = request.app.state.live.preview(cid)
            if frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
            elif status["status"] in ("STOPPED", "FAILED"):
                break
            await asyncio.sleep(0.125)

    status = request.app.state.live.status(cid)
    frame = request.app.state.live.preview(cid)
    if not frame and status["status"] in ("STOPPED", "FAILED"):
        raise HTTPException(404, f"Camera stream offline ({status['message']})")

    return StreamingResponse(
        frame_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.post("/cameras", status_code=201)
def create_camera(body: CameraCreate):
    cid = "CAM-" + uuid.uuid4().hex[:6].upper()
    db.execute(
        "INSERT INTO cameras(id,name,zone) VALUES(?,?,?)",
        (cid, body.name, json.dumps(body.zone)),
    )
    return db.one("SELECT * FROM cameras WHERE id=?", (cid,))


@router.delete("/cameras/{cid}")
def delete_camera(cid: str, request: Request):
    if not db.one("SELECT id FROM cameras WHERE id=?", (cid,)):
        raise HTTPException(404, "Camera not found")
    footage_count = db.one(
        "SELECT COUNT(*) AS n FROM videos WHERE camera_id=?", (cid,)
    )["n"]
    if footage_count > 0:
        raise HTTPException(
            400,
            f"Cannot delete camera with {footage_count} associated footage recordings. Delete footage first.",
        )
    request.app.state.live.stop(cid)
    db.execute("DELETE FROM cameras WHERE id=?", (cid,))
    return {"deleted": True, "id": cid}


@router.patch("/cameras/{cid}")
def update_camera(cid: str, body: CameraCreate):
    if not db.one("SELECT id FROM cameras WHERE id=?", (cid,)):
        raise HTTPException(404, "Camera not found")
    db.execute(
        "UPDATE cameras SET name=?,zone=? WHERE id=?",
        (body.name, json.dumps(body.zone), cid),
    )
    return db.one("SELECT * FROM cameras WHERE id=?", (cid,))


@router.post("/videos", status_code=201)
def upload(
    request: Request,
    file: UploadFile = File(...),
    camera_id: str | None = Form(None),
):
    if not camera_id or camera_id in ("", "auto", "default", "undefined", "null"):
        existing_cam = db.one("SELECT id FROM cameras ORDER BY created_at ASC LIMIT 1")
        if existing_cam:
            camera_id = existing_cam["id"]
        else:
            camera_id = "CAM-MAIN"
            db.execute(
                "INSERT INTO cameras(id,name,zone) VALUES(?,?,?)",
                (camera_id, "Main Camera (Default)", "[]"),
            )
    elif not db.one("SELECT id FROM cameras WHERE id=?", (camera_id,)):
        raise HTTPException(404, "Choose a configured camera")
    filename = Path(file.filename or "upload").name
    suffix = Path(filename).suffix.lower()
    supported_formats = (
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
        ".m4v",
        ".wmv",
        ".flv",
        ".ts",
        ".3gp",
    )
    if suffix not in supported_formats:
        raise HTTPException(
            415,
            f"Supported video formats: MP4, MOV, AVI, MKV, WEBM, M4V, WMV, FLV, TS (received {suffix or 'none'})",
        )
    vid = str(uuid.uuid4())
    path = DATA / "uploads" / f"{vid}{suffix}"
    size = 0
    try:
        with path.open("wb") as target:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD:
                    raise HTTPException(413, "File exceeds upload limit")
                if shutil.disk_usage(DATA).free < len(chunk) + 256 * 1024 * 1024:
                    raise HTTPException(507, "Insufficient free storage")
                target.write(chunk)
        meta = probe(path)
        keys = ["id", "filename", "path", "camera_id", *meta]
        db.execute(
            "INSERT INTO videos("
            + ",".join(keys)
            + ") VALUES("
            + ",".join("?" for _ in keys)
            + ")",
            (vid, filename, str(path), camera_id, *meta.values()),
        )
    except ValueError as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(422, str(exc))
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        file.file.close()
    request.app.state.pipeline.enqueue(vid)
    return public_video(get_video(vid))


@router.get("/videos")
def videos():
    return [
        public_video(v)
        for v in db.rows("SELECT * FROM videos ORDER BY created_at DESC")
    ]


@router.get("/videos/{vid}")
@router.get("/videos/{vid}/status")
def video(vid: str):
    return public_video(get_video(vid))


@router.get("/videos/{vid}/source")
def source(vid: str):
    v = get_video(vid)
    return FileResponse(
        v["path"], filename=v["filename"], content_disposition_type="inline"
    )


@router.post("/videos/{vid}/process")
def process(vid: str, request: Request):
    get_video(vid)
    if not request.app.state.pipeline.enqueue(vid):
        raise HTTPException(409, "Video already queued or processing")
    return public_video(get_video(vid))


@router.get("/videos/{vid}/segments")
def segments(vid: str):
    get_video(vid)
    return [
        json.loads(x["payload"])
        for x in db.rows(
            "SELECT payload FROM video_segments WHERE video_id=? ORDER BY timestamp",
            (vid,),
        )
    ]


@router.get("/videos/{vid}/evidence")
def evidence(vid: str, start: float, end: float):
    from backend.search.evidence import describe
    import math

    video = get_video(vid)
    if (
        not math.isfinite(start)
        or not math.isfinite(end)
        or not 0 <= start <= end <= video["duration"]
    ):
        raise HTTPException(422, "Choose an interval inside the source video")
    return describe(video, start, end)


@router.delete("/videos/{vid}")
def delete_video(vid: str, request: Request):
    state = request.app.state
    with state.pipeline.lock:
        v = get_video(vid)
        if vid in state.pipeline.active:
            raise HTTPException(409, "Wait for processing to finish before deleting")
        state.store.delete_video(vid)
        clips = db.rows("SELECT path FROM clips WHERE video_id=?", (vid,))
        db.execute("DELETE FROM videos WHERE id=?", (vid,))
        Path(v["path"]).unlink(missing_ok=True)
        for p in (DATA / "thumbnails").glob(f"{vid}_*.jpg"):
            p.unlink(missing_ok=True)
        for c in clips:
            Path(c["path"]).unlink(missing_ok=True)
        # Search history contains thumbnails and metadata of source footage.
        with db.connection() as conn:
            for row in conn.execute("SELECT id,results FROM search_history").fetchall():
                result = json.loads(row["results"])
                result["results"] = [
                    r for r in result["results"] if r["video_id"] != vid
                ]
                conn.execute(
                    "UPDATE search_history SET results=? WHERE id=?",
                    (json.dumps(result), row["id"]),
                )
    return {"deleted": True}


@router.post("/search")
def search(body: SearchRequest, request: Request):
    try:
        return request.app.state.search.search(**body.model_dump())
    except Exception as exc:
        import logging

        logging.exception("Search failed")
        raise HTTPException(
            503, "Search unavailable. Check model and vector database status in System."
        ) from exc


@router.get("/search/{sid}")
def past_search(sid: str):
    row = db.one("SELECT results FROM search_history WHERE id=?", (sid,))
    if not row:
        raise HTTPException(404, "Investigation not found")
    return json.loads(row["results"])


@router.post("/clips")
def clip(body: ClipRequest):
    video = get_video(body.video_id)
    if (
        body.start > body.end
        or (body.start == body.end and not body.context)
        or body.end > video["duration"]
    ):
        raise HTTPException(422, "Choose an event interval inside the source video")
    try:
        return generate(video, body.start, body.end, context=body.context)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/clips/{cid}")
def clip_file(cid: str, download: bool = False):
    c = db.one("SELECT * FROM clips WHERE id=?", (cid,))
    if not c:
        raise HTTPException(404, "Clip not found")
    return FileResponse(
        c["path"],
        media_type="video/mp4",
        filename=f"context-{cid}.mp4",
        content_disposition_type="attachment" if download else "inline",
    )


@router.get("/alerts")
def alerts():
    return db.rows(
        "SELECT a.*,v.filename,v.duration FROM alerts a JOIN videos v ON v.id=a.video_id ORDER BY a.created_at DESC,a.timestamp DESC"
    )


@router.patch("/alerts/{aid}")
def alert_update(aid: str, body: AlertUpdate):
    if not db.one("SELECT id FROM alerts WHERE id=?", (aid,)):
        raise HTTPException(404, "Alert not found")
    db.execute("UPDATE alerts SET status=? WHERE id=?", (body.status, aid))
    return db.one("SELECT * FROM alerts WHERE id=?", (aid,))
