Get oriented on this project quickly. I'm either starting a new session or picking up where I left off.

## Steps

1. **Read CLAUDE.md** (project-level if it exists) for project context and conventions.
2. **Read README.md** if present — it often has setup, architecture, or intent not in CLAUDE.md.
3. **Scan the file tree** — understand the top-level structure. Don't go deep yet.
4. **Check for task tracking** — look for `tasks.md`, `TODO`, open issues, or any in-repo tracking files.
5. **Check git status** — what branch am I on? Any uncommitted work? Recent commits?
6. **Read recent git log** — last 10 commits, one-line format. Note what's been changing.
7. **Identify the current state** — is there work in progress? What seems active?

## Output

Give me a brief situational report:
- **Project:** what this is, in one sentence
- **Stack:** languages, frameworks, key dependencies
- **Branch:** current branch and its status
- **Recent activity:** 2-3 sentence summary of recent commits
- **In-flight work:** any uncommitted changes or WIP
- **Open tasks:** anything flagged in task-tracking files, if present
- **Key files:** the 3-5 most important files I'd want to look at first

Keep it tight. I'll ask follow-up questions if I need more depth.

## Arguments

`$ARGUMENTS` is an optional focus area or specific question. Example: `/catchup focus on the auth flow` narrows the report. If omitted, give the full overview.

$ARGUMENTS
