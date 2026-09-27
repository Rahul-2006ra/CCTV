# Reference audit — 2026-09-25

No source code copied. We inspected README files, file trees, implementation modules and license presence. Downloads used for inspection are outside this repository. This is a new implementation.

| Area | Looking Glass | CCTV-Vision | SentrySearch | Event-Driven Video Analytics |
|---|---|---|---|---|
| Architecture | Local sampled-frame retrieval | Appearance-focused offline CLI | Video-chunk retrieval CLI | Distributed event-driven services |
| Backend | FastAPI; ingestion/models/search/store modules | Large Python main.py | Python package, provider adapters, CLI | FastAPI + Kafka producer/consumers |
| Frontend | React/Vite/Tailwind | CLI and annotated output | CLI | Streamlit |
| AI | YOLO-World, SigLIP, Florence, MiniCPM, Llama | YOLOv8, MediaPipe, EfficientNet-B4 attributes | Gemini/Qwen cloud; local Qwen3-VL, MLX | YOLOv8, CLIP |
| Video | 1 FPS sampling; frames and crops | OpenCV sequential frames | Overlapping video chunks, FFmpeg | OpenCV resized JPEGs over Kafka |
| Tracking | ByteTrack via supervision | IoU/Hungarian custom tracker | No detector tracking central to retrieval | No persistent tracker in inspected worker |
| Embeddings | SigLIP frame/crop | No semantic vector retrieval in main pipeline | Video/text/image embeddings | CLIP object crops/text |
| Vector DB | Embedded Qdrant | None | ChromaDB | Qdrant server |
| Search | Vector candidates and optional reranking | Structured appearance filters | Similarity, threshold, dedupe, optional rerank | Text-vector nearest neighbors |
| Clips | Not a central documented extraction subsystem | Annotated MP4 export | FFmpeg padding/copy/re-encode | No clip extraction in inspected services |
| License | No license grant found | No license grant found | Apache-2.0 | README reserves all rights |
| Ideas used | Scene + crop index; local modules | Upper-body color signal | Context windows, boundary handling | Separate processing and retrieval interfaces |
| Limitations informing this build | Heavy optional models; inspected embedder hard-codes dimension and search rescales scores | Custom tracking; sensitive attribute heads excluded | Larger local model; cloud defaults; chunk-level timestamps | Deployment overhead; hard-coded vector dimension; no local workstation UX |

Sources: [Looking Glass](https://github.com/hsn07pk/looking-glass), [CCTV-Vision](https://github.com/glenngriggs/CCTV-Vision), [SentrySearch](https://github.com/ssrajadh/sentrysearch), [Event-Driven Video Analytics](https://github.com/sitta07/event-driven-video-analytics).

Selection: one local worker, YOLOv8n with the library's ByteTrack integration, Transformers CLIP ViT-B/32, normalized vectors with dimension from model configuration, persistent Qdrant, SQLite, and an independently written React workstation. No Kafka, cloud API, identity inference or attribute classifiers. Source-time and ranking evidence remain explicit.
