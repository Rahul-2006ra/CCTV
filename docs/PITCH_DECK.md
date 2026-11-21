# SentinelAI: Pitch Deck & Live Demonstration Master Script

## Slide 1: The CCTV Blindspot Crisis
* **The Reality:** There are over 1 billion surveillance cameras deployed globally.
* **The Vulnerability:** 99% of surveillance video is passive and unindexed. When a perimeter breach or security incident occurs, security officers spend 4 to 16 hours manually scrubbing through footage.
* **The Pain Point:** By the time human operators identify what happened, suspects have departed the facility and evidence is disputed.

---

## Slide 2: Introducing SentinelAI
* **Tagline:** Autonomous Surveillance Intelligence & Forensic Reconstruction Platform.
* **Core Philosophy:** Upgrading legacy CCTV networks into an autonomous, proactive defense intelligence grid without requiring $1 of new hardware.
* **The 4 Cornerstones:**
  1. Real-time Composite Risk Scoring ($0–100\%$).
  2. Multi-Camera Route Reconstruction (Cross-camera Re-ID).
  3. Autonomous AI Investigation Copilot.
  4. Court-Admissible Forensic Case Dossiers.

---

## Slide 3: Technical Breakthrough: Multi-Camera Re-ID without Heavy Hardware
* Traditional Re-ID systems require multi-gigabyte neural models running on dedicated servers.
* **Our Innovation:** SentinelAI achieves cross-camera tracking by fusing existing 512-dimensional CLIP crop vectors with two-pass HSV spatial color histograms in Qdrant, constrained by temporal-topological trajectory graphs.
* **Performance:** Sub-second retrieval across 100,000+ indexed frames with sub-millisecond route synthesis.

---

## Slide 4: 90-Second Winning Live Demo Choreography

### Phase 1: Security Command Center (0:00 - 0:25)
* Open the **Command Center** page.
* Point to the live multi-camera grid and the **DEFCON Threat Barometer** actively evaluating camera telemetry.
* Highlight the real-time alert feed displaying flagged incursions with calculated threat scores.

### Phase 2: Autonomous Incursion Escalation (0:25 - 0:45)
* Target enters North Perimeter $\rightarrow$ SentinelAI flags a **Restricted Zone Incursion** and escalates facility posture to **DEFCON 2 (HIGH)**.
* Show the one-click **"DISPATCH TACTICAL RESPONSE"** simulated trigger.

### Phase 3: Cross-Camera Route Reconstruction (0:45 - 1:10)
* Jump to **Route Reconstruction**.
* Query: *"person in red hoodie"*.
* SentinelAI renders the full cross-camera journey:
  `CAM-01 (Perimeter North) ──► CAM-02 (Service Alley) ──► CAM-03 (Rear Lobby)`
* Each step displays the exact entry/exit timestamps, dwell duration, and tactical action summary.

### Phase 4: AI Copilot & Forensic Dossier Export (1:10 - 1:30)
* Open the **Copilot Agent** drawer.
* Ask: *"Summarize all high-risk perimeter breaches."*
* Copilot outputs an instantaneous tactical situational briefing.
* Click **"Export Forensic Case File"**.
* Open the resulting formal dossier complete with suspect profile, timeline table, and tamper-evident SHA-256 seal.
* Conclude: *"What previously required an entire security team 6 hours to piece together was autonomously resolved in 90 seconds."*
