# Bootstrap templates

Used by `/first-boot`. Two modes:

- **Global** (`/first-boot --global`) — writes `~/.claude/CLAUDE.md` from `CLAUDE.global.template.md`. Interviews the user about identity, preferences, environment. One-time; subsequent runs offer to augment rather than overwrite.
- **Project** (`/first-boot`, run inside a project dir) — writes `./CLAUDE.md` from `CLAUDE.project.template.md`. Interviews about stack, key files, external systems, domain. Appends a "Relevant Skills & References" block based on stack answers.

## How the templates work

Each template has `[BOOT: ...]` placeholders with instructions for the agent running `/first-boot`. The agent:

1. Reads the template.
2. For each `[BOOT: ...]` block, asks the user the relevant question(s) conversationally (not a rigid Q&A — group and adapt).
3. Replaces each block with the user's answer, formatted to match the surrounding style.
4. Removes the `<!-- FIRST-BOOT: ... -->` meta-comments at the top.
5. Writes the final file to its destination.

## Design notes

- Templates are opinionated defaults drawn from Mike's style (concise, no filler). The global template preserves his existing preferences verbatim; first-boot augments rather than replacing them.
- The per-project template includes a "Relevant Skills & References" section that the agent fills conditionally — e.g., a C3 stack triggers pointers to `c3-*` skills, a React project pulls in frontend references.
- If a project CLAUDE.md already exists, `/first-boot` reads it first and asks whether to augment, replace, or skip.
