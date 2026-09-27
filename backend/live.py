"""Session-only RTSP credentials, bounded capture, and finalized segment ingestion."""

import shutil
import signal
import subprocess
import threading
import time
import uuid
import sys
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from backend.config import DATA, MAX_LIVE_CAMERAS
from backend.processing.media import probe
from backend.storage import db


def local_devices():
    if sys.platform.startswith("linux"):
        return [
            dict(id=str(p), name=p.name)
            for p in sorted(Path("/dev").glob("video[0-9]*"))
        ]
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-f",
                    "avfoundation",
                    "-list_devices",
                    "true",
                    "-i",
                    "",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            video = result.stderr.split("AVFoundation video devices:")[-1].split(
                "AVFoundation audio devices:"
            )[0]
            return [
                dict(id=i, name=name)
                for i, name in re.findall(r"\[(\d+)\] ([^\n]+)", video)
                if "Capture screen" not in name
            ]
        except (OSError, subprocess.SubprocessError):
            return []
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-f",
                    "dshow",
                    "-list_devices",
                    "true",
                    "-i",
                    "dummy",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="ignore",
            )
            names = re.findall(r'"([^"]+)"\s+\(video\)', result.stderr)
            return [dict(id=name, name=name) for name in names]
        except (OSError, subprocess.SubprocessError):
            return []
    return []


def capture_command(url, folder, segment_seconds=30, source_type="rtsp"):
    if source_type == "usb":
        if sys.platform == "win32":
            inputs = ["-f", "dshow", "-rtbufsize", "100M", "-i", f"video={url}"]
        elif sys.platform == "darwin":
            inputs = ["-f", "avfoundation", "-framerate", "30", "-i", f"{url}:none"]
        else:
            inputs = ["-f", "v4l2", "-i", url]
    elif source_type == "http":
        inputs = [
            "-protocol_whitelist",
            "http,https,tcp,tls,crypto",
            "-rw_timeout",
            "10000000",
            "-i",
            url,
        ]
    else:
        inputs = ["-rtsp_transport", "tcp", "-timeout", "10000000", "-i", url]
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        *inputs,
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        "scale='min(1280,iw)':-2,fps=15",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-g",
        "30",
        "-sc_threshold",
        "0",
        "-force_key_frames",
        f"expr:gte(t,n_forced*{segment_seconds})",
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        "-segment_format",
        "mp4",
        str(folder / "%06d.mp4"),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        "fps=4,scale=640:-2",
        "-f",
        "image2",
        "-update",
        "1",
        "-atomic_writing",
        "1",
        str(folder / "preview.jpg"),
    ]


class LiveManager:
    def __init__(self, pipeline, segment_seconds=30):
        self.pipeline = pipeline
        self.segment_seconds = segment_seconds
        self.sessions = {}
        self.lock = threading.RLock()

    def status(self, cid):
        with self.lock:
            s = self.sessions.get(cid)
            if not s:
                return dict(
                    status="STOPPED",
                    segments=0,
                    message="Not connected",
                    preview=False,
                    fps=15,
                    resolution="1280x720",
                    elapsed_seconds=0,
                    stream_url=f"/api/cameras/{cid}/stream",
                )
            preview = s.get("preview")
            try:
                fresh = preview and time.time() - preview.stat().st_mtime < 15
            except OSError:
                fresh = False
            elapsed = 0
            if s.get("started_at"):
                try:
                    dt = datetime.fromisoformat(s["started_at"])
                    elapsed = max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
                except Exception:
                    elapsed = 0
            return dict(
                status=s["status"],
                segments=s["segments"],
                message=s["message"],
                preview=bool(fresh),
                started_at=s["started_at"],
                duration_minutes=s["duration_minutes"],
                fps=15,
                resolution="1280x720",
                elapsed_seconds=elapsed,
                stream_url=f"/api/cameras/{cid}/stream",
            )

    def start(self, cid, url, duration_minutes, source_type="rtsp"):
        from urllib.parse import urlsplit

        if source_type == "usb":
            if url not in {d["id"] for d in local_devices()}:
                raise ValueError(
                    "Choose an available USB camera on the server computer. Check its camera permission."
                )
        elif urlsplit(url).scheme not in (
            {"rtsp", "rtsps"} if source_type == "rtsp" else {"http", "https"}
        ):
            raise ValueError("The stream URL must match the selected connection type.")
        with self.lock:
            old = self.sessions.get(cid)
            if old and old["thread"].is_alive():
                raise ValueError(
                    "This camera is already connecting or recording. Stop it first."
                )
            if sum(s["thread"].is_alive() for s in self.sessions.values()) >= MAX_LIVE_CAMERAS:
                raise ValueError(
                    f"This local app supports up to {MAX_LIVE_CAMERAS} simultaneous live cameras."
                )
            if not shutil.which("ffmpeg"):
                raise ValueError("Install FFmpeg before connecting a camera.")
            s = dict(
                status="CONNECTING",
                segments=0,
                message="Connecting to camera…",
                started_at=datetime.now(timezone.utc).isoformat(),
                duration_minutes=duration_minutes,
                source_type=source_type,
                stop=threading.Event(),
            )
            s["thread"] = threading.Thread(
                target=self._run, args=(cid, url, s), daemon=True
            )
            self.sessions[cid] = s
            s["thread"].start()
            return self.status(cid)

    def stop(self, cid):
        with self.lock:
            s = self.sessions.get(cid)
            if s and s["thread"].is_alive():
                s["status"] = "STOPPING"
                s["message"] = "Finalizing the current recording…"
                s["stop"].set()
        return self.status(cid)

    def preview(self, cid):
        with self.lock:
            s = self.sessions.get(cid)
            if s and self.status(cid)["preview"]:
                try:
                    return s["preview"].read_bytes()
                except OSError:
                    pass
            return None

    @staticmethod
    def _terminate(proc):
        if proc.poll() is None:
            if proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.write(b"q\n")
                    proc.stdin.flush()
                except (OSError, ValueError):
                    pass
            try:
                proc.wait(timeout=6)
                return
            except subprocess.TimeoutExpired:
                pass
            if sys.platform == "win32":
                proc.terminate()
            else:
                proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=6)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

    def _ingest(self, cid, path, recorded_at, session):
        meta = probe(path)
        vid = str(uuid.uuid4())
        target = DATA / "uploads" / f"{vid}.mp4"
        path.replace(target)
        keys = [
            "id",
            "filename",
            "path",
            "camera_id",
            "source_kind",
            "recorded_at",
            *meta,
        ]
        try:
            db.execute(
                f"INSERT INTO videos({','.join(keys)}) VALUES({','.join('?' for _ in keys)})",
                (
                    vid,
                    f"Live {cid} {recorded_at.isoformat()}.mp4",
                    str(target),
                    cid,
                    "live",
                    recorded_at.isoformat(),
                    *meta.values(),
                ),
            )
        except Exception:
            target.replace(path)
            raise
        self.pipeline.enqueue(vid)
        session["segments"] += 1

    def _run(self, cid, url, session):
        deadline = time.monotonic() + session["duration_minutes"] * 60
        failed = False
        try:
            for attempt in range(4):
                if session["stop"].is_set() or time.monotonic() >= deadline:
                    break
                folder = DATA / "live" / cid / uuid.uuid4().hex
                folder.mkdir(parents=True, exist_ok=True)
                session["preview"] = folder / "preview.jpg"
                proc = None
                seen = set()
                origin = None
                try:
                    # stderr may include credentials. Never persist or return FFmpeg's output.
                    proc = subprocess.Popen(
                        capture_command(
                            url, folder, self.segment_seconds, session["source_type"]
                        ),
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    connected = time.monotonic()
                    while proc.poll() is None:
                        if session["stop"].wait(0.5) or time.monotonic() >= deadline:
                            break
                        if shutil.disk_usage(DATA).free < 512 * 1024 * 1024:
                            raise ValueError(
                                "Recording stopped: less than 512 MB of free storage remains."
                            )
                        with self.pipeline.lock:
                            if len(self.pipeline.active) >= 6:
                                raise ValueError(
                                    "Recording stopped: indexing is falling behind. Wait for queued footage, then reconnect."
                                )
                        preview = session["preview"]
                        if preview.exists():
                            if origin is None:
                                origin = datetime.now(timezone.utc)
                            if time.time() - preview.stat().st_mtime > 20:
                                break
                            session.update(
                                status="RECORDING",
                                message="Recording; completed 30-second segments are indexed automatically.",
                            )
                        elif time.monotonic() - connected > 20:
                            break
                        files = sorted(folder.glob("*.mp4"))
                        for path in files[:-1]:
                            if path.name not in seen:
                                self._ingest(
                                    cid,
                                    path,
                                    (origin or datetime.now(timezone.utc))
                                    + timedelta(
                                        seconds=int(path.stem) * self.segment_seconds
                                    ),
                                    session,
                                )
                                seen.add(path.name)
                finally:
                    if proc:
                        self._terminate(proc)
                    for path in sorted(folder.glob("*.mp4")):
                        if path.name not in seen:
                            try:
                                self._ingest(
                                    cid,
                                    path,
                                    (origin or datetime.now(timezone.utc))
                                    + timedelta(
                                        seconds=int(path.stem) * self.segment_seconds
                                    ),
                                    session,
                                )
                            except ValueError:
                                path.unlink(
                                    missing_ok=True
                                )  # Incomplete container after failed connection.
                    session["preview"].unlink(missing_ok=True)
                    if not list(folder.iterdir()):
                        folder.rmdir()
                if session["stop"].is_set() or time.monotonic() >= deadline:
                    break
                if attempt == 3:
                    raise ValueError(
                        "Cannot keep the camera connected. Check its stream URL, credentials, network, or USB permissions."
                    )
                session.update(
                    status="RECONNECTING",
                    message=f"Stream interrupted. Reconnecting ({attempt + 1}/3)…",
                )
                if session["stop"].wait(2**attempt):
                    break
        except Exception as exc:
            failed = True
            # Only our own fixed errors are exposed; subprocess/OS errors can contain a URL.
            message = (
                str(exc)
                if isinstance(exc, ValueError)
                and str(exc).startswith(("Recording stopped:", "Cannot keep"))
                else "Live capture failed. Check FFmpeg, camera connection, and available storage."
            )
            session.update(status="FAILED", message=message)
        finally:
            if not failed:
                session.update(
                    status="STOPPED",
                    message="Recording stopped. Saved segments remain available in Footage.",
                )

    def close(self):
        with self.lock:
            sessions = list(self.sessions.values())
            for session in sessions:
                session["stop"].set()
        for session in sessions:
            session["thread"].join()
