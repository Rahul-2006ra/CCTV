---
title: CamTrace Intelligence
emoji: 🎥
colorFrom: blue
colorTo: green
sdk: docker
pinned: true
app_port: 7860
short_description: AI CCTV Intelligence Platform - SIH 2026 | Team Phoenix
---

# CamTrace Intelligence

### AI-Based Intelligent Video Analytics Platform for Border Surveillance Using Existing CCTV Infrastructure

> **Smart India Hackathon 2026**  
> **Problem Statement ID:** SIH26187  
> **Theme:** Smart Automation | **Category:** Software  
> **Team ID:** S4D068-1 | **Team Name:** Phoenix  

---

## 📌 Executive Summary

**CamTrace Intelligence** is an AI-powered visual investigation platform that transforms raw CCTV footage into searchable, verifiable evidence. It empowers border surveillance operators, law enforcement, and security investigators to locate and refine people, vehicles, objects, or scenario events using natural-language queries, instantly retrieving contextual video evidence clips rather than isolated, inconclusive still frames.

---

## ⚖️ Problem Statement & Solution

| Existing Issue | CamTrace Solution |
| :--- | :--- |
| **Manual CCTV Search** | **Natural-Language Video Search** via multimodal semantic embeddings |
| **Hours of Footage** | **Fast Evidence Retrieval** with sub-second vector search & adaptive sampling |
| **Too Many Matches** | **Progressive Query Refinement** using multi-attribute clues and scenario constraints |
| **Hard to Track Events** | **AI-Based Detection & Tracking** using YOLOv8, ByteTrack, and spatial-temporal grouping |

### Innovation & Uniqueness
- **Searchable Visual Database:** Ingests raw CCTV feeds (MP4, MOV, AVI) and extracts dense visual-semantic representations.
- **Progressive Search Funnel:** Allows investigators to iteratively layer clues (color, object type, secondary attributes, zone entry) to narrow hundreds of candidates down to exact matches.
- **Natural-Language Understanding:** Query surveillance footage in plain English (e.g., *"Find a person wearing a red shirt and backpack entering through main gate"*).
- **Contextual Evidence Clips:** Automatically generates continuous, forensically verifiable video clips with preceding and succeeding temporal context via FFmpeg.

---

## 🔄 Step-by-Step Workflow & System Architecture

The CamTrace intelligence pipeline converts raw surveillance streams into forensically verified video evidence in six distinct phases:

```
[1. Load & Process Footage] ──► [2. Create Visual Database] ──► [3. Natural Language Search]
                                                                          │
[6. Contextual Evidence Clip] ◄── [5. Progressive Refinement] ◄── [4. Find & Rank Events]
```

### 1. Load & Process CCTV Footage
*Turn raw video into searchable visual data.*
- Ingests uploaded recordings or live RTSP streams (`MP4`, `MOV`, `AVI`).
- Executes adaptive frame sampling and fast sequential frame streaming.
- Runs **YOLOv8** for real-time person, vehicle, and object detection.
- Applies **ByteTrack** for persistent multi-object tracking and trajectory association across frames.

### 2. Create Visual Database
*Extract dense visual information from each detected entity.*
- Extracts bounding box crops for detected entities and full-scene frames.
- Generates 512-dimensional visual embeddings using **CLIP (ViT-B/32)**.
- Indexes vectors into **Qdrant Vector Database** alongside rich structured metadata:
  - Dominant color features (upper body, lower body, vehicle paint)
  - Entity category (`person`, `car`, `truck`, `backpack`, `handbag`, etc.)
  - Camera source identifier and camera zone coordinates
  - Absolute timestamps and continuous track IDs

### 3. Search Using Natural Language
*Describe what you remember — the system searches what happened.*
- Translates natural language descriptions into multimodal query vectors.
- Automatically parses structured filters:
  - **Entity Class:** Person, vehicle, bag
  - **Color Attributes:** Red, black, white, blue, etc.
  - **Scenario Constraints:** Restricted boundary crossings, entry/exit gates, dwell time

### 4. Find & Rank Matching Events
*Retrieve candidate events, not just isolated frames.*
- Performs cosine similarity search across high-dimensional vector space in Qdrant.
- Applies multi-signal ranking combining semantic similarity, attribute match scores, and rule verification.
- Returns candidate event clusters across multiple camera streams.

### 5. Refine the Search (Progressive Clue Funnel)
*Add details iteratively to eliminate false positives.*
- **Step 5.1:** Query `"Red shirt"` → *20 candidate events*
- **Step 5.2:** Add clue `"+ black pants"` → *8 candidate events*
- **Step 5.3:** Add clue `"+ backpack"` → *3 candidate events*
- **Step 5.4:** Add constraint `"Enters through main gate"` → *1–2 high-confidence matches*

### 6. Generate Contextual Evidence Clip
*From matching event to verified video evidence.*
- Performs temporal grouping of adjacent matching frames into continuous time windows.
- Automatically invokes **FFmpeg** to extract and re-encode a verified video clip with customizable before-and-after context (e.g., ±10 seconds).
- Provides instant HTTP Range streaming for continuous video playback, scrubbing, and forensic export.

---

## 🛠 Technology Stack

| Technology | Role |
| :--- | :--- |
| **Python 3.11** | Core backend processing engine and pipeline orchestration |
| **FastAPI** | High-performance asynchronous REST API, Range streaming, and WebSockets |
| **React + TypeScript** | Modern, responsive investigative workstation UI |
| **OpenCV** | Computer vision, video stream decoding, and frame transformations |
| **YOLOv8 (Ultralytics)** | Deep learning object detection for surveillance scenes |
| **ByteTrack** | Real-time multi-target tracking across temporal frames |
| **CLIP (OpenAI)** | Multimodal vision-language embeddings for zero-shot text-to-visual search |
| **Qdrant** | Low-latency vector database for high-dimensional similarity search |
| **FFmpeg** | Video probing, fast seeking, transcoding, and evidence clip extraction |

---

## 📊 Feasibility, Viability & Risk Mitigation

### Feasibility Highlights
- **Existing Setup:** Operates on standard RTSP and MP4 camera streams without requiring costly specialized hardware upgrades.
- **Proven AI Stack:** Integrates state-of-the-art open-source vision models (YOLOv8, ByteTrack, CLIP).
- **Cost-Effective:** Zero proprietary licensing fees; lightweight CPU and GPU execution options.
- **Rapid Prototype:** Production-ready architecture verified end-to-end for competition and operational deployment.

### Potential Risks & Mitigation Strategies

| Potential Risk | Key Concern | Mitigation Strategy |
| :--- | :--- | :--- |
| **Large Video Data** | High storage & processing overhead on long surveillance recordings | **Efficient Storage:** Adaptive frame sampling, fast keyframe streaming, thumbnail downscaling, and unified vector indexing. |
| **Real-time Performance** | Slower search latency with massive libraries | **Optimized Search Pipeline:** Batched PyTorch tensor encoding, cached neutral projections, and indexed Qdrant collections. |
| **False Detections** | Irrelevant candidate matches from crowded scenes | **Improved Accuracy:** Progressive multi-clue refinement funnels, attribute validation, and spatial rule engines. |
| **Privacy & Security** | Sensitive surveillance footage and unauthorized access | **Access Control & Privacy:** Encrypted local data storage, role-based API access, and credential obfuscation. |

---

## 🌟 Impact & Benefits

### Impact
- **Faster Investigations:** Reduces evidence discovery time from days and hours to seconds.
- **Reduced Manual Effort:** Eliminates manual, fatigue-prone scrubbing through continuous CCTV feeds.
- **Better Incident Response:** Enables border security forces and law enforcement to respond swiftly with actionable intelligence.
- **Improved Public Safety:** Transforms passive surveillance infrastructure into an active, intelligent security asset.

### Key Benefits
- **Natural-Language Search:** Accessible to field operators without specialized query syntax.
- **Progressive Refinement:** Layers clues dynamically until ground truth is pinpointed.
- **Forensic Video Clips:** Produces court-ready, contextual evidence clips rather than ambiguous stills.
- **Zero Infrastructure Replacement:** Bridges modern AI directly with legacy CCTV systems.

---

## 📚 Research & References

1. **NIST — Face in Video Evaluation (FIVE):** Performance metrics for video surveillance evaluation.  
   [https://www.nist.gov/programs-projects/face-video-evaluation-five](https://www.nist.gov/programs-projects/face-video-evaluation-five)
2. **BoT-SORT — Robust Associations for Multi-Pedestrian Tracking:**  
   [https://arxiv.org/abs/2206.14651](https://arxiv.org/abs/2206.14651)
3. **Ultralytics YOLOv8 Documentation:**  
   [https://docs.ultralytics.com/](https://docs.ultralytics.com/)
4. **OpenCV Video Surveillance & Object Tracking:**  
   [https://docs.opencv.org/doc/doxygen/html/dc/d6b/group__video__track.html](https://docs.opencv.org/doc/doxygen/html/dc/d6b/group__video__track.html)
5. **Learning Transferable Visual Models From Natural Language Supervision (CLIP):**  
   [https://arxiv.org/abs/2103.00020](https://arxiv.org/abs/2103.00020)
6. **Text-to-Video Retrieval: A Survey:**  
   [https://arxiv.org/abs/2201.08071](https://arxiv.org/abs/2201.08071)

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11
- Node.js 20+
- FFmpeg installed and available on system PATH

### 2. Local Setup

```bash
# Clone the repository
git clone https://github.com/Rahul-2006ra/CCTV.git
cd CCTV

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 3. Run Application

```powershell
# Option A: Windows PowerShell launcher
.\start.ps1

# Option B: Manual Launch (Two terminals)
# Terminal 1 - Backend:
uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend:
npm run dev --prefix frontend
```

### 4. Access the Platform
- **Investigation Station:** [http://localhost:5173/investigation](http://localhost:5173/investigation)
- **Footage Library:** [http://localhost:5173/footage](http://localhost:5173/footage)
- **Camera Configurations:** [http://localhost:5173/cameras](http://localhost:5173/cameras)
- **API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health:** [http://localhost:8000/api/system/health](http://localhost:8000/api/system/health)

---

## 🐳 Unified Docker & Cloud Deployment

CamTrace includes a multi-stage Docker build that compiles the frontend and runs the backend on a single port for zero-configuration cloud deployment:

```bash
# Build the unified container
docker build -t camtrace-intelligence .

# Run on port 7860
docker run -p 7860:7860 camtrace-intelligence
```

For 1-click cloud deployment on **Railway**, **Render**, or **Hugging Face Spaces**, refer to [`DEPLOYMENT.md`](DEPLOYMENT.md).

---

## 👥 Team Phoenix

- **Hackathon:** Smart India Hackathon 2026
- **Problem Statement:** SIH26187 — *AI based Intelligent Video Analytics Platform for border Surveillance using existing CCTV infrasturcture*
- **Theme:** Smart Automation (Software)
- **Team ID:** S4D068-1
- **Team Name:** Phoenix
