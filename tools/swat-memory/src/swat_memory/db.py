"""SQLite connection factory, sqlite-vec loader, and schema bootstrap/migration."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import sqlite_vec

from . import config

_SCHEMA = (Path(__file__).parent / "schema.sql").read_text()


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or config.DB_PATH
    config.ensure_dirs()
    conn = sqlite3.connect(str(path), isolation_level=None, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def bootstrap(conn: sqlite3.Connection) -> None:
    """Create tables/indexes if missing, run migrations, seed schema_version. Idempotent."""
    conn.executescript(_SCHEMA)
    _migrate(conn)
    conn.execute(
        "INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', ?)",
        (config.SCHEMA_VERSION,),
    )


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _migrate(conn: sqlite3.Connection) -> None:
    """Migrate legacy schemas forward. Currently: v1 (BLOB embedding columns) -> v2 (sqlite-vec)."""
    if _has_column(conn, "facts", "embedding"):
        _migrate_facts_v1_to_v2(conn)
    if _has_column(conn, "episodes", "embedding"):
        _migrate_episodes_v1_to_v2(conn)
    set_meta(conn, "schema_version", config.SCHEMA_VERSION)


def _migrate_facts_v1_to_v2(conn: sqlite3.Connection) -> None:
    for r in conn.execute("SELECT id, embedding FROM facts WHERE embedding IS NOT NULL"):
        conn.execute(
            "INSERT OR REPLACE INTO facts_vec(rowid, embedding) VALUES (?, ?)",
            (r["id"], r["embedding"]),
        )
    conn.executescript(
        """
        CREATE TABLE facts_new (
          id           INTEGER PRIMARY KEY AUTOINCREMENT,
          subject      TEXT    NOT NULL,
          content      TEXT    NOT NULL,
          type         TEXT    NOT NULL,
          domain       TEXT,
          confidence   REAL    NOT NULL DEFAULT 0.8,
          content_hash TEXT    NOT NULL,
          source_path  TEXT,
          created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
          updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
          UNIQUE(subject, type)
        );
        INSERT INTO facts_new(id, subject, content, type, domain, confidence,
                              content_hash, source_path, created_at, updated_at)
          SELECT id, subject, content, type, domain, confidence,
                 content_hash, source_path, created_at, updated_at FROM facts;
        DROP TABLE facts;
        ALTER TABLE facts_new RENAME TO facts;
        CREATE INDEX IF NOT EXISTS idx_facts_type   ON facts(type);
        CREATE INDEX IF NOT EXISTS idx_facts_domain ON facts(domain);
        """
    )


def _migrate_episodes_v1_to_v2(conn: sqlite3.Connection) -> None:
    for r in conn.execute("SELECT id, embedding FROM episodes WHERE embedding IS NOT NULL"):
        conn.execute(
            "INSERT OR REPLACE INTO episodes_vec(rowid, embedding) VALUES (?, ?)",
            (r["id"], r["embedding"]),
        )
    conn.executescript(
        """
        CREATE TABLE episodes_new (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          summary     TEXT    NOT NULL,
          importance  REAL    NOT NULL DEFAULT 5.0,
          tags        TEXT    NOT NULL DEFAULT '[]',
          created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
          last_seen   TEXT    NOT NULL DEFAULT (datetime('now')),
          last_decay  TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        INSERT INTO episodes_new(id, summary, importance, tags, created_at, last_seen, last_decay)
          SELECT id, summary, importance, tags, created_at, last_seen, last_decay FROM episodes;
        DROP TABLE episodes;
        ALTER TABLE episodes_new RENAME TO episodes;
        CREATE INDEX IF NOT EXISTS idx_episodes_importance ON episodes(importance);
        CREATE INDEX IF NOT EXISTS idx_episodes_created    ON episodes(created_at);
        """
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
