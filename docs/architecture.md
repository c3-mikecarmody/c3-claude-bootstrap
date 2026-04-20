# Architecture

How the pieces fit. Start here after running `./install.sh` to understand what you just put on your machine.

## What the installer produces

```
~/.claude/
├── CLAUDE.md               ← global identity (seeded from template if none existed)
├── commands/
│   ├── catchup.md          ← stock commands
│   ├── commit.md
│   ├── debug.md
│   ├── document.md
│   ├── plan.md
│   ├── review.md
│   ├── first-boot.md       ← custom: onboarding interview
│   └── spawn-agent.md      ← custom: headed agent in a new Terminal
├── scripts/
│   └── spawn-agent.sh      ← osascript wrapper
├── bootstrap/
│   ├── CLAUDE.global.template.md
│   ├── CLAUDE.project.template.md
│   └── README.md
└── settings.json           ← swat-memory MCP + SessionStart/Stop hooks merged in
```

Plus, if swat-memory was installed (default):

```
~/claude-bootstrap/tools/swat-memory/   (source stays in the repo, not copied)
├── .venv/                              ← created by scripts/install.sh
├── src/swat_memory/
├── hooks/
│   ├── session_start.py
│   ├── stop_summarize.py
│   └── com.c3.swat-memory.maintenance.plist
└── ...

~/Library/LaunchAgents/com.c3.swat-memory.maintenance.plist  ← loaded via launchctl
~/.claude/swat-memory/memory.db                              ← SQLite DB, created on first run
~/.claude/swat-memory/maintenance.{log,err}                  ← launchd stdout/stderr
```

## Installer lifecycle (`install.sh`)

Runs in this order:

1. **Base copy** — commands, scripts, bootstrap templates into `~/.claude/`. Collisions get backed up to `~/.claude/.bootstrap-backup-<timestamp>/` before overwrite.
2. **Seed `~/.claude/CLAUDE.md`** — if no global `CLAUDE.md` exists, copy the template (with `[BOOT:]` placeholders intact) so first session triggers onboarding. If one exists, leave it alone.
3. **swat-memory install** (skippable with `--no-memory`):
   - Run `tools/swat-memory/scripts/install.sh` (creates `.venv`, pip-installs package editable, renders plist from `__REPO__`/`__HOME__` placeholders, loads via `launchctl`).
   - Merge MCP + hooks config into `~/.claude/settings.json` — parses existing JSON, appends `swat-memory` MCP entry, adds `SessionStart` + `Stop` hooks. Idempotent: re-run strips prior `swat-memory` entries before adding new ones.
4. **Next-steps banner** — tells the user what to do: restart Claude Code, expect a first-boot prompt, optionally migrate existing markdown memory.

### Install modes

- **`copy` (default)** — physical copies in `~/.claude/`. Good for deployment.
- **`--link`** — symlinks into `~/.claude/`. Good for hacking on this repo — edits in the repo reflect immediately.
- **`--force`** — overwrite existing files (still with backups).

## Why it's split into scripts + markdown + Python

- **Markdown for commands** — Claude Code auto-discovers `~/.claude/commands/*.md`. The frontmatter `description` field surfaces the command to the user; the body is the prompt Claude sees when invoked. No code, no manifest.
- **Shell scripts for macOS automation** — `spawn-agent.sh` uses `osascript`. Keeping it out of the markdown command file means the command stays readable and the AppleScript quoting stays in one place.
- **Python for memory** — SQLite + embeddings + an MCP server is non-trivial. Lives as its own package (`tools/swat-memory/`) so it has a normal pyproject lifecycle, a venv, and tests.

## settings.json merging

The installer parses `~/.claude/settings.json` as JSON, mutates it in memory, writes it back. Key properties:

- **Idempotent** — Before adding the `swat-memory` MCP entry or hooks, any prior `swat-memory` entries are stripped (matched by command substring). Re-running install doesn't accumulate duplicates.
- **Preserves user-authored config** — Unrelated `mcpServers` entries, unrelated `hooks` events (PreToolUse, etc.), top-level keys like `theme` — all untouched.
- **Backed up every run** — `settings.json.bak-<timestamp>` before each modification.
- **Aborts on JSON errors** — If the file is not valid JSON, the installer errors rather than silently reformatting it.

The merge logic is an inline Python heredoc in `install.sh`. Tested via a synthetic `settings.json` in `CONTRIBUTING.md`'s install-test pattern.

## Auto-prompt on first session (seed-then-prompt)

The subtle piece: `install.sh` copies the global CLAUDE.md template verbatim to `~/.claude/CLAUDE.md` when none exists. That file has `[BOOT:]` placeholders *and* a top-of-file comment telling any Claude session that encounters them:

> *If you see any `[bracketed placeholder]` at boot time, it means the user hasn't completed first-boot — offer to run `/first-boot --global`.*

So on the user's first session after install, Claude loads the global CLAUDE.md, sees the placeholder, and proactively offers onboarding. No "go read the README" step.

If the user already has a rich global CLAUDE.md, the installer leaves it alone (no seed) — the prompt doesn't fire, and the user can run `/first-boot --global` manually if they want to augment.

## Uninstall

`uninstall.sh` reverses by file-content match:

- For each file the installer copied, compare the installed version to the repo version. If they match (or are symlinks pointing back to the repo), remove. If they differ (user edited), leave alone.
- Run `tools/swat-memory/scripts/uninstall.sh` which unloads the launchd plist.
- Strip `swat-memory` entries from `~/.claude/settings.json` (same merge logic, reverse direction).
- **Preserve the DB** at `~/.claude/swat-memory/memory.db`. Delete manually for a clean slate.
- Backups in `~/.claude/.bootstrap-backup-*/` are never auto-deleted.

## Related

- [first-boot.md](first-boot.md) — what happens after the auto-prompt fires
- [memory.md](memory.md) — what swat-memory actually does with the DB it creates
- [spawn-agent.md](spawn-agent.md) — the other custom command
- [../TOOLING.md](../TOOLING.md) — design rationale for *why* the architecture is this shape
