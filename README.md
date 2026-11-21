<div align="center">
  <h1>🛡️ SentinelAI</h1>
  <h3>Autonomous Surveillance Intelligence &amp; Forensic Reconstruction Platform</h3>
  <p><b>Transforming existing CCTV networks into proactive, autonomous defense intelligence grids.</b></p>
  
  <p>
    <a href="#-key-capabilities">Capabilities</a> &bull;
    <a href="#-system-architecture">Architecture</a> &bull;
    <a href="#-quickstart-guide">Quickstart</a> &bull;
    <a href="#-90-second-demo-script">Live Demo</a> &bull;
    <a href="#-hackathon-presentation">Pitch Deck</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Platform-SentinelAI-0284c7?style=for-the-badge&logo=shield" alt="Platform" />
    <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react" alt="React" />
    <img src="https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?style=for-the-badge" alt="Qdrant" />
    <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge" alt="YOLOv8" />
  </p>
</div>

---

## 📌 Executive Summary

**SentinelAI** is an enterprise-grade autonomous surveillance intelligence platform engineered for border defense, critical infrastructure, smart cities, and security command centers. Moving physical surveillance beyond passive recording and reactive manual search, SentinelAI delivers:

1. **Cross-Camera Route Reconstruction (Re-ID):** Automatically tracks and connects suspect paths across non-overlapping camera blindspots using multimodal CLIP visual embeddings and spatial-temporal graph traversal.
2. **Dynamic Composite Risk Scoring ($0–100\%$):** Real-time threat index evaluating perimeter polygon incursion, loitering duration, velocity anomalies, and abandoned baggage.
3. **Autonomous AI Investigation Copilot:** An interactive LLM reasoning agent answering complex situational inquiries and drafting military-grade tactical incident briefings.
4. **Certified Forensic Dossier Generation:** Compiles court-admissible PDF/HTML case files complete with suspect visual profiles, timeline tables, and tamper-evident SHA-256 cryptographic hashes.
5. **Palantir/Anduril-Style Command Center:** High-density tactical Security Operations Center (SOC) dashboard with live multi-camera feeds, DEFCON threat barometer, and one-click tactical dispatch.

---

## ⚖️ Legacy Surveillance vs. SentinelAI

| Challenge in Traditional CCTV | SentinelAI Autonomous Capability |
| :--- | :--- |
| **Siloed Camera Streams:** Target is lost the moment they walk into another camera's view. | **Cross-Camera Trajectory Re-ID:** Fuses CLIP embeddings and HSV color histograms to reconstruct full multi-camera route. |
| **Passive Post-Event Scrubbing:** Operators spend 4–16 hours manually watching footage. | **Autonomous Anomaly Discovery:** Continuous real-time detection of loitering, zone breaches, and abandoned payloads. |
| **Alarm Fatigue & Flat Tables:** Unprioritized alert lists with high false-positive rates. | **Composite Risk Scoring ($0–100$):** Multi-factor threat calculation categorizing threats into DEFCON defense tiers. |
| **Disputed Forensic Evidence:** Loose `.mp4` video exports vulnerable to tampering disputes. | **Certified Case Dossiers:** Automated forensic compilation with cryptographically signed SHA-256 chain of custody. |

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 SENTINELAI C4 ARCHITECTURE                             │
└────────────────────────────────────────────────────────────────────────────────────────┘

  [EDGE SENSORS]                [PERCEPTION LAYER]               [INTELLIGENCE PLATFORM]
 ┌──────────────┐              ┌──────────────────┐             ┌────────────────────────┐
 │ RTSP Camera  ├─────────────►│ YOLOv8n Detect   ├────────────►│ ThreatEngine           │
 │ IP Cameras   │  FFmpeg      │ ByteTrack IDs    │ Bounding    │ (Loiter, Breach, Bag)  │
 │ Video Files  ├─────────────►│ HSV Histograms   │ Box Crops   └───────────┬────────────┘
 └──────────────┘              └────────┬─────────┘                         │
                                        │                                   ▼
                                        ▼                       ┌────────────────────────┐
                               ┌──────────────────┐             │ RiskScoringEngine      │
                               │ CLIP ViT-B/32    ├────────────►│ (Composite 0-100 Score)│
                               │ 512d Embeddings  │             └───────────┬────────────┘
                               └────────┬─────────┘                         │
                                        │                                   ▼
                                        ▼                       ┌────────────────────────┐
                               ┌──────────────────┐             │ ReidEngine & RouteGraph│
                               │ Qdrant Vector DB ├────────────►│ (Cross-Camera Path)    │
                               │ (Cosine Metric)  │             └───────────┬────────────┘
                               └──────────────────┘                         │
                                                                            ▼
  [PRESENTATION LAYER]          [AUTONOMOUS AGENTS]             ┌────────────────────────┐
 ┌──────────────────────┐      ┌──────────────────┐             │ SQLite Metadata        │
 │ Tactical SOC Center  │◄─────┤ AI Copilot Agent ├────────────►│ Threat Entities, Cases │
 │ Multi-Camera HUD Wall│      │ PDF Report Gen   │             └────────────────────────┘
 └──────────────────────┘      └──────────────────┘
```

---

## 🚀 Key Modules & Capabilities

### 1. Security Command Center (`/command-center`)
High-density visual interface featuring:
* Live DEFCON Threat Barometer with real-time risk scores.
* Synchronized multi-camera video wall with camera status indicators.
* Real-time Threat Telemetry feed displaying incoming anomalies with explainable factors.
* Emergency Tactical Dispatch simulator.

### 2. Multi-Camera Route Reconstruction (`/routes`)
* Input any natural-language target description or select an active track ID.
* Automatically synthesizes cross-camera transitions with chronological timestamps, dwell durations, inferred actions, and thumbnail crops.
* One-click export to a certified forensic case file.

### 3. AI Investigation Copilot (Slide-out Drawer)
* Conversational investigation assistant trained on spatial-temporal security telemetry.
* Clickable prompt templates: *"Summarize high-risk perimeter breaches"*, *"Identify abandoned payloads"*, *"Audit suspect route"*.
* Outputs structured situational awareness briefings with threat level assessments and actionable security recommendations.

### 4. Forensic Incident Repository (`/cases`)
* Digital case file archive storing certified investigation reports.
* Full chain-of-custody tracking with SHA-256 cryptographic hashes.
* Print-ready HTML/PDF downloads suitable for law enforcement and legal defense.

### 5. Threat Analytics & Heatmaps (`/analytics`)
* 24-hour temporal incursion distribution histograms.
* Camera risk rankings and sensor health indicators.
* Operational KPIs: Mean Time to Detect (MTTD), system availability, and vector index volume.

---

## 🛠️ Quickstart Guide

### Prerequisites
* Python 3.10+
* Node.js 18+
* FFmpeg installed and available on system PATH

### 1. Clone Repository & Setup Backend
```bash
# Clone repository
git clone https://github.com/Rahul-2006ra/CCTV.git sentinel-ai
cd sentinel-ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Download neural weights (YOLOv8n & CLIP ViT-B/32)
python scripts/download_models.py
```

### 2. Setup Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Prime Demo Environment (Optional)
```bash
# Seed realistic 4-camera breach scenario for instant demonstration
python scripts/generate_synthetic_threats.py
```

### 4. Launch SentinelAI
```bash
# Start backend server
python -m backend.main
```
Navigate to `http://localhost:8000` (or `http://localhost:5173` if running Vite dev server) to access the SentinelAI Command Center.

---

## 🎬 90-Second Demo Script for Judges

1. **The Tactical Command Center (0:00 - 0:25):**
   * Open the **Command Center** page.
   * Highlight the live 4-camera grid and the global **DEFCON Threat Barometer** actively evaluating facility telemetry.
2. **Autonomous Incursion Escalation (0:25 - 0:45):**
   * Show flagged **Restricted Zone Incursion** alerts with pulsing crimson **Risk Badges**.
   * Demonstrate the **"DISPATCH TACTICAL RESPONSE"** button triggering instant lockdown.
3. **Cross-Camera Route Reconstruction (0:45 - 1:10):**
   * Navigate to **Route Reconstruction**.
   * Query: *"person wearing red jacket with backpack"*.
   * Watch SentinelAI reconstruct the full suspect trajectory:
     `CAM-01 (Perimeter North) ──► CAM-02 (Service Alley) ──► CAM-03 (Rear Lobby)`.
4. **AI Copilot & Forensic Dossier Export (1:10 - 1:30):**
   * Open the **Copilot Agent** drawer and ask: *"Summarize the incident."*
   * Copilot generates an instant military-grade tactical situation report.
   * Click **"Export Forensic Case File"** to reveal a certified, tamper-evident PDF dossier sealed with a SHA-256 cryptographic hash.

---

## 📄 License & Credits
Licensed under the [Apache 2.0 License](LICENSE). Built for Smart India Hackathon & AI competitions.
