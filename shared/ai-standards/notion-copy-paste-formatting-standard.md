# Notion Copy/Paste Formatting Standard

Use this standard for any AI output intended to be pasted into Notion pages, SOPs, dashboards, campaign pages, database page bodies, or documentation.

Minimum enforcement:
- Put all commands, code, snippets, prompts, formulas, queries, structured payloads, and multi-line templates in fenced code blocks so Notion renders them in copyable boxes.
- Use a language tag when known, for example `bash`, `powershell`, `json`, `yaml`, `sql`, `python`, `javascript`, or `text`.
- Keep each fenced block directly copy/paste ready. Do not put commentary, bullets, or explanation text inside the block.
- Use inline backticks only for short identifiers or literals embedded in prose, such as filenames, environment variable names, property names, and one-line tokens.
- If there are multiple separate copy targets, split them into separate fenced blocks instead of combining unrelated material.
- Preserve exact whitespace, quotes, and line breaks so the pasted content stays executable or structurally valid.
