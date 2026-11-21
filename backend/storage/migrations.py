"""Database schema migrations for SentinelAI Intelligence Platform."""

import logging
from backend.storage.db import connection

logger = logging.getLogger(__name__)


def run_migrations():
    """Apply schema extensions for threat intelligence, routes, and cases."""
    with connection() as c:
        # 1. Threat Entities table for tracking suspects across cameras
        c.execute("""
        CREATE TABLE IF NOT EXISTS threat_entities (
            id TEXT PRIMARY KEY,
            track_id INTEGER,
            composite_score REAL DEFAULT 0.0,
            severity_level TEXT DEFAULT 'LOW',
            object_type TEXT DEFAULT 'person',
            first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            primary_crop_path TEXT,
            color_fingerprint TEXT,
            status TEXT DEFAULT 'ACTIVE',
            details TEXT DEFAULT '{}'
        );
        """)

        # 2. Multi-camera Trajectory Nodes
        c.execute("""
        CREATE TABLE IF NOT EXISTS trajectory_nodes (
            id TEXT PRIMARY KEY,
            entity_id TEXT,
            camera_id TEXT REFERENCES cameras(id),
            video_id TEXT REFERENCES videos(id),
            track_id INTEGER,
            timestamp_entry REAL,
            timestamp_exit REAL,
            action_type TEXT,
            step_order INTEGER,
            confidence REAL,
            thumbnail_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 3. Investigation Cases for formal forensic tracking
        c.execute("""
        CREATE TABLE IF NOT EXISTS investigation_cases (
            id TEXT PRIMARY KEY,
            case_number TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            investigator_id TEXT NOT NULL,
            status TEXT DEFAULT 'OPEN',
            threat_level TEXT DEFAULT 'ELEVATED',
            summary TEXT,
            hash_signature TEXT,
            pdf_report_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            closed_at TEXT
        );
        """)

        # 4. Evidence items linked to cases
        c.execute("""
        CREATE TABLE IF NOT EXISTS case_evidence (
            id TEXT PRIMARY KEY,
            case_id TEXT REFERENCES investigation_cases(id) ON DELETE CASCADE,
            video_id TEXT REFERENCES videos(id),
            clip_id TEXT REFERENCES clips(id),
            timestamp REAL,
            notes TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 5. Add columns to existing alerts table if present
        table_names = {row["name"] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "alerts" in table_names:
            alert_cols = {row["name"] for row in c.execute("PRAGMA table_info(alerts)")}
            if "threat_score" not in alert_cols:
                c.execute("ALTER TABLE alerts ADD COLUMN threat_score REAL DEFAULT 0.0")
            if "rule_category" not in alert_cols:
                c.execute("ALTER TABLE alerts ADD COLUMN rule_category TEXT DEFAULT 'SPATIAL'")

        # 6. Add indices for fast spatial-temporal traversal
        c.execute("CREATE INDEX IF NOT EXISTS idx_trajectory_entity ON trajectory_nodes(entity_id, step_order);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_trajectory_camera ON trajectory_nodes(camera_id, timestamp_entry);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_threat_score ON threat_entities(composite_score DESC);")

    logger.info("SentinelAI database migrations applied successfully.")
