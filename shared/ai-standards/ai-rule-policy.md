# AI Rule Policy

## Scope
Use machine-level instruction files as global baselines and project-root instruction files as local enforcement points.

## Baselines
- `<user-home>\AGENTS.md`
- `<user-home>\CLAUDE.md`
- `<user-home>\GEMINI.md`
- `<user-home>\CHATGPT.md`

## Canonical standards
- `<workspace-root>\shared\ai-standards\local-naming-standard.md`
- `<workspace-root>\shared\ai-standards\notion-copy-paste-formatting-standard.md`
- `<workspace-root>\shared\ai-standards\social-campaign-output-standard.md`
- `<workspace-root>\shared\ai-standards\session-closeout-standard.md`
- `<workspace-root>\shared\ai-standards\blog-database-template-standard.md`
- `<workspace-root>\shared\ai-standards\writing-natural-punctuation-standard.md`

## Project-root enforcement
- Put instruction files at each real project root, not every child folder.
- Determine the governing rule set from the nearest registered or detected project root.
- Use managed rule blocks so global standards can be updated without overwriting local project context.
