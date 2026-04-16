# Design notes

Meta-document for maintainers. Describes what's in this repo, why it's shaped the way it is, and the gotchas we hit while building it.

## Contents

```
claude-bootstrap/
├── README.md                        # user-facing: what, install, customize
├── TOOLING.md                       # this file
├── install.sh / uninstall.sh        # idempotent, with backups
├── bootstrap/                       # CLAUDE.md templates with [BOOT:] placeholders
│   ├── CLAUDE.global.template.md
│   ├── CLAUDE.project.template.md
│   └── README.md
├── commands/                        # slash commands (auto-discovered by Claude Code)
│   ├── first-boot.md                # CUSTOM — onboarding interview
│   ├── spawn-agent.md               # CUSTOM — headed agent in a new Terminal
│   ├── catchup.md / plan.md / review.md / document.md / debug.md / commit.md
├── scripts/
│   └── spawn-agent.sh               # osascript wrapper
├── tools/
│   └── swat-memory/                 # local MCP memory backend (Python + SQLite + launchd)
└── examples/
    └── CLAUDE.md.example            # sanitized reference output
```

## Design choices

### Commands as markdown
Claude Code auto-discovers `~/.claude/commands/*.md`. Each file's frontmatter `description` + body becomes both a `/slash-command` for the user and a skill Claude can invoke via the Skill tool. No code, no manifest — just markdown.

### Scripts > inline automation
For anything touching macOS (Terminal, Finder, launchd), write a shell script in `scripts/` and have the command doc point at it. Keeps the command prose readable and sidesteps AppleScript quoting.

### Tempfile pattern for multi-line args
When passing prose into a shell pipeline (e.g., a prompt into `claude`), write to a `/tmp` file and pass `@<path>`. Avoids repeated `\"`-escaping. See `scripts/spawn-agent.sh`.

### Augment, don't overwrite
Anything touching user-authored content (especially `CLAUDE.md`, `settings.json`) defaults to preserving what's there. Explicit opt-in for replace. Collisions get backed up, never silently clobbered.

### Bootstrap is agent-driven, not wizard-driven
No bash `read -p` loop — `/first-boot` is a conversational interview in Claude. Feels less like a form, can adapt based on what it sees in the filesystem, and matches the user's tone.

### Memory is first-class
The `swat-memory` MCP server + `SessionStart`/`Stop` hooks are included by default. Rationale: the templates alone get you style; the memory backend is what makes onboarding *stick* across sessions — Claude actually remembers who you are and what you're working on, not just re-reads a static file.

## Gotchas

### macOS `mktemp` substitution
BSD `mktemp` on macOS doesn't substitute `XXXXXX` if a suffix follows. `mktemp /tmp/foo-XXXXXX.sh` creates a literal `foo-XXXXXX.sh` (and collides on the second call). Fix: `mktemp /tmp/foo-XXXXXX` with X's at the end and skip the suffix — `chmod +x` works fine without it.

### `--append-system-prompt` vs replace
Claude Code's harness identity ("You are Claude Code…") cannot be replaced, only appended to. `/spawn-agent --system` uses `--append-system-prompt` under the hood. For strong persona enforcement, lean on the message-level prompt too, not just the system prompt.

### `settings.json` merging
The installer parses, merges, writes. It removes prior `swat-memory` entries before adding new ones (so re-running install doesn't accumulate duplicate hooks). Any hand-edited JSON oddities will break the merge — the installer aborts rather than guess.

## Not here (and why)

- **Hooks beyond swat-memory's `SessionStart`/`Stop`** — add via `settings.json` if you need automated behaviors triggered by events. The `update-config` skill (bundled with Claude Code) handles this.
- **MCP servers beyond swat-memory** — live in project-scoped `.mcp.json` or Claude Desktop config. Out of scope for a starter kit.
- **Plugins** — managed by Claude Code's plugin system; installed plugins appear in the skills roster prefixed like `plugin-dev:create-plugin`. This repo is deliberately pre-plugin.

## Changelog

- **Initial release** — `/spawn-agent`, `/first-boot`, bootstrap templates, swat-memory bundled as default install.
