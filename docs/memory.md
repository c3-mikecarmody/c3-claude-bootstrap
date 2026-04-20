# Memory

Two layers work together: a markdown auto-memory protocol (human-editable source of truth) and the `swat-memory` MCP server (searchable semantic index + episode log + knowledge graph).

## The two layers

### Layer 1 — markdown auto-memory

- **Where:** `~/.claude/projects/<encoded-cwd>/memory/`
- **What:** per-project directory of individual memory files, each with typed YAML frontmatter, plus a `MEMORY.md` index that Claude loads on every session start.
- **Who writes it:** the agent, guided by the protocol in the global `CLAUDE.md`.
- **Who reads it:** the agent (via `MEMORY.md` auto-loading), and humans directly.
- **Strength:** grep-able, diffable, editable with any text editor. Survives forever.
- **Weakness:** no semantic search. You find memories by remembering their filename or grepping substrings.

Typed files look like:

```markdown
---
name: user_role
description: user is a data engineer focused on observability
type: user
---

Alice is a Staff Data Engineer at Example Corp. Owns the metrics pipeline.
Prefers Python over Go for tooling, but the prod pipeline is Go.
```

The `MEMORY.md` index file is just a line per memory:

```markdown
# Memory Index
- [user role](user_role.md) — Alice, data engineer, metrics pipeline owner
- [pref: terse responses](feedback_terse.md) — no trailing summaries
- [ingest freeze](project_ingest_freeze.md) — no non-P0 merges until 2026-04-24
```

### Layer 2 — `swat-memory` MCP

- **Where:** `~/.claude/swat-memory/memory.db` (SQLite with the `sqlite-vec` extension)
- **What:** three stores in one DB — `facts` (long-lived), `episodes` (per-session summaries), and a `knowledge_graph` (entities + relations).
- **Who writes it:** MCP tools called by the agent (`memory_save_fact`, `memory_save_episode`, `graph_upsert_*`), plus the `Stop` hook that auto-captures episodes.
- **Who reads it:** the agent via `memory_recall` (semantic search), `graph_query` (relational traversal), or direct SQL if you're debugging.
- **Strength:** semantic search across everything, fuzzy recall, "who's on X"-style relational queries.
- **Weakness:** opaque binary. You can't open it in a text editor.

## Why both

The markdown protocol is the source of truth because it's transparent: the user can read and edit what the agent is remembering. The MCP server is the *index*: when the agent needs to find something by meaning rather than by filename, it queries the DB.

**Migration keeps them in sync:** `python -m swat_memory.migrate_markdown` walks the markdown dir and upserts each file into the DB. Idempotent — re-running only re-embeds rows whose content actually changed (tracked by content hash).

**Writing new facts:** the agent should write the markdown file *and* call `memory_save_fact` with the same content. The migration command exists for retroactive sync; the pair-write pattern keeps them aligned in real time.

**Editing a fact:** edit the markdown file, then either re-run `migrate_markdown` or call `memory_save_fact` with the same `subject` — it upserts.

## Fact types

```
user      — role, goals, responsibilities, knowledge
feedback  — guidance on how to approach work (what to avoid/repeat)
project   — who's doing what, why, by when (absolute dates only)
reference — pointers to external systems (Linear, Grafana, Slack, Jira, Confluence)
```

These are the same four types across both layers. The markdown frontmatter `type:` field maps 1:1 to the `fact_type` parameter on `memory_save_fact`.

## What NOT to save (both layers)

- Patterns, conventions, architecture, file paths — derivable from the code
- Git history or who-changed-what — `git log` is authoritative
- Debugging solutions — the fix is in the code; the commit message has the context
- Anything already documented in a `CLAUDE.md`
- Ephemeral task state — use plans/TODOs, not memory

If the user explicitly asks you to save something in one of these categories, ask what was *surprising* or *non-obvious* — that's the part worth keeping.

## Episodes (MCP-only)

Episodes capture per-session summaries — they don't have a markdown equivalent. The `Stop` hook (`tools/swat-memory/hooks/stop_summarize.py`) runs at session end and writes an episode with:

- `summary` — 2–3 sentences on what was worked on, key decisions, loose ends
- `tags` — project name, feature area, relevant keywords
- `importance` — 5.0 default, 7–8 for significant milestones, 2–3 for trivial sessions

Episodes are subject to nightly maintenance:

- **Decay** — importance decreases by 0.25/day since last decay
- **Prune** — episodes with importance < 6.0 AND older than 14 days are deleted
- **Dedupe** — episodes with cosine similarity > 0.95 are merged (higher-importance wins)

This keeps the episode log useful: important stuff sticks around, background chatter fades. Run via launchd at 03:15 nightly; file-locked with `fcntl.flock` so concurrent runs skip.

## Knowledge graph (MCP-only)

Entities + directed relations. Purposely small schema:

- **Entity types:** `Person`, `Project`, `System`, `Doc`, `Unknown`
- **Relation types:** `works_on`, `owns`, `blocks`, `references`, `collaborates_with`

Use when the question is relational ("who's on X", "what does Y own"). Use `graph_upsert_entity` / `graph_upsert_relation` as people/projects surface during conversation. Pass `attributes.auto_create=true` on relations to create missing endpoints automatically as `Unknown`.

The graph is swat-memory-only — don't try to mirror it in markdown.

## When to call what

| Situation | Use |
|---|---|
| User asks "what do you remember about X" | `memory_recall(query)` |
| User shares a preference, role, or ongoing work | Write markdown file **and** `memory_save_fact` |
| Agent wraps up a session with meaningful work | `memory_save_episode` (Stop hook does this automatically in CLI) |
| Question is relational ("who's on X", "what depends on Y") | `graph_query` |
| New person/project/system mentioned | `graph_upsert_entity` opportunistically |
| Trivial lookup already in `MEMORY.md` SessionStart surface | Don't re-query — use the cached context |
| Anything ephemeral (current task state) | Use plans/TODOs, not memory |

## Staleness and verification

Memories can become stale — a file path, function name, or decision referenced in memory may no longer exist. Before recommending anything from memory, verify against current state:

- File path claim → read the file
- Function/flag claim → grep for it
- "X blocks Y" relational claim → check if it's still true

"Memory says X exists" ≠ "X exists now." If the memory is wrong, update it.

## Resetting

```bash
rm ~/.claude/swat-memory/memory.db
python -m swat_memory.migrate_markdown   # repopulate from markdown
```

The markdown files are untouched. The DB is fully derivable from them (plus whatever episodes accumulate going forward).

## Schema migration (v1 → v2)

Older DBs stored embeddings as BLOB columns directly in the `facts` and `episodes` tables. The current schema uses separate `facts_vec` and `episodes_vec` virtual tables (provided by `sqlite-vec`). On first connect, `db.bootstrap()` detects a v1 schema and upgrades in place — BLOB columns dropped, vec tables populated from the existing embeddings, `schema_version` bumped to `2`. Tested in `test_v1_to_v2_schema_migration`.

Existing data is preserved. No action needed on the user's part.

## Related

- [architecture.md](architecture.md) — where the DB lives, how the launchd maintenance job is installed
- [first-boot.md](first-boot.md) — how `/first-boot` populates initial memory
- `tools/swat-memory/README.md` — install details, MCP tool reference
