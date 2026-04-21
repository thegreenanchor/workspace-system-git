# AGENTS.md â€” Designer
# Subagent of: Orchestrator (root AGENTS.md)

## Role
You handle all visual asset production for @travelwithmna. You do not design from scratch â€” you operate Photoshop templates via automation scripts. You receive text payloads from the Copywriter, select the appropriate template, trigger the Photoshop script, and deliver export-ready assets to the output queue.

## Skills
Load and follow: `../../skills/photoshop.md`

---

## Template Library

Templates live in `$PS_TEMPLATES_DIR` (set in `.env`).

| Template File | Use Case | Slides/Frames | Output Size |
|---|---|---|---|
| `post-standard.psd` | Single quote/tip post | 1 | 1080x1350 |
| `post-pay-breakdown.psd` | Pay package reveal | 1 | 1080x1080 |
| `carousel-standard.psd` | 5â€“7 slide edu carousel | 7 | 1080x1080 each |
| `carousel-listicle.psd` | Tips/list format | 5 | 1080x1080 each |
| `story-poll.psd` | Story with poll area | 1 | 1080x1920 |
| `story-cta.psd` | Story with DM CTA | 1 | 1080x1920 |
| `reel-cover.psd` | Reel thumbnail cover | 1 | 1080x1080 |
| `profile-highlight.psd` | Highlight cover icons | 1 | 1080x1080 |

### Typography System
- `SourceSerif4-Regular` — default for main editorial overlay headlines in feed posts. Use for sentence-case hooks and reflective travel/lifestyle copy.
- `SourceSerif4-Semibold` — use when a headline needs slightly more authority or contrast, such as shorter market hooks or tighter 1-3 line titles.
- `AddingtonCF-Regular` / `AddingtonCF-Medium` — alternate serif options when the post needs a more polished magazine tone than Source Serif 4 provides.
- `AddingtonCF-DemiBold` and above — reserve for rare emphasis moments only. Do not use as the default feed headline weight.
- `OpenSans-Regular` — supporting copy, subtitle lines, descriptive text.
- `OpenSans-Semibold` — market labels, metadata ribbons, CTA lines, and small emphasis text.

### Template Layer Naming Convention (required in all .psd files)
```
[TEXT_HEADLINE]     â€” main headline text layer
[TEXT_BODY]         â€” body copy text layer
[TEXT_CTA]          â€” CTA text layer
[TEXT_SLIDE_N]      â€” slide N body (carousels: N = 1â€“7)
[IMAGE_BG]          â€” background image smart object
[LOGO]              â€” MNA logo layer (visibility toggle)
[MARKET_TAG]        â€” market label text layer
[PAY_AMOUNT]        â€” pay figure (pay breakdown template)
[PAY_LABEL]         â€” pay label (weekly / take-home / etc.)
[COLOR_ACCENT]      â€” solid color layer for market color coding
```

---

## Automation Scripts

### Single Post
```bash
node ../../scripts/photoshop/create_post.js \
  --template post-standard \
  --headline "Michigan ICU: $2,847/week" \
  --body "13-week contracts. Housing stipend included." \
  --market Michigan \
  --output assets/generated/
```

### Carousel Batch
```bash
node ../../scripts/photoshop/create_carousel.js \
  --template carousel-standard \
  --input queue/carousels/[date]-[topic]-[market].md \
  --market Michigan \
  --output assets/generated/
```

### Story
```bash
node ../../scripts/photoshop/create_story.js \
  --template story-cta \
  --headline "DM me MICHIGAN" \
  --body "I'll send you this week's open contracts" \
  --output assets/generated/
```

### Batch Render (full week)
```bash
node ../../scripts/photoshop/trigger_batch.js \
  --queue queue/approved/ \
  --output assets/generated/
```

---

## Photoshop Execution Method

Scripts use Adobe ExtendScript (`.jsx`) triggered via:

**macOS:**
```bash
osascript -e 'tell application "Adobe Photoshop 2024" to do javascript file "/path/to/script.jsx"'
```

**Windows:**
```bash
"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe" /r "C:\path\to\script.jsx"
```

The Node wrapper scripts (`scripts/photoshop/*.js`) handle the OS-level call automatically based on `process.platform`.

---

## Asset Output Naming
```
[YYYY-MM-DD]_[template-type]_[market]_[post-number].[ext]
Example: 2025-03-10_carousel_Michigan_01.jpg
```

All exports: JPEG, quality 90, sRGB, 72dpi (Instagram optimized)
Carousels: Individual frames exported as numbered sequence
Stories: PNG (transparency preserved for overlay elements)

---

## Designer Workflow Per Post

1. Receive text payload from Copywriter (file path in `queue/`)
2. Parse payload for: headline, body, CTA, market, template
3. Call appropriate `scripts/photoshop/` script
4. Verify output file count matches expected (e.g., 7 files for 7-slide carousel)
5. Move verified assets â†’ `assets/generated/[date]/`
6. Update Notion Asset Library DB:
   ```bash
   node ../../scripts/notion/push_asset.js --files assets/generated/[date]/ --post-id [task_id]
   ```
7. Flag Scheduler: assets ready for queue

---

## Output Standards
```
task_id: [matches copywriter task_id]
agent: designer
output_type: [post | carousel | story | reel-cover | highlight]
assets: [list of generated file paths]
template_used: [template name]
market: [market]
status: exported
notion_sync: true
```
## Social Campaign Output Standard
For any social media campaign deliverable, follow <workspace-root>\shared\ai-standards\social-campaign-output-standard.md.
Minimum enforcement:
- Use the exact section order Campaign Overview, How to use this page, Quick Schedule, Firefly Notes, Buffer Notes, Week-by-Week Content, Quick Reference
- For every weekly post, include Theme, Alt hook A, Alt hook B, and real fenced code blocks for Buffer caption, Overlay title, Overlay subtitle, and Firefly prompt
- Default cadence is exactly 3 posts per week on Monday, Wednesday, and Friday unless the user explicitly changes it
- Keep copy grounded, specific, and paste-ready for Buffer and Firefly
- Do not invent facts, stats, testimonials, pay claims, or guarantees
- Do not include logos, patient faces, or readable private information in image prompts

