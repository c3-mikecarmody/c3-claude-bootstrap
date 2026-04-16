---
description: Interview the user and scaffold CLAUDE.md — globally (~/.claude/CLAUDE.md) or per-project (./CLAUDE.md).
---

Drive a conversational onboarding interview and produce a populated CLAUDE.md from the bootstrap templates at `~/.claude/bootstrap/`. Two modes.

## Modes

- `--global` — target is `~/.claude/CLAUDE.md` (user-level identity and preferences). Use `CLAUDE.global.template.md`.
- `--project` (default if no flag) — target is `./CLAUDE.md` in the current working directory. Use `CLAUDE.project.template.md`.
- If the user invokes with no args and ambiguity exists, ask once: global or project.

## Step-by-step

1. **Detect state.** Check whether the target file exists.
   - If it exists and contains no `[BOOT:` placeholders, ask: augment, replace, or skip? Default to augment (keep existing content, only add/refresh the sections they want updated).
   - If it exists with `[BOOT:` placeholders, resume — only interview for the unfilled sections.
   - If it doesn't exist, copy the template contents as a working draft.

2. **Read the template.** Load `~/.claude/bootstrap/CLAUDE.<mode>.template.md`. Each `[BOOT: ...]` block describes what to ask and the format the answer should take.

3. **Interview.** Work through placeholders conversationally. Rules:
   - Group related questions into single messages. Don't ask one question at a time like a form.
   - Skip sections that clearly don't apply (e.g., email drafting if the user doesn't use Claude for email).
   - Infer from context where safe — e.g., if in a git repo, you can `ls` and `git log` to guess stack rather than asking "what language". Confirm, don't interrogate.
   - Match the user's tone. If they're terse, be terse. If they elaborate, match depth.

4. **Fill templates.** Replace each `[BOOT: ...]` block with the user's answer, formatted to match the surrounding bullets/prose. Remove the top `<!-- FIRST-BOOT: ... -->` meta-comment when done.

5. **Conditional skill/reference injection (project mode only).** For the "Relevant Skills & References" section, look at the stack answers and append pointers to skills that actually apply. Draw from the skills list surfaced in the current session. Examples:
   - C3 AI stack → list `c3-type-generation`, `c3-calc-fields`, `c3-acls`, etc. as relevant; link to `.claude/*.md` instruction files if present.
   - React frontend → `frontend-design:frontend-design`, relevant frontend `.md` instructions.
   - Anthropic SDK app → `claude-api` skill.
   - Plugin development → `plugin-dev:*` skills.
   Only list what's actually relevant. Don't dump the whole roster.

6. **Write the file.** Write the filled template to the target path. If augmenting an existing file, merge carefully — preserve anything the user wrote that wasn't a placeholder.

7. **Report back.** One line: what was written, where, and what got skipped. Offer a follow-up: "Run `/catchup` to have me read it all and confirm I've got it" (project mode) or "Anything else I should know about you before we go?" (global mode).

## Special cases

- **Global mode when `~/.claude/CLAUDE.md` already has rich content** (like Mike's existing file): default to augment — don't wipe his "Who I Am" or "Communication" sections. Ask which sections he wants to refresh.
- **Project mode in a non-git dir**: still works, just skip any git-derived inference.
- **Project mode in a dir with a parent CLAUDE.md** (e.g., a subfolder of a project): ask whether to create a new CLAUDE.md here or edit the parent.

## Rules for the interview

- Be fast. Aim for 5 minutes global, 5 minutes project. Fewer questions > more.
- Don't ask about things you can see in the filesystem. Read first, confirm second.
- Write in the user's voice, first-person. Don't make it sound like an AI wrote it.
- If the user says "just make something up reasonable," do it — then show them and ask for corrections.

## Arguments

`$ARGUMENTS` — `--global`, `--project`, or empty.

$ARGUMENTS
