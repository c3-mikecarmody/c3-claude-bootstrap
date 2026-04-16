from swat_memory import db


def test_bootstrap_creates_tables(conn):
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"episodes", "facts", "entities", "relations", "meta"}.issubset(tables)


def test_schema_version_seeded(conn):
    assert db.get_meta(conn, "schema_version") == "1"


def test_bootstrap_idempotent(conn):
    db.bootstrap(conn)  # second call should not raise
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "episodes" in tables


def test_meta_upsert(conn):
    db.set_meta(conn, "foo", "bar")
    db.set_meta(conn, "foo", "baz")
    assert db.get_meta(conn, "foo") == "baz"
