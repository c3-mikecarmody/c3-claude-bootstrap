Perform a code review on the specified target. If no target is given, review all uncommitted changes (staged + unstaged).

## Scope

- If I give you a file or path: review that.
- If I give you a commit range or branch: review the diff.
- If nothing specified: run `git diff` and `git diff --cached` and review everything.

## What to Look For

1. **Bugs & logic errors** — things that are actually broken or will break.
2. **Edge cases** — unhandled nulls, empty arrays, off-by-ones, race conditions.
3. **Security** — exposed secrets, injection vectors, unsafe operations.
4. **Clarity** — confusing naming, misleading comments, code that's clever when it should be clear.
5. **Unnecessary complexity** — over-abstraction, premature generalization, dead code.

## What NOT to Do

- Don't nitpick formatting or style unless it hurts readability.
- Don't suggest refactors beyond the scope of the changes.
- Don't rewrite the code — just flag the issues.
- Don't pad with compliments. If it's clean, say "looks good" and move on.

## Output Format

For each issue:
- **File:line** — one-line summary of the issue
- Severity: `bug` | `warning` | `nit`
- Brief explanation if non-obvious

End with a one-line overall verdict.

$ARGUMENTS
