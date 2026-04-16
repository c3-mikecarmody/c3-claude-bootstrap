"""One-shot: walk existing Claude Code auto-memory files → populate facts (+ best-effort entities)."""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import yaml

from . import config, db, facts, graph

log = logging.getLogger("swat-memory.migrate")

def _default_source() -> Path:
    """Claude Code stores per-project memory at ~/.claude/projects/<encoded-cwd>/memory.
    Encoding is a leading '-' plus slashes replaced with '-'. Resolve for the current cwd."""
    encoded = "-" + str(Path.cwd()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded / "memory"


DEFAULT_SOURCE = _default_source()

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_markdown(path: Path) -> tuple[dict, str] | None:
    text = path.read_text(encoding="utf-8-sig")  # strips BOM if present
    m = _FRONTMATTER_RE.match(text)
    if not m:
        log.warning("no frontmatter in %s — skipping", path.name)
        return None
    front = yaml.safe_load(m.group(1)) or {}
    body = m.group(2).strip()
    return front, body


def _domain_from_filename(path: Path, type_: str) -> str:
    stem = path.stem
    prefix = f"{type_}_"
    return stem[len(prefix):] if stem.startswith(prefix) else stem


def _extract_people(body: str) -> list[str]:
    """Best-effort: pull bolded names out of a `## Key People` or similar section.
    Returns a deduped list. Zero false-positive tolerance: if the heading isn't there, return []."""
    m = re.search(r"#{1,3}\s*(Key People|Members|Team|Owners?)\s*\n(.*?)(?=\n#{1,3}\s|\Z)", body, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    block = m.group(2)
    names = re.findall(r"\*\*([A-Z][A-Za-z.'\- ]+?)\*\*", block)
    # Drop obvious field labels
    filtered = [n.strip() for n in names if not n.strip().endswith(":")]
    seen = set()
    out = []
    for n in filtered:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def migrate(source: Path, dry_run: bool = False) -> dict:
    if not source.exists():
        raise FileNotFoundError(source)

    created = 0
    updated = 0
    re_embedded = 0
    skipped = 0
    entities_created = 0
    relations_created = 0

    with db.session() as conn:
        if not dry_run:
            conn.execute("BEGIN IMMEDIATE")
        for path in sorted(source.glob("*.md")):
            if path.name == "MEMORY.md":
                continue
            parsed = parse_markdown(path)
            if parsed is None:
                skipped += 1
                continue
            front, body = parsed
            type_ = front.get("type")
            name = front.get("name")
            if not name or type_ not in config.FACT_TYPES:
                log.warning("bad frontmatter in %s (name=%r type=%r) — skipping", path.name, name, type_)
                skipped += 1
                continue

            if dry_run:
                log.info("[dry-run] would upsert %s [%s]", name, type_)
                continue

            result = facts.save(
                conn,
                subject=name,
                content=body,
                type=type_,
                domain=_domain_from_filename(path, type_),
                confidence=0.9,
                source_path=str(path),
            )
            if result["created"]:
                created += 1
            else:
                updated += 1
            if result["re_embedded"]:
                re_embedded += 1

            if type_ == "project":
                ent = graph.upsert_entity(conn, name=name, entity_type="Project")
                if ent["created"]:
                    entities_created += 1
                for person in _extract_people(body):
                    p = graph.upsert_entity(conn, name=person, entity_type="Person")
                    if p["created"]:
                        entities_created += 1
                    try:
                        rel = graph.upsert_relation(
                            conn,
                            from_name=person,
                            to_name=name,
                            rel_type="works_on",
                        )
                        if rel["created"]:
                            relations_created += 1
                    except (LookupError, ValueError):
                        pass

        if not dry_run:
            db.set_meta(conn, "last_migration", _now())
            conn.execute("COMMIT")

    return {
        "facts_created": created,
        "facts_updated": updated,
        "facts_re_embedded": re_embedded,
        "skipped": skipped,
        "entities_created": entities_created,
        "relations_created": relations_created,
    }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    p = argparse.ArgumentParser(description="Migrate Claude Code markdown memory into swat-memory.")
    p.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    result = migrate(args.source, dry_run=args.dry_run)
    log.info("migration result: %s", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
