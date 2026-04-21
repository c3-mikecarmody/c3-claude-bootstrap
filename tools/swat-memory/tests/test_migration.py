from pathlib import Path

from swat_memory import config, db, embeddings, facts, migrate_markdown


FRONTMATTER = """---
name: {name}
description: test
type: {type}
---
{body}
"""


def _write(dir_: Path, stem: str, name: str, type_: str, body: str) -> Path:
    p = dir_ / f"{stem}.md"
    p.write_text(FRONTMATTER.format(name=name, type=type_, body=body))
    return p


def test_migrate_imports_facts(tmp_path, conn, monkeypatch):
    monkeypatch.setattr(migrate_markdown, "DEFAULT_SOURCE", tmp_path)
    _write(tmp_path, "user_role", "User Role", "user", "Mike is an SE at C3 AI.")
    _write(tmp_path, "feedback_terse", "Be terse", "feedback", "Keep responses short.")
    (tmp_path / "MEMORY.md").write_text("# index\n")  # should be skipped

    # Patch config.DB_PATH pathway via our conn fixture — migrate uses db.session()
    # which re-resolves DB_PATH; the fixture already monkeypatches it.
    result = migrate_markdown.migrate(tmp_path)
    assert result["facts_created"] == 2
    assert result["skipped"] == 0
    assert facts.count(conn) == 2


def test_migrate_idempotent_no_reembed(tmp_path, conn):
    _write(tmp_path, "user_role", "User Role", "user", "Mike is an SE.")
    calls = {"n": 0}
    orig = embeddings.encode_one

    def counting(text):
        calls["n"] += 1
        return orig(text)

    import swat_memory.facts as fm
    original_encode_one = fm.embeddings.encode_one
    fm.embeddings.encode_one = counting
    try:
        migrate_markdown.migrate(tmp_path)
        first = calls["n"]
        migrate_markdown.migrate(tmp_path)  # no content change → no re-embed
        assert calls["n"] == first
    finally:
        fm.embeddings.encode_one = original_encode_one


def test_migrate_body_change_reembeds(tmp_path, conn):
    p = _write(tmp_path, "user_role", "User Role", "user", "Mike is an SE.")
    migrate_markdown.migrate(tmp_path)
    p.write_text(FRONTMATTER.format(name="User Role", type="user", body="Mike is a senior SE."))
    result = migrate_markdown.migrate(tmp_path)
    assert result["facts_re_embedded"] == 1
    assert result["facts_updated"] == 1


def test_migrate_bad_frontmatter_skipped(tmp_path, conn):
    (tmp_path / "broken.md").write_text("no frontmatter here\n")
    result = migrate_markdown.migrate(tmp_path)
    assert result["skipped"] == 1


def test_v1_to_v2_schema_migration(tmp_path, monkeypatch):
    """Seed a v1-shaped DB (embedding BLOB columns, no vec tables) and verify bootstrap
    migrates to v2 cleanly: vec tables populated, BLOB columns dropped, schema_version=2."""
    import sqlite3
    import sqlite_vec

    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(config, "LOG_DIR", tmp_path)

    # Hand-build v1 schema: embedding BLOB columns, no vec tables.
    raw = sqlite3.connect(str(db_path), isolation_level=None)
    raw.enable_load_extension(True)
    sqlite_vec.load(raw)
    raw.enable_load_extension(False)
    raw.executescript("""
        CREATE TABLE episodes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          summary TEXT NOT NULL,
          importance REAL NOT NULL DEFAULT 5.0,
          tags TEXT NOT NULL DEFAULT '[]',
          embedding BLOB,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          last_seen TEXT NOT NULL DEFAULT (datetime('now')),
          last_decay TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE facts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          subject TEXT NOT NULL,
          content TEXT NOT NULL,
          type TEXT NOT NULL,
          domain TEXT,
          confidence REAL NOT NULL DEFAULT 0.8,
          embedding BLOB,
          content_hash TEXT NOT NULL,
          source_path TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now')),
          UNIQUE(subject, type)
        );
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO meta(key, value) VALUES ('schema_version', '1');
    """)
    blob = embeddings.to_blob(embeddings.encode_one("legacy row"))
    raw.execute(
        "INSERT INTO facts(subject, content, type, embedding, content_hash) VALUES (?, ?, ?, ?, ?)",
        ("legacy-subj", "legacy content", "reference", blob, "abc"),
    )
    raw.execute(
        "INSERT INTO episodes(summary, embedding) VALUES (?, ?)",
        ("legacy episode", blob),
    )
    raw.close()

    # Run bootstrap via the normal connect path; expect in-place migration.
    conn = db.connect(db_path)
    db.bootstrap(conn)

    assert db.get_meta(conn, "schema_version") == "2"
    facts_cols = {r["name"] for r in conn.execute("PRAGMA table_info(facts)")}
    episodes_cols = {r["name"] for r in conn.execute("PRAGMA table_info(episodes)")}
    assert "embedding" not in facts_cols
    assert "embedding" not in episodes_cols
    assert conn.execute("SELECT COUNT(*) FROM facts_vec").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM episodes_vec").fetchone()[0] == 1
    # Data preserved
    assert conn.execute("SELECT subject FROM facts").fetchone()["subject"] == "legacy-subj"
    conn.close()


def test_migrate_project_creates_entities(tmp_path, conn):
    body = """Mike's team.

## Key People
- **Mike Carmody** — lead
- **Grace Juan** — collaborator
"""
    _write(tmp_path, "project_swat", "SWAT", "project", body)
    result = migrate_markdown.migrate(tmp_path)
    assert result["entities_created"] >= 3  # SWAT + 2 people
    assert result["relations_created"] == 2
