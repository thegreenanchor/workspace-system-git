# MNA Healthcare Marketing Team Workspace

## Project Overview

This workspace supports an AI marketing team for MNA Healthcare, a healthcare staffing agency. The team creates and manages marketing content targeting both healthcare professionals and facility decision-makers.

## Services Offered

- Blog content creation
- SEO optimization
- Social media management
- Email campaigns
- Market research and analytics

## Target Audiences

### Primary: Travel Healthcare Professionals
- Registered Nurses (RN)
- Licensed Practical Nurses / Licensed Vocational Nurses (LPN/LVN)
- Certified Nursing Assistants (CNA)
- Allied Health Professionals

### Secondary: Healthcare Facility Decision Makers
- Staffing coordinators
- Nursing directors
- HR managers at facilities using travel nurses

## Brand Voice Guidelines

- **Professional**: Maintain credibility and expertise
- **Approachable**: Friendly and welcoming tone
- **Jargon-free**: Clear, accessible language for all audiences

## Workspace Structure

```
marketing_team/
â”œâ”€â”€ clients/           # Client-specific folders and projects
â”œâ”€â”€ content/           # Blog posts, articles, and content assets
â”œâ”€â”€ strategies/        # Content strategies and marketing plans
â”œâ”€â”€ research/          # Market research and data analysis
â”œâ”€â”€ social-media/      # Social media content and calendars
â”œâ”€â”€ email-campaigns/   # Email marketing materials
â”œâ”€â”€ reports/           # Performance reports and analytics
â”œâ”€â”€ templates/         # Reusable templates for deliverables
â””â”€â”€ assets/            # Brand assets, images, and media
../../../../shared/scoring-models/     # Shared quality and risk scoring models
```

## Agent Routing Rules

This workspace has four specialized agents. Delegate tasks based on the rules below. If a request spans multiple agents, coordinate by delegating each part to the appropriate agent.

### content-strategist
**Delegate when the user asks to:**
- Research market trends, competitors, or audience behavior
- Develop a content strategy, messaging framework, or topic clusters
- Create content briefs for blog posts, articles, or campaigns
- Plan a content calendar with strategic direction (themes, pillars, timing)
- Identify content gaps or SEO/keyword opportunities
- Align content plans with brand voice or business objectives

**Do NOT delegate here for:** Writing social posts, building slide decks, pulling analytics data, or creating visuals.

### social-media-specialist
**Delegate when the user asks to:**
- Write social media posts or captions for LinkedIn, Instagram, Facebook, or short-form video
- Build a social media content calendar
- Create hashtag sets or campaign themes for social channels
- Repurpose a blog, report, or internal update into social media content
- Generate a visual for a social post (see `branded-social-visual.md` for the public-repo placeholder)
- Plan or organize social media content around an event, holiday, or campaign

**Do NOT delegate here for:** Long-form content strategy, analytics/dashboards, or slide decks.

### data-analyst
**Delegate when the user asks to:**
- Pull or analyze website traffic, engagement, or conversion data from GA4
- Investigate a performance drop, spike, or anomaly
- Create an interactive HTML dashboard or data visualization
- Compare channel performance (organic vs. paid, social vs. direct, etc.)
- Generate a performance report with metrics and recommendations
- Provide data to support or validate content or campaign decisions

**Do NOT delegate here for:** Writing content, creating presentations, or social media posts.

### presentation-specialist
**Delegate when the user asks to:**
- Turn a report, document, or data set into a PowerPoint slide deck
- Create a client-facing or leadership presentation
- Build a slide deck summarizing a strategy, campaign, or performance review
- Transform research findings or analytics into visual storytelling slides

**Do NOT delegate here for:** Writing social posts, pulling raw analytics, content strategy, or creating social media graphics.

### Multi-Agent Coordination
Some requests require multiple agents working together:
- **Campaign launch**: content-strategist (strategy/briefs) + social-media-specialist (social posts/visuals) + data-analyst (baseline metrics)
- **Performance review**: data-analyst (pull data/dashboard) + presentation-specialist (slide deck) + social-media-specialist (social summary posts)
- **Blog-to-social repurposing**: content-strategist (brief/messaging) + social-media-specialist (platform posts/visuals)
- **Quarterly planning**: content-strategist (strategy/calendar) + social-media-specialist (social calendar) + data-analyst (prior period data)

When coordinating, ensure consistent messaging, data points, and brand voice across all agent outputs.

## Working Guidelines

- All content should address client pain points
- Maintain consistent brand voice across all channels
- Reference templates in `templates/` for standardized deliverables
- Score blog, social campaign, research, and general writing outputs using the mapped scoring models in `templates/Scoring Model Map.md`; save completed scorecards in `reports/content-quality-scores/`
- Append this qualifier to all task requests by default:
  "Now, think deeply about this task and use an internal quality rubric: What does world-class output look like for this taskx Then critique your output against that standard and provide an improved version that meets that higher bar."
- Store performance data and analytics in `reports/`
- Keep brand assets organized in `assets/`

## Social Campaign Output Standard

For any social media campaign deliverable, follow `<workspace-root>\shared\ai-standards\social-campaign-output-standard.md`.

Minimum enforcement:
- Use the exact section order `Campaign Overview`, `How to use this page`, `Quick Schedule`, `Firefly Notes`, `Buffer Notes`, `Week-by-Week Content`, `Quick Reference`
- For every weekly post, include `Theme`, `Alt hook A`, `Alt hook B`, and real fenced code blocks for `Buffer caption`, `Overlay title`, `Overlay subtitle`, and `Firefly prompt`
- Default cadence is exactly 3 posts per week on Monday, Wednesday, and Friday unless the user explicitly changes it
- Keep copy grounded, specific, and paste-ready for Buffer and Firefly
- Do not invent facts, stats, testimonials, pay claims, or guarantees
- Do not include logos, patient faces, or readable private information in image prompts

## Naming Standard

For local folders, repos, and deliverables in this workspace, follow `<workspace-root>\shared\ai-standards\local-naming-standard.md`.

Minimum enforcement:
- Use lowercase `kebab-case`
- Use `YYYY-MM-DD` for dated files
- Use business slugs only: `mna`, `tga`, `tgah`, `shl`, `personal`

## Session Closeout Standard

For every AI interaction, follow `<workspace-root>\shared\ai-standards\session-closeout-standard.md`.

Minimum enforcement:
- Log every AI interaction
- Tool-capable clients must submit through the local tooling in `<workspace-root>\ai_rules\`
- Weaker clients must output a human-readable closeout plus JSON fallback
- Do not end a session without either successful submission or JSON fallback output

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
