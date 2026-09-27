from ultralytics import YOLO
from backend.config import YOLO_PATH
from backend.embeddings.clip_engine import preferred_device

CLASSES = [0, 1, 2, 3, 5, 7, 24, 26, 28]
LABELS = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "bus",
    "truck",
    "backpack",
    "handbag",
    "suitcase",
]


class Detector:
    def __init__(self):
        self.model = None
        self.device = preferred_device()
        self.status = "Not loaded"

    def load(self):
        if self.model is None:
            self.status = "Loading"
            try:
                self.model = YOLO(str(YOLO_PATH))
                self.status = "Loaded"
            except Exception:
                self.status = "Error"
                raise

    def reset(self):
        self.load()
        if self.model.predictor is not None:
            for tracker in getattr(self.model.predictor, "trackers", []):
                tracker.reset()

    def detect(self, frame):
        self.load()
        options = dict(
            persist=True,
            tracker="bytetrack.yaml",
            classes=CLASSES,
            imgsz=640,
            conf=0.25,
            verbose=False,
        )
        try:
            result = self.model.track(frame, device=self.device, **options)[0]
        except RuntimeError:
            if self.device == "cpu":
                raise
            self.device = "cpu"
            result = self.model.track(frame, device="cpu", **options)[0]
        boxes = result.boxes
        detections = []
        for box in boxes:
            detections.append(
                dict(
                    label=result.names[int(box.cls.item())],
                    confidence=float(box.conf.item()),
                    bounding_box=[round(float(x), 2) for x in box.xyxy[0].tolist()],
                    track_id=int(box.id.item()) if box.id is not None else None,
                )
            )
        return detections
