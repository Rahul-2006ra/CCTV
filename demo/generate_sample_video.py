"""Create a diagnostic video from NASA's public-domain astronaut photograph.
This is a photographic test fixture, NOT real CCTV or an action benchmark.
No rectangles stand in for objects; models process the real photograph.
"""

import argparse
import subprocess
from pathlib import Path
import cv2
import numpy as np
from skimage import data


def generate(output, seconds=12):
    image = cv2.cvtColor(data.astronaut(), cv2.COLOR_RGB2BGR)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(".avi")
    writer = cv2.VideoWriter(str(temp), cv2.VideoWriter_fourcc(*"MJPG"), 12, (768, 576))
    if not writer.isOpened():
        raise RuntimeError("Video writer unavailable")
    for i in range(seconds * 12):
        frame = np.full((576, 768, 3), 25, dtype=np.uint8)
        # A slow pan changes the actual image location and exercises tracking.
        x = 40 + int(90 * i / (seconds * 12))
        frame[32:544, x : x + 512] = image
        writer.write(frame)
    writer.release()
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(temp),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )
    temp.unlink()
    print(output.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="demo/photographic-test.mp4")
    args = parser.parse_args()
    generate(args.output)
