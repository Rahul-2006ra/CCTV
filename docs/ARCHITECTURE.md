# SentinelAI: System Architecture & Technical Specifications

## 1. Executive Summary
SentinelAI is an autonomous surveillance intelligence platform engineered to transform legacy multi-camera CCTV networks into proactive defense grids. Unlike traditional video analytics suites that rely on post-incident manual playback or basic heuristic alarms, SentinelAI introduces:
1. **Zero-Shot Directional Threat Vectors** using multimodal CLIP embeddings.
2. **Cross-Camera Trajectory Re-Identification** via combined feature affinity and topology graphs.
3. **Dynamic Composite Risk Scoring ($0–100$)** with explainable factor attribution.
4. **Autonomous AI Investigation Copilot** for natural-language situational awareness.
5. **Court-Admissible Forensic Incident Dossiers** with SHA-256 evidence integrity hashing.

---

## 2. High-Level C4 Architecture Diagram

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

## 3. Mathematical Foundations

### 3.1 Composite Risk Score Equation
For any tracked entity $e$, the composite threat score $S(e) \in [0, 100]$ is computed as:
$$S(e) = \min\left(100, \; S_0 + w_{\text{zone}} \cdot I_{\text{zone}} + w_{\text{vel}} \cdot f(v) + w_{\text{dwell}} \cdot g(t_{\text{dwell}}) + w_{\text{unattended}} \cdot I_{\text{bag}} + w_{\text{night}} \cdot I_{\text{night}}\right)$$
Where:
- $S_0 = 10.0$ (baseline presence)
- $w_{\text{zone}} = 35.0$
- $w_{\text{vel}} = 20.0$, $f(v) = \min(1.0, \frac{v - v_{\text{thresh}}}{0.15})$
- $w_{\text{dwell}} = 25.0$, $g(t_{\text{dwell}}) = \min(1.0, \frac{t_{\text{dwell}} - t_{\text{loiter}}}{30.0})$
- $w_{\text{unattended}} = 30.0$
- $w_{\text{night}} = 15.0$

### 3.2 Cross-Camera Re-ID Feature Affinity
Cross-camera association between target vector $v_A$ and candidate vector $v_B$ is computed without heavy dedicated Re-ID weights:
$$\text{Affinity}(A, B) = \alpha \cdot \hat{S}_{\text{cos}}(v_A, v_B) + \beta \cdot \text{Intersection}(H_A, H_B)$$
Where:
- $\hat{S}_{\text{cos}}(v_A, v_B) = \max\left(0, \frac{\cos(v_A, v_B) - 0.45}{0.55}\right)$
- $\alpha = 0.75, \; \beta = 0.25$
- $\text{Intersection}(H_A, H_B)$ is the discrete torso/vehicle HSV histogram overlap.

---

## 4. Database Schema Structure
The underlying relational metadata is managed via SQLite in WAL mode:
- `threat_entities`: Active suspect tracks across cameras.
- `trajectory_nodes`: Spatio-temporal steps linking camera IDs, intervals, dwell times, and risk levels.
- `investigation_cases`: Certified forensic incident case files with SHA-256 hashes.
- `case_evidence`: Video segments and clips tagged to cases.
- `alerts`: Raw telemetry events enriched with `threat_score` and `rule_category`.
- `cameras`: Sensor records with polygonal restricted zone coordinates.
- `videos`: Media ingestion catalog with processing states.
