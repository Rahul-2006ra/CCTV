"""One-time model download; subsequent runs use the local model cache."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.embeddings.clip_engine import ClipEngine
from backend.detection.detector import Detector

if __name__ == "__main__":
    detector = Detector()
    detector.load()
    engine = ClipEngine()
    engine.load()
    print(
        f"Models ready; embedding dimension={engine.get_embedding_dimension()}, device={engine.device}"
    )
