import os
from pathlib import Path
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import sys
venv_bin = str(Path(sys.executable).parent)
if venv_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{venv_bin}{os.pathsep}{os.environ.get('PATH', '')}"

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv("CCTV_DATA_DIR", str(ROOT / "data"))).resolve()
for folder in ("uploads", "clips", "thumbnails", "qdrant", "models"):
    (DATA / folder).mkdir(parents=True, exist_ok=True)
MODEL_DIR = Path(os.getenv("CCTV_MODEL_DIR", str(DATA / "models"))).resolve()
MODEL_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(MODEL_DIR / "huggingface"))
os.environ.setdefault("YOLO_CONFIG_DIR", str(DATA / "models" / "ultralytics"))
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
SAMPLE_FPS = float(os.getenv("CCTV_SAMPLE_FPS", "1"))
if not 0 < SAMPLE_FPS <= 10:
    raise ValueError("CCTV_SAMPLE_FPS must be greater than 0 and at most 10")
MAX_SAMPLE_FRAMES = int(os.getenv("CCTV_MAX_SAMPLE_FRAMES", "300"))
MODEL = os.getenv("CCTV_EMBEDDING_MODEL", "openai/clip-vit-base-patch32")
YOLO_PATH = MODEL_DIR / "yolov8n.pt"
CLIP_BEFORE = float(os.getenv("CCTV_CLIP_BEFORE", "10"))
CLIP_AFTER = float(os.getenv("CCTV_CLIP_AFTER", "10"))
MAX_UPLOAD = int(os.getenv("CCTV_MAX_UPLOAD_MB", "102400")) * 1024 * 1024
MAX_LIVE_CAMERAS = int(os.getenv("CCTV_MAX_LIVE_CAMERAS", "8"))

if CLIP_BEFORE < 0 or CLIP_AFTER < 0 or CLIP_BEFORE + CLIP_AFTER <= 0:
    raise ValueError("Clip context must be non-negative and total more than zero")
