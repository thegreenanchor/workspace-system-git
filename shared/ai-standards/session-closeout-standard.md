# Session Closeout Standard

## Logging threshold
- Log every AI interaction.

## Required metadata
- `session_id`
- `business`
- `project_name`
- `assistant_name`
- `client_surface`
- `session_type`
- `started_at`
- `ended_at`
- `status`
- `submission_stage`

## Required content
- `session_summary`
- `work_completed`
- `deliverables`
- `links`
- `next_steps`
- `open_questions`
- `full_transcript`

## Rules
- Transcript is mandatory for every session.
- At least one content section beyond metadata must be non-empty.
- Deliverables may be empty for advisory, planning, or Q-and-A sessions.
- Tool-capable clients submit through the local submitter.
- Weaker clients emit a human summary plus JSON fallback for manual submit.
