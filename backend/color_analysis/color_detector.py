import cv2
import numpy as np

COLORS = [
    "red",
    "orange",
    "yellow",
    "green",
    "cyan",
    "blue",
    "purple",
    "pink",
    "black",
    "white",
    "gray",
    "brown",
]


def analyze(rgb, person=False):
    h, w = rgb.shape[:2]
    if person:
        rgb = rgb[
            int(h * 0.22) : max(int(h * 0.58), int(h * 0.22) + 1),
            int(w * 0.2) : max(int(w * 0.8), int(w * 0.2) + 1),
        ]
    if not rgb.size:
        return {}
    hsv = cv2.cvtColor(cv2.resize(rgb, (64, 64)), cv2.COLOR_RGB2HSV)
    h, s, v = [hsv[:, :, i].astype(float) for i in range(3)]
    labels = np.full(h.shape, 10)
    chromatic = (s > 55) & (v > 55)
    for idx, mask in [
        (0, (h < 9) | (h >= 174)),
        (1, (h >= 9) & (h < 23)),
        (2, (h >= 23) & (h < 36)),
        (3, (h >= 36) & (h < 85)),
        (4, (h >= 85) & (h < 100)),
        (5, (h >= 100) & (h < 130)),
        (6, (h >= 130) & (h < 155)),
        (7, (h >= 155) & (h < 174)),
    ]:
        labels[mask & chromatic] = idx
    labels[(h >= 9) & (h < 25) & (s > 60) & (v < 155) & (v > 55)] = 11
    labels[v <= 55] = 8
    labels[(s <= 40) & (v >= 200)] = 9
    counts = np.bincount(labels.ravel(), minlength=len(COLORS)) / labels.size
    return {name: round(float(counts[i]), 4) for i, name in enumerate(COLORS)}
