# Changelog

All notable changes to this project will be documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Memory usage guidance baked into `bootstrap/CLAUDE.global.template.md` — both the markdown auto-memory protocol (types, when to save, how-to) and the `swat-memory` MCP tool reference (when to call `memory_recall`, division of labor between markdown and the semantic index, graph schema).
- `LICENSE` (MIT).
- `CONTRIBUTING.md` — how to test the installer, run swat-memory tests, style guide, non-goals.
- `CHANGELOG.md` — this file.

## [0.1.0] — 2026-04-16

Initial release.

### Added
- **Slash commands** — six stock (`/plan`, `/review`, `/catchup`, `/document`, `/debug`, `/commit`) plus two custom:
  - `/spawn-agent` — open a new macOS Terminal window running an interactive `claude` session with a starter prompt and optional `--system` persona.
  - `/first-boot` — conversational onboarding interview that scaffolds `~/.claude/CLAUDE.md` (`--global`) or `./CLAUDE.md` (project mode).
- **Bootstrap templates** — `CLAUDE.global.template.md` and `CLAUDE.project.template.md` with `[BOOT: ...]` placeholder blocks the first-boot agent walks through conversationally.
- **Helper scripts** — `scripts/spawn-agent.sh` (osascript → Terminal.app or iTerm2 via `SPAWN_AGENT_TERMINAL=iterm`).
- **swat-memory (bundled)** — local MCP server + SessionStart/Stop hooks + nightly launchd maintenance. SQLite-backed, local embeddings (fastembed), semantic recall across facts and episodes, knowledge graph (Person/Project/System/Doc with typed relations), decay/prune/dedupe.
- **Installer** — `./install.sh` copies (or `--link` symlinks) commands, scripts, templates into `~/.claude/`, backs up collisions, installs swat-memory by default (opt out with `--no-memory`), safely merges MCP + hook config into `settings.json` (idempotent — stale entries removed on re-run). Seeds `~/.claude/CLAUDE.md` from the global template if none exists, so first-session Claude prompts the user to run `/first-boot --global`.
- **Uninstaller** — `./uninstall.sh`, skips locally-modified files, keeps the memory DB by default.
- **Docs** — `README.md` (user-facing), `TOOLING.md` (design notes + macOS `mktemp` gotcha), `examples/CLAUDE.md.example` (sanitized reference).

### Notes
- macOS-only (Terminal automation + launchd).
- Requires Python ≥ 3.11 for swat-memory; skip with `--no-memory` if unavailable.
