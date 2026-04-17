"""Unified semantic search over facts + episodes backed by sqlite-vec."""
from __future__ import annotations

import json
import sqlite3

from . import embeddings


def _query_facts(conn: sqlite3.Connection, q_blob: bytes, k: int, fact_types: list[str] | None) -> list[dict]:
    # Over-fetch from the ANN index, then filter by type in Python. sqlite-vec MATCH
    # doesn't support arbitrary WHERE joins cheaply, so this is the pragmatic play
    # until fact counts justify something fancier.
    rows = conn.execute(
        "SELECT v.rowid AS id, v.distance, f.subject, f.content, f.type, f.domain, f.confidence "
        "FROM facts_vec v JOIN facts f ON f.id = v.rowid "
        "WHERE v.embedding MATCH ? AND k = ? ORDER BY v.distance",
        (q_blob, max(k * 4, k)),
    ).fetchall()
    out = []
    for r in rows:
        if fact_types is not None and r["type"] not in fact_types:
            continue
        out.append({
            "kind": "fact",
            "id": r["id"],
            "subject": r["subject"],
            "content": r["content"],
            "type": r["type"],
            "domain": r["domain"],
            "confidence": r["confidence"],
            "score": 1.0 - float(r["distance"]),
        })
        if len(out) >= k:
            break
    return out


def _query_episodes(conn: sqlite3.Connection, q_blob: bytes, k: int) -> list[dict]:
    rows = conn.execute(
        "SELECT v.rowid AS id, v.distance, e.summary, e.importance, e.tags "
        "FROM episodes_vec v JOIN episodes e ON e.id = v.rowid "
        "WHERE v.embedding MATCH ? AND k = ? ORDER BY v.distance",
        (q_blob, k),
    ).fetchall()
    return [
        {
            "kind": "episode",
            "id": r["id"],
            "summary": r["summary"],
            "importance": r["importance"],
            "tags": json.loads(r["tags"] or "[]"),
            "score": 1.0 - float(r["distance"]),
        }
        for r in rows
    ]


def recall(
    conn: sqlite3.Connection,
    query: str,
    k: int = 5,
    types: list[str] | None = None,
) -> list[dict]:
    """Semantic search across facts + episodes using the sqlite-vec ANN index.

    `types` filters facts by fact.type (user|feedback|project|reference);
    pass the literal "episode" to include episodes. If `types` is None/empty,
    both episodes and all fact types are searched.
    """
    if not query.strip():
        return []

    # Semantics:
    #   types None/empty         -> everything (facts + episodes, unrestricted)
    #   types = ["episode"]      -> episodes only
    #   types = [fact_types...]  -> those fact types only, no episodes
    #   types = mix              -> both, restricted
    include_episodes = True
    fact_types: list[str] | None = None   # None == unrestricted
    query_facts = True
    if types:
        requested_fact_types = [t for t in types if t != "episode"]
        include_episodes = "episode" in types
        if requested_fact_types:
            fact_types = requested_fact_types
        else:
            query_facts = False

    q_blob = embeddings.to_blob(embeddings.encode_one(query))
    hits: list[dict] = []
    if query_facts:
        hits.extend(_query_facts(conn, q_blob, k, fact_types))
    if include_episodes:
        hits.extend(_query_episodes(conn, q_blob, k))

    hits.sort(key=lambda h: -h["score"])
    return hits[:k]
