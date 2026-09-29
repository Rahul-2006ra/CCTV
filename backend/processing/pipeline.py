import json
import logging
import math
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
import cv2
from PIL import Image
from backend.config import DATA, SAMPLE_FPS, MAX_SAMPLE_FRAMES
from backend.storage import db
from backend.color_analysis.color_detector import analyze
from backend.events.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, embedder, detector, store):
        self.embedder, self.detector, self.store = embedder, detector, store
        self.executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="cctv-worker"
        )
        self.lock = threading.RLock()
        self.active = set()
        self.cancelled = set()
        self.stopping = False

    def cancel(self, vid):
        with self.lock:
            self.cancelled.add(vid)
            self.active.discard(vid)
            try:
                db.update_video(vid, status="FAILED", error="Processing cancelled by user")
                db.execute(
                    "UPDATE processing_jobs SET status='FAILED',error='Processing cancelled',finished_at=CURRENT_TIMESTAMP WHERE video_id=? AND status NOT IN ('READY','FAILED')",
                    (vid,),
                )
            except Exception:
                pass

    def enqueue(self, vid):
        with self.lock:
            self.cancelled.discard(vid)
            if vid in self.active:
                return False
            self.active.add(vid)
            job = str(uuid.uuid4())
            db.update_video(
                vid,
                status="QUEUED",
                progress=0,
                error=None,
                frames=0,
                objects=0,
                embeddings=0,
            )
            db.execute(
                "INSERT INTO processing_jobs(id,video_id,status) VALUES(?,?,?)",
                (job, vid, "QUEUED"),
            )
            self.executor.submit(self.process, vid, job)
            return True

    def _flush_batch(self, images, payloads, segments, alerts):
        if not images:
            return 0
        for offset in range(0, len(images), 32):
            chunk_imgs = images[offset : offset + 32]
            chunk_payloads = payloads[offset : offset + 32]
            vectors = self.embedder.encode_images(chunk_imgs)
            self.store.upsert(vectors, chunk_payloads)
        with db.connection() as conn:
            if segments:
                conn.executemany(
                    "INSERT INTO video_segments(id,video_id,timestamp,payload) VALUES(?,?,?,?)",
                    segments,
                )
            if alerts:
                conn.executemany(
                    "INSERT INTO alerts(id,video_id,camera_id,timestamp,event_type,severity,track_id,details) VALUES(?,?,?,?,?,?,?,?)",
                    alerts,
                )
        return len(images)

    def process(self, vid, job):
        cap = None
        try:
            with self.lock:
                if self.stopping or vid in self.cancelled:
                    logger.info("Processing aborted early for video %s", vid)
                    return

            video = db.one("SELECT * FROM videos WHERE id=?", (vid,))
            db.update_video(vid, status="PROCESSING")
            db.execute(
                "UPDATE processing_jobs SET status='PROCESSING' WHERE id=?", (job,)
            )
            self.store.delete_video(vid)
            db.execute("DELETE FROM video_segments WHERE video_id=?", (vid,))
            db.execute("DELETE FROM alerts WHERE video_id=?", (vid,))
            self.embedder.load()
            self.detector.reset()
            self.store.ensure(self.embedder.get_embedding_dimension())
            camera = db.one("SELECT * FROM cameras WHERE id=?", (video["camera_id"],))
            rules = RuleEngine(json.loads(camera["zone"]) if camera else [])
            cap = cv2.VideoCapture(video["path"])
            if not cap.isOpened():
                raise ValueError("Cannot decode source video")

            raw_fps = float(video.get("fps") or 30.0)
            if raw_fps <= 0:
                raw_fps = 30.0
            duration = max(1.0, float(video.get("duration") or 1.0))
            frame_count = int(video.get("frame_count") or round(duration * raw_fps))

            # Adaptive sampling: For long videos (>5 mins), automatically adjust sampling rate
            # so that large recordings index rapidly (e.g. in 20-40 seconds instead of hours)
            target_fps = SAMPLE_FPS
            if MAX_SAMPLE_FRAMES > 0 and duration * SAMPLE_FPS > MAX_SAMPLE_FRAMES:
                target_fps = MAX_SAMPLE_FRAMES / duration

            step = max(1, round(raw_fps / max(0.001, target_fps)))
            total = math.ceil(frame_count / step)

            count = objects = embedded = 0
            current_frame_pos = 0

            batch_images = []
            batch_payloads = []
            batch_segments = []
            batch_alerts = []
            last_progress_time = time.monotonic()

            for index in range(0, frame_count, step):
                if self.stopping or vid in self.cancelled:
                    logger.info("Processing halted for video %s (cancelled or stopping)", vid)
                    return

                # Fast sequential frame skipping:
                # For small skips (<30 frames), cap.grab() is faster than seeking.
                # For larger skips, cap.set with POS_MSEC jumps directly.
                skip = index - current_frame_pos
                if 0 <= skip < 30:
                    for _ in range(skip):
                        if not cap.grab():
                            break
                        current_frame_pos += 1
                else:
                    target_msec = (index / raw_fps) * 1000.0
                    cap.set(cv2.CAP_PROP_POS_MSEC, target_msec)
                    current_frame_pos = index

                ok, frame = cap.read()
                current_frame_pos += 1
                if not ok:
                    if count > 0:
                        logger.info("Reached end of video stream at frame %s", index)
                        break
                    raise ValueError(f"Video decoding failed at frame {index}")

                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                if timestamp <= 0 and index > 0:
                    timestamp = index / raw_fps

                h, w = frame.shape[:2]
                if max(h, w) > 960:
                    scale = 960.0 / max(h, w)
                    frame = cv2.resize(frame, (round(w * scale), round(h * scale)))
                    h, w = frame.shape[:2]

                detections = self.detector.detect(frame)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_name = f"{vid}_{index}.jpg"
                frame_path = DATA / "thumbnails" / frame_name

                # High-speed thumbnail write (max 640px, JPEG 80 quality for fast disk I/O)
                if max(h, w) > 640:
                    scale_t = 640.0 / max(h, w)
                    thumb = cv2.resize(frame, (round(w * scale_t), round(h * scale_t)))
                else:
                    thumb = frame
                if not cv2.imwrite(str(frame_path), thumb, [cv2.IMWRITE_JPEG_QUALITY, 80]):
                    raise ValueError("Cannot write thumbnail")

                base = dict(
                    video_id=vid,
                    camera_id=video["camera_id"],
                    timestamp=timestamp,
                    frame_path=f"/media/thumbnails/{frame_name}",
                    detected_objects=detections,
                    frame_width=w,
                    frame_height=h,
                )
                scene_payload = dict(
                    base,
                    object_type="scene",
                    track_id=None,
                    colors={},
                    bounding_box=None,
                )
                batch_images.append(Image.fromarray(rgb))
                batch_payloads.append(scene_payload)
                batch_segments.append(
                    (str(uuid.uuid4()), vid, timestamp, json.dumps(scene_payload))
                )

                for det in detections:
                    x1, y1, x2, y2 = [int(n) for n in det["bounding_box"]]
                    crop = rgb[max(0, y1) : min(h, y2), max(0, x1) : min(w, x2)]
                    if not crop.size:
                        continue
                    colors = analyze(crop, person=det["label"] == "person")
                    det["colors"] = colors
                    batch_images.append(Image.fromarray(crop))
                    batch_payloads.append(
                        dict(
                            base,
                            object_type=det["label"],
                            track_id=det["track_id"],
                            colors=colors,
                            bounding_box=det["bounding_box"],
                            detection_confidence=det["confidence"],
                        )
                    )

                for event in rules.evaluate(detections, timestamp, w, h):
                    batch_alerts.append(
                        (
                            str(uuid.uuid4()),
                            vid,
                            video["camera_id"],
                            event["timestamp"],
                            event["event_type"],
                            event["severity"],
                            event["track_id"],
                            event["details"],
                        )
                    )

                count += 1
                objects += len(detections)

                # Batch flush to CLIP and Qdrant every 32 images
                if len(batch_images) >= 32:
                    embedded += self._flush_batch(
                        batch_images, batch_payloads, batch_segments, batch_alerts
                    )
                    batch_images.clear()
                    batch_payloads.clear()
                    batch_segments.clear()
                    batch_alerts.clear()

                # Throttled progress update (max twice per second) to prevent DB lock contention
                now = time.monotonic()
                if now - last_progress_time >= 0.5:
                    last_progress_time = now
                    db.update_video(
                        vid,
                        progress=min(99, count / max(1, total) * 100),
                        frames=count,
                        objects=objects,
                        embeddings=embedded,
                    )

            # Flush any remaining items in the buffer
            if batch_images:
                embedded += self._flush_batch(
                    batch_images, batch_payloads, batch_segments, batch_alerts
                )
                batch_images.clear()
                batch_payloads.clear()
                batch_segments.clear()
                batch_alerts.clear()

            if not count:
                raise ValueError("No frames decoded")
            db.update_video(
                vid,
                status="READY",
                progress=100,
                frames=count,
                objects=objects,
                embeddings=embedded,
            )
            db.execute(
                "UPDATE processing_jobs SET status='READY',finished_at=CURRENT_TIMESTAMP WHERE id=?",
                (job,),
            )
        except Exception:
            with self.lock:
                if vid in self.cancelled or self.stopping:
                    return
            logger.exception("Processing failed for %s", vid)
            try:
                self.store.delete_video(vid)
            except Exception:
                logger.exception("Failed to clean partial vectors")
            message = "Processing failed. Check models, source video, storage and backend log; then re-index."
            db.update_video(vid, status="FAILED", error=message)
            db.execute(
                "UPDATE processing_jobs SET status='FAILED',error=?,finished_at=CURRENT_TIMESTAMP WHERE id=?",
                (message, job),
            )
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
            with self.lock:
                self.active.discard(vid)
                self.cancelled.discard(vid)

    def close(self):
        self.stopping = True
        self.executor.shutdown(wait=True, cancel_futures=True)
