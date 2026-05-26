import sqlite3
import threading
import time
from app.config import settings
from app.db.models import Role

_local = threading.local()
_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(settings.SQLITE_DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _init_schema(_local.conn)
    return _local.conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role       TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content    TEXT NOT NULL,
            created_at REAL NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );
    """)
    conn.commit()


def create_session(session_id: str, user_id: str) -> None:
    now = time.time()
    with _lock:
        conn = _get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, user_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, now, now),
        )
        conn.commit()


def save_message(session_id: str, role: Role, content: str) -> None:
    now = time.time()
    with _lock:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (now, session_id),
        )
        conn.commit()


def get_session_messages(session_id: str, limit: int = 6) -> list[dict]:
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            """
            SELECT role, content FROM (
                SELECT role, content, created_at FROM messages
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ) ORDER BY created_at ASC
            """,
            (session_id, limit),
        ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


def get_all_messages(session_id: str) -> list[dict]:
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
    return [{"role": row["role"], "content": row["content"], "created_at": row["created_at"]} for row in rows]
