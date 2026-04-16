from pathlib import Path

from swat_memory import embeddings, facts, migrate_markdown


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
