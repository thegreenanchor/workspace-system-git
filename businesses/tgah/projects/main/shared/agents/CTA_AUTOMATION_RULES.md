<!--
LOCAL PATH: <drive-backup-root>\Areas\The Hub\TGA_Ecosystem_Codex\shared\agents\CTA_AUTOMATION_RULES.md
-->

# CTA Automation Rules - Command Matrix

**Owner:**  Offer Alignment Director  
**Governance:**  Systems Architect  
**Used by:** Flywheel Coordinator, Link Hub Architect, all Execution Agents

---

# 1) Purpose

This document defines how CTAs are assigned, enforced, escalated, and limited across:

-  PURPLE - TGA Health (tgah)
-  BLUE - Side Hustle Labs (shl)
-  GREEN - The Green Anchor (tga)

The goal is to keep each brand aligned with its funnel maturity:

PURPLE -> discovery / lifestyle / affiliate  
BLUE -> systems / education / builder  
GREEN -> authority / services / implementation

---

# 2) Core Rule (Non-Negotiable)

Each brand has a **default CTA authority layer**.

Execution agents MUST NOT assign CTAs outside their allowed layer.

If content requires a higher-tier CTA -> escalate via Flywheel Coordinator.

---

# 3) CTA Layers (System Standard)

- Primary = Main business objective for that brand
- Secondary = Nurture / onboarding
- Bridge = Moves user to next brand layer
- Loopback = Sends authority users back to education
- Utility = Low-pressure navigation/support

---

# 4) Brand CTA Command Matrix

##  PURPLE - TGA Health (tgah)

### Allowed Primary CTA
- "Shop Picks"
- "Daily Wellness Favorites"
- Affiliate or product-focused landing pages

### Allowed Secondary CTA
- Free wellness starter
- Email signup (lifestyle focused)

### Required Bridge CTA
Must include a bridge pointing to BLUE when system/process language appears.

Examples:
- "Want the system behind thisx"
- "See the workflow I use"

### Forbidden CTAs
[do not use] Services  
[do not use] Audits  
[do not use] Architecture builds  
[do not use] Authority consulting

### Escalation Trigger
If content includes:
- workflow
- framework
- automation
- "how I built"

-> Create BLUE task.

---

##  BLUE - Side Hustle Labs (shl)

### Allowed Primary CTA
- Free template
- Workflow starter
- Systems toolkit

### Allowed Secondary CTA
- Weekly systems email
- "Start Here" hub

### Required Bridge CTA
Must include GREEN bridge when authority signals appear.

Examples:
- "Want this built for youx"
- "Get the full system audit"

### Forbidden CTAs
[do not use] Direct affiliate heavy selling  
[do not use] Lifestyle shopping funnels

### Escalation Trigger
If content includes:
- architecture
- system buildout
- done-for-you
- consulting

-> Create GREEN task.

---

##  GREEN - The Green Anchor (tga)

### Allowed Primary CTA
- Marketing System Health Check
- System Audit
- Architecture Strategy

### Allowed Secondary CTA
- Case Studies
- How It Works
- Portfolio

### Optional Loopback CTA
May include BLUE educational assets if user intent is DIY.

Examples:
- "Want to build it yourself firstx"
- "Grab the template version"

### Approval Required
All GREEN Primary CTAs require:
 Systems Architect approval.

---

# 5) CTA Assignment Logic (Used by Flywheel Coordinator)

When routing a task:

IF Brand = tgah
-> Default CTA Layer = Primary (Shop/Picks)
-> Add Bridge only if system language exists

IF Brand = shl
-> Default CTA Layer = Primary (Template/System)
-> Add Bridge to GREEN when authority signals exist

IF Brand = tga
-> Default CTA Layer = Primary (Audit/Health Check)
-> Flag Approval Required = TRUE

---

# 6) Linktree Automation Rules (Link Hub Architect)

Each brand Linktree must maintain:

## PURPLE
1-2 Primary  
2-3 Secondary  
1 Bridge -> BLUE  
Utility links allowed

## BLUE
1 Primary Template  
2 Secondary  
1 Bridge -> GREEN  
Utility links allowed

## GREEN
1 Primary Service  
2 Secondary Authority  
Optional Loopback -> BLUE

Total links per tree:
8-12 maximum.

---

# 7) Momentum Overrides (Used by  Momentum Indicator)

If system imbalance detected:

Too much PURPLE traffic:
-> increase BLUE bridge placement

Too much BLUE education:
-> increase GREEN bridge visibility

Too much GREEN authority:
-> add BLUE loopback CTA

Momentum overrides do NOT change brand rules - only emphasis.

---

# 8) Execution Agent Guardrails

Execution agents must:

- assign CTA according to brand defaults
- never invent new CTA types
- escalate when CTA exceeds brand authority

Violation examples:
- PURPLE blog ending with "Book a system audit"
- BLUE template pushing affiliate shopping links
- GREEN page pushing lifestyle product lists

---

# 9) Stop Conditions

Agents must STOP and escalate if:

- CTA request conflicts with brand authority layer
- Offer Alignment Director flags monetization misalignment
- Systems Architect review required

---

# 10) Relationship to Other System Files

- `Research/System_Design.md` -> defines funnel philosophy
- `docs/06_agent_activation_logic.md` -> defines when agents activate
- `shared/agents/AGENT_REGISTRY.md` -> defines who is allowed to write where