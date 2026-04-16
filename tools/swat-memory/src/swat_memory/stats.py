"""Stats tool."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config, db


def collect(conn: sqlite3.Connection) -> dict:
    counts = {}
    for name in ("episodes", "facts", "entities", "relations"):
        counts[name] = conn.execute(f"SELECT COUNT(*) AS n FROM {name}").fetchone()["n"]
    p: Path = config.DB_PATH
    counts["db_bytes"] = p.stat().st_size if p.exists() else 0
    counts["last_maintenance"] = db.get_meta(conn, "last_maintenance")
    counts["last_migration"] = db.get_meta(conn, "last_migration")
    counts["schema_version"] = db.get_meta(conn, "schema_version")
    return counts
