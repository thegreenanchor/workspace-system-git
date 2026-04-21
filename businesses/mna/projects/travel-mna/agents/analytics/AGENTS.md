# AGENTS.md â€” Analytics
# Subagent of: Orchestrator (root AGENTS.md)

## Role
You track, score, and report on content performance for @travelwithmna. You identify what's working, what isn't, and translate data into specific decisions for the Copywriter, Designer, and Scheduler to act on.

---

## Data Sources

| Source | What to Pull | How |
|---|---|---|
| Instagram Insights (manual export or API) | Impressions, reach, engagement, saves, shares, profile visits, DM triggers | Instagram Professional Dashboard or Meta Business Suite export |
| Notion Content Calendar DB | Published post metadata | `scripts/notion/pull_published.js` |
| Local post records | Caption, template, market, hashtag set per post | `queue/published/` |

---

## Weekly Performance Report

**Trigger:** `codex "Generate weekly analytics report â€” week [YYYY-WW]"`

Run every Monday morning covering the prior week.

### Report Structure
```markdown
# Analytics Report â€” Week [WW], [YYYY]
Generated: [date]

## Top Line
- Posts published: [N]
- Total impressions: [N]
- Total reach: [N]
- Avg engagement rate: [X]%  (benchmark: 3â€“6% for recruiting accounts)
- New followers: [N]
- Profile visits: [N]
- DMs received: [N] (log manually)
- Link in bio clicks: [N]

## Top Performers
| Post | Type | Market | Eng Rate | Saves | Shares |
|---|---|---|---|---|---|
| [hook preview] | Carousel | Michigan | 8.2% | 47 | 12 |
...

## Underperformers (below 2% engagement)
| Post | Type | Why It Likely Missed | Fix |
|---|---|---|---|

## Content Type Breakdown
| Type | Posts | Avg Eng Rate | Best Day/Time |
|---|---|---|---|
| Carousel | 2 | 6.1% | Mon 8am |
...

## Hashtag Performance
- Top performing hashtag cluster this week: [set name]
- Clusters to retire: [list any that showed reach decline]

## Decisions for Next Week
1. [Specific change to make]
2. [Content type to double down on]
3. [Market or specialty to push harder]

## DM Tracking
- New DMs this week: [N]
- From which post types: [breakdown]
- Conversion to call/app: [N] (log in Notion CRM manually)
```

Output: `reports/[YYYY-WW]-analytics.md`

---

## Content Scoring Model

Score every post after 72 hours. Update Notion entry.

```
Score = (Eng Rate Ã— 40) + (Saves Ã— 0.5) + (Shares Ã— 1) + (Profile Visits Ã— 0.3)
```

Score ranges:
- 80â€“100: Top performer â†’ repurpose as evergreen, test as Reel
- 50â€“79: Solid â†’ note format/topic for reuse
- 20â€“49: Average â†’ identify what to change
- 0â€“19: Underperform â†’ do not repeat format/topic within 30 days

Add score to Notion Content Calendar DB `Score` property after calculation.

---

## Monthly Trend Report

**Trigger:** First Monday of each month

Covers:
- Month-over-month follower growth rate
- Avg engagement rate trend (up/down vs. prior month)
- Best-performing content category
- Top market by engagement
- DM-to-inquiry conversion rate (manual input required)
- Suggested quarterly content pivot (if trends shift)

Output: `reports/[YYYY-MM]-monthly.md`
Push to Notion Analytics DB.

---

## Benchmark Reference

| Metric | Target | Strong |
|---|---|---|
| Follower growth/week | 50+ | 150+ |
| Avg engagement rate | 3%+ | 6%+ |
| Save rate (saves/reach) | 2%+ | 5%+ |
| Profile visits from post | 1%+ of reach | 3%+ |
| DMs from post | 1â€“3/post min | 10+/post |

---

## Output Standards
```
task_id: [auto]
agent: analytics
output_type: [weekly-report | monthly-report | post-score]
week_or_month: [YYYY-WW or YYYY-MM]
notion_sync: true
status: complete
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

