import threading
from functools import lru_cache
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
from backend.config import MODEL, MODEL_DIR


def preferred_device():
    import os

    requested = os.getenv("CCTV_DEVICE", "auto")
    if requested not in ("auto", "mps", "cpu", "cuda"):
        raise ValueError("CCTV_DEVICE must be auto, mps, cpu, or cuda")
    if requested == "cuda" or (requested == "auto" and torch.cuda.is_available()):
        return "cuda"
    if requested == "mps" or (
        requested == "auto"
        and hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return "mps"
    return "cpu"


class ClipEngine:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = preferred_device()
        self.status = "Not loaded"
        self.error = None
        self.lock = threading.RLock()
        self.dimension = None

    def load(self):
        with self.lock:
            if self.model is not None:
                return
            self.status = "Loading"
            try:
                local = MODEL_DIR / "clip-vit-base-patch32"
                source = (
                    str(local)
                    if MODEL == "openai/clip-vit-base-patch32"
                    and (local / ".ready").exists()
                    else MODEL
                )
                try:
                    processor = CLIPProcessor.from_pretrained(source, use_fast=False, local_files_only=True)
                    model = CLIPModel.from_pretrained(source, local_files_only=True).eval()
                except Exception:
                    processor = CLIPProcessor.from_pretrained(source, use_fast=False)
                    model = CLIPModel.from_pretrained(source).eval()
                try:
                    model.to(self.device)
                except RuntimeError:
                    if self.device == "cpu":
                        raise
                    self.device = "cpu"
                    model.to("cpu")
                self.processor, self.model = processor, model
                self.dimension = int(model.config.projection_dim)
                self.status = "Loaded"
                self.error = None
            except Exception:
                self.status = "Error"
                self.error = "Embedding model could not load. Run scripts/download_models.py; check disk space and network."
                raise

    def _encode(self, **kwargs):
        with self.lock:
            self.load()
            inputs = self.processor(return_tensors="pt", **kwargs).to(self.device)
            method = (
                self.model.get_text_features
                if "text" in kwargs
                else self.model.get_image_features
            )
            with torch.inference_mode():
                try:
                    result = method(**inputs)
                except RuntimeError:
                    if self.device == "cpu":
                        raise
                    self.device = "cpu"
                    self.model.to("cpu")
                    result = method(**inputs.to("cpu"))
                if hasattr(result, "pooler_output") and result.pooler_output is not None:
                    result = result.pooler_output
                elif hasattr(result, "image_embeds") and result.image_embeds is not None:
                    result = result.image_embeds
                elif hasattr(result, "text_embeds") and result.text_embeds is not None:
                    result = result.text_embeds
                elif not isinstance(result, torch.Tensor) and hasattr(result, "last_hidden_state"):
                    result = result.last_hidden_state[:, 0]
                result = torch.nn.functional.normalize(result.float(), dim=-1)
            vectors = result.cpu().numpy().astype(np.float32)
            if not np.isfinite(vectors).all() or vectors.shape[-1] != self.dimension:
                raise RuntimeError("Invalid embedding output")
            return vectors

    @lru_cache(maxsize=128)
    def encode_text(self, query):
        return self._encode(text=[query], padding=True, truncation=True)[0]

    def encode_images(self, images):
        return self._encode(
            images=[
                im.convert("RGB")
                if isinstance(im, Image.Image)
                else Image.fromarray(im).convert("RGB")
                for im in images
            ]
        )

    def encode_image(self, image):
        return self.encode_images([image])[0]

    def get_embedding_dimension(self):
        self.load()
        return self.dimension
