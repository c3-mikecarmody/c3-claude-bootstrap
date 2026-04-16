import pytest

from swat_memory import graph


def test_upsert_entity_idempotent(conn):
    a = graph.upsert_entity(conn, name="Mike", entity_type="Person", attributes={"role": "SE"})
    b = graph.upsert_entity(conn, name="Mike", entity_type="Person", attributes={"team": "SWAT"})
    assert a["id"] == b["id"]
    assert a["created"] is True and b["created"] is False
    row = conn.execute("SELECT attributes FROM entities WHERE id = ?", (a["id"],)).fetchone()
    import json
    assert json.loads(row["attributes"]) == {"role": "SE", "team": "SWAT"}


def test_relation_requires_existing_endpoints_by_default(conn):
    graph.upsert_entity(conn, name="Mike", entity_type="Person")
    with pytest.raises(LookupError):
        graph.upsert_relation(conn, from_name="Mike", to_name="SWAT", rel_type="works_on")


def test_relation_auto_create(conn):
    graph.upsert_entity(conn, name="Mike", entity_type="Person")
    rel = graph.upsert_relation(
        conn, from_name="Mike", to_name="SWAT", rel_type="works_on",
        attributes={"auto_create": True},
    )
    assert rel["created"] is True
    row = conn.execute("SELECT type FROM entities WHERE name='SWAT'").fetchone()
    assert row["type"] == "Unknown"


def test_self_loop_rejected(conn):
    graph.upsert_entity(conn, name="Mike", entity_type="Person")
    with pytest.raises(ValueError):
        graph.upsert_relation(conn, from_name="Mike", to_name="Mike", rel_type="works_on")


def test_query_bfs_depth(conn):
    for n, t in [("Mike", "Person"), ("Grace", "Person"), ("SWAT", "Project"), ("Agent-Solver", "Project")]:
        graph.upsert_entity(conn, name=n, entity_type=t)
    graph.upsert_relation(conn, from_name="Mike", to_name="SWAT", rel_type="works_on")
    graph.upsert_relation(conn, from_name="Grace", to_name="SWAT", rel_type="works_on")
    graph.upsert_relation(conn, from_name="SWAT", to_name="Agent-Solver", rel_type="owns")

    r1 = graph.query(conn, entity_name="Mike", depth=1)
    assert {n["name"] for n in r1["nodes"]} == {"Mike", "SWAT"}

    r2 = graph.query(conn, entity_name="Mike", depth=2)
    assert {n["name"] for n in r2["nodes"]} == {"Mike", "SWAT", "Grace", "Agent-Solver"}


def test_query_missing_entity(conn):
    r = graph.query(conn, entity_name="nope", depth=1)
    assert r["root"] is None and r["nodes"] == [] and r["edges"] == []


def test_query_depth_zero_returns_only_root(conn):
    graph.upsert_entity(conn, name="Mike", entity_type="Person")
    graph.upsert_entity(conn, name="SWAT", entity_type="Project")
    graph.upsert_relation(conn, from_name="Mike", to_name="SWAT", rel_type="works_on")
    r = graph.query(conn, entity_name="Mike", depth=0)
    assert [n["name"] for n in r["nodes"]] == ["Mike"]
    assert r["edges"] == []


def test_query_handles_cycles(conn):
    for n in ("A", "B", "C"):
        graph.upsert_entity(conn, name=n, entity_type="Person")
    graph.upsert_relation(conn, from_name="A", to_name="B", rel_type="collaborates_with")
    graph.upsert_relation(conn, from_name="B", to_name="C", rel_type="collaborates_with")
    graph.upsert_relation(conn, from_name="C", to_name="A", rel_type="collaborates_with")
    r = graph.query(conn, entity_name="A", depth=5)
    assert {n["name"] for n in r["nodes"]} == {"A", "B", "C"}
    assert len(r["edges"]) == 3  # each edge visited exactly once
