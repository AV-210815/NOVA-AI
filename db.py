"""SQLite persistence for accounts, chat history, and NOVA Nutrition logs.

Replaces browser localStorage (chats) and the single-file health_log.json —
both are now scoped per signed-in user. Uses the standard library's sqlite3,
no new dependency.
"""
import json
import shutil
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_sub TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    name TEXT,
    picture TEXT,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    assistant TEXT NOT NULL DEFAULT 'nebula',
    title TEXT NOT NULL,
    messages_json TEXT NOT NULL,
    updated_at INTEGER NOT NULL,
    pinned INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS health_entries (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    timestamp TEXT NOT NULL,
    description TEXT NOT NULL,
    items_json TEXT NOT NULL DEFAULT '[]',
    calories REAL NOT NULL,
    nutrients_present_json TEXT NOT NULL,
    deficiencies_json TEXT NOT NULL
);
"""


@contextmanager
def get_db():
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def backup_db() -> None:
    """Copies nova.db to a timestamped backup every time the server starts, so
    an accidental data loss (during testing, a bad migration, anything) has
    something to recover from — this exists because a chats-table wipe
    happened during development with no backup available to undo it. Keeps
    the most recent 10 backups; older ones are pruned automatically.
    """
    if not config.DB_PATH.exists():
        return
    backup_dir = config.DATA_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(config.DB_PATH, backup_dir / f"nova-{timestamp}.db")

    backups = sorted(backup_dir.glob("nova-*.db"))
    for old in backups[:-10]:
        old.unlink()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(SCHEMA)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(health_entries)")}
        if "items_json" not in columns:
            conn.execute("ALTER TABLE health_entries ADD COLUMN items_json TEXT NOT NULL DEFAULT '[]'")
        chat_columns = {row["name"] for row in conn.execute("PRAGMA table_info(chats)")}
        if "assistant" not in chat_columns:
            conn.execute("ALTER TABLE chats ADD COLUMN assistant TEXT NOT NULL DEFAULT 'nebula'")
        if "pinned" not in chat_columns:
            conn.execute("ALTER TABLE chats ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")


# --- Users & sessions ---

SESSION_LIFETIME_SECONDS = 30 * 24 * 60 * 60  # 30 days


def upsert_user(google_sub: str, email: str, name: str, picture: str) -> sqlite3.Row:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO users (google_sub, email, name, picture, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(google_sub) DO UPDATE SET email=excluded.email, name=excluded.name, picture=excluded.picture
            """,
            (google_sub, email, name, picture, int(time.time())),
        )
        return conn.execute("SELECT * FROM users WHERE google_sub = ?", (google_sub,)).fetchone()


def create_session(user_id: int) -> str:
    token = uuid.uuid4().hex
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, int(time.time()) + SESSION_LIFETIME_SECONDS),
        )
    return token


def get_user_by_session(token: str) -> sqlite3.Row | None:
    if not token:
        return None
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT users.* FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ? AND sessions.expires_at > ?
            """,
            (token, int(time.time())),
        ).fetchone()
        return row


def delete_session(token: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


# --- Chats ---

def list_chats(user_id: int, assistant: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, updated_at, pinned FROM chats WHERE user_id = ? AND assistant = ? ORDER BY updated_at DESC",
            (user_id, assistant),
        ).fetchall()
        return [{"id": r["id"], "title": r["title"], "updatedAt": r["updated_at"], "pinned": bool(r["pinned"])} for r in rows]


def list_all_chats(user_id: int) -> list[dict]:
    """Every chat across every assistant — used by NOVA Observatory's star map."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, assistant, title, updated_at, pinned FROM chats WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "assistant": r["assistant"],
                "title": r["title"],
                "updatedAt": r["updated_at"],
                "pinned": bool(r["pinned"]),
            }
            for r in rows
        ]


def toggle_pin(user_id: int, assistant: str, chat_id: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT pinned FROM chats WHERE user_id = ? AND assistant = ? AND id = ?",
            (user_id, assistant, chat_id),
        ).fetchone()
        if not row:
            return False
        new_value = 0 if row["pinned"] else 1
        conn.execute(
            "UPDATE chats SET pinned = ? WHERE user_id = ? AND assistant = ? AND id = ?",
            (new_value, user_id, assistant, chat_id),
        )
        return bool(new_value)


def get_chat(user_id: int, assistant: str, chat_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, title, messages_json, updated_at FROM chats WHERE user_id = ? AND assistant = ? AND id = ?",
            (user_id, assistant, chat_id),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "messages": json.loads(row["messages_json"]),
            "updatedAt": row["updated_at"],
        }


def save_chat(user_id: int, assistant: str, chat_id: str, title: str, messages: list[dict]) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO chats (id, user_id, assistant, title, messages_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET title=excluded.title, messages_json=excluded.messages_json, updated_at=excluded.updated_at
            """,
            (chat_id, user_id, assistant, title, json.dumps(messages), int(time.time() * 1000)),
        )


def delete_chat(user_id: int, assistant: str, chat_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM chats WHERE user_id = ? AND assistant = ? AND id = ?", (user_id, assistant, chat_id))


def rename_chat(user_id: int, assistant: str, chat_id: str, title: str) -> bool:
    """Only touches the title — not messages_json/updated_at — so an
    auto-generated title (or a manual rename) doesn't bump the chat to the
    top of "Recent" the way actually chatting does.
    """
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE chats SET title = ? WHERE user_id = ? AND assistant = ? AND id = ?",
            (title, user_id, assistant, chat_id),
        )
        return cur.rowcount > 0


# --- NOVA Nutrition entries ---

def load_health_entries(user_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM health_entries WHERE user_id = ? ORDER BY timestamp ASC",
            (user_id,),
        ).fetchall()
        return [
            {
                "timestamp": r["timestamp"],
                "description": r["description"],
                "items": json.loads(r["items_json"]),
                "calories": r["calories"],
                "nutrients_present": json.loads(r["nutrients_present_json"]),
                "deficiencies": json.loads(r["deficiencies_json"]),
            }
            for r in rows
        ]


def append_health_entry(user_id: int, entry: dict) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO health_entries
                (id, user_id, timestamp, description, items_json, calories, nutrients_present_json, deficiencies_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                user_id,
                entry["timestamp"],
                entry["description"],
                json.dumps(entry["items"]),
                entry["calories"],
                json.dumps(entry["nutrients_present"]),
                json.dumps(entry["deficiencies"]),
            ),
        )


def delete_health_entry(user_id: int, timestamp: str) -> bool:
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM health_entries WHERE user_id = ? AND timestamp = ?",
            (user_id, timestamp),
        )
        return cur.rowcount > 0
