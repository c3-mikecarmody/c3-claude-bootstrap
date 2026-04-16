"""MCP stdio server wiring the 7 tools to the DB."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import db, embeddings, episodes, facts, graph, recall, stats

mcp = FastMCP("swat-memory")


@mcp.tool()
def memory_recall(query: str, k: int = 5, types: list[str] | None = None) -> list[dict]:
    """Semantic search across facts + episodes. Returns ranked hits with a `score` (cosine).

    `types` filters by fact type (`user`, `feedback`, `project`, `reference`) and/or the
    literal `episode`. Omit or pass null to search everything.
    """
    with db.session() as conn:
        return recall.recall(conn, query=query, k=k, types=types)


@mcp.tool()
def memory_save_fact(
    subject: str,
    content: str,
    fact_type: str,
    domain: str | None = None,
    confidence: float = 0.8,
) -> dict:
    """Upsert a fact. Keyed by (subject, fact_type). Re-embeds only when content changes.
    `fact_type` must be one of: user, feedback, project, reference."""
    blob, content_hash = facts.compute_embedding(content)  # outside write lock
    with db.session() as conn:
        conn.execute("BEGIN IMMEDIATE")
        result = facts.save(
            conn,
            subject=subject,
            content=content,
            type=fact_type,
            domain=domain,
            confidence=confidence,
            precomputed_blob=blob,
            precomputed_hash=content_hash,
        )
        conn.execute("COMMIT")
        return result


@mcp.tool()
def memory_save_episode(
    summary: str, tags: list[str] | None = None, importance: float = 5.0
) -> dict:
    """Insert a new episode; the summary is embedded for semantic recall."""
    blob = episodes.compute_embedding(summary)  # outside write lock
    with db.session() as conn:
        conn.execute("BEGIN IMMEDIATE")
        result = episodes.save(
            conn, summary=summary, tags=tags, importance=importance, precomputed_blob=blob
        )
        conn.execute("COMMIT")
        return result


@mcp.tool()
def graph_query(entity_name: str, rel_type: str | None = None, depth: int = 1) -> dict:
    """Traverse the knowledge graph from `entity_name` up to `depth` hops.
    Returns {root, nodes, edges}."""
    with db.session() as conn:
        return graph.query(conn, entity_name=entity_name, rel_type=rel_type, depth=depth)


@mcp.tool()
def graph_upsert_entity(
    name: str, entity_type: str, attributes: dict | None = None
) -> dict:
    """Create or update an entity. `entity_type` in {Person, Project, System, Doc, Unknown}."""
    with db.session() as conn:
        conn.execute("BEGIN IMMEDIATE")
        result = graph.upsert_entity(conn, name=name, entity_type=entity_type, attributes=attributes)
        conn.execute("COMMIT")
        return result


@mcp.tool()
def graph_upsert_relation(
    from_name: str,
    to_name: str,
    rel_type: str,
    attributes: dict | None = None,
) -> dict:
    """Create or update a directed relation. Set `attributes.auto_create=true` to
    auto-create missing endpoints as type 'Unknown'."""
    with db.session() as conn:
        conn.execute("BEGIN IMMEDIATE")
        result = graph.upsert_relation(
            conn,
            from_name=from_name,
            to_name=to_name,
            rel_type=rel_type,
            attributes=attributes,
        )
        conn.execute("COMMIT")
        return result


@mcp.tool()
def memory_stats() -> dict:
    """Counts, DB size, last maintenance/migration timestamps, schema version."""
    with db.session() as conn:
        return stats.collect(conn)


def run() -> None:
    embeddings.prewarm()
    mcp.run()
