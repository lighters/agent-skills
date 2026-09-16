---
name: weekly-report-generator
description: >-
  Use when generating a high-fidelity HTML/PDF weekly report (cover, Gantt
  timeline, deliverables status, this-week cards) from structured JSON —
  especially corporate project weekly reports for email or sync.
---
# Weekly Report Generator（企业高阶周报生成器）

Package root on this computer: `/home/box/agent-data/workflows/weekly-report-generator`

Source: https://github.com/lighters/agent-skills (`skills/weekly-report-generator`)

Produce presentation-grade HTML + PDF weekly reports (4 slides: Cover, Gantt Work Plan Overview, Deliverables & Status, This Week / Task Management). Match the visual fidelity of enterprise PPT weekly reports.

## Before generating

1. Read the input format guide: `/home/box/agent-data/workflows/weekly-report-generator/references/input_format_guide.md`
2. Optionally skim `/home/box/agent-data/workflows/weekly-report-generator/examples/sample_data.json`
3. Build a JSON data file for the target project/week (cover, timeline, deliverables, thisWeek). Do not invent status — pull from the project's task source of truth.

## Generate

```bash
cd /home/box/agent-data/workflows/weekly-report-generator

python3 scripts/generate_report.py \
  --data /path/to/data.json \
  --theme classic-navy \
  --output /workspace/weekly-report.html

python3 scripts/export_pdf.py \
  --input /workspace/weekly-report.html \
  --output /workspace/weekly-report.pdf
```

Themes: `astrazeneca` / `classic-navy`, `novartis`, `bayer`, `jnj`, `novo-nordisk`, `vercel-minimal`.

## Timeline JSON (summary)

- `timeline.currentWeek`: week id for the "We are here" pointer
- `timeline.weeks[]`: `{ id, name, dates, isHoliday?, holidayName? }`
- `timeline.tasks[]`: `{ workstream, category, task, start, end, status, milestone? }` or `spans[]` for multi-phase bars
- task `status`: `completed` | `active` | `planned`

## Deliverables / This week (summary)

- `deliverables.items[]`: `{ milestone, progress, date, status, risk }` with risk `good` | `caution` | `risk` | `none`
- `thisWeek`: `subtitle`, `overallStatus`, `previousTasks`, `nextSteps`, `risks`, `milestones`


## Presentation / deck mode

Generated HTML defaults to normal scroll. Enter **演示模式** from the toolbar (or press `P`, or open with `?present=1`):

- Pages: Cover → Timeline/Overview → Deliverables → This Week
- Keys: `←` / `→`, `Space` (next), `Esc` exit, `F` fullscreen; click left/right half of slide to navigate
- Print/PDF unchanged — each slide still prints as one page

## Delivery

Attach HTML and/or PDF for the user. Prefer PDF when they need an email-ready attachment.

## Files

- `scripts/generate_report.py`, `scripts/export_pdf.py`
- `templates/weekly_report_template.html`, `templates/theme-presets.json`
- `references/input_format_guide.md`, `references/data_schema.md`
- `examples/sample_data.json`
