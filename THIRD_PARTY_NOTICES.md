# Third-party notices

Audit date: 2026-09-25. The four reference projects were inspected before implementation. No source was copied from them. Absence of a license is not permission to reuse source.

## Looking Glass

Author: hsn07pk and contributors

Repository: https://github.com/hsn07pk/looking-glass

License: No license grant found

What was used: Architecture/reference only — no source code copied.

What was modified: None

## CCTV-Vision

Author: Lucas Morris, Glenn Griggs, Shubhanshu Pokharel

Repository: https://github.com/glenngriggs/CCTV-Vision

License: No license grant found

What was used: Architecture/reference only — no source code copied.

What was modified: None

## SentrySearch

Author: ssrajadh and contributors

Repository: https://github.com/ssrajadh/sentrysearch

License: Apache-2.0

What was used: Architecture/reference only — no source code copied.

What was modified: None

## Event-Driven Video Analytics

Author: Sitta Boonkaew

Repository: https://github.com/sitta07/event-driven-video-analytics

License: All rights reserved (README)

What was used: Architecture/reference only — no source code copied.

What was modified: None

## Ultralytics YOLO / ByteTrack integration

Author: Ultralytics contributors

Repository: https://github.com/ultralytics/ultralytics

License: AGPL-3.0

What was used: Unmodified dependency; YOLOv8n detection weights and ByteTrack tracking.

What was modified: None; used through public APIs

## CLIP ViT-B/32

Author: OpenAI

Repository: https://github.com/openai/CLIP

License: MIT

What was used: Unmodified model checkpoint via Hugging Face Transformers.

What was modified: None; used through public APIs

## Transformers

Author: Hugging Face contributors

Repository: https://github.com/huggingface/transformers

License: Apache-2.0

What was used: Unmodified text/image model inference dependency.

What was modified: None; used through public APIs

## PyTorch / TorchVision

Author: PyTorch contributors

Repository: https://github.com/pytorch/pytorch

License: BSD-3-Clause

What was used: Unmodified tensor inference libraries.

What was modified: None; used through public APIs

## Qdrant client

Author: Qdrant contributors

Repository: https://github.com/qdrant/qdrant-client

License: Apache-2.0

What was used: Persistent embedded vector storage.

What was modified: None; used through public APIs

## FastAPI

Author: Sebastián Ramírez and contributors

Repository: https://github.com/fastapi/fastapi

License: MIT

What was used: Backend API framework.

What was modified: None; used through public APIs

## React

Author: Meta and contributors

Repository: https://github.com/facebook/react

License: MIT

What was used: Frontend UI runtime.

What was modified: None; used through public APIs

## Vite

Author: Vite contributors

Repository: https://github.com/vitejs/vite

License: MIT

What was used: Frontend build and development server.

What was modified: None; used through public APIs

## Lucide

Author: Lucide contributors

Repository: https://github.com/lucide-icons/lucide

License: ISC

What was used: UI icons.

What was modified: None; used through public APIs

## OpenCV

Author: OpenCV contributors

Repository: https://github.com/opencv/opencv

License: Apache-2.0

What was used: Frame decoding and image processing.

What was modified: None; used through public APIs

## FFmpeg

Author: FFmpeg contributors

Repository: https://ffmpeg.org/legal.html

License: LGPL-2.1-or-later / optional GPL components

What was used: Installed executable invoked for probing and clips; not bundled. libx264 builds include GPL components.

What was modified: None; used through public APIs

## NASA astronaut photograph

Author: NASA

Repository: https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.astronaut

License: Public domain (NASA)

What was used: Unmodified photograph embedded in a panning diagnostic video. Not CCTV.

What was modified: None; used through public APIs

## scikit-image

Author: scikit-image contributors

Repository: https://github.com/scikit-image/scikit-image

License: BSD-3-Clause

What was used: Demo image access only; unmodified dependency.

What was modified: None; used through public APIs

## Distribution

This prototype is licensed under AGPL-3.0-or-later to accommodate the Ultralytics dependency. Preserve LICENSE and these notices with source distributions. Installed distributions retain their original license files in site-packages and node_modules. Runtime dependencies are not vendored. Review model cards and all dependency terms before deployment or redistribution. FFmpeg is a separately installed program. No sensitive-attribute classifier from CCTV-Vision is used.

## NumPy

Author: NumPy contributors

Repository: https://numpy.org

License: BSD-3-Clause

What was used: Vector and image arrays.

What was modified: None; unmodified dependency.

## SciPy

Author: SciPy contributors

Repository: https://scipy.org

License: BSD-3-Clause

What was used: Tracking numerical dependency.

What was modified: None; unmodified dependency.

## Pillow

Author: Pillow contributors

Repository: https://python-pillow.org

License: MIT-CMU

What was used: Image handling.

What was modified: None; unmodified dependency.

## Pydantic

Author: Pydantic contributors

Repository: https://github.com/pydantic/pydantic

License: MIT

What was used: Request validation.

What was modified: None; unmodified dependency.

## Uvicorn

Author: Tom Christie and contributors

Repository: https://github.com/encode/uvicorn

License: BSD-3-Clause

What was used: ASGI application server.

What was modified: None; unmodified dependency.

## SQLite

Author: SQLite authors

Repository: https://sqlite.org/copyright.html

License: Public domain

What was used: Metadata database, via Python standard library.

What was modified: None; unmodified dependency.

## TypeScript

Author: Microsoft and contributors

Repository: https://github.com/microsoft/TypeScript

License: Apache-2.0

What was used: Frontend type checking.

What was modified: None; unmodified dependency.

## python-multipart

Author: Andrew Dunham and contributors

Repository: https://github.com/Kludex/python-multipart

License: Apache-2.0

What was used: Multipart video upload parsing.

What was modified: None; unmodified dependency.

## lap

Author: lap contributors

Repository: https://github.com/gatagat/lap

License: BSD-2-Clause

What was used: Assignment solver used by tracker.

What was modified: None; unmodified dependency.

## pytest

Author: pytest contributors

Repository: https://github.com/pytest-dev/pytest

License: MIT

What was used: Automated backend tests.

What was modified: None; unmodified dependency.

## HTTPX

Author: Encode contributors

Repository: https://github.com/encode/httpx

License: BSD-3-Clause

What was used: API test client and Qdrant dependency.

What was modified: None; unmodified dependency.

## Playwright

Author: Microsoft and contributors

Repository: https://github.com/microsoft/playwright

License: Apache-2.0

What was used: Automated browser verification.

What was modified: None; unmodified dependency.

The complete installed dependency inventory, including transitive packages, is recorded in docs/DEPENDENCY_LICENSES.json and docs/FRONTEND_LICENSES.json. Upstream license files remain in their installed packages.
