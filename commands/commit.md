Stage and commit the current work with a well-formed commit message.

## Steps

1. **Check what's changed.** Run `git status` and `git diff` (staged + unstaged). Get the full picture before touching anything.
2. **Identify what belongs together.** If there are unrelated changes, flag them — don't bundle unrelated work into one commit.
3. **Stage the right files.** Add specific files by name. Never use `git add -A` or `git add .` blindly — check for anything that shouldn't be committed (env files, build artifacts, secrets).
4. **Draft the commit message.** Follow the format below. Wait for my approval before committing.
5. **Commit.** Once approved, commit and confirm success.

## Commit Message Format

```
<type>: <short imperative summary> (~50 chars)

<why this change was needed — not what the diff already shows>
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`

- Lead with *why*, not *what*. The diff shows what changed; the message explains the reason.
- If the why is obvious from the summary line, skip the body.
- Keep the subject line under 72 characters.
- No period at the end of the subject line.

## Rules

- Never commit `.env`, credentials, or secrets. Warn me if I ask.
- Never amend a published commit. Create a new one.
- Never skip hooks (`--no-verify`) unless I explicitly ask.
- If a pre-commit hook fails, fix the issue — don't bypass it.

## Arguments

`$ARGUMENTS` is an optional message hint or scope. Example: `/commit fix the token refresh bug`. If omitted, infer from the diff.

$ARGUMENTS
