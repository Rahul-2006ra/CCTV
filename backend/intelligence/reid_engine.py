"""SentinelAI Multi-Camera Re-ID Feature Affinity Engine."""

import numpy as np
from typing import Dict, List, Any, Optional


class ReidEngine:
    """Computes cross-camera feature affinity using multimodal CLIP visual vectors

    and HSV torso/vehicle color histograms.
    """

    def __init__(self, clip_weight: float = 0.75, color_weight: float = 0.25):
        self.clip_weight = clip_weight
        self.color_weight = color_weight

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity between two normalized vectors."""
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot / (norm1 * norm2))

    @staticmethod
    def color_intersection(c1: Dict[str, Any], c2: Dict[str, Any]) -> float:
        """Calculate color profile similarity between two detected crops."""
        if not c1 or not c2:
            return 0.5  # Neutral fallback

        # If discrete color match (upper / lower or main)
        matches = 0
        total = 0
        for key in ("upper", "lower", "color", "dominant"):
            if key in c1 and key in c2:
                total += 1
                if c1[key] == c2[key]:
                    matches += 1

        if total > 0:
            return matches / total
        return 0.5

    def compute_affinity(
        self,
        v1: np.ndarray,
        v2: np.ndarray,
        color1: Optional[Dict[str, Any]] = None,
        color2: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compute composite Re-ID affinity score between 0.0 and 1.0."""
        cos_sim = self.cosine_similarity(v1, v2)
        # Rescale cosine similarity from typical CLIP range (0.4-1.0) to (0.0-1.0)
        norm_cos = max(0.0, min(1.0, (cos_sim - 0.45) / 0.55))

        col_sim = self.color_intersection(color1 or {}, color2 or {})
        composite = self.clip_weight * norm_cos + self.color_weight * col_sim
        return float(np.clip(composite, 0.0, 1.0))
