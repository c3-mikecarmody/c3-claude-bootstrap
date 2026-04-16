"""SQLite connection factory and schema bootstrap."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config

_SCHEMA = (Path(__file__).parent / "schema.sql").read_text()


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or config.DB_PATH
    config.ensure_dirs()
    conn = sqlite3.connect(str(path), isolation_level=None, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def bootstrap(conn: sqlite3.Connection) -> None:
    """Create tables/indexes if missing and seed schema_version. Idempotent."""
    conn.executescript(_SCHEMA)
    conn.execute(
        "INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', ?)",
        (config.SCHEMA_VERSION,),
    )


@contextmanager
def session(db_path: Path | None = None):
    conn = connect(db_path)
    bootstrap(conn)
    try:
        yield conn
    finally:
        conn.close()


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
