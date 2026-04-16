Write or update structured documentation for the specified topic or the project as a whole. Output goes to a `docs/` folder in the project root.

## Behavior

- If `docs/` doesn't exist, create it.
- **If a topic is specified and the doc already exists:** read the existing file first, then update it in place — extend, correct, or restructure as needed. Don't blindly overwrite.
- **If a topic is specified and no doc exists:** create a new file for that topic.
- **If no topic is specified:** generate or update `docs/README.md` as a documentation index covering the full project. Check what docs already exist and update the index to match.

## Document Structure

Each doc should be a standalone markdown file in `docs/` with:
- A clear title as H1
- Brief purpose statement (1-2 sentences)
- Substantive content organized with H2/H3 headings
- Code examples where they clarify usage
- Links to related docs within the folder where applicable

## Naming Convention

- Use kebab-case filenames: `docs/api-authentication.md`, `docs/deployment-guide.md`
- Always maintain a `docs/README.md` as the index/table of contents
- Update the index whenever you add or modify a doc

## Rules

- Write for a developer joining the project, not for me — I already know this stuff.
- Be specific and concrete. No filler paragraphs.
- Include real examples from the actual codebase, not hypothetical ones.
- If documenting an API or interface, include request/response shapes.
- Don't document obvious things. Focus on what's non-obvious, project-specific, or easy to get wrong.
- When updating an existing doc, preserve accurate content — only change what's wrong, outdated, or incomplete.

## Arguments

`$ARGUMENTS` is the topic to document. Example: `/document authentication flow`. If omitted, generate or update the full index.

$ARGUMENTS
