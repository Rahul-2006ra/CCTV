import json
import subprocess
from fractions import Fraction
from pathlib import Path


def probe(path):
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=180,
            check=True,
        )
        data = json.loads(proc.stdout)
        video = next(s for s in data.get("streams", []) if s.get("codec_type") == "video")
        rate = video.get("avg_frame_rate", "0/1")
        if rate in ("0/0", "0/1", "N/A", "", None):
            rate = video.get("r_frame_rate", "30/1")
        try:
            fps = float(Fraction(rate))
        except (ValueError, ZeroDivisionError):
            fps = 30.0
        if fps <= 0:
            fps = 30.0

        raw_duration = video.get("duration")
        format_duration = data.get("format", {}).get("duration")
        if raw_duration not in (None, "N/A", ""):
            duration = float(raw_duration)
        elif format_duration not in (None, "N/A", ""):
            duration = float(format_duration)
        else:
            tags = video.get("tags", {})
            tag_dur = tags.get("DURATION") or tags.get("DURATION-eng")
            if tag_dur:
                parts = tag_dur.split(":")
                if len(parts) == 3:
                    duration = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                else:
                    duration = 1.0
            else:
                nb = video.get("nb_frames")
                if str(nb).isdigit() and fps > 0:
                    duration = float(nb) / fps
                else:
                    duration = 1.0

        width = int(video.get("width") or 0)
        height = int(video.get("height") or 0)
        if duration <= 0 or fps <= 0 or width <= 0 or height <= 0:
            raise ValueError("Invalid video stream dimensions or duration")

        nb_frames = video.get("nb_frames")
        frame_count = (
            int(nb_frames)
            if str(nb_frames).isdigit() and int(nb_frames) > 0
            else max(1, round(duration * fps))
        )

        return dict(
            duration=duration,
            fps=fps,
            width=width,
            height=height,
            frame_count=frame_count,
            codec=video.get("codec_name", "unknown"),
            size=Path(path).stat().st_size,
        )
    except FileNotFoundError as exc:
        raise ValueError("FFprobe is unavailable. Install FFmpeg.") from exc
    except (
        subprocess.SubprocessError,
        ValueError,
        KeyError,
        StopIteration,
        ZeroDivisionError,
    ) as exc:
        raise ValueError(
            "Cannot read video. Please upload a valid video file (MP4, MKV, AVI, MOV, WEBM, etc.) with a video stream."
        ) from exc


def verify_decode(path):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-f", "null", "-"],
        capture_output=True,
        check=True,
        timeout=120,
    )
