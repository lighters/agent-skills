---
name: weekly-report-generator
description: >-
  Use when generating a high-fidelity HTML/PDF weekly report (cover, Gantt
  timeline, deliverables status, this-week cards, and optional Slide 5+ discussion/proposal slides)
  from structured JSON — especially corporate project weekly reports for email or sync.
---
# Weekly Report Generator（企业高阶周报生成器）

Directory: `skills/weekly-report-generator` · Source: https://github.com/lighters/agent-skills

Turns one JSON file into a presentation-grade HTML report (Cover → Gantt Work Plan → Deliverables → This Week → optional Slide 5+ discussion pages) and a 16:9 PDF. Python standard library only; PDF export needs a local Chrome/Chromium/Edge.

## Workflow

1. Read `references/input_format_guide.md` (field-by-field guide with examples). `references/schema.json` is the exact contract; `examples/sample_data.json` is a complete example.
2. Write the JSON for the target project/week. **Do not invent status** — take tasks, dates and status from the project's source of truth; ask when it is missing.
3. Validate and fix until clean:
   ```bash
   cd skills/weekly-report-generator
   python3 scripts/generate_report.py --data report.json --validate
   ```
   Errors (exit 1) are wrong types/enums, missing fields, week ids that don't exist, non-adjacent workstream/category rows, and non Mon-Fri weeks. Warnings flag unknown fields (usually typos) — fix those too.
4. Generate and export:
   ```bash
   python3 scripts/generate_report.py --data report.json --theme astrazeneca --output weekly-report.html
   python3 scripts/export_pdf.py --input weekly-report.html --output weekly-report.pdf
   ```
5. Deliver the HTML and/or PDF. Prefer the PDF for email attachments.

Themes: `astrazeneca` / `classic-navy`, `novartis`, `bayer`, `jnj`, `novo-nordisk`, `wukong-green`, `vercel-minimal` (default: the JSON `theme`, else `astrazeneca`).

Customer PowerPoint template: add `--pptx /path/to/template.pptx` to reuse its cover/content backgrounds, logo and colors (slide rendering and image compression use macOS `qlmanage`/`sips`; on other systems it falls back to the raw layout images, uncompressed).

The HTML is rendered in the browser from the embedded JSON, so it must be opened with JavaScript enabled; `export_pdf.py` uses headless Chrome, which runs the same renderer.

## Rules that the validator cannot fully check

### Timeline weeks: Monday–Friday, holidays annotated

- Each regular `timeline.weeks[].dates` is **Monday to Friday**, `M.D-M.D` (e.g. `9.14-9.18`), or `YYYY.M.D-YYYY.M.D` across years. The year comes from `project.reportDate`.
- **Never guess weekdays.** Compute them:
  ```python
  import datetime
  d = datetime.date(2026, 9, 16)
  mon = d - datetime.timedelta(days=d.weekday())
  fri = mon + datetime.timedelta(days=4)
  f"{mon.month}.{mon.day}-{fri.month}.{fri.day}"  # "9.14-9.18"
  ```
- Statutory-holiday weeks (国庆、春节、劳动节、中秋、端午、清明、元旦…): `"isHoliday": true` plus `"holidayName": "国庆假期"`. They render as a full-height golden column; no task bar is drawn there.
- `--fix-dates` aligns non-holiday weeks to Mon-Fri **and writes the file back**; `--strict-dates` makes date issues fatal during generation.

### Slide 3 vs Slide 4

- **Slide 3 `deliverables`** — only major deliverables and milestone gates (需求基线确认, 系统开发完成, SIT/UAT 签收, Go-Live). Audience: sponsors/PMO. `progress` is a 1-2 sentence summary, `-` if not started.
- **Slide 4 `thisWeek`** — tactical work: what was done, next week's steps, immediate risks, the next two weeks' milestones. Bug fixes, API debugging and meetings go here, never on Slide 3.

### Slide 5+ `discussionSlides` (optional)

Add a page only when the meeting has to discuss or decide something. Layouts: `comparison` (options A/B/C with badges and a verdict), `cards` (2-4 column matrix), `agenda` / `deep-dive` (problem → proposal → impact rows), `table` (evaluation matrix), `custom` (raw HTML). An optional `conclusion` shows the decision or sign-off request. Pages are numbered from 5 automatically.

## Files

- `scripts/generate_report.py` — validate, embed data, apply theme/PPTX; `scripts/validate_data.py` — schema + cross-field checks
- `scripts/export_pdf.py` — headless Chrome PDF export; `scripts/pptx_extractor.py` — PPTX asset extraction
- `templates/weekly_report_template.html` — renderer, themes, presentation/edit modes
- `references/input_format_guide.md`, `references/schema.json`, `examples/sample_data.json`

End-user features of the generated HTML (presentation mode, in-place editing, in-browser PPTX import) are described in `README.md`.
