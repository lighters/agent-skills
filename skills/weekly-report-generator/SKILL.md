---
name: weekly-report-generator
description: >-
  Use when generating a high-fidelity HTML/PDF weekly report (cover, Gantt
  timeline, deliverables status, this-week cards, and optional Slide 5+ discussion/proposal slides)
  from structured JSON — especially corporate project weekly reports for email or sync.
---
# Weekly Report Generator（企业高阶周报生成器）

Directory: `skills/weekly-report-generator`

Source: https://github.com/lighters/agent-skills (`skills/weekly-report-generator`)

Produce presentation-grade HTML + PDF weekly reports (4 core slides: Cover, Gantt Work Plan Overview, Deliverables & Status, This Week / Task Management; plus optional Slide 5+ Discussion & Proposal slides for meeting topics and architectural trade-offs). Match the visual fidelity of enterprise PPT weekly reports.

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

Themes: `astrazeneca` / `classic-navy`, `novartis`, `bayer`, `jnj`, `novo-nordisk`, `wukong-green`, `vercel-minimal`.

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

## Slide 3 (Deliverables / Output Status) Guidance (CRITICAL for Agents)

- **Purpose & Scope**: Focus **strictly on major project deliverables and key strategic milestones** (主要交付物与核心里程碑跟进，如各阶段成果确认、系统开发完成、SIT/UAT 验收签收、系统正式上线 Go-Live 等).
- **DO NOT write granular task progress here**: Everyday tactical tasks, operational bug fixes, or low-level implementation details **belong on Slide 4 (`thisWeek`)**, NEVER on Slide 3.
- `deliverables.items[]`: `{ milestone, progress, date, status, risk }`
  - `milestone`: Major deliverable or milestone gate name (e.g. `手机端&web端重点功能系统开发完成`, `业务验收测试(UAT)签收`)
  - `progress`: High-level summary of deliverables readiness (1-2 sentences, or `-` if pending)
  - `date`: Target delivery date (`YYYY.M.D`)
  - `status`: `已完成` | `进行中` | `未开始` (or `completed` | `active` | `planned`)
  - `risk`: `good` (🟢) | `caution` (🟡) | `risk` (🔴) | `none` (-)

## Slide 4 (This Week / Task Management) Guidance

- **Purpose & Scope**: Tactical weekly execution tasks, operational progress, next week steps, and immediate risks.
- `thisWeek`: `subtitle`, `overallStatus`, `previousTasks`, `nextSteps`, `risks`, `milestones`

## Slide 5+ (Discussion & Proposal Slides) Guidance (方案研讨与议题扩展页)

- **Purpose & Scope**: The standard 4-slide structure serves as the foundation. In enterprise weekly meetings, teams often need to discuss specific technical proposals, architectural trade-offs, process alignment, or strategic decisions. Agents can add one or more discussion slides via `discussionSlides: [...]` (or `appendixSlides`).
- **Supported Layouts**:
  1. `comparison`: Solution comparison mode (e.g. Option A vs Option B vs Option C). Best for architectural trade-offs, vendor comparisons, or tech stack selections. Each card supports:
     - `title`, `badge` (e.g. `"推荐方案"`, `"备选方案"`), `badgeType` (`recommended` | `alternative` | `warning` | `neutral`)
     - `summary`: Short summary callout box
     - `items`: Structured key-value rows (`[{label: "核心优势", text: "..."}, ...]`)
     - `points`: Bullet list points (`["point 1", ...]`)
     - `verdict`: Green bottom verdict box (e.g. `"结论：作为长期首选，建议本期采纳落地。"`)
  2. `cards`: Multi-column card matrix (2, 3, or 4 columns grid). Ideal for multiple initiative reviews, workstream breakdowns, or parallel milestone status.
  3. `agenda` / `deep-dive`: Two-column horizontal row cards (left header banner, right detailed narrative). Ideal for structured discussions: Background & Pain Points → Proposed Solutions → Expected Impact.
  4. `table`: Evaluation matrix table (`headers: [...]`, `rows: [[...], ...]`).
  5. `custom`: Free-form HTML injection via `html: "..."`.
- **Top Badges & Category Pills**:
  - `category`: Gray pill tag on top right (e.g. `"架构选型"`, `"流程规范"`).
  - `badge`: Theme-colored badge on top right (e.g. `"方案决策"`, `"周会决议"`).
- **Bottom Conclusion Box (`conclusion`)**:
  - Highlights weekly meeting decisions or pending approval items (e.g. `{ badge: "周会决议待确认", text: "..." }` or a plain string).
- **Page Numbering**: Slides are automatically numbered starting from Page 5 (`5`, `6`, `7`...), fully integrated into Presentation Mode (1 / N) and 16:9 PDF export.

## Presentation / deck mode

Generated HTML defaults to normal scroll. Enter **演示模式** from the toolbar (or press `P`, or open with `?present=1`):

- Pages: Dynamic 1 to N slides (Cover → Timeline → Deliverables → This Week → Discussion Slides 5..N)
- Keys: `←` / `→`, `Space` (next), `Esc` exit, `F` fullscreen; click left/right half of slide to navigate
- Seamless viewport fitting with zero letterboxing / black borders
- Print/PDF unchanged — each slide still prints cleanly as one 16:9 page

## Interactive WYSIWYG Content Editing (所见即所得直接编辑模式)

Users can modify small phrasing or fix typos directly in the browser without asking the Agent to re-run the skill:

- **Activate Edit Mode**: Click the **「✏️ 编辑内容」** button in the top toolbar, press `E` (when not typing), or simply **double-click** any text element on the slide.
- **Direct Editing**: Click anywhere on titles, table cells, task cards, or discussion points and edit text like in a word processor.
- **Save & Export**:
  - Click **「💾 另存 HTML」** to download the modified standalone HTML with all text edits permanently preserved and synced to the embedded JSON data.
  - Click **「导出 PDF / 打印」** to print the modified DOM to vector PDF immediately.
  - Press `Esc` or click **「完成编辑」** to exit edit mode.

## Delivery

Attach HTML and/or PDF for the user. Prefer PDF when they need an email-ready attachment.

## Files

- `scripts/generate_report.py`, `scripts/export_pdf.py`
- `templates/weekly_report_template.html`, `templates/theme-presets.json`
- `references/input_format_guide.md`, `references/data_schema.md`
- `examples/sample_data.json`
