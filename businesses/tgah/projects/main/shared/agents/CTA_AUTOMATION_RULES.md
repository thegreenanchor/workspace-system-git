<!--
LOCAL PATH: <drive-backup-root>\Areas\The Hub\TGA_Ecosystem_Codex\shared\agents\CTA_AUTOMATION_RULES.md
-->

# CTA Automation Rules â€” Command Matrix

**Owner:** ðŸŽ¯ Offer Alignment Director  
**Governance:** ðŸ§± Systems Architect  
**Used by:** Flywheel Coordinator, Link Hub Architect, all Execution Agents

---

# 1) Purpose

This document defines how CTAs are assigned, enforced, escalated, and limited across:

- ðŸŸª PURPLE â€” TGA Health (tgah)
- ðŸŸ¦ BLUE â€” Side Hustle Labs (shl)
- ðŸŸ© GREEN â€” The Green Anchor (tga)

The goal is to keep each brand aligned with its funnel maturity:

PURPLE â†’ discovery / lifestyle / affiliate  
BLUE â†’ systems / education / builder  
GREEN â†’ authority / services / implementation

---

# 2) Core Rule (Non-Negotiable)

Each brand has a **default CTA authority layer**.

Execution agents MUST NOT assign CTAs outside their allowed layer.

If content requires a higher-tier CTA â†’ escalate via Flywheel Coordinator.

---

# 3) CTA Layers (System Standard)

- Primary = Main business objective for that brand
- Secondary = Nurture / onboarding
- Bridge = Moves user to next brand layer
- Loopback = Sends authority users back to education
- Utility = Low-pressure navigation/support

---

# 4) Brand CTA Command Matrix

## ðŸŸª PURPLE â€” TGA Health (tgah)

### Allowed Primary CTA
- â€œShop Picksâ€
- â€œDaily Wellness Favoritesâ€
- Affiliate or product-focused landing pages

### Allowed Secondary CTA
- Free wellness starter
- Email signup (lifestyle focused)

### Required Bridge CTA
Must include a bridge pointing to BLUE when system/process language appears.

Examples:
- â€œWant the system behind thisxâ€
- â€œSee the workflow I useâ€

### Forbidden CTAs
âŒ Services  
âŒ Audits  
âŒ Architecture builds  
âŒ Authority consulting

### Escalation Trigger
If content includes:
- workflow
- framework
- automation
- â€œhow I builtâ€

â†’ Create BLUE task.

---

## ðŸŸ¦ BLUE â€” Side Hustle Labs (shl)

### Allowed Primary CTA
- Free template
- Workflow starter
- Systems toolkit

### Allowed Secondary CTA
- Weekly systems email
- â€œStart Hereâ€ hub

### Required Bridge CTA
Must include GREEN bridge when authority signals appear.

Examples:
- â€œWant this built for youxâ€
- â€œGet the full system auditâ€

### Forbidden CTAs
âŒ Direct affiliate heavy selling  
âŒ Lifestyle shopping funnels

### Escalation Trigger
If content includes:
- architecture
- system buildout
- done-for-you
- consulting

â†’ Create GREEN task.

---

## ðŸŸ© GREEN â€” The Green Anchor (tga)

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
- â€œWant to build it yourself firstxâ€
- â€œGrab the template versionâ€

### Approval Required
All GREEN Primary CTAs require:
ðŸ§± Systems Architect approval.

---

# 5) CTA Assignment Logic (Used by Flywheel Coordinator)

When routing a task:

IF Brand = tgah
â†’ Default CTA Layer = Primary (Shop/Picks)
â†’ Add Bridge only if system language exists

IF Brand = shl
â†’ Default CTA Layer = Primary (Template/System)
â†’ Add Bridge to GREEN when authority signals exist

IF Brand = tga
â†’ Default CTA Layer = Primary (Audit/Health Check)
â†’ Flag Approval Required = TRUE

---

# 6) Linktree Automation Rules (Link Hub Architect)

Each brand Linktree must maintain:

## PURPLE
1â€“2 Primary  
2â€“3 Secondary  
1 Bridge â†’ BLUE  
Utility links allowed

## BLUE
1 Primary Template  
2 Secondary  
1 Bridge â†’ GREEN  
Utility links allowed

## GREEN
1 Primary Service  
2 Secondary Authority  
Optional Loopback â†’ BLUE

Total links per tree:
8â€“12 maximum.

---

# 7) Momentum Overrides (Used by ðŸ§­ Momentum Indicator)

If system imbalance detected:

Too much PURPLE traffic:
â†’ increase BLUE bridge placement

Too much BLUE education:
â†’ increase GREEN bridge visibility

Too much GREEN authority:
â†’ add BLUE loopback CTA

Momentum overrides do NOT change brand rules â€” only emphasis.

---

# 8) Execution Agent Guardrails

Execution agents must:

- assign CTA according to brand defaults
- never invent new CTA types
- escalate when CTA exceeds brand authority

Violation examples:
- PURPLE blog ending with â€œBook a system auditâ€
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

- `Research/System_Design.md` â†’ defines funnel philosophy
- `docs/06_agent_activation_logic.md` â†’ defines when agents activate
- `shared/agents/AGENT_REGISTRY.md` â†’ defines who is allowed to write where