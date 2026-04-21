# Workspace Improvement Game Plan
**Owner:** Jose Suarez
**Date:** 2026-04-07
**Scope:** ai_rules broker, openclaw, businesses ops, shared standards, osint-toolkit

---

## PHASE 1 - Harden (Weeks 1-2)
*Fix what's already breaking. No structural changes.*

---

### 1. Add retry logic to the submission pipeline

**Problem:** `submit_session.py` makes 3 synchronous calls (Notion, Google Docs, SQLite) in sequence. If any step fails mid-chain, you get `completed-with-log-error` - a zombie state where the task succeeded but the log is incomplete. Already showing in `worker.log`.

**Fix:**

In `submit_session.py`, wrap each remote call with a retry decorator:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def submit_to_notion(payload): ...

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def append_to_google_doc(payload): ...
```

Add a fallback queue: if all retries fail, append the payload path to `cli_broker_runtime/failed_submissions.jsonl` with a timestamp and failure reason. Run a separate recovery pass at the start of each worker cycle.

**Files touched:** `submit_session.py`, `cli_broker_worker.py`
**Outcome:** Eliminates `completed-with-log-error`. Failed submissions get a retry path instead of silent data loss.

---

### 2. Separate task state from log sync state

**Problem:** `BrokerResult.status` conflates two things: did the task succeed, and did the log submission succeed. This is why "completed-with-log-error" exists as a status - it's load-bearing instead of exceptional.

**Fix:**

Add a second field to `BrokerResult`:

```python
@dataclass
class BrokerResult:
    ...
    status: str              # "completed" | "failed" - task execution only
    logging_status: str      # "submitted" | "partial" | "pending" | "failed"
```

Update `cli_broker_worker.py` to set these independently. Update `worker.log` format to log both fields. Update any downstream checks that look at `status` for submission state.

**Files touched:** `cli_broker.py`, `cli_broker_worker.py`, `submit_session.py`
**Outcome:** Clean separation. A task can be "completed / logging: pending" without being an error condition.
**[VERIFY]:** Check if `BrokerResult` is a dataclass or dict in `cli_broker.py` before implementing.

---

### 3. Harden sync_rules.py marker validation

**Problem:** `sync_rules.py` injects rule blocks using HTML comment markers (`<!-- BEGIN MANAGED: {rule_name} -->`). If someone edits a managed file manually and breaks the marker structure, the next sync either silently fails or corrupts the file.

**Fix:**

Add a `--check` mode that validates all markers before writing:

```python
def validate_markers(content: str, rule_name: str) -> bool:
    begin = f"<!-- BEGIN MANAGED: {rule_name} -->"
    end = f"<!-- END MANAGED: {rule_name} -->"
    begin_count = content.count(begin)
    end_count = content.count(end)
    return begin_count == end_count == 1

# Run before any write:
for rule_name in rule_blocks:
    if not validate_markers(existing_content, rule_name):
        log.warning(f"Marker mismatch for {rule_name} in {filepath} - skipping")
        continue
```

Add a checksum to each injected block (comment line with MD5 of the block content) so you can detect if managed content was manually modified.

**Files touched:** `sync_rules.py`
**Outcome:** Sync is idempotent and safe. Manual edits don't silently corrupt rule state.

---

### 4. Convert auth errors to active alerts

**Problem:** When a provider fails auth (`gemini is not ready for headless broker use`), the task goes to `failed/` silently. You find out when you check logs, which may be hours later.

**Fix:**

In `cli_broker_worker.py`, detect auth errors by their current stderr strings and fire a webhook:

```python
AUTH_ERROR_SIGNALS = [
    "not ready for headless broker use",
    "Complete interactive authentication",
    "EPERM: operation not permitted, uv_spawn 'reg'"
]

def is_auth_error(stderr: str) -> bool:
    return any(sig in stderr for sig in AUTH_ERROR_SIGNALS)

# After provider subprocess fails:
if is_auth_error(result.stderr):
    fire_n8n_alert(provider_id, task_id, result.stderr)
```

Point `fire_n8n_alert()` at your existing n8n webhook -> Slack. Include: provider name, task ID, timestamp, first line of stderr.

**Files touched:** `cli_broker_worker.py`, `common.py` (add webhook helper)
**Outcome:** Auth failures surface in Slack within minutes, not hours.

---

### 5. Add startup config validation

**Problem:** `config.yaml` and `global_cli_policy.yaml` are loaded at runtime with no schema validation. A bad value (wrong path, missing key, typo in provider name) fails silently or causes an unhandled exception mid-task.

**Fix:**

Add a `validate_config()` function that runs at worker startup before processing any tasks:

```python
REQUIRED_CONFIG_KEYS = [
    "broker.task_queue_root",
    "broker.global_policy_path",
    "broker.provider_timeout",
    "notion.database_id",
    "sqlite.path",
]

def validate_config(cfg: dict) -> list[str]:
    errors = []
    for key_path in REQUIRED_CONFIG_KEYS:
        if not deep_get(cfg, key_path):
            errors.append(f"Missing config key: {key_path}")
    # Verify all provider executables actually exist on disk
    for provider_id, provider_cfg in cfg.get("providers", {}).items():
        exe = provider_cfg.get("executable")
        if exe and not Path(exe).exists():
            errors.append(f"Provider '{provider_id}' executable not found: {exe}")
    return errors
```

If any errors, log them all and exit before processing inbox. Don't silently degrade.

**Files touched:** `cli_broker_worker.py`, `common.py`
**Outcome:** Misconfiguration fails fast at startup, not mid-task.

---

### 6. Map the full submission pipeline (prerequisite for Phase 2)

**Action:** Before simplifying anything, document the exact call chain from `cli_broker_worker.py` through `submit_session.py` -> `archive.py` -> Notion -> Google Docs -> SQLite. Write it as a flowchart in `ai_rules/SUBMISSION_PIPELINE.md`.

Note: which steps are blocking vs. async, what the failure mode is for each hop, and what partial state looks like. This becomes the source of truth for Phase 2 consolidation.

**Files touched:** New file `ai_rules/SUBMISSION_PIPELINE.md`
**Outcome:** You can make Phase 2 changes without re-reverse-engineering the system.

---

## PHASE 2 - Simplify (Weeks 3-4)
*Reduce surface area. Consolidate where duplication creates risk.*

---

### 7. Make SQLite canonical; push Notion + Google Docs async

**Problem:** Every task blocks on 3 synchronous remote calls. One slow Notion API response delays the next inbox task. Google Docs and Notion have different uptime characteristics than your local SQLite.

**Fix:**

Refactor the submission flow:
1. Task completes -> write to SQLite immediately (synchronous, local, fast)
2. Mark `logging_status = "pending_remote"`
3. Enqueue Notion + Google Docs writes to a background queue (simple JSONL file or in-memory queue with a separate thread)
4. Background sync thread processes the queue and updates `logging_status` to `submitted` when done

This way, task processing never blocks on remote API calls.

**Files touched:** `submit_session.py`, `cli_broker_worker.py`, new `sync_worker.py`
**Outcome:** Task throughput decoupled from API latency. SQLite is always authoritative.

---

### 8. Provider consolidation audit

**Decision point:** You're maintaining Codex + Gemini + Claude with different auth setups, prompt-passing mechanisms, and failure modes. That's 3x the operational overhead.

**Action:**
1. Pull 30 days of `worker.log` data and count: tasks per provider, success rate per provider, average execution time per provider
2. Map which task categories are actually going to which provider (check `done/` folder task_category distribution)
3. Ask: if you dropped one provider, what would you losex

**Decision criteria:**
- If Gemini handles >80% of research/content tasks successfully -> keep it, reconsider Codex
- If Claude review tasks are <5% of volume -> route those to Gemini or Codex instead
- Keep whichever 2 providers cover 95%+ of actual task volume

**Files touched:** `global_cli_policy.yaml` (routing changes), `config.yaml` (remove decommissioned provider)
**Outcome:** 2 providers instead of 3. Reduces auth surface, failure modes, and maintenance.

---

### 9. openclaw extension audit

**Problem:** 83+ extensions means 83+ potential maintenance surfaces. Many are likely installed but dormant.

**Action:**
1. Check `openclaw/extensions/` - look for any usage logs, last-modified dates, or import references in `src/`
2. Build `openclaw/SKILLS_MANIFEST.md`: list every extension with status (active / dormant / unknown), last known use date, and which business uses it
3. Archive dormant extensions to `openclaw/extensions/_archive/` - don't delete, just move

**Files touched:** `openclaw/extensions/`, new `openclaw/SKILLS_MANIFEST.md`
**Outcome:** Clear picture of what's live vs. dead weight. Easier onboarding for future collaborators.

---

### 10. Standardize businesses/ ops folder templates

**Problem:** MNA, SHL, TGA, TGAH all have parallel folder structures (ops/, assets/, projects/, archive/) but likely divergent contents and no shared template.

**Action:**
1. Pick one business as the reference (MNA - most mature based on having `MNA_Knowledge_Documents/`)
2. Document its ops/ folder structure in `shared/ai-standards/ops-folder-template.md`
3. Run a gap analysis: what's in MNA/ops/ that's missing from SHL/ops/, TGA/ops/, TGAH/ops/x
4. Create placeholder files where gaps exist so the structure is consistent

**Files touched:** `shared/ai-standards/ops-folder-template.md` (new), `businesses/*/ops/`
**Outcome:** Consistent structure across all 4 orgs. Rule blocks and automation can target paths reliably.

---

### 11. Add status frontmatter to shared/ai-standards files

**Problem:** The rule blocks in `ai_rules/rule_blocks/` and standards in `shared/ai-standards/` have no versioning or status metadata. You can't tell what's current, draft, or superseded.

**Fix:**

Add frontmatter to every standards file:

```yaml
---
standard: naming-standard
version: 1.2
status: active  # active | draft | deprecated
last_updated: 2026-04-07
applies_to: [mna, tga, tgah, shl, personal]
enforced_by: sync_rules.py
---
```

Update `sync_rules.py` to read `status` and skip injection of `deprecated` blocks.

**Files touched:** All `ai_rules/rule_blocks/*.md`, all `shared/ai-standards/*.md`, `sync_rules.py`
**Outcome:** Standards are self-documenting. Deprecated rules stop propagating automatically.

---

## PHASE 3 - Expand (Month 2+)
*Build on the hardened, simplified foundation.*

---

### 12. Observability dashboard

Once SQLite is canonical (item 7), build a simple dashboard:
- n8n workflow: poll `session_log.db` every hour -> format summary -> post to Slack
- Metrics: tasks completed today, tasks failed, logging_status breakdown, provider distribution
- Alert thresholds: >3 failures in an hour, any provider with 0 completions in 24h

**Files touched:** n8n (external), `session_log.db` schema (add index on `completed_at`)

---

### 13. Cross-business asset sync via shared/

**Goal:** Assets created for one business (templates, scoring models, AI standards) should be discoverable by others without copy-paste.

**Action:**
- Build `shared/asset-registry.md`: index of every reusable asset, which business owns it, which businesses use it
- Add a `sync_shared_assets.py` script that copies approved assets from `shared/` into each business's `assets/` folder on a schedule

**Files touched:** New `shared/asset-registry.md`, new `sync_shared_assets.py`

---

### 14. Wire OSINT toolkit into business workflows

**Current state:** `osint-toolkit/` is standalone with its own cases/, targets/, reports/ structure.

**Opportunity:**
- MNA: competitor intelligence on other travel nurse staffing firms
- TGA: prospect research before B2B outreach
- TGA Health: affiliate program research

**Action:**
- Add an `osint-toolkit/integrations/` folder with one script per use case
- Wire outputs (reports/) into the ai_rules broker as context files for research tasks - so Gemini can act on OSINT data automatically

**Files touched:** `osint-toolkit/integrations/` (new), `ai_rules/instruction_templates/` (add OSINT context injection)

---

### 15. openclaw skills deployment pipeline

**Goal:** Move openclaw from a dev repo to a deployed system with CI checks.

**Action:**
1. Audit `openclaw/skills/` - document which skills are production-ready vs. prototype
2. Add a `skills/MANIFEST.yaml` with skill status, dependencies, and platform targets
3. Set up GitHub Actions (`.github/workflows/` already exists) to run skill validation on PR
4. Define "deployed" vs. "local-only" skill states

**Files touched:** `openclaw/skills/MANIFEST.yaml` (new), `openclaw/.github/workflows/`

---

## Phase Gate Criteria

**Before starting Phase 2:**
- [ ] Zero `completed-with-log-error` entries in last 7 days of `worker.log`
- [ ] `sync_rules.py --check` passes on all project roots
- [ ] Auth alerts firing to Slack (test with a bad credential)
- [ ] `SUBMISSION_PIPELINE.md` written and accurate

**Before starting Phase 3:**
- [ ] SQLite is canonical - Notion/GDocs are async
- [ ] Provider count is 2 (one decommissioned)
- [ ] All 4 business ops/ folders follow shared template
- [ ] All rule blocks have status frontmatter

---

*Items marked [VERIFY] require a file read before implementing - file names and function names are based on prior analysis and should be confirmed against current state.*
