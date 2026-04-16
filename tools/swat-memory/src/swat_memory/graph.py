"""Knowledge graph: entity + relation upsert, BFS traversal."""
from __future__ import annotations

import json
import sqlite3
from collections import deque

from . import config


def upsert_entity(
    conn: sqlite3.Connection,
    *,
    name: str,
    entity_type: str,
    attributes: dict | None = None,
) -> dict:
    if entity_type not in config.ENTITY_TYPES:
        raise ValueError(
            f"unknown entity type {entity_type!r}; expected one of {sorted(config.ENTITY_TYPES)}"
        )
    attrs = attributes or {}
    row = conn.execute(
        "SELECT id, attributes FROM entities WHERE name = ? AND type = ?",
        (name, entity_type),
    ).fetchone()
    if row is None:
        cur = conn.execute(
            "INSERT INTO entities(name, type, attributes) VALUES (?, ?, ?)",
            (name, entity_type, json.dumps(attrs)),
        )
        return {"id": cur.lastrowid, "created": True}
    merged = {**json.loads(row["attributes"] or "{}"), **attrs}
    conn.execute(
        "UPDATE entities SET attributes = ? WHERE id = ?",
        (json.dumps(merged), row["id"]),
    )
    return {"id": row["id"], "created": False}


def _resolve(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, name, type FROM entities WHERE name = ? ORDER BY id LIMIT 1",
        (name,),
    ).fetchone()


def upsert_relation(
    conn: sqlite3.Connection,
    *,
    from_name: str,
    to_name: str,
    rel_type: str,
    attributes: dict | None = None,
) -> dict:
    if rel_type not in config.RELATION_TYPES:
        raise ValueError(
            f"unknown relation type {rel_type!r}; expected one of {sorted(config.RELATION_TYPES)}"
        )
    attrs = attributes or {}
    auto_create = bool(attrs.pop("auto_create", False))

    def _get_or_create(name: str) -> int:
        row = _resolve(conn, name)
        if row is not None:
            return row["id"]
        if not auto_create:
            raise LookupError(f"entity {name!r} not found and auto_create=False")
        return upsert_entity(conn, name=name, entity_type="Unknown")["id"]

    from_id = _get_or_create(from_name)
    to_id = _get_or_create(to_name)
    if from_id == to_id:
        raise ValueError("self-loop relation not allowed")

    existing = conn.execute(
        "SELECT id, attributes FROM relations WHERE from_id = ? AND to_id = ? AND rel_type = ?",
        (from_id, to_id, rel_type),
    ).fetchone()
    if existing is None:
        cur = conn.execute(
            "INSERT INTO relations(from_id, to_id, rel_type, attributes) VALUES (?, ?, ?, ?)",
            (from_id, to_id, rel_type, json.dumps(attrs)),
        )
        return {"id": cur.lastrowid, "created": True}
    merged = {**json.loads(existing["attributes"] or "{}"), **attrs}
    conn.execute(
        "UPDATE relations SET attributes = ? WHERE id = ?",
        (json.dumps(merged), existing["id"]),
    )
    return {"id": existing["id"], "created": False}


def query(
    conn: sqlite3.Connection,
    entity_name: str,
    rel_type: str | None = None,
    depth: int = 1,
) -> dict:
    """BFS from entity up to `depth` hops. Edges traversed in both directions."""
    root = _resolve(conn, entity_name)
    if root is None:
        return {"root": None, "nodes": [], "edges": []}

    nodes: dict[int, dict] = {}
    edges: list[dict] = []
    seen_edges: set[int] = set()
    frontier: deque[tuple[int, int]] = deque([(root["id"], 0)])
    visited: set[int] = set()

    while frontier:
        node_id, dist = frontier.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)
        row = conn.execute(
            "SELECT id, name, type, attributes FROM entities WHERE id = ?", (node_id,)
        ).fetchone()
        if row is None:
            continue
        nodes[node_id] = {
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "attributes": json.loads(row["attributes"] or "{}"),
        }
        if dist >= depth:
            continue

        params: list = [node_id, node_id]
        where = "(from_id = ? OR to_id = ?)"
        if rel_type:
            where += " AND rel_type = ?"
            params.append(rel_type)
        for e in conn.execute(
            f"SELECT id, from_id, to_id, rel_type, attributes FROM relations WHERE {where}",
            params,
        ):
            if e["id"] in seen_edges:
                continue
            seen_edges.add(e["id"])
            edges.append({
                "id": e["id"],
                "from_id": e["from_id"],
                "to_id": e["to_id"],
                "rel_type": e["rel_type"],
                "attributes": json.loads(e["attributes"] or "{}"),
            })
            other = e["to_id"] if e["from_id"] == node_id else e["from_id"]
            if other not in visited:
                frontier.append((other, dist + 1))

    return {
        "root": nodes.get(root["id"]),
        "nodes": list(nodes.values()),
        "edges": edges,
    }
