"""Populates realistic multi-camera security demo scenarios for SentinelAI."""

import uuid
from datetime import datetime, timezone
from backend.storage import db
from backend.storage.db import init_db

def seed_demo_data():
    init_db()
    print("Seeding SentinelAI Tactical Multi-Camera Demo Environment...")

    # 1. Seed Cameras
    cameras = [
        ("CAM-01-NORTH", "Perimeter North Gate", "[[0.1, 0.1], [0.9, 0.1], [0.9, 0.4], [0.1, 0.4]]"),
        ("CAM-02-ALLEY", "Restricted Service Alley", "[[0.2, 0.3], [0.8, 0.3], [0.8, 0.8], [0.2, 0.8]]"),
        ("CAM-03-LOBBY", "Rear Commercial Lobby", "[[0.15, 0.2], [0.85, 0.2], [0.85, 0.75], [0.15, 0.75]]"),
        ("CAM-04-PERIM", "East Fence Boundary", "[[0.05, 0.05], [0.95, 0.05], [0.95, 0.35], [0.05, 0.35]]"),
    ]

    for cid, cname, czone in cameras:
        db.execute(
            "INSERT OR REPLACE INTO cameras(id, name, zone) VALUES(?, ?, ?)",
            (cid, cname, czone)
        )
    print(f"✓ Created {len(cameras)} tactical camera zones.")

    # 2. Seed Mock Video Feeds
    videos = [
        ("VID-DEMO-01", "sector_north_incursion.mp4", "/data/uploads/sector_north.mp4", "CAM-01-NORTH", 120.0, 30.0, 1920, 1080, 3600, "h264", 15400000, "READY", 100.0, 120, 340, 340),
        ("VID-DEMO-02", "service_alley_dropoff.mp4", "/data/uploads/service_alley.mp4", "CAM-02-ALLEY", 120.0, 30.0, 1920, 1080, 3600, "h264", 14200000, "READY", 100.0, 120, 290, 290),
        ("VID-DEMO-03", "lobby_evasion_exit.mp4", "/data/uploads/lobby_exit.mp4", "CAM-03-LOBBY", 120.0, 30.0, 1920, 1080, 3600, "h264", 16800000, "READY", 100.0, 120, 410, 410),
    ]

    for vid, vname, vpath, vcid, dur, fps, w, h, frames, codec, size, stat, prog, f_cnt, objs, emb in videos:
        db.execute(
            """
            INSERT OR REPLACE INTO videos(id, filename, path, camera_id, duration, fps, width, height, frame_count, codec, size, status, progress, frames, objects, embeddings)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (vid, vname, vpath, vcid, dur, fps, w, h, frames, codec, size, stat, prog, f_cnt, objs, emb)
        )
    print("✓ Registered 3 synchronized video feeds.")

    # 3. Seed Realistic Multi-Camera Threat Scenario
    # Suspect Target #8842 crosses CAM-01 -> CAM-02 -> CAM-03
    alerts = [
        ("ALT-001", "VID-DEMO-01", "CAM-01-NORTH", 14.5, "Restricted Zone Incursion", "CRITICAL", 42, "Target entered sensitive fence perimeter polygon with face concealed.", 92.0, "PERIMETER_BREACH"),
        ("ALT-002", "VID-DEMO-01", "CAM-01-NORTH", 28.0, "Extended Loitering Pattern", "HIGH", 42, "Target loitering at perimeter barrier for > 25s.", 78.0, "BEHAVIORAL_ANOMALY"),
        ("ALT-003", "VID-DEMO-02", "CAM-02-ALLEY", 48.0, "Suspicious Rapid Movement", "HIGH", 42, "Subject accelerating into unmonitored blind corridor (speed: 0.38 u/s).", 74.0, "DYNAMIC_ANOMALY"),
        ("ALT-004", "VID-DEMO-02", "CAM-02-ALLEY", 65.5, "Unattended Payload Deposited", "CRITICAL", 88, "Black tactical bag abandoned near power distribution terminal.", 89.0, "TACTICAL_ANOMALY"),
        ("ALT-005", "VID-DEMO-03", "CAM-03-LOBBY", 92.0, "Restricted Zone Incursion", "HIGH", 42, "Rapid transit through rear emergency exit without badge authentication.", 81.0, "PERIMETER_BREACH"),
    ]

    for aid, vid, cid, ts, etype, sev, tid, details, tscore, cat in alerts:
        db.execute(
            """
            INSERT OR REPLACE INTO alerts(id, video_id, camera_id, timestamp, event_type, severity, track_id, details, threat_score, rule_category)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (aid, vid, cid, ts, etype, sev, tid, details, tscore, cat)
        )
    print(f"✓ Seeded {len(alerts)} coordinated threat alerts.")

    # 4. Seed Certified Investigation Case
    db.execute(
        """
        INSERT OR REPLACE INTO investigation_cases(id, case_number, title, investigator_id, status, threat_level, summary, hash_signature, pdf_report_path)
        VALUES('CASE-ALPHA-01', 'CASE-ALPHA-01', 'Perimeter Incursion & Payload Deposit at Sector North', 'CHIEF-INSP-204', 'CERTIFIED', 'CRITICAL', 'Autonomous correlation of Subject #42 transitioning from North Perimeter to Service Alley, depositing an unattended payload, and escaping via Rear Lobby.', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '/api/intelligence/reports/CASE-ALPHA-01/download')
        """
    )
    print("✓ Seeded certified investigation case CASE-ALPHA-01.")
    print("Demo environment successfully primed! Ready for live hackathon demonstration.")

if __name__ == "__main__":
    seed_demo_data()
