# Upstream contribution — `c3-e/c3toolsprompts`

This repo and [`c3-e/c3toolsprompts`](https://github.com/c3-e/c3toolsprompts) (Mahesh Subrahmanya's agent toolkit) overlap in scope. Rather than compete, the memory architecture from here is being contributed upstream. This doc explains what's in both, what differs, and the divergence policy when upstream lands.

## Current state

- **`c3-e/c3toolsprompts` PR #61** (Mahesh) — open, not yet merged. Adds `tools/` with 11 agent personas, 12 slash commands, Cursor + CLI support, MCP configs, quality hooks, tmux orchestration, and an `/onboard` wizard.
- **`c3-e/c3toolsprompts` PR #62** (us, stacked on #61) — open. Adds `tools/agent_memory/` (the repo's `tools/swat-memory/` renamed for namespace neutrality), integrates it into his `setup.sh`, adds a Cursor rule for parity with the CLI hooks. Purely additive.

## What's in both places

| Piece | Here | Upstream (`tools/agent_memory/` in PR #62) |
|---|---|---|
| Memory MCP server | `tools/swat-memory/` | `tools/agent_memory/` (renamed) |
| Markdown auto-memory protocol doc | `bootstrap/CLAUDE.global.template.md` | appended to `tools/project-instructions/CLAUDE.md` |
| MCP + Stop/SessionStart hooks | registered via `install.sh` into `~/.claude/settings.json` | registered via Mahesh's `setup.sh` into `.claude/settings.json` (per-project) |
| Cursor MCP entry | N/A (CLI-only here) | added to `tools/mcp/cursor-mcp.json` |
| Cursor hook parity (rule) | N/A | `tools/project-instructions/agent-memory.mdc` |

## What's only here

- `/first-boot` — conversational onboarding interview (identity global, context per-project)
- `/spawn-agent` — headed agent in a new Terminal window
- `bootstrap/` templates with the `[BOOT:]` placeholder convention
- Seed-then-prompt pattern — installer drops the template at `~/.claude/CLAUDE.md` so first session auto-offers onboarding
- Global (per-user) scope — our installer targets `~/.claude/`, not per-project

## What's only upstream

- 11 agent personas (architect, backend-engineer, frontend-specialist, test-engineer, data-engineer, code-reviewer, doc-writer, performance-profiler, refactoring-expert, scrum-master, sme)
- `/team` command + Claude Code Agent Teams runtime integration
- 10 additional slash commands (`/review`, `/test`, `/docs`, `/onboard`, `/architect-plan`, `/standup`, `/deploy-check`, `/create-agent`, `/create-command`, `/setup-sme`, `/task-flow`)
- Cursor IDE support (parallel `.cursor/` deployment)
- Multi-event quality hooks (PostToolUse lint, PreToolUse secrets guard, TeammateIdle lint+build gate, TaskCompleted reminder)
- tmux multi-agent orchestration (`agents-start`, `agents-monitor`, `agents-kill`)
- C3 MCP auto-install with interactive token collection
- Per-project scope — his installer targets `./.claude/` + `./.cursor/` in the current repo

## `/onboard` vs. `/first-boot`

Different jobs that got similar names.

- **`/onboard`** (upstream) — project config wizard. Collects app name, package name, business domain, cluster URL, team/initials, MCP tokens (C3AI, GitHub, Atlassian). Structured form via `AskQuestion × 5`. Fills `[Your App Name]`-style placeholders in `CLAUDE.md`.
- **`/first-boot`** (here) — identity + codebase context interview. Conversational, infers from filesystem, groups questions, adapts to tone. Fills `[BOOT: ...]` placeholder blocks.

They don't overlap on placeholder namespaces. Both can safely populate the same `CLAUDE.md`. The intended user flow when both exist:

1. `/first-boot --global` once (identity, style, environment)
2. Per project: `/onboard` (config, tokens) and `/first-boot` (context). Either order works.

A follow-up PR after #62 will add `/first-boot` upstream alongside `/onboard`.

## Divergence policy when upstream lands

Once `c3-e/c3toolsprompts` PR #61 + #62 merge, the memory architecture lives in two places: here and there. Going forward:

1. **Upstream is canonical for the memory backend.** Bug fixes, schema changes, new MCP tools — go to `c3-e/c3toolsprompts` first via PR. Mirror back to this repo by copying `tools/agent_memory/` → `tools/swat-memory/` with the reverse rename.
2. **This repo is canonical for the onboarding experience.** `/first-boot`, `/spawn-agent`, the bootstrap templates, the seed-then-prompt pattern — belong here. Upstream gets them via a PR that adds the commands alongside Mahesh's existing ones.
3. **Config drift is fine.** The installer logic (`install.sh` here, `setup.sh` there) doesn't need to converge — they serve different scopes (global vs. per-project).
4. **If this repo gets retired,** the final state we'd want upstream to inherit is: memory + `/first-boot` + `/spawn-agent` + bootstrap templates + seed-then-prompt. Everything else is specific to this repo's standalone use case.

## Why keep this repo at all

- **Personal / non-C3 use.** This repo installs globally, works outside C3 AI projects, and doesn't require the agent persona scaffolding upstream provides.
- **Iteration sandbox.** Faster to land experiments here before pushing upstream.
- **Graceful minimal install.** Someone who wants just memory + onboarding without the full C3 agent kit can install from here with ~5 files.

If all of that stops being useful, the exit is clean: retire this repo, point everything at upstream.

## Related

- [architecture.md](architecture.md) — what the installer here actually does
- [memory.md](memory.md) — the memory architecture in detail (applies to both repos)
- [first-boot.md](first-boot.md) — the onboarding command (here-only for now)
