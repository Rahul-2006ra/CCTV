# Changelog

All notable changes to the SentinelAI Platform are documented in this file.

## [1.0.0] - SentinelAI Flagship Release - 2026-11-21

### Added
- **Threat Intelligence Engine:** Real-time behavioral anomaly discovery (loitering, zone breach, abandoned objects, sudden flight).
- **Composite Risk Scoring Engine:** Multi-factor $0–100$ threat score calculation with defense severity tiers (CRITICAL, HIGH, ELEVATED, GUARDED, NORMAL).
- **Multi-Camera Route Reconstruction:** Cross-camera target Re-ID linking disjoint camera streams via CLIP embeddings and HSV color histograms.
- **AI Investigation Copilot:** Autonomous natural language reasoning agent providing tactical situational briefings.
- **Forensic Dossier Generator:** Certified incident case compilation with SHA-256 digital chain of custody hashing.
- **Security Command Center Dashboard:** Palantir/Anduril-inspired tactical SOC interface with DEFCON barometer and live multi-camera feeds.
- **Threat Analytics Module:** 24-hour incursion distribution histograms and sensor risk rankings.
- **Synthetic Demo Seeder:** `scripts/generate_synthetic_threats.py` for priming hackathon demo scenarios.

### Changed
- Preserved existing YOLOv8, ByteTrack, CLIP, Qdrant, and FastAPI core pipelines with additive wrappers.
- Upgraded SQLite metadata store with `threat_entities`, `trajectory_nodes`, and `investigation_cases`.
- Modernized frontend navigation with tactical DEFCON indicators and AI Copilot drawer.
- Rewrote documentation, architecture specifications, and hackathon presentation guides.
