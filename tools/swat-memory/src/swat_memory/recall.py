"""Unified cosine search over facts + episodes."""
from __future__ import annotations

import json
import sqlite3

import numpy as np

from . import embeddings


def recall(
    conn: sqlite3.Connection,
    query: str,
    k: int = 5,
    types: list[str] | None = None,
) -> list[dict]:
    """Embedding search across facts + episodes.

    `types` filters facts by fact.type (user|feedback|project|reference);
    pass the literal "episode" to include episodes. If `types` is None/empty,
    both episodes and all fact types are searched.
    """
    if not query.strip():
        return []

    # Semantics:
    #   types is None/empty  -> search everything (all fact types + episodes)
    #   types contains "episode" only        -> episodes only
    #   types contains fact types only       -> those fact types only, no episodes
    #   types contains "episode" + fact types -> both, restricted
    include_episodes = True
    fact_types: list[str] | None = None
    if types:
        fact_types = [t for t in types if t != "episode"]
        include_episodes = "episode" in types

    q_vec = embeddings.encode_one(query)

    candidates: list[tuple[dict, np.ndarray]] = []

    if fact_types is None or fact_types:
        if fact_types:
            placeholders = ",".join(["?"] * len(fact_types))
            rows = list(conn.execute(
                f"SELECT id, subject, content, type, domain, confidence, embedding "
                f"FROM facts WHERE type IN ({placeholders})",
                fact_types,
            ))
        else:
            rows = list(conn.execute(
                "SELECT id, subject, content, type, domain, confidence, embedding FROM facts"
            ))
        for r in rows:
            vec = embeddings.from_blob(r["embedding"])
            if vec is None:
                continue
            candidates.append(({
                "kind": "fact",
                "id": r["id"],
                "subject": r["subject"],
                "content": r["content"],
                "type": r["type"],
                "domain": r["domain"],
                "confidence": r["confidence"],
            }, vec))

    if include_episodes:
        for r in conn.execute(
            "SELECT id, summary, importance, tags, embedding FROM episodes"
        ):
            vec = embeddings.from_blob(r["embedding"])
            if vec is None:
                continue
            candidates.append(({
                "kind": "episode",
                "id": r["id"],
                "summary": r["summary"],
                "importance": r["importance"],
                "tags": json.loads(r["tags"] or "[]"),
            }, vec))

    if not candidates:
        return []

    matrix = np.stack([v for _, v in candidates])
    scores = embeddings.cosine_matrix(q_vec, matrix)
    order = np.argsort(-scores)[:k]

    out = []
    for idx in order:
        hit = dict(candidates[int(idx)][0])
        hit["score"] = float(scores[int(idx)])
        out.append(hit)
    return out
