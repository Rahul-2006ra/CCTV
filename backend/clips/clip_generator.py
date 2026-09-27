import subprocess
import uuid
from backend.config import DATA, CLIP_BEFORE, CLIP_AFTER
from backend.processing.media import probe, verify_decode
from backend.storage import db


def generate(video, start, end, context=True):
    lower = max(0, start - (CLIP_BEFORE if context else 0))
    upper = min(video["duration"], end + (CLIP_AFTER if context else 0))
    if upper <= lower:
        raise ValueError("Clip interval is outside the source video.")
    cid = str(uuid.uuid4())
    path = DATA / "clips" / f"{cid}.mp4"
    base = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        str(lower),
        "-i",
        video["path"],
        "-t",
        str(upper - lower),
        "-map",
        "0:v:0",
        "-an",
    ]
    method = "stream copy"
    try:
        subprocess.run(
            base
            + [
                "-c:v",
                "copy",
                "-avoid_negative_ts",
                "make_zero",
                "-movflags",
                "+faststart",
                str(path),
            ],
            capture_output=True,
            timeout=120,
            check=True,
        )
        metadata = probe(path)
        # Copy is accepted only for the complete, browser-compatible source interval.
        # Mid-GOP cuts cannot guarantee exact frame alignment; re-encode those.
        if (
            lower > 0
            or upper < video["duration"]
            or metadata["codec"] != "h264"
            or abs(metadata["duration"] - (upper - lower)) > max(0.15, 2 / video["fps"])
        ):
            raise ValueError(
                "Re-encoding required for frame-accurate/browser-compatible clip"
            )
        verify_decode(path)
    except (subprocess.SubprocessError, ValueError):
        method = "h264 re-encode"
        try:
            subprocess.run(
                base
                + [
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "20",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(path),
                ],
                capture_output=True,
                timeout=300,
                check=True,
            )
            metadata = probe(path)
            verify_decode(path)
            if abs(metadata["duration"] - (upper - lower)) > max(
                0.15, 2 / video["fps"]
            ):
                raise ValueError("Clip duration verification failed")
        except Exception:
            path.unlink(missing_ok=True)
            raise ValueError("Clip generation failed. Check FFmpeg and source video.")
    db.execute(
        "INSERT INTO clips(id,video_id,start,end,path,method) VALUES(?,?,?,?,?,?)",
        (cid, video["id"], lower, upper, str(path), method),
    )
    return dict(
        id=cid,
        video_id=video["id"],
        start=lower,
        end=upper,
        url=f"/media/clips/{cid}.mp4",
        method=method,
        download_url=f"/api/clips/{cid}?download=true",
    )
