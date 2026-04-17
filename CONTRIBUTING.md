# Contributing

Thanks for your interest. This kit is opinionated — concise communication, no trailing summaries, minimal ceremony — so contributions that preserve that feel are easiest to merge.

## Ways to contribute

- **New slash commands** — drop a `.md` file in `commands/` following the pattern of existing ones (frontmatter with `description`, clear step-by-step body). Keep each command focused on one thing.
- **Template improvements** — edits to `bootstrap/CLAUDE.global.template.md` or `bootstrap/CLAUDE.project.template.md`. Placeholder blocks follow the `[BOOT: ...]` convention; the boot agent reads instructions inside the brackets.
- **Bug fixes** — installer, swat-memory, command scripts. Include a reproduction case.
- **swat-memory features** — new MCP tools, maintenance behavior, graph semantics. See `tools/swat-memory/README.md` and the tests in `tools/swat-memory/tests/`.
- **Documentation** — anything in `README.md`, `TOOLING.md`, or inline comments that confused you as a new reader.

## Before opening a PR

1. **Test the installer against a throwaway `$HOME`.** The pattern:
   ```bash
   FAKE_HOME=$(mktemp -d) && HOME="$FAKE_HOME" ./install.sh --no-memory
   ```
   Verify the expected files land in `$FAKE_HOME/.claude/` and any colliding files get backed up.
2. **Run the swat-memory tests** if you touched anything under `tools/swat-memory/`:
   ```bash
   cd tools/swat-memory
   source .venv/bin/activate && PYTHONPATH=src pytest tests/
   ```
3. **No personal paths.** Grep for `/Users/` in anything you added — those are installer-time substitutions, never committed.
4. **No personal bios.** The `examples/CLAUDE.md.example` and bootstrap templates are generic by design. Add your personalization via `/first-boot --global` locally, not in-repo.

## Style

- **Markdown** — ATX headings (`##`), no emoji unless mission-critical, bullets over prose for reference material.
- **Bash** — `set -euo pipefail` at the top of every script. Quote variables. Prefer POSIX-ish; avoid bashisms where a simple alternative exists.
- **Python** — follow whatever's already in `tools/swat-memory/`. Type hints welcome.

## Commit messages

Explain *why*, not just *what*. If a change is non-obvious, mention the constraint that drove it. Short subject (< 72 chars), body for context if needed.

## Non-goals

- **Cross-platform support** (Linux, Windows) — currently macOS-only. Terminal automation and launchd are macOS-specific. PRs that add Linux support are welcome but out of scope for the core team.
- **Making this a plugin.** It deliberately predates Claude Code's plugin system. If plugins mature in a way that absorbs this functionality, we'd migrate; until then, stay simple.
- **Managing Claude Code itself.** Install, auth, and updates are upstream's problem.

## Questions

Open an issue or ping a maintainer. If the question is about *why* something is shaped the way it is, `TOOLING.md` probably has the answer.
