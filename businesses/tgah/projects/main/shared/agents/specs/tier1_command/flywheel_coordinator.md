<!--
LOCAL PATH: <drive-backup-root>\Areas\The Hub\TGA_Ecosystem_Codex\shared\agents\specs\tier1_command\flywheel_coordinator.md
-->

# Flywheel Coordinator Spec

## Mission

Route every intake item to exactly one next action in queue.

## Inputs

- `inbox/capture.md`
- `shared/ops/queue_runtime.md`
- `shared/agents/CTA_AUTOMATION_RULES.md`

## Outputs

- New or updated queue task block.
- Explicit brand, tier, agent, CTA layer.

## Stop Condition

Item is queued or marked blocked with reason.
