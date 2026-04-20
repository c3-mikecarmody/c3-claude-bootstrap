# `/first-boot` — conversational onboarding

How the interview works, what the `[BOOT:]` placeholders mean, and when to use `--global` vs. the default project mode.

## Two modes

### `/first-boot --global`

- **Target:** `~/.claude/CLAUDE.md`
- **Purpose:** identity, communication preferences, environment
- **Runs:** once per user (can re-run to augment)
- **Template:** `bootstrap/CLAUDE.global.template.md`

Interview covers:
- Who you are (role, background, primary domains) — free-form paragraph
- Environment (OS, shell, editor, primary languages)
- Optional: email-drafting preferences (skipped if you don't use Claude for email)

### `/first-boot` (project mode, default)

- **Target:** `./CLAUDE.md` in the current working directory
- **Purpose:** codebase context — stack, key files, externals, domain jargon
- **Runs:** once per project (re-run to augment)
- **Template:** `bootstrap/CLAUDE.project.template.md`

Interview covers:
- What the project is (purpose, state, audience)
- Stack & tooling (languages, frameworks, package manager, test runner, build/deploy)
- Key files & entry points (3–6 critical ones)
- External systems & integrations (APIs, DBs, third-party services)
- Domain jargon (acronyms, terms the agent won't otherwise know)
- How to run / test / ship (the actual commands, not aspirational ones)
- Project-specific rules
- Conditional skills/references injection (see below)
- Open questions / TODOs

## `[BOOT:]` placeholder convention

Templates contain blocks like:

```markdown
## Who I Am

[BOOT: Ask 2–3 questions — role/title, background, primary domains they work in.
Write 2–3 short paragraphs, first-person, no filler. Voice should read like
a peer introducing themselves to a collaborator, not a résumé.]
```

The command driver reads the template, walks these blocks in order, asks the user the relevant questions conversationally (grouping related ones), and replaces the block with the filled-in answer. The top-of-file `<!-- FIRST-BOOT: ... -->` meta-comment is stripped once the file is complete.

**Important:** the placeholder *contains* the prompt instructions for the agent. Editing a template means editing the question the interview agent asks.

## Conversational vs. form

The `/first-boot` command does *not* ask questions one at a time like a form. The command spec instructs the agent to:

- Group related questions into single messages
- Infer from the filesystem first (git log, file tree, package.json) — only ask when inference fails
- Skip sections that clearly don't apply
- Match the user's tone (terse → terse, verbose → verbose)

So a real session looks less like "Q1: role? Q2: background? Q3: domains?" and more like: *"Based on the files I see this looks like a React + C3 AI package. A few quick questions to confirm: what's the app for (one sentence), what's the deploy target, and is there anything under `legacy/` I should leave alone?"*

## Conditional skill/reference injection (project mode)

The `## Relevant Skills & References` section of the project template is special. After filling the rest of the template, the agent:

1. Looks at the stack answers (languages, frameworks)
2. Consults the skills roster loaded in the current Claude Code session
3. Appends pointers to **only the skills that actually apply**

Examples:

- Stack mentions C3 AI → append `c3-type-generation`, `c3-calc-fields`, `c3-acls`, etc. Link to any `.claude/*.md` instruction files in the repo.
- React frontend → append `frontend-design:frontend-design` and any frontend `.md` instruction files.
- Uses the Anthropic SDK → `claude-api` skill.
- Plugin development → `plugin-dev:*` skills.

Don't dump the whole skills list — the references section should be short and relevant. The goal is "when the agent is working on this repo, these skills are worth checking."

## Seed-then-prompt (auto-trigger on first install)

On fresh install, `install.sh` copies the global template verbatim to `~/.claude/CLAUDE.md`. The template starts with this HTML comment:

```markdown
<!--
FIRST-BOOT: The sections below in [brackets] are placeholders. The boot agent
interviews the user and replaces them. Once filled, delete the brackets and this
comment. If you see any [bracketed placeholder] at boot time, it means the user
hasn't completed first-boot — offer to run `/first-boot --global`.
-->
```

Every Claude Code session loads `~/.claude/CLAUDE.md` as context. When that file contains placeholders, the agent sees them and offers the interview — no "go read the README" step needed.

Once `/first-boot --global` completes, the placeholders are gone and the prompt stops firing. If the user had a pre-existing global `CLAUDE.md`, the installer leaves it alone — no seed, no prompt.

## Augment vs. replace (existing CLAUDE.md)

If `CLAUDE.md` already exists with no placeholders, the command asks:

- **Augment** (default) — keep existing content, only refresh the sections you want updated. Good for "my team got new conventions, update the project-specific rules section."
- **Replace** — full re-interview, wipe existing content.
- **Skip** — no-op.

If `CLAUDE.md` exists *with* `[BOOT:]` placeholders (partial onboarding), the command resumes — only interviews for the unfilled sections.

## Handoff / wrap-up

Project mode closes with:

- One-line summary: which sections were filled, which skipped, which skills got linked
- Offer: `/catchup` to read everything end-to-end, or just give the agent a task
- If uncommitted changes, open TODOs, or a stale README are visible, mention *one* as a concrete starting point rather than asking "what do you want to do?"

Global mode closes with:

- One-line summary
- Note that memory is now primed — this identity will persist across sessions (via swat-memory if installed)
- Ask: "anything else I should know about how you work?"

## Relation to `c3-e/c3toolsprompts`

Our `/first-boot` is different from Mahesh's `/onboard` (in [c3toolsprompts PR #61](https://github.com/c3-e/c3toolsprompts/pull/61)):

- `/onboard` — project config wizard (tokens, cluster URL, package name, team/initials). Structured form.
- `/first-boot` — identity and codebase context interview. Conversational.

They're complementary — different questions, different UX, different placeholder namespaces in the CLAUDE.md. See [upstream-contribution.md](upstream-contribution.md).

## Related

- [architecture.md](architecture.md) — where the template files live and how the seed pattern works
- [memory.md](memory.md) — how answers from `/first-boot` end up in persistent memory
