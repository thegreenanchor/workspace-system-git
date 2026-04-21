<!-- BEGIN MANAGED: naming-standard -->
## Naming Standard

Follow `<workspace-root>\shared\ai-standards\local-naming-standard.md`.

Minimum enforcement:
- Use lowercase `kebab-case`
- Use `YYYY-MM-DD` for dated files
- Use business slugs only: `mna`, `tga`, `tgah`, `shl`, `personal`
<!-- END MANAGED: naming-standard -->

<!-- BEGIN MANAGED: social-campaign-output-standard -->
## Social Campaign Output Standard

Follow `<workspace-root>\shared\ai-standards\social-campaign-output-standard.md`.

Minimum enforcement:
- Use the exact section order `Campaign Overview`, `How to use this page`, `Quick Schedule`, `Firefly Notes`, `Buffer Notes`, `Week-by-Week Content`, `Quick Reference`
- For every weekly post, include `Theme`, `Alt hook A`, `Alt hook B`, and fenced blocks for `Buffer caption`, `Overlay title`, `Overlay subtitle`, and `Firefly prompt`
- Default cadence is Monday, Wednesday, Friday unless explicitly changed
<!-- END MANAGED: social-campaign-output-standard -->

<!-- BEGIN MANAGED: session-closeout-standard -->
## Session Closeout Standard

Follow `<workspace-root>\shared\ai-standards\session-closeout-standard.md`.

Minimum enforcement:
- Every AI interaction must be logged
- Tool-capable clients call the local submitter
- Weaker clients emit a human summary plus JSON fallback
- Full transcript is required
<!-- END MANAGED: session-closeout-standard -->

<!-- BEGIN MANAGED: cli-ownership-policy -->
## CLI Ownership Policy
- Use `Codex CLI` as the default implementation and integration hub.
- Use `Gemini CLI` for research, Google-stack work, and content-focused specialist roles when the local broker maps the task there.
- Use `Claude Code` for review, refactor, hardening, and presentation/deck specialist roles when the local broker maps the task there.
- If the current project contains `AI_ROUTING.yaml`, treat it as the local source of truth for role-to-provider routing.
- If no local `AI_ROUTING.yaml` exists, use `<workspace-root>\ai_rules\global_cli_policy.yaml` as the routing default.
- Treat provider separation as intentional system architecture, not a convenience preference.
- Do not suggest collapsing, consolidating, or bypassing provider roles for convenience unless the user explicitly asks to override the routing policy.
- When asked which CLI should handle a task, answer from the routing source of truth and state whether the route came from `AI_ROUTING.yaml` or `global_cli_policy.yaml`.
- If a task belongs to a non-local provider, enqueue it through `<workspace-root>\ai_rules\enqueue_cli_task.py` instead of manually opening another terminal.
- For a blocking handoff, use the broker with `--wait` so the delegated CLI runs headlessly and returns the result to the current workflow.
- Keep final repo-changing integration in `Codex CLI` unless the user explicitly overrides that policy.
<!-- END MANAGED: cli-ownership-policy -->

<!-- BEGIN MANAGED: notion-copy-paste-formatting -->
## Notion Copy/Paste Formatting Standard

Follow `<workspace-root>\shared\ai-standards\notion-copy-paste-formatting-standard.md`.

Minimum enforcement:
- For any output intended for Notion, put commands, code, snippets, prompts, formulas, structured payloads, and multi-line templates in fenced code blocks
- Use a language tag when known
- Keep each block directly copy/paste ready with no commentary inside the block
<!-- END MANAGED: notion-copy-paste-formatting -->
