# WSL Media Ingest SOP

## Purpose

This setup is a WSL-first media intake system for collecting reference media, extracting metadata, and keeping a structured record in Notion.

Current runtime:
- Kali in WSL for commands and scripts
- `yt-dlp` for supported-source downloads
- `ffmpeg` and `ffprobe` for merge, conversion, and media inspection
- Notion as the searchable database and operating dashboard
- local state in `~/.config/ai-rules-media-ingest/state.json` for dedupe and database reuse

Core scripts:
- `media_ingest.py`
- `media_maintenance.py`

## What You Can Do Right Now

Use this system for:
- building a reference library of music videos, ads, reels, interviews, podcasts, shorts, and image/video examples
- collecting source material for moodboards, shot references, pacing references, and edit inspiration
- pulling audio-only references for vocal study, sound design study, lyric review, or music breakdowns
- creating a Notion-backed archive of downloaded media with file path, source URL, uploader, duration, counts, and technical media metadata
- preventing repeated downloads and repeated Notion entries for the same source after the first successful indexed run
- auditing and cleaning older duplicate local files from before dedupe existed
- reporting duplicate Notion pages for the same source key

## Standard Operating Workflows

### 1. Ingest A New Asset

Run:

```bash
python3 ./ai_rules/media_ingest.py "REAL_SUPPORTED_URL_HERE"
```

Result:
- media is downloaded into `./raw-media-downloads`
- the file is sorted into `audio`, `video`, `image`, or `other`
- Notion gets a page in the media database
- the successful source key is saved for dedupe

### 2. Preview A Source Before Writing To Notion

Run:

```bash
python3 ./ai_rules/media_ingest.py "REAL_SUPPORTED_URL_HERE" --dry-run
```

Use this when you want to confirm:
- the source resolves correctly
- the chosen format looks right
- the metadata payload is usable

Current behavior:
- dry-run skips Notion writes
- dry-run cleans up the downloaded local file after inspection

### 3. Pull Audio Only

Run:

```bash
python3 ./ai_rules/media_ingest.py "REAL_SUPPORTED_URL_HERE" --audio-only
```

Use this for:
- vocal references
- sample references
- lyric review
- podcast or interview capture

### 4. Audit Duplicate Files

Report only:

```bash
python3 ./ai_rules/media_maintenance.py
```

Delete older duplicate local files:

```bash
python3 ./ai_rules/media_maintenance.py --apply
```

### 5. Audit Duplicate Notion Pages

Run:

```bash
python3 ./ai_rules/media_maintenance.py --check-notion
```

Use this when:
- the workflow changed over time
- you imported the same source before dedupe existed
- you want to see which source keys have more than one Notion page

## High-Value Use Cases

Good project ideas on top of this setup:

### Reference Vault

Build a private library for:
- music video references
- edit pacing references
- typography and motion references
- ad and brand references
- talking-head structure references

### Vocal And Performance Library

Use audio-only or full video ingest to organize:
- vocal covers
- live performances
- studio takes
- breakdown videos
- artist references by era, tone, or genre

### Competitor And Market Research

Track:
- creator references
- competitor campaigns
- high-performing content formats
- content trends by niche

### Prompt And Production Input Library

Turn the database into a staging area for:
- Firefly prompt references
- Photoshop composition references
- shot list inspiration
- thumbnail and cover reference boards

## Agents To Add Next

If you want this to become a full media operations system, add agents around the ingest step instead of overloading the ingest script itself.

Recommended agents:

### 1. Metadata Enricher

Job:
- summarize why the asset matters
- write a short creative note
- extract likely use cases

Output:
- `Creative Summary`
- `Why It Matters`
- `Use Case`

### 2. Transcriber

Job:
- pull transcript from spoken content
- extract quotes, hooks, and timestamps

Output:
- transcript file
- notable quotes
- clip timestamps

### 3. Tagging Agent

Job:
- assign controlled tags like `genre`, `format`, `energy`, `camera style`, `editing style`, `hook type`

Output:
- normalized tags for Notion

### 4. Clip Planner

Job:
- identify reusable clip windows
- suggest shorts, reels, or excerpt ideas

Output:
- clip list
- suggested titles
- suggested captions

### 5. Prompt Pack Agent

Job:
- turn ingested references into reusable prompt language for image/video generation

Output:
- Firefly prompt pack
- shot references
- style notes

### 6. QA / Dedupe Agent

Job:
- check for duplicate local files
- check for duplicate Notion pages
- verify `Source Key`, `Source URL`, and `Local Path Tail`

Output:
- maintenance report

### 7. Publishing Handoff Agent

Job:
- convert approved references into downstream tasks for design, editing, or posting workflows

Output:
- task records
- production queue entries

## How To Turn This Into A Project

Recommendation:
- keep the current scripts in `ai_rules` while the workflow is still changing
- split into a dedicated project once you start adding multiple agents, multiple databases, or recurring workflows

Recommended project name:
- `media-ops`
- or `reference-library`

Recommended project structure:

```text
projects/media-ops/
  AGENTS.md
  AI_ROUTING.yaml
  README.md
  docs/
  prompts/
  scripts/
  workflows/
  reports/
  exports/
```

Add these project-level pieces:
- `AGENTS.md` for roles, workflows, file ownership, and naming rules
- `AI_ROUTING.yaml` to decide which agent runs where
- `docs/` for SOPs, schemas, and maintenance rules
- `workflows/` for ingest, enrich, clip, export, and publish stages

## Recommended Notion Expansion

Current database is enough for raw ingest, but a full project should add:

### Media Library

Keep as the system of record for:
- source URL
- source key
- uploader
- local path
- media metadata

### Collections

Use for:
- playlists
- campaigns
- creative themes
- artist folders
- study folders

### Tasks

Use for:
- clip extraction
- transcript cleanup
- tag review
- thumbnail or cover creation

### Exports

Use for:
- final clips
- prompt packs
- derived summaries

## Suggested Milestones

### Phase 1

Stabilize ingest:
- finish naming and dedupe rules
- confirm Notion schema
- clean old duplicates

### Phase 2

Add intelligence:
- transcript agent
- tagging agent
- creative summary agent

### Phase 3

Turn it into production ops:
- project-level agents
- recurring queues
- exports and task handoff
- reporting and review cadence

## Operating Rules

Keep these rules:
- ingest first, enrich second
- keep source media immutable after ingest
- use dedupe before manual cleanup
- let Notion be the index, not the only storage location
- keep local file paths stable
- avoid manual renames outside the workflow unless you also update the state and Notion record

## Next Best Additions

If you want the highest-value next steps, do them in this order:

1. add transcript generation
2. add controlled tagging
3. add clip planning
4. add collection-level organization in Notion
5. split into a dedicated `media-ops` project with its own agents
