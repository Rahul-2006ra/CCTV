import sqlite3
from contextlib import contextmanager
from backend.config import DATA


@contextmanager
def connection():
    conn = sqlite3.connect(DATA / "metadata.sqlite3", timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with connection() as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.executescript("""
        CREATE TABLE IF NOT EXISTS cameras(id TEXT PRIMARY KEY,name TEXT NOT NULL,zone TEXT NOT NULL DEFAULT '[]',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS videos(id TEXT PRIMARY KEY,filename TEXT NOT NULL,path TEXT NOT NULL,camera_id TEXT REFERENCES cameras(id),duration REAL,fps REAL,width INTEGER,height INTEGER,frame_count INTEGER,codec TEXT,size INTEGER,status TEXT DEFAULT 'UPLOADED',progress REAL DEFAULT 0,frames INTEGER DEFAULT 0,objects INTEGER DEFAULT 0,embeddings INTEGER DEFAULT 0,error TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS processing_jobs(id TEXT PRIMARY KEY,video_id TEXT REFERENCES videos(id) ON DELETE CASCADE,status TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,finished_at TEXT,error TEXT);
        CREATE TABLE IF NOT EXISTS video_segments(id TEXT PRIMARY KEY,video_id TEXT REFERENCES videos(id) ON DELETE CASCADE,timestamp REAL,payload TEXT);
        CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY,video_id TEXT REFERENCES videos(id) ON DELETE CASCADE,camera_id TEXT,timestamp REAL,event_type TEXT,severity TEXT,status TEXT DEFAULT 'NEW',track_id INTEGER,details TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS search_history(id TEXT PRIMARY KEY,query TEXT,results TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS clips(id TEXT PRIMARY KEY,video_id TEXT REFERENCES videos(id) ON DELETE CASCADE,start REAL,end REAL,path TEXT,method TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS segments_video ON video_segments(video_id,timestamp);
        """)
        columns = {row["name"] for row in c.execute("PRAGMA table_info(videos)")}
        for name, definition in (
            ("source_kind", "TEXT DEFAULT 'upload'"),
            ("recorded_at", "TEXT"),
        ):
            if name not in columns:
                c.execute(f"ALTER TABLE videos ADD COLUMN {name} {definition}")
        c.execute(
            "UPDATE videos SET status='FAILED',error='Processing interrupted. Re-index to retry.' WHERE status NOT IN ('READY','FAILED','UPLOADED')"
        )
        c.execute(
            "UPDATE processing_jobs SET status='FAILED',error='Application restarted' WHERE status NOT IN ('READY','FAILED')"
        )
        camera_count = c.execute("SELECT COUNT(*) FROM cameras").fetchone()[0]
        if camera_count == 0:
            c.execute(
                "INSERT INTO cameras(id,name,zone) VALUES('CAM-MAIN', 'Main Camera (Default)', '[]')"
            )


def rows(sql, params=()):
    with connection() as c:
        return [dict(x) for x in c.execute(sql, params).fetchall()]


def one(sql, params=()):
    result = rows(sql, params)
    return result[0] if result else None


def execute(sql, params=()):
    with connection() as c:
        c.execute(sql, params)


def update_video(vid, **values):
    allowed = {"status", "progress", "frames", "objects", "embeddings", "error"}
    if not set(values) <= allowed:
        raise ValueError("Invalid update fields")
    execute(
        "UPDATE videos SET " + ",".join(f"{k}=?" for k in values) + " WHERE id=?",
        (*values.values(), vid),
    )
