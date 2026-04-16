Systematically diagnose and fix a bug. Trace the full causal chain before proposing anything.

## Steps

1. **Reproduce.** Confirm you can reproduce the problem. If I've described it, restate the failure condition clearly. If you can run code, do so.
2. **Isolate.** Narrow the blast radius. What's the smallest scope where the bug exists? Rule out red herrings.
3. **Trace the causal chain.** Follow the execution path from input to failure. Read the relevant code — don't guess. Identify the *root cause*, not just the symptom.
4. **Propose the fix.** One fix targeting the root cause. Explain why this addresses the cause and not just the symptom. Flag any side effects or related fragility.
5. **Verify.** After applying the fix, confirm the failure condition no longer occurs. Check for regressions in adjacent behavior.

## Rules

- Don't propose a fix before completing the trace. A guess is not a diagnosis.
- If you find multiple issues, fix the root cause first. List the others separately.
- If the root cause is unclear after tracing, say so — don't fabricate confidence.
- Don't add defensive code to mask the bug. Fix it.

## Output Format

- **Failure condition:** one sentence
- **Root cause:** what's actually wrong and where
- **Fix:** what to change and why
- **Verification:** how you confirmed it works

## Arguments

`$ARGUMENTS` is the bug description or error. Example: `/debug token refresh fails after 1 hour`. If omitted, infer from recent context or ask.

$ARGUMENTS
