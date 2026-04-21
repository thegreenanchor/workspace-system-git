# MNA Healthcare Marketing Team (Codex Project Config)

This file is the Codex project instruction source for this workspace.

## Purpose
Support an AI marketing team for MNA Healthcare (healthcare staffing) creating:
- Blog content
- SEO content
- Social media campaigns
- Email campaigns
- Research briefs
- Performance reporting inputs

## Brand voice
- Professional
- Approachable
- Jargon-free

## Workspace structure
- `content/`: blogs, decks, content assets
- `research/`: market and topic research
- `strategies/`: briefs, content strategy artifacts
- `social-media/`: social plans and post assets
- `email-campaigns/`: email materials
- `reports/`: scorecards and performance outputs
- `templates/`: reusable templates and SOPs
- `../../../../shared/scoring-models/`: shared rubric models

## Agent routing
Use these routing rules for task ownership:

### content-strategist
Use for:
- Market and audience research
- Content strategy and topic clusters
- Campaign/brief planning
- SEO opportunity and gap analysis

Do not use for:
- Writing social posts
- Building decks
- Pulling analytics dashboards

### social-media-specialist
Use for:
- Social posts/captions
- Social campaign calendars
- Hashtag and campaign theme work
- Repurposing blog/research into platform posts

Do not use for:
- Long-form strategy
- Analytics investigations
- Slide deck builds

### data-analyst
Use for:
- Traffic, conversion, engagement analysis
- Channel comparisons
- Performance investigations
- Dashboard/report generation

Do not use for:
- Writing blog/social copy
- Presentation authoring

### presentation-specialist
Use for:
- Turning docs/data into decks
- Client/leadership presentations
- Strategy/research summary slides

Do not use for:
- Social post writing
- Raw analytics pulling
- Content strategy drafting

## Cross-agent coordination
- Campaign launch: content-strategist + social-media-specialist + data-analyst
- Performance review: data-analyst + presentation-specialist + social-media-specialist
- Blog-to-social repurpose: content-strategist + social-media-specialist
- Quarterly planning: content-strategist + social-media-specialist + data-analyst

## Quality and scoring workflow
Always score deliverables using `templates/Scoring Model Map.md`.
Store completed scorecards in `reports/content-quality-scores/`.

### Current rubric mapping
- Blog posts -> `../../../../shared/scoring-models/dual-visibility-blog-rubric-seo-llm.md`
- Social media campaigns -> `../../../../shared/scoring-models/social-media-campaign-evaluation-rubric.md`
- Research deliverables -> `../../../../shared/scoring-models/ai-signal-scoring-rubric-pro-brand-builder.md`
- General writing -> `../../../../shared/scoring-models/ai-signal-scoring-rubric-marketing-content-review.md`
- Conversion risk assessments -> `../../../../shared/scoring-models/conversion-risk-scoring-model.md`

## Mandatory request qualifier
Append this qualifier to all task requests by default:

"Now, think deeply about this task and use an internal quality rubric: What does world-class output look like for this task? Then critique your output against that standard and provide an improved version that meets that higher bar."

## Delivery standards
- Address client pain points directly
- Keep messaging consistent across channels
- Use templates in `templates/`
- Save scoring artifacts in `reports/content-quality-scores/`
- Keep outputs client-ready and reusable

## Social Campaign Output Standard
- For any social media campaign deliverable, follow `<workspace-root>\shared\ai-standards\social-campaign-output-standard.md`
- Output campaign work as a Notion campaign page with the exact section order `Campaign Overview`, `How to use this page`, `Quick Schedule`, `Firefly Notes`, `Buffer Notes`, `Week-by-Week Content`, `Quick Reference`
- For every weekly post, include `Theme`, `Alt hook A`, `Alt hook B`, and real fenced code blocks for `Buffer caption`, `Overlay title`, `Overlay subtitle`, and `Firefly prompt`
- Default cadence is exactly 3 posts per week on Monday, Wednesday, and Friday unless the user explicitly changes it
- Do not invent facts, stats, testimonials, pay claims, or guarantees
- Do not include logos, patient faces, or readable private information in Firefly prompts

## Naming Standard
- Follow `<workspace-root>\shared\ai-standards\local-naming-standard.md`
- Use lowercase `kebab-case` for local folders, repos, and deliverables
- Use `YYYY-MM-DD` for dated files
- Use business slugs only: `mna`, `tga`, `tgah`, `shl`, `personal`

## Session Closeout Standard
- Follow `<workspace-root>\shared\ai-standards\session-closeout-standard.md`
- Log every AI interaction
- Tool-capable clients must submit through the local tooling in `<workspace-root>\ai_rules\`
- Weaker clients must output a human-readable closeout plus JSON fallback
- Do not end a session without either successful submission or JSON fallback output

## Prompt quality standard (Nano Banana)
- For any image-generation prompt deliverable, verify prompt structure and parameters against the latest available Nano Banana documentation before finalizing output.
- If documentation access is unavailable in-session, explicitly state assumptions and provide the prompt in a format that is easy to revalidate once docs are accessible.
- Optimize prompts for deterministic, production-quality outputs (clear subject, composition, style, lighting, aspect ratio, exclusions, and rendering intent).

## Notes
- `CLAUDE.md` can remain as legacy context, but Codex behavior should follow this `AGENTS.md`.

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
