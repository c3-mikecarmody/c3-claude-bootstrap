# Documentation index

Technical docs for `c3-claude-bootstrap` — companion to the top-level `README.md` (user-facing quickstart) and `TOOLING.md` (design rationale).

Use this index when you need detail beyond install-and-run. Each doc is focused; start here and drill into the one that matches your question.

## Docs in this folder

- [**architecture.md**](architecture.md) — how the pieces fit: installer lifecycle, what lands where in `~/.claude/`, how commands are discovered, how `settings.json` merging stays idempotent.
- [**first-boot.md**](first-boot.md) — conversational onboarding flow. What the `[BOOT:]` placeholders mean, how `/first-boot --global` vs `/first-boot` differ, how the seed-then-prompt pattern triggers Claude to offer onboarding on first session.
- [**memory.md**](memory.md) — the two memory layers (markdown auto-memory protocol + swat-memory MCP) and how they coexist. Includes the fact taxonomy, `MEMORY.md` index conventions, when to call `memory_recall` vs. grep markdown.
- [**spawn-agent.md**](spawn-agent.md) — how `/spawn-agent` opens new Terminal windows, the `--system` persona flag, iTerm2 override, the `@file` prompt pattern, and why it uses a `/tmp` launcher script instead of inline `osascript`.
- [**upstream-contribution.md**](upstream-contribution.md) — relationship to [`c3-e/c3toolsprompts` PR #62](https://github.com/c3-e/c3toolsprompts/pull/62). What ships in both repos, what differs, divergence policy when upstream lands.

## Root-level docs (out of `docs/`)

- [`../README.md`](../README.md) — user-facing quickstart: what's in the box, install, first use.
- [`../TOOLING.md`](../TOOLING.md) — design rationale for the meta-choices (commands as markdown, scripts over inline automation, augment vs. overwrite). Also where the macOS `mktemp` gotcha is recorded.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — how to test changes (clean-room `$HOME` pattern), style guide, explicit non-goals.
- [`../CHANGELOG.md`](../CHANGELOG.md) — release history.

## Reading order

New to the project:
1. Root `README.md` — install and try it
2. `docs/architecture.md` — understand what you just installed
3. `docs/first-boot.md` + `docs/memory.md` — understand the two features that actually matter day-to-day
4. Root `TOOLING.md` — understand *why* it's shaped this way (skip unless you're about to change something)

Working on a PR:
1. `../CONTRIBUTING.md`
2. `../TOOLING.md`
3. Whatever focused doc matches the subsystem you're touching
