# swat-memory

Local MCP server providing persistent memory for Claude Code sessions. Three stores in one SQLite file:

- **Facts** — structured long-lived knowledge (user, feedback, project, reference). Replaces the markdown auto-memory substrate.
- **Episodes** — session summaries with importance scoring, decay, and consolidation.
- **Knowledge graph** — entities (Person, Project, System, Doc) + directed relations.

Semantic recall across facts + episodes via local embeddings (fastembed, BAAI/bge-small-en-v1.5). No API calls. No daemon.

## Install

Normally installed via the top-level `claude-bootstrap` installer (`./install.sh`), which runs `scripts/install.sh` here and patches `~/.claude/settings.json` with resolved paths automatically.

Standalone install:

```bash
cd tools/swat-memory
./scripts/install.sh
```

The installer creates `.venv`, pip-installs the package editable, renders and loads the launchd plist at `~/Library/LaunchAgents/com.c3.swat-memory.maintenance.plist` (runs nightly at 03:15).

Then add the following to `~/.claude/settings.json` (merge with existing blocks — replace `${SWAT_MEMORY_ROOT}` with the absolute path to this directory):

```json
{
  "mcpServers": {
    "swat-memory": {
      "command": "${SWAT_MEMORY_ROOT}/.venv/bin/python",
      "args": ["-m", "swat_memory"]
    }
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "${SWAT_MEMORY_ROOT}/.venv/bin/python ${SWAT_MEMORY_ROOT}/hooks/session_start.py"
        }]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "${SWAT_MEMORY_ROOT}/.venv/bin/python ${SWAT_MEMORY_ROOT}/hooks/stop_summarize.py"
        }]
      }
    ]
  }
}
```

Then migrate the existing markdown memory:

```bash
source .venv/bin/activate
python -m swat_memory.migrate_markdown         # real run
python -m swat_memory.migrate_markdown --dry-run  # preview
```

## MCP tools

- `memory_recall(query, k=5, types=[])` — cosine search across facts + episodes
- `memory_save_fact(subject, content, type, domain?, confidence=0.8)`
- `memory_save_episode(summary, tags=[], importance=5.0)`
- `graph_query(entity_name, rel_type?, depth=1)` — BFS traversal
- `graph_upsert_entity(name, entity_type, attributes={})`
- `graph_upsert_relation(from_name, to_name, rel_type, attributes={})` — pass `attributes.auto_create=true` to create missing endpoints
- `memory_stats()` — counts, DB size, last maintenance/migration

## Maintenance

Nightly job (launchd) runs `python -m swat_memory.maintenance`:

- **Decay**: importance -= 0.25 per day since last decay
- **Prune**: delete episodes with importance < 6.0 AND older than 14 days
- **Dedupe**: merge near-duplicate episodes (cosine > 0.95), keep higher-importance

File-locked via `fcntl.flock` so concurrent runs skip.

## Tests

```bash
source .venv/bin/activate
pip install pytest
PYTHONPATH=src pytest tests/
```

The suite uses a deterministic stub embedder (conftest.py), so fastembed is not required to run tests.

## Rollback

```bash
./scripts/uninstall.sh
```

Removes the launchd plist. DB is preserved at `~/.claude/swat-memory/memory.db`; delete manually for a clean slate. Remove the `mcpServers` and `hooks` blocks for `swat-memory` from `~/.claude/settings.json` by hand.
