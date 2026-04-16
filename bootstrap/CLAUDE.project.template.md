# [PROJECT_NAME]

<!--
FIRST-BOOT: The sections below in [brackets] are placeholders. The boot agent
interviews the user and replaces them. Delete brackets and this comment when done.
If any [bracketed placeholder] remains at boot time, offer to run `/first-boot`.
-->

## What This Project Is

[BOOT: One paragraph — what is this repo/project, who it serves, what state it's in (prototype, production, greenfield, legacy). Ask the user directly; don't guess from code.]

## Stack & Tooling

[BOOT: Ask about languages, frameworks, package manager, test runner, build system, deploy target. One short bullet per item. Keep it to what's actually in use, not what might be.]

- Languages:
- Framework(s):
- Package manager:
- Tests:
- Build / deploy:

## Key Files & Entry Points

[BOOT: Ask which files matter most — the 3–6 places a new contributor (or agent) should read first. Capture purpose in one line each.]

- `path/to/file` — what lives here

## External Systems & Integrations

[BOOT: Anything touched outside this repo — APIs, databases, third-party services, MCP servers, auth providers. List with one-line purpose and where credentials live (or note that they're in env/secret manager — never paste them).]

## Domain Jargon

[BOOT: Any acronyms or terms specific to this domain/business that the agent should know to avoid looking clueless. Skip if none.]

## How to Run / Test / Ship

[BOOT: The actual commands. `npm run dev`, `pytest`, `make deploy`, etc. Not aspirational — what the user actually types today.]

- Run locally:
- Run tests:
- Lint / typecheck:
- Ship:

## Project-Specific Rules

[BOOT: Anything the agent should DO or NOT DO that's specific to this project. Skip if there's nothing beyond the global CLAUDE.md. Examples:
  - "Never touch files under `legacy/` — that's frozen."
  - "All migrations go through Alembic, don't hand-write SQL."
  - "UI uses Kendo React only, no Material UI."
]

## Relevant Skills & References

<!--
FIRST-BOOT: Based on stack answers, the boot agent appends pointers here to
skills/instructions that apply. Examples of what to append if the stack matches:

- C3 AI: link `.claude/*.md` instruction files; list relevant `c3-*` skills from
  the available skills roster (c3-type-generation, c3-calc-fields, c3-acls, etc.)
- React frontend: point to `frontend-c3.md` or equivalent, plus the
  `frontend-design:frontend-design` skill for creative UI work
- Python backend: `python-c3.md`, relevant c3 skills
- Anthropic SDK apps: `claude-api` skill
- Plugin development: `plugin-dev:*` skills
- General CLAUDE.md hygiene: `claude-md-management:claude-md-improver`

Only list what's actually relevant to this project's stack. Don't dump the whole
roster. One line per reference.
-->

[BOOT: Append relevant references here.]

## Open Questions / TODO

[BOOT: Ask if there's anything in-flight the agent should know about — half-done work, known bugs, pending decisions. Skip if greenfield.]
