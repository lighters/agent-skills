---
name: weekly-report-generator
description: >-
  Use when generating a high-fidelity HTML/PDF weekly report (cover, Gantt
  timeline, deliverables status, this-week cards) from structured JSON —
  especially corporate project weekly reports for email or sync.
---
# Weekly Report Generator（企业高阶周报生成器）

Directory: `skills/weekly-report-generator`

Source: https://github.com/lighters/agent-skills (`skills/weekly-report-generator`)

Produce presentation-grade HTML + PDF weekly reports (4 slides: Cover, Gantt Work Plan Overview, Deliverables & Status, This Week / Task Management). Match the visual fidelity of enterprise PPT weekly reports.

## Before generating

1. Read the input format guide: `skills/weekly-report-generator/references/input_format_guide.md`
2. Optionally skim `skills/weekly-report-generator/examples/sample_data.json`
3. Build a JSON data file for the target project/week (cover, timeline, deliverables, thisWeek). Do not invent status — pull from the project's task source of truth.

## Generate

```bash
cd skills/weekly-report-generator

python3 scripts/generate_report.py \
  --data examples/sample_data.json \
  --theme classic-navy \
  --output weekly-report.html

python3 scripts/export_pdf.py \
  --input weekly-report.html \
  --output weekly-report.pdf
```

Themes: `astrazeneca` / `classic-navy`, `novartis`, `bayer`, `jnj`, `novo-nordisk`, `vercel-minimal`.

## Work Plan Date & Holiday Constraints (CRITICAL for Agents)

When constructing `timeline.weeks[]`, agents MUST strictly follow these business calendar rules:

1. **Strict Monday-to-Friday Work Weeks (周一至周五约束)**:
   - Every standard work week in `timeline.weeks[].dates` MUST represent **Monday to Friday** (`周一至周五`).
   - Format: `M.D-M.D` (e.g. `9.14-9.18`, `10.12-10.16`), or `YYYY.M.D-YYYY.M.D` across year boundaries.
   - Start day MUST be **Monday** (`weekday() == 0`).
   - End day MUST be **Friday** (`weekday() == 4`).
   - **DO NOT guess calendar days!** Verify with Python before writing the JSON:
     ```python
     import datetime
     d = datetime.date(2026, 9, 16)
     mon = d - datetime.timedelta(days=d.weekday())  # Monday
     fri = mon + datetime.timedelta(days=4)           # Friday
     # Dates string: f"{mon.month}.{mon.day}-{fri.month}.{fri.day}" -> "9.14-9.18"
     ```

2. **Statutory Holiday Annotation (法定节假日标注)**:
   - When a week corresponds to a statutory holiday (如国庆假期、春节假期、劳动节、中秋节、端午节、清明节、元旦等):
     - Set `"isHoliday": true`
     - Set `"holidayName": "<假期名称>"` (e.g. `"国庆假期"`, `"春节假期"`)
     - The Gantt chart automatically renders the holiday week as a golden vertical highlight column with the holiday name vertically centered. Regular task bars do not occupy holiday columns.

3. **Date Validation & Auto-Fix CLI**:
   - Validate dates without generating: `python3 scripts/generate_report.py --data <file.json> --check-dates`
   - Auto-align non-holiday dates to Monday-Friday: `python3 scripts/generate_report.py --data <file.json> --fix-dates`
   - Strict mode: `python3 scripts/generate_report.py --data <file.json> --strict-dates`

## Timeline JSON (summary)

- `timeline.currentWeek`: week id for the "We are here" pointer
- `timeline.weeks[]`: `{ id, name, dates, isHoliday?, holidayName? }` (strictly Mon-Fri, or statutory holiday)
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
