"""Episode CRUD + maintenance helpers (decay, prune, dedupe)."""
from __future__ import annotations

import json
import sqlite3

import numpy as np

from . import config, embeddings


def save(
    conn: sqlite3.Connection,
    *,
    summary: str,
    tags: list[str] | None = None,
    importance: float = 5.0,
    precomputed_blob: bytes | None = None,
) -> dict:
    tags_json = json.dumps(list(tags or []))
    blob = precomputed_blob if precomputed_blob is not None else embeddings.to_blob(
        embeddings.encode_one(embeddings.truncate_for_embed(summary))
    )
    cur = conn.execute(
        "INSERT INTO episodes(summary, importance, tags) VALUES (?, ?, ?)",
        (summary, importance, tags_json),
    )
    conn.execute(
        "INSERT INTO episodes_vec(rowid, embedding) VALUES (?, ?)",
        (cur.lastrowid, blob),
    )
    return {"id": cur.lastrowid}


def compute_embedding(summary: str) -> bytes:
    return embeddings.to_blob(embeddings.encode_one(embeddings.truncate_for_embed(summary)))


def all_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM episodes"))


def count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM episodes").fetchone()["n"]


def decay(conn: sqlite3.Connection) -> int:
    """Decrease importance by DECAY_RATE per full day since last_decay, clamped at 0.0.
    Advances last_decay by exactly N days (not to `now`) so fractional drift accumulates
    across runs instead of being silently discarded by floor(days)."""
    rows = list(
        conn.execute(
            "SELECT id, importance, julianday('now') - julianday(last_decay) AS days "
            "FROM episodes"
        )
    )
    touched = 0
    for r in rows:
        days = int(r["days"] or 0)
        if days <= 0:
            continue
        new_imp = max(0.0, float(r["importance"]) - config.DECAY_RATE * days)
        conn.execute(
            "UPDATE episodes SET importance = ?, "
            "last_decay = datetime(last_decay, ?) WHERE id = ?",
            (new_imp, f"+{days} days", r["id"]),
        )
        touched += 1
    return touched


def prune(conn: sqlite3.Connection) -> int:
    """Delete episodes with importance below cutoff AND older than grace period."""
    doomed = [
        r["id"]
        for r in conn.execute(
            "SELECT id FROM episodes WHERE importance < ? "
            "AND julianday('now') - julianday(created_at) > ?",
            (config.IMPORTANCE_CUTOFF, config.PRUNE_GRACE_DAYS),
        )
    ]
    for rowid in doomed:
        conn.execute("DELETE FROM episodes_vec WHERE rowid = ?", (rowid,))
        conn.execute("DELETE FROM episodes WHERE id = ?", (rowid,))
    return len(doomed)


def dedupe(conn: sqlite3.Connection) -> int:
    """Merge near-duplicate episodes (cosine > DEDUPE_COSINE). Keeps higher-importance.
    Reads embeddings back from episodes_vec rather than keeping a parallel BLOB column."""
    rows = all_rows(conn)
    if len(rows) < 2:
        return 0
    ids = [r["id"] for r in rows]
    vec_rows = conn.execute(
        f"SELECT rowid, embedding FROM episodes_vec WHERE rowid IN ({','.join(['?'] * len(ids))})",
        ids,
    ).fetchall()
    vec_by_id = {r["rowid"]: np.frombuffer(r["embedding"], dtype=np.float32) for r in vec_rows}
    kept = [r for r in rows if r["id"] in vec_by_id]
    if len(kept) < 2:
        return 0
    matrix = np.stack([vec_by_id[r["id"]] for r in kept])
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12
    normed = matrix / norms
    sims = normed @ normed.T

    removed = 0
    alive = [True] * len(kept)
    for i in range(len(kept)):
        if not alive[i]:
            continue
        for j in range(i + 1, len(kept)):
            if not alive[j]:
                continue
            if float(sims[i, j]) <= config.DEDUPE_COSINE:
                continue
            a, b = kept[i], kept[j]
            keep, drop = (a, b) if a["importance"] >= b["importance"] else (b, a)
            merged_tags = sorted({*json.loads(a["tags"] or "[]"), *json.loads(b["tags"] or "[]")})
            conn.execute(
                "UPDATE episodes SET tags = ?, last_seen = datetime('now') WHERE id = ?",
                (json.dumps(merged_tags), keep["id"]),
            )
            conn.execute("DELETE FROM episodes_vec WHERE rowid = ?", (drop["id"],))
            conn.execute("DELETE FROM episodes WHERE id = ?", (drop["id"],))
            alive[i if drop is a else j] = False
            removed += 1
            if drop is a:
                break
    return removed
