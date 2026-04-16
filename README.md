# claude-bootstrap

Opinionated starter kit for Claude Code: custom slash commands, onboarding templates, and a local memory backend. One `./install.sh` gets you set up.

## What's in the box

- **Slash commands** (`commands/`) — `/plan`, `/review`, `/catchup`, `/document`, `/debug`, `/commit`, plus custom ones:
  - `/spawn-agent` — open a new Terminal window running an interactive Claude session with a starter prompt
  - `/first-boot` — conversational interview that scaffolds a `CLAUDE.md` (global or per-project)
- **Bootstrap templates** (`bootstrap/`) — `CLAUDE.md` templates with `[BOOT:]` placeholders the first-boot agent walks through
- **Helper scripts** (`scripts/`) — e.g., `spawn-agent.sh` (osascript → Terminal.app)
- **swat-memory** (`tools/swat-memory/`) — local MCP server + hooks providing persistent memory across Claude Code sessions: facts, episodes, knowledge graph, semantic recall via local embeddings, nightly decay/prune/dedupe maintenance. Python + SQLite, no daemon, no API calls.
- **Example CLAUDE.md** (`examples/`) — a sanitized baseline to compare against after running `/first-boot --global`

## Install

```bash
git clone <this-repo> ~/claude-bootstrap
cd ~/claude-bootstrap
./install.sh
```

By default this **copies** the relevant files into `~/.claude/` and installs swat-memory (creates a venv, loads a launchd job, patches `~/.claude/settings.json` to register the MCP server + `SessionStart`/`Stop` hooks).

Flags:

- `--no-memory` — skip swat-memory (just commands/scripts/templates)
- `--link` — symlink into `~/.claude/` instead of copying (good for hacking on this repo)
- `--force` — overwrite existing files (collisions always get backed up to `~/.claude/.bootstrap-backup-<timestamp>/`)

## First use

1. Restart Claude Code (or open a new session) so it picks up the new commands, hooks, and MCP server.
2. From any project or a fresh shell:
   - `/first-boot --global` — interview yourself into `~/.claude/CLAUDE.md` (identity, preferences, environment).
   - `/first-boot` — run inside a project dir to scaffold `./CLAUDE.md` (stack, key files, externals, domain jargon, relevant skills).
3. (Optional, existing users) migrate any markdown auto-memory you already have:
   ```bash
   cd <your-project-you've-been-using>
   source ~/claude-bootstrap/tools/swat-memory/.venv/bin/activate
   python -m swat_memory.migrate_markdown --dry-run
   python -m swat_memory.migrate_markdown
   ```

## Uninstall

```bash
./uninstall.sh            # removes everything, keeps the memory DB
./uninstall.sh --keep-memory   # leaves swat-memory installed
```

Files that were locally modified are left alone (detected via checksum mismatch); the installer's backups are never auto-deleted.

## Requirements

- macOS (Terminal/iTerm2 automation and launchd are macOS-specific; Linux support not wired up yet)
- Python ≥ 3.11 (for swat-memory; skip with `--no-memory` if unavailable)
- Claude Code CLI installed and authenticated

## Customizing

This kit is opinionated — concise communication defaults, no trailing summaries, no option menus, etc. The templates and example `CLAUDE.md` are the intended entry points for personalization:

- **Personal preferences** → `bootstrap/CLAUDE.global.template.md` drives `/first-boot --global`. Edit the template if your team wants different defaults before rollout.
- **Project conventions** → `bootstrap/CLAUDE.project.template.md`.
- **Commands** → add/edit `commands/*.md` before install; they're plain markdown.

## License & sharing

Internal / team-shared. See `TOOLING.md` for design rationale and the `mktemp` gotcha we hit along the way.
