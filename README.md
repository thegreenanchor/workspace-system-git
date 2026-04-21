# Workspace System Git

This repository is the shareable version of the AI workspace system I use to run multi-CLI work across projects with Codex CLI, Gemini CLI, and Claude Code.

It captures the rules, routing model, submission/logging tooling, and selected business agent definitions that make the system work, while removing local secrets, machine-specific paths, runtime state, and private working content.

## What this repository contains

- `AGENTS.md`: workspace-wide operating guardrails
- `shared/ai-standards/`: reusable standards for campaign output, naming, Notion formatting, session closeout, and other shared conventions
- `ai_rules/`: the local tooling layer for routing, queueing, broker health checks, session submission, and managed rule sync
- `businesses/`: selected agent-definition files from active business projects, kept as examples of how the system is applied in real project structures
- `workspace-game-plan.md` and `workspace-systems-outline.md`: higher-level system thinking, operating notes, and structure

## What was intentionally removed

This export is not a full working clone of the original workspace.

It does not include:

- secrets, tokens, auth caches, or local `.env` values
- private user paths, machine-specific home directories, or local drive mappings
- local runtime folders, SQLite state, temp payloads, or generated broker data
- client deliverables, reports, campaign content, archives, or internal operating files that were not needed to explain the system
- unrelated nested repositories or vendor checkouts

Where paths or IDs mattered for documentation, they were replaced with placeholders such as `<workspace-root>`, `<user-home>`, `<drive-backup-root>`, and `<codex-session-root>`.

## How to read the repo

If you are new to the system, start here:

1. Read `AGENTS.md` for the top-level operating rules.
2. Read `workspace-systems-outline.md` for the architecture view.
3. Open `ai_rules/README.md` for the tooling layer and command surface.
4. Browse `shared/ai-standards/` to see the standards the system enforces.
5. Browse the included business agent files to see how those rules and routes get applied inside real projects.

## How the system is organized

At a high level, the system works like this:

- shared standards define how work should look
- routing rules decide whether Codex CLI, Gemini CLI, or Claude Code should handle a given task
- local broker tooling handles delegation, queueing, and health checks
- session submission tooling logs work into the archive and external systems
- project-level agent files specialize the system for specific businesses or workflows

The intent is not to force one model to do everything. Codex acts as the main implementation and integration hub, Gemini is used for research and Google-stack work, and Claude is used for review, refactor, hardening, and presentation-heavy specialist work. The structure is built around role separation, predictable routing, and a documented workflow layer that can survive across projects.

## Important usage notes

- Treat this repository as a documented system export, not as a turnkey install
- You will need your own environment variables, credentials, database IDs, and archive destinations before any external integrations can run
- Some scripts assume Windows-first paths or local desktop tooling, even though the sensitive path details have been sanitized here
- Review `ai_rules/config.yaml`, `.env.example`, and `ai_rules/README.md` before trying to wire it into another environment

## Why this repo exists

I wanted a clean public-facing copy of the system itself, separate from the live workspace it came from.

That means this repo is meant to show:

- how the operating rules are structured
- how Codex, Gemini, and Claude are routed into different roles
- how logging and submission are wired into the workflow
- how project-specific agent definitions sit on top of the shared system

It is the system, without the private residue of the machine it was built on.
