import json
import logging
import math
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
import cv2
from PIL import Image
from backend.config import DATA, SAMPLE_FPS
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
        self.stopping = False

    def enqueue(self, vid):
        with self.lock:
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

    def process(self, vid, job):
        cap = None
        try:
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
            step = max(1, round(video["fps"] / SAMPLE_FPS))
            total = math.ceil(video["frame_count"] / step)
            count = objects = embedded = 0
            for index in range(0, video["frame_count"], step):
                if self.stopping:
                    raise RuntimeError("Shutdown interrupted processing")
                cap.set(cv2.CAP_PROP_POS_FRAMES, index)
                ok, frame = cap.read()
                if not ok:
                    if count > 0:
                        logger.info("Reached end of video stream at frame %s", index)
                        break
                    raise ValueError(f"Video decoding failed at frame {index}")
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                if timestamp <= 0 and index > 0:
                    timestamp = index / video["fps"]
                h, w = frame.shape[:2]
                if max(h, w) > 1280:
                    frame = cv2.resize(
                        frame,
                        (round(w * 1280 / max(h, w)), round(h * 1280 / max(h, w))),
                    )
                    h, w = frame.shape[:2]
                db.update_video(vid, status="DETECTING")
                detections = self.detector.detect(frame)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_name = f"{vid}_{index}.jpg"
                frame_path = DATA / "thumbnails" / frame_name
                if not cv2.imwrite(str(frame_path), frame):
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
                images = [Image.fromarray(rgb)]
                payloads = [
                    dict(
                        base,
                        object_type="scene",
                        track_id=None,
                        colors={},
                        bounding_box=None,
                    )
                ]
                for det in detections:
                    x1, y1, x2, y2 = [int(n) for n in det["bounding_box"]]
                    crop = rgb[max(0, y1) : min(h, y2), max(0, x1) : min(w, x2)]
                    if not crop.size:
                        continue
                    colors = analyze(crop, person=det["label"] == "person")
                    det["colors"] = colors
                    images.append(Image.fromarray(crop))
                    payloads.append(
                        dict(
                            base,
                            object_type=det["label"],
                            track_id=det["track_id"],
                            colors=colors,
                            bounding_box=det["bounding_box"],
                            detection_confidence=det["confidence"],
                        )
                    )
                db.update_video(vid, status="EMBEDDING")
                for offset in range(0, len(images), 16):
                    vectors = self.embedder.encode_images(images[offset : offset + 16])
                    db.update_video(vid, status="INDEXING")
                    self.store.upsert(vectors, payloads[offset : offset + 16])
                    embedded += len(vectors)
                db.execute(
                    "INSERT INTO video_segments(id,video_id,timestamp,payload) VALUES(?,?,?,?)",
                    (str(uuid.uuid4()), vid, timestamp, json.dumps(payloads[0])),
                )
                for event in rules.evaluate(detections, timestamp, w, h):
                    db.execute(
                        "INSERT INTO alerts(id,video_id,camera_id,timestamp,event_type,severity,track_id,details) VALUES(?,?,?,?,?,?,?,?)",
                        (
                            str(uuid.uuid4()),
                            vid,
                            video["camera_id"],
                            event["timestamp"],
                            event["event_type"],
                            event["severity"],
                            event["track_id"],
                            event["details"],
                        ),
                    )
                count += 1
                objects += len(detections)
                db.update_video(
                    vid,
                    progress=min(99, count / total * 100),
                    frames=count,
                    objects=objects,
                    embeddings=embedded,
                )
            if not count:
                raise ValueError("No frames decoded")
            db.update_video(vid, status="READY", progress=100)
            db.execute(
                "UPDATE processing_jobs SET status='READY',finished_at=CURRENT_TIMESTAMP WHERE id=?",
                (job,),
            )
        except Exception:
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
                cap.release()
            with self.lock:
                self.active.discard(vid)

    def close(self):
        self.stopping = True
        self.executor.shutdown(wait=True, cancel_futures=True)
