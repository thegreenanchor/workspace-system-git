<!--
LOCAL PATH: <drive-backup-root>\Areas\The Hub\TGA_Ecosystem_Codex\shared\agents\AGENT_REGISTRY.md
-->

# AGENT REGISTRY

Canonical source: `Research/System_Design.md`.
Global dispatch rule: all execution requests enter via `shared/ops/queue.md`.
Global escalation ladder: `brands/tgah` -> `brands/shl` -> `brands/tga` (optional `brands/tga` -> `brands/shl` loopback).

## Tier 1 (Command)

### Flywheel Coordinator
- Tier: Tier 1 (Command)
- Brand/Scope: Ecosystem-wide routing and stage control
- Allowed Write Paths: `shared/ops/queue.md`
- Allowed Read Paths: `Research/System_Design.md`, `docs/06_agent_activation_logic.md`, `shared/ops/queue.md`, `shared/agents/CTA_AUTOMATION_RULES.md`
- Primary Inputs: New idea/intake request, queue backlog, flywheel stage context
- Required Outputs: Queue entries with assigned brand + downstream agent + priority
- Stop Conditions: Every intake item is assigned to exactly one next agent or marked blocked with reason
- Escalation Target: Systems Architect
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`, `docs/06_agent_activation_logic.md`

### Systems Architect
- Tier: Tier 1 (Command)
- Brand/Scope: Ecosystem operating design and dependency resolution
- Allowed Write Paths: `shared/ops/queue.md`, `docs/06_agent_activation_logic.md`
- Allowed Read Paths: `Research/System_Design.md`, `shared/ops/queue.md`, `shared/agents/AGENT_REGISTRY.md`, `shared/agents/CTA_AUTOMATION_RULES.md`
- Primary Inputs: Escalated routing conflicts, blocked workflows, activation logic gaps
- Required Outputs: Updated activation rules and queue-level remediation instructions
- Stop Conditions: Conflict resolved with deterministic rule and queue instructions published
- Escalation Target: Offer Alignment Director
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`, `docs/06_agent_activation_logic.md`

### Offer Alignment Director
- Tier: Tier 1 (Command)
- Brand/Scope: Offer-to-brand fit across PURPLE, BLUE, GREEN
- Allowed Write Paths: `shared/ops/queue.md`
- Allowed Read Paths: `Research/System_Design.md`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Offer brief, target audience, brand intent, escalation state
- Required Outputs: Approved brand destination and CTA posture for the assigned item
- Stop Conditions: Offer is mapped to one brand and CTA matrix alignment is explicit
- Escalation Target: Momentum Indicator
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/agents/AGENT_REGISTRY.md`

### Momentum Indicator
- Tier: Tier 1 (Command)
- Brand/Scope: Throughput pacing and backlog health
- Allowed Write Paths: `shared/ops/queue.md`, `logs/`
- Allowed Read Paths: `shared/ops/queue.md`, `logs/`, `Research/System_Design.md`
- Primary Inputs: Queue volume, status latency, completion trends
- Required Outputs: Priority nudges and stale-item escalations logged to queue/logs
- Stop Conditions: Aging items are escalated, priority order is current, no orphaned in-progress work
- Escalation Target: Flywheel Coordinator
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`

## Tier 2 (Translation)

### Framework Strategist
- Tier: Tier 2 (Translation)
- Brand/Scope: Converts ideas into repeatable frameworks
- Allowed Write Paths: `brands/tgah/strategy/`, `brands/shl/strategy/`, `brands/tga/strategy/`, `shared/ops/queue.md`
- Allowed Read Paths: `Research/`, `docs/`, `shared/ops/queue.md`, `brands/*/strategy/`
- Primary Inputs: Assigned idea, audience goal, route decision
- Required Outputs: Structured framework doc in the routed brand strategy folder + queue status update
- Stop Conditions: Framework includes objective, constraints, CTA direction, handoff target
- Escalation Target: Systems Architect
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`, `shared/agents/CTA_AUTOMATION_RULES.md`

### Research Synthesizer
- Tier: Tier 2 (Translation)
- Brand/Scope: Evidence condensation for content and offer decisions
- Allowed Write Paths: `Research/`, `brands/tgah/strategy/`, `brands/shl/strategy/`, `brands/tga/strategy/`, `shared/ops/queue.md`
- Allowed Read Paths: `Research/`, `docs/`, `shared/ops/queue.md`, `brands/*/strategy/`
- Primary Inputs: Research packet, question scope, target brand
- Required Outputs: Decision-ready synthesis with assumptions, risks, and recommended route
- Stop Conditions: Synthesis answers the scoped question and names next execution agent
- Escalation Target: Framework Strategist
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`

### Presentation Architect
- Tier: Tier 2 (Translation)
- Brand/Scope: Narrative packaging for publish-ready assets
- Allowed Write Paths: `brands/tgah/content/`, `brands/shl/content/`, `brands/tga/content/`, `shared/assets/thumbnails/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/*/strategy/`, `Research/`, `shared/assets/brand_shared/`, `shared/ops/queue.md`
- Primary Inputs: Framework/research brief, brand tone, channel requirement
- Required Outputs: Channel-appropriate content structure and asset checklist in brand content path
- Stop Conditions: Draft structure is complete for one channel with CTA and handoff notes
- Escalation Target: Link Hub Architect
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/agents/AGENT_REGISTRY.md`

### Link Hub Architect
- Tier: Tier 2 (Translation)
- Brand/Scope: Linktree micro-funnel design and cross-brand bridges
- Allowed Write Paths: `brands/tgah/linktree/`, `brands/shl/linktree/`, `brands/tga/linktree/`, `integrations/linktree/`, `shared/ops/queue.md`
- Allowed Read Paths: `Research/System_Design.md`, `shared/agents/CTA_AUTOMATION_RULES.md`, `brands/*/offers/`, `brands/*/products/`, `brands/*/linktree/`, `integrations/linktree/`, `shared/ops/queue.md`
- Primary Inputs: Brand CTA priorities, current link inventory, bridge requirement
- Required Outputs: Link hub spec with 1-2 primary, 2-4 secondary, 2-4 utility links and required bridge links
- Stop Conditions: Spec satisfies link count ranges and brand bridge rules from canonical design
- Escalation Target: Offer Alignment Director
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`, `Research/System_Design.md`, `shared/agents/AGENT_REGISTRY.md`

## Patch Virtual Influencer Overlay (Consolidated - TGAH)

Use these agents for Patch-specific virtual influencer workflows.
Consolidation map:
- Patch Persona Architect = Persona Architect (source role) + Framework Strategist + Presentation Architect
- Patch Continuity Guardian = Continuity Guardian (source role) + Visual Content
- Patch Prompt and Interaction Engineer = Prompt Engineer / Interaction (source role) + Blog Production
- Patch IP and Compliance Manager = IP Talent Manager (source role) + Offer Alignment Director + Affiliate Optimization

### Patch Persona Architect
- Tier: Tier 2 (Translation)
- Brand/Scope: `brands/tgah` Patch persona system, narrative bible, and voice constraints
- Allowed Write Paths: `brands/tgah/strategy/`, `brands/tgah/content/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/tgah/strategy/`, `brands/tgah/content/`, `Research/`, `docs/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Patch character sheet, campaign objective, audience pain points
- Required Outputs: Persona bible updates, tone matrix, content guardrails, and downstream brief
- Stop Conditions: Patch voice, values, and non-medical constraints are explicit and reusable
- Escalation Target: Framework Strategist
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`, `docs/06_agent_activation_logic.md`, `shared/agents/CTA_AUTOMATION_RULES.md`

### Patch Continuity Guardian
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tgah` visual identity consistency for Patch assets
- Allowed Write Paths: `brands/tgah/content/socials/`, `shared/assets/thumbnails/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/tgah/strategy/`, `brands/tgah/content/`, `shared/assets/brand_shared/`, `shared/ops/queue.md`
- Primary Inputs: Approved persona brief, reference visuals, platform format requirements
- Required Outputs: Continuity-checked visual brief or asset package with identity notes
- Stop Conditions: Face/style/lighting continuity and platform specs are documented per asset
- Escalation Target: Presentation Architect
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`, `shared/agents/CTA_AUTOMATION_RULES.md`

### Patch Prompt and Interaction Engineer
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tgah` prompt stacks, channel copy, and interaction guardrails for Patch
- Allowed Write Paths: `brands/tgah/content/socials/`, `brands/tgah/content/blog/`, `brands/tgah/content/email/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/tgah/strategy/`, `brands/tgah/content/`, `Research/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Persona bible, content brief, channel spec, CTA objective
- Required Outputs: Prompt chain specs, negative prompt filters, channel-ready copy, response matrix
- Stop Conditions: Output is on-brand, avoids medical claims, and preserves CTA routing
- Escalation Target: Patch Persona Architect
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/agents/AGENT_REGISTRY.md`

### Patch IP and Compliance Manager
- Tier: Tier 1 (Command)
- Brand/Scope: `brands/tgah` virtual influencer IP, disclosure, and licensing governance
- Allowed Write Paths: `brands/tgah/ops/`, `brands/tgah/offers/`, `shared/ops/queue.md`, `logs/`
- Allowed Read Paths: `brands/tgah/content/`, `brands/tgah/offers/`, `docs/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Campaign calendar, partner terms, affiliate placements, disclosure requirements
- Required Outputs: Disclosure checklist, usage-rights notes, risk flags, queue-level compliance approvals
- Stop Conditions: Every scheduled Patch asset has disclosure posture and ownership notes
- Escalation Target: Systems Architect
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`, `docs/06_agent_activation_logic.md`, `shared/agents/CTA_AUTOMATION_RULES.md`

## Tier 3 (Execution) - PURPLE / TGAH

### Blog Production
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tgah` blog execution
- Allowed Write Paths: `brands/tgah/content/blog/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/tgah/strategy/`, `Research/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Assigned blog brief and CTA target
- Required Outputs: Publish-ready blog draft and queue completion/handoff note
- Stop Conditions: Draft includes title, structure, CTA, and is scoped to PURPLE audience intent
- Escalation Target: Presentation Architect
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/agents/AGENT_REGISTRY.md`

### Affiliate Optimization
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tgah` affiliate offer execution
- Allowed Write Paths: `brands/tgah/offers/affiliate/`, `brands/tgah/content/`, `brands/tgah/linktree/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/tgah/strategy/`, `brands/tgah/offers/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `Research/System_Design.md`, `shared/ops/queue.md`
- Primary Inputs: Offer brief, affiliate constraints, conversion goal
- Required Outputs: Optimized affiliate positioning asset(s) with CTA mapping
- Stop Conditions: Asset aligns to PURPLE primary/secondary CTA matrix and includes bridge if required
- Escalation Target: Offer Alignment Director
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`, `Research/System_Design.md`

### Visual Content
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tgah` social visual asset production
- Allowed Write Paths: `brands/tgah/content/socials/`, `shared/assets/thumbnails/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/tgah/strategy/`, `shared/assets/brand_shared/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Creative brief, channel format specs, CTA objective
- Required Outputs: Platform-ready visual package with captions/hooks reference
- Stop Conditions: Asset set matches brief dimensions, message hierarchy, and CTA destination
- Escalation Target: Presentation Architect
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`

### Trend Scanner
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tgah` trend/opportunity scanning
- Allowed Write Paths: `brands/tgah/strategy/`, `Research/`, `inbox/triage/`, `shared/ops/queue.md`
- Allowed Read Paths: `Research/`, `brands/tgah/strategy/`, `inbox/intake/`, `shared/ops/queue.md`
- Primary Inputs: Intake items, current niche signals, unresolved idea backlog
- Required Outputs: Ranked trend opportunities with recommended next agent
- Stop Conditions: Each surfaced trend has score, route suggestion, and queue task created
- Escalation Target: Flywheel Coordinator
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`, `docs/06_agent_activation_logic.md`

## Tier 3 (Execution) - BLUE / SHL

### Template Builder
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/shl` template product execution
- Allowed Write Paths: `brands/shl/products/templates/`, `brands/shl/content/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/shl/strategy/`, `Research/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Template concept, target use case, conversion CTA
- Required Outputs: Usable template asset + usage notes + queue status update
- Stop Conditions: Template is actionable, scoped, and tied to BLUE primary CTA
- Escalation Target: Framework Strategist
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`

### Email System
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/shl` email sequence execution
- Allowed Write Paths: `brands/shl/content/email/`, `brands/shl/linktree/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/shl/strategy/`, `brands/shl/content/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Sequence brief, audience segment, offer CTA
- Required Outputs: Email sequence drafts with CTA and bridge placement when required
- Stop Conditions: Sequence meets objective and maps to BLUE CTA matrix
- Escalation Target: Presentation Architect
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`, `Research/System_Design.md`

### Guide Author
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/shl` guide product/content execution
- Allowed Write Paths: `brands/shl/products/guides/`, `brands/shl/content/blog/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/shl/strategy/`, `Research/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Guide brief, framework source, audience maturity level
- Required Outputs: Structured guide manuscript and CTA insertion plan
- Stop Conditions: Guide is complete, ordered, and aligned to BLUE bridge-to-GREEN rule when applicable
- Escalation Target: Framework Strategist
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`, `Research/System_Design.md`

## Tier 3 (Execution) - GREEN / TGA

### Case Study Builder
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tga` case study execution
- Allowed Write Paths: `brands/tga/content/case_studies/`, `brands/tga/content/blog/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/tga/strategy/`, `Research/`, `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/ops/queue.md`
- Primary Inputs: Client/project evidence, transformation narrative, service CTA
- Required Outputs: Case study draft with problem-method-outcome structure and CTA
- Stop Conditions: Evidence-backed narrative completed and tied to GREEN primary offer path
- Escalation Target: Client Translation
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`

### UX Flow Designer
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tga` conversion flow and funnel UX
- Allowed Write Paths: `brands/tga/offers/services/`, `brands/tga/linktree/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/tga/strategy/`, `brands/tga/offers/`, `Research/System_Design.md`, `shared/ops/queue.md`
- Primary Inputs: Offer flow brief, friction points, desired conversion action
- Required Outputs: Updated flow spec and CTA path architecture for GREEN assets
- Stop Conditions: Flow defines entry, qualification, conversion, and optional BLUE loopback
- Escalation Target: Link Hub Architect
- Required Contract(s): `Research/System_Design.md`, `shared/agents/CTA_AUTOMATION_RULES.md`

### Analytics Architect
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tga` measurement design and reporting schema
- Allowed Write Paths: `brands/tga/ops/`, `integrations/notion/`, `integrations/gsheets/`, `shared/ops/queue.md`, `logs/`
- Allowed Read Paths: `brands/tga/ops/`, `integrations/notion/`, `integrations/gsheets/`, `shared/ops/queue.md`, `Research/System_Design.md`
- Primary Inputs: Funnel KPIs, reporting requirements, system constraints, GSheet data source (as local CSV)
- Required Outputs: Tracking schema, KPI definitions, reporting workflow notes, updated CSV in `integrations/gsheets/`
- Stop Conditions: Every required KPI has source, definition, and update cadence documented; local CSV is updated.
- Escalation Target: Systems Architect
- Required Contract(s): `shared/agents/AGENT_REGISTRY.md`

### Client Translation
- Tier: Tier 3 (Execution)
- Brand/Scope: `brands/tga` client-facing translation of systems work
- Allowed Write Paths: `brands/tga/content/portfolio/`, `brands/tga/content/blog/`, `brands/tga/offers/coaching/`, `shared/ops/queue.md`
- Allowed Read Paths: `brands/tga/strategy/`, `brands/tga/content/case_studies/`, `brands/tga/offers/`, `Research/`, `shared/ops/queue.md`
- Primary Inputs: Technical/system artifact, client objective, communication channel
- Required Outputs: Client-ready narrative artifact mapped to service/coaching CTA
- Stop Conditions: Output is non-technical, accurate, and includes a clear next action
- Escalation Target: Presentation Architect
- Required Contract(s): `shared/agents/CTA_AUTOMATION_RULES.md`, `shared/agents/AGENT_REGISTRY.md`



