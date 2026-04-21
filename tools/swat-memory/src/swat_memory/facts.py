"""Fact CRUD. Upsert by (subject, type); re-embed only when content hash changes."""
from __future__ import annotations

import hashlib
import sqlite3

from . import config, embeddings


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_vec(conn: sqlite3.Connection, rowid: int, blob: bytes) -> None:
    conn.execute("DELETE FROM facts_vec WHERE rowid = ?", (rowid,))
    conn.execute("INSERT INTO facts_vec(rowid, embedding) VALUES (?, ?)", (rowid, blob))


def save(
    conn: sqlite3.Connection,
    *,
    subject: str,
    content: str,
    type: str,
    domain: str | None = None,
    confidence: float = 0.8,
    source_path: str | None = None,
    precomputed_blob: bytes | None = None,
    precomputed_hash: str | None = None,
) -> dict:
    """Upsert a fact. If `precomputed_blob` / `precomputed_hash` are supplied the caller
    has already done the expensive embed outside the write lock; otherwise this falls
    back to encoding inline (tests/migration)."""
    if type not in config.FACT_TYPES:
        raise ValueError(f"unknown fact type {type!r}; expected one of {sorted(config.FACT_TYPES)}")

    h = precomputed_hash or _hash(content)
    existing = conn.execute(
        "SELECT id, content_hash FROM facts WHERE subject = ? AND type = ?",
        (subject, type),
    ).fetchone()

    def _encode() -> bytes:
        if precomputed_blob is not None:
            return precomputed_blob
        return embeddings.to_blob(embeddings.encode_one(embeddings.truncate_for_embed(content)))

    if existing is None:
        blob = _encode()
        cur = conn.execute(
            "INSERT INTO facts(subject, content, type, domain, confidence, content_hash, source_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (subject, content, type, domain, confidence, h, source_path),
        )
        _write_vec(conn, cur.lastrowid, blob)
        return {"id": cur.lastrowid, "created": True, "re_embedded": True}

    if existing["content_hash"] == h:
        conn.execute(
            "UPDATE facts SET domain = COALESCE(?, domain), confidence = ?, "
            "source_path = COALESCE(?, source_path), updated_at = datetime('now') WHERE id = ?",
            (domain, confidence, source_path, existing["id"]),
        )
        return {"id": existing["id"], "created": False, "re_embedded": False}

    blob = _encode()
    conn.execute(
        "UPDATE facts SET content = ?, domain = COALESCE(?, domain), confidence = ?, "
        "content_hash = ?, source_path = COALESCE(?, source_path), "
        "updated_at = datetime('now') WHERE id = ?",
        (content, domain, confidence, h, source_path, existing["id"]),
    )
    _write_vec(conn, existing["id"], blob)
    return {"id": existing["id"], "created": False, "re_embedded": True}


def compute_embedding(content: str) -> tuple[bytes, str]:
    """Expensive work to run *outside* the write transaction: encode + hash."""
    blob = embeddings.to_blob(embeddings.encode_one(embeddings.truncate_for_embed(content)))
    return blob, _hash(content)


def list_all(conn: sqlite3.Connection, *, type: str | None = None) -> list[sqlite3.Row]:
    if type:
        return list(conn.execute("SELECT * FROM facts WHERE type = ? ORDER BY updated_at DESC", (type,)))
    return list(conn.execute("SELECT * FROM facts ORDER BY updated_at DESC"))


def count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM facts").fetchone()["n"]
