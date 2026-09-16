#!/usr/bin/env python3
"""
Weekly Report HTML Generator
Generates high-fidelity corporate weekly report HTML and PDF from structured JSON data.
Part of the weekly-report-generator Antigravity skill.
"""

import json
import os
import re
import sys
import datetime
import argparse
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_timeline_dates(timeline_data, project_data, auto_fix=False, strict=False):
    """
    Validates work plan timeline weeks against standard business calendar rules:
    1. Standard work weeks MUST be Monday to Friday (周一至周五).
    2. Format: 'M.D-M.D' (or 'YYYY.M.D-YYYY.M.D', 'M/D-M/D').
    3. Statutory holidays (isHoliday: true) MUST have a non-empty holidayName (e.g. '国庆假期', '春节假期').
    4. Provides detailed diagnostic warnings with suggested Monday-to-Friday spans.
    5. Optionally auto-fixes dates in place if auto_fix=True.
    """
    weeks = timeline_data.get("weeks", [])
    if not weeks:
        return []

    # Infer target year
    year = None
    report_date = str(project_data.get("reportDate", ""))
    m_yr = re.search(r"(\d{4})", report_date)
    if m_yr:
        year = int(m_yr.group(1))
    else:
        period = str(project_data.get("period", ""))
        m_yr = re.search(r"(\d{4})", period)
        if m_yr:
            year = int(m_yr.group(1))
    if not year:
        year = datetime.date.today().year

    weekdays_cn = ["周一 (Mon)", "周二 (Tue)", "周三 (Wed)", "周四 (Thu)", "周五 (Fri)", "周六 (Sat)", "周日 (Sun)"]
    issues = []
    fixed_count = 0

    date_pattern = re.compile(
        r'^(?:(\d{4})[./-])?(\d{1,2})[./-月](\d{1,2})[日]?\s*[-~～至到]\s*(?:(\d{4})[./-])?(\d{1,2})[./-月](\d{1,2})[日]?$'
    )

    for idx, w in enumerate(weeks):
        w_id = w.get("id", f"Week-{idx+1}")
        dates_str = str(w.get("dates", "")).strip()
        is_holiday = w.get("isHoliday", False)
        holiday_name = str(w.get("holidayName", "")).strip()

        if is_holiday and not holiday_name:
            issues.append(f"Week '{w_id}': marked 'isHoliday: true' but 'holidayName' is missing. Please specify the statutory holiday (e.g. '国庆假期', '春节假期').")

        if not dates_str:
            issues.append(f"Week '{w_id}': 'dates' is empty. Expected Monday-to-Friday format 'M.D-M.D'.")
            continue

        m = date_pattern.match(dates_str)
        if not m:
            issues.append(f"Week '{w_id}': Unable to parse dates '{dates_str}'. Expected format: 'M.D-M.D' (e.g. '9.14-9.18').")
            continue

        y1, m1, d1, y2, m2, d2 = m.groups()
        yr1 = int(y1) if y1 else year
        yr2 = int(y2) if y2 else (yr1 + 1 if int(m2) < int(m1) else yr1)

        try:
            dt1 = datetime.date(yr1, int(m1), int(d1))
            dt2 = datetime.date(yr2, int(m2), int(d2))
        except ValueError as e:
            issues.append(f"Week '{w_id}': Invalid calendar date in '{dates_str}': {e}")
            continue

        if dt2 < dt1:
            issues.append(f"Week '{w_id}': End date ({dt2}) is earlier than start date ({dt1}).")
            continue

        # Standard work week check (non-holiday)
        if not is_holiday:
            start_wd = dt1.weekday()
            end_wd = dt2.weekday()
            if start_wd != 0 or end_wd != 4:
                # Calculate correct Monday and Friday:
                # If end date is already Friday, Monday is 4 days prior
                if end_wd == 4:
                    friday = dt2
                    monday = friday - datetime.timedelta(days=4)
                # If start date is Sunday (weekday 6, mistakenly used as week start), Monday is next day
                elif start_wd == 6:
                    monday = dt1 + datetime.timedelta(days=1)
                    friday = monday + datetime.timedelta(days=4)
                # Otherwise, align to start date's Monday
                else:
                    monday = dt1 - datetime.timedelta(days=start_wd)
                    friday = monday + datetime.timedelta(days=4)

                expected_str = f"{monday.month}.{monday.day}-{friday.month}.{friday.day}"

                msg = (
                    f"Week '{w_id}' ('{dates_str}'): Start {dt1} is {weekdays_cn[start_wd]} (expected Monday), "
                    f"end {dt2} is {weekdays_cn[end_wd]} (expected Friday). "
                    f"Work plan standard requires Monday-to-Friday. Suggested: '{expected_str}'"
                )
                issues.append(msg)

                if auto_fix:
                    w["dates"] = expected_str
                    fixed_count += 1

    if fixed_count > 0:
        print(f"🔧 [Date Auto-Fix] Automatically adjusted {fixed_count} week(s) to exact Monday-to-Friday dates.")

    if issues:
        print("\n" + "=" * 76, file=sys.stderr)
        print("⚠️  [Work Plan Timeline Date Validation Warnings]", file=sys.stderr)
        print("   Each regular week in Work Plan must represent Monday to Friday (周一至周五),", file=sys.stderr)
        print("   and statutory holidays must have a clear holidayName annotation.", file=sys.stderr)
        print("-" * 76, file=sys.stderr)
        for issue in issues:
            print(f"   • {issue}", file=sys.stderr)
        print("=" * 76 + "\n", file=sys.stderr)

        if strict:
            raise ValueError(f"Timeline date validation failed with {len(issues)} issue(s). Use --fix-dates to auto-correct.")

    return issues

def build_gantt_rows_html(timeline_data):
    """
    Dynamically generates the complete table body for Slide 2 (Timeline Gantt)
    Handles automatic rowspan for workstreams and categories, holiday highlight column,
    task progress spans, milestone stars, and "We are here" pointer.
    """
    weeks = timeline_data.get("weeks", [])
    tasks = timeline_data.get("tasks", [])
    if not tasks:
        tasks = timeline_data.get("rows", []) # backward compatibility

    # 1. Calculate rowspans for workstreams and categories
    workstream_counts = {}
    ws_cat_counts = {}
    
    for t in tasks:
        ws = t.get("workstream", "默认工作流")
        cat = t.get("category", "通用")
        workstream_counts[ws] = workstream_counts.get(ws, 0) + 1
        ws_cat_key = f"{ws}___{cat}"
        ws_cat_counts[ws_cat_key] = ws_cat_counts.get(ws_cat_key, 0) + 1

    rendered_ws = set()
    rendered_cat = set()
    tbody_lines = []
    
    week_ids = [w["id"] for w in weeks]
    holiday_weeks = {w["id"]: w.get("holidayName", "假期") for w in weeks if w.get("isHoliday")}
    current_week_id = timeline_data.get("currentWeek", "W16")
    we_are_here_text = timeline_data.get("weAreHereText", "We are here")

    for row_idx, t in enumerate(tasks):
        ws = t.get("workstream", "默认工作流")
        cat = t.get("category", "通用")
        task_name = t.get("task", "")
        
        # Support both 'spans' list and direct 'start'/'end'/'status'
        spans = t.get("spans", [])
        if not spans and "start" in t and "end" in t:
            spans = [{
                "start": t["start"],
                "end": t["end"],
                "status": t.get("status", "completed")
            }]
            
        # Support both 'milestone' (str/bool) and 'stars' (list)
        milestone = t.get("milestone", None)
        stars = t.get("stars", [])
        if milestone:
            if isinstance(milestone, str):
                stars.append(milestone)
            elif milestone is True and "end" in t:
                stars.append(t["end"])

        ws_cat_key = f"{ws}___{cat}"
        row_cells = []
        
        # Workstream cell with rowspan
        if ws not in rendered_ws:
            rendered_ws.add(ws)
            ws_span = workstream_counts[ws]
            row_cells.append(f'<td rowspan="{ws_span}" class="col-workstream" style="background:#f8fafc; font-weight:700;">{ws}</td>')
            
        # Category cell with rowspan
        if ws_cat_key not in rendered_cat:
            rendered_cat.add(ws_cat_key)
            cat_span = ws_cat_counts[ws_cat_key]
            row_cells.append(f'<td rowspan="{cat_span}" class="col-category">{cat}</td>')
            
        # Task title
        row_cells.append(f'<td class="col-task">{task_name}</td>')
        
        # Week columns
        for w_idx, w_id in enumerate(week_ids):
            # Special Holiday Column (rendered once with full rowspan across all tasks)
            if w_id in holiday_weeks:
                if row_idx == 0:
                    holiday_name = holiday_weeks[w_id]
                    holiday_content = f'<div class="holiday-col-text">{holiday_name}</div>'
                    holiday_style = ''
                    if w_id == current_week_id:
                        holiday_content += f"""
                <div class="we-are-here-indicator" data-week="{w_id}">
                  <span class="red-arrow-up"></span>
                  <span>{we_are_here_text}</span>
                </div>
                """
                        holiday_style = ' style="position: relative;"'
                    row_cells.append(f'<td rowspan="{len(tasks)}" class="cell-holiday"{holiday_style}>{holiday_content}</td>')
                continue # Handled by vertical rowspan on row 0

            # Determine if this week falls into any task span
            cell_class = ""
            for s in spans:
                s_start_id = s.get("start")
                s_end_id = s.get("end")
                s_status = s.get("status", s.get("type", "completed"))

                start_idx = week_ids.index(s_start_id) if s_start_id in week_ids else 999
                end_idx = week_ids.index(s_end_id) if s_end_id in week_ids else -1

                if start_idx <= w_idx <= end_idx:
                    if s_status in ["completed", "done"]:
                        cell_class = "gantt-bar-completed"
                    elif s_status in ["active", "ongoing", "current"]:
                        cell_class = "gantt-bar-active"
                    else:
                        cell_class = "gantt-bar-planned"
                    break
            
            # Check milestone star
            cell_content = ""
            if w_id in stars:
                cell_content = '<span class="milestone-star">★</span>'
            
            # Check "We are here" indicator (in current-week cell; CSS left:50% centers it)
            if row_idx == len(tasks) - 1 and w_id == current_week_id:
                cell_content += f'''
                <div class="we-are-here-indicator" data-week="{w_id}">
                  <span class="red-arrow-up"></span>
                  <span>{we_are_here_text}</span>
                </div>
                '''
                
            cls_attr = f' class="{cell_class}"' if cell_class else ''
            style_attr = ' style="position: relative;"' if (row_idx == len(tasks) - 1 and w_id == current_week_id) else ''
            row_cells.append(f'<td{cls_attr}{style_attr}>{cell_content}</td>')

        tbody_lines.append(f"            <tr>{''.join(row_cells)}</tr>")

    return "\n".join(tbody_lines)

def build_gantt_thead_html(timeline_data):
    """Dynamically generates the table header row with weeks and dates"""
    weeks = timeline_data.get("weeks", [])
    ths = [
        '<th class="gantt-header-th col-workstream">Workstream</th>',
        '<th class="gantt-header-th col-category">Category</th>',
        '<th class="gantt-header-th col-task">Tasks</th>'
    ]
    current_week_id = timeline_data.get("currentWeek")
    for w in weeks:
        w_id = w.get("id", "")
        w_name = w.get("name", w_id)
        w_date = w.get("dates", "")
        extra_style = ""
        if w.get("isHoliday"):
            extra_style = ' style="background-color: #d97706;"'
        elif w.get("isCurrent") or (current_week_id and w_id == current_week_id):
            extra_style = ' style="background-color: var(--brand-primary-dark);"'
        ths.append(f'<th class="gantt-header-th col-week"{extra_style}><div class="week-title">{w_name}</div><div class="week-date">{w_date}</div></th>')
    return "\n            <tr>" + "".join(ths) + "</tr>"

def build_deliverables_tbody_html(deliv_data):
    """Generates table rows for Slide 3 (Deliverables & Status)"""
    items = deliv_data.get("items", [])
    rows = []
    for item in items:
        status = item.get("status", "未开始")
        if "完成" in status or status.lower() == "completed":
            pill_cls = "completed"
        elif "进行" in status or status.lower() in ["ongoing", "active"]:
            pill_cls = "ongoing"
        else:
            pill_cls = "pending"
            
        risk = item.get("risk", "none").lower()
        if risk in ["good", "norisk", "no_risk"]:
            dot_html = '<span class="status-dot dot-good"></span>'
        elif risk in ["caution", "warning", "medium"]:
            dot_html = '<span class="status-dot dot-caution"></span>'
        elif risk in ["risk", "high", "danger"]:
            dot_html = '<span class="status-dot dot-risk"></span>'
        else:
            dot_html = '<span style="color:#94a3b8;">-</span>'

        rows.append(f"""            <tr>
              <td class="col-m-name">{item.get('milestone', '')}</td>
              <td class="col-m-prog">{item.get('progress', '') or '-'}</td>
              <td class="col-m-date">{item.get('date', '')}</td>
              <td class="col-m-stat"><span class="status-pill {pill_cls}">{status}</span></td>
              <td class="col-m-indi">{dot_html}</td>
            </tr>""")
    return "\n".join(rows)

def build_task_mgmt_components(tasks_data):
    """Generates the card bodies and milestone rows for Slide 4 (This week's work)"""
    # 1. Previous tasks
    prev_items = []
    for idx, item in enumerate(tasks_data.get("previousTasks", []), 1):
        tag = f"<span class='ppt-tag'>【{item['tag']}】</span>" if item.get("tag") else ""
        content = item.get("content", "")
        prev_items.append(f"""              <div class="ppt-list-item">
                <span class="ppt-list-num">{idx}.</span>
                <div>{tag}{content}</div>
              </div>""")
    
    # 2. Next steps
    next_items = []
    for idx, item in enumerate(tasks_data.get("nextSteps", []), 1):
        tag = f"<span class='ppt-tag'>【{item['tag']}】</span>" if item.get("tag") else ""
        content = item.get("content", "")
        next_items.append(f"""              <div class="ppt-list-item">
                <span class="ppt-list-num">{idx}.</span>
                <div>{tag}{content}</div>
              </div>""")

    # 3. Risks
    risk_items = []
    for idx, item in enumerate(tasks_data.get("risks", []), 1):
        tag = f"<span class='ppt-tag'>【{item['tag']}】</span>" if item.get("tag") else ""
        content = item.get("content", "")
        risk_items.append(f"""              <div class="ppt-list-item">
                <span class="ppt-list-num">{idx}.</span>
                <div>{tag}{content}</div>
              </div>""")

    # 4. Milestones table
    ms_rows = []
    for item in tasks_data.get("milestones", []):
        ms_rows.append(f"""                <tr>
                  <td>{item.get('name', '-')}</td>
                  <td>{item.get('date', '-')}</td>
                </tr>""")

    return {
        "prev_html": "\n".join(prev_items) if prev_items else "<div style='color:#94a3b8;'>暂无内容</div>",
        "next_html": "\n".join(next_items) if next_items else "<div style='color:#94a3b8;'>暂无内容</div>",
        "risk_html": "\n".join(risk_items) if risk_items else "<div style='color:#94a3b8;'>暂无风险</div>",
        "ms_html": "\n".join(ms_rows) if ms_rows else "<tr><td>-</td><td>-</td></tr>"
    }

def html_escape(text):
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

def get_badge_class(badge_type, badge_text):
    if badge_type:
        bt = str(badge_type).lower()
        if bt in ("recommended", "success"):
            return "badge-recommended"
        if bt in ("alternative", "info"):
            return "badge-alternative"
        if bt in ("warning", "risk"):
            return "badge-warning"
        if bt == "neutral":
            return "badge-neutral"
    t = str(badge_text or "").lower()
    if any(k in t for k in ["推荐", "首选", "recommended"]):
        return "badge-recommended"
    if any(k in t for k in ["备选", "alternative", "方案b"]):
        return "badge-alternative"
    if any(k in t for k in ["风险", "注意", "warning", "待定"]):
        return "badge-warning"
    return "badge-neutral"

def build_discussion_slides_html(discussion_slides, start_page_num=5):
    """
    Generates HTML for Slide 5+ (Discussion & Proposal Slides).
    Supports layouts: comparison, cards, agenda, deep-dive, table, custom.
    """
    slides_html = []
    for idx, slide in enumerate(discussion_slides):
        page_num = start_page_num + idx
        title = html_escape(slide.get("title", f"议题研讨 {idx + 1}"))
        subtitle = html_escape(slide.get("subtitle", "周会方案讨论与决策项"))
        
        badge_text = slide.get("badge")
        badge_html = f'<span class="discussion-badge">{html_escape(badge_text)}</span>' if badge_text else ""
        
        cat_text = slide.get("category")
        cat_html = f'<span class="discussion-category-pill">{html_escape(cat_text)}</span>' if cat_text else ""
        
        layout = slide.get("layout", "comparison")
        body_content = ""
        
        if layout in ("comparison", "cards"):
            cards = slide.get("cards", [])
            cols = slide.get("columns") or (4 if len(cards) >= 4 else (3 if len(cards) == 3 else 2))
            grid_class = "grid-cols-4" if cols == 4 else ("grid-cols-3" if cols == 3 else "grid-cols-2")
            
            cards_list = []
            for c in cards:
                c_title = html_escape(c.get("title", ""))
                c_badge = c.get("badge")
                c_bclass = get_badge_class(c.get("badgeType"), c_badge)
                c_badge_html = f'<span class="card-badge {c_bclass}">{html_escape(c_badge)}</span>' if c_badge else ""
                
                c_summary = c.get("summary")
                c_sum_html = f'<div class="card-summary">{html_escape(c_summary)}</div>' if c_summary else ""
                
                c_items_html = ""
                items = c.get("items", [])
                if items:
                    rows = []
                    for it in items:
                        lbl = html_escape(it.get("label", ""))
                        txt = html_escape(it.get("text", it.get("value", "")))
                        rows.append(f'<div class="discussion-item-row"><span class="item-label">{lbl}</span><span class="item-text">{txt}</span></div>')
                    c_items_html = f'<div class="card-items">\n' + "\n".join(rows) + '\n</div>'
                
                c_points_html = ""
                points = c.get("points", [])
                if points:
                    pts = "".join(f'<li>{html_escape(p)}</li>' for p in points)
                    c_points_html = f'<ul class="discussion-points-list">{pts}</ul>'
                
                c_verdict = c.get("verdict")
                c_verdict_html = f'<div class="card-verdict">{html_escape(c_verdict)}</div>' if c_verdict else ""
                
                cards_list.append(f'''
            <div class="discussion-card">
              <div class="discussion-card-header">
                <span class="card-header-title">{c_title}</span>
                {c_badge_html}
              </div>
              <div class="discussion-card-body">
                {c_sum_html}
                {c_items_html}
                {c_points_html}
                {c_verdict_html}
              </div>
            </div>''')
            
            body_content = f'<div class="discussion-grid {grid_class}">{"".join(cards_list)}\n          </div>'

        elif layout in ("agenda", "deep-dive"):
            sections = slide.get("sections", [])
            secs_list = []
            for s_idx, sec in enumerate(sections):
                s_title = html_escape(sec.get("title", f"议题 {s_idx + 1}"))
                s_content = sec.get("contentHtml") if sec.get("contentHtml") else html_escape(sec.get("content", ""))
                secs_list.append(f'''
            <div class="agenda-row-card">
              <div class="agenda-row-side">{s_title}</div>
              <div class="agenda-row-content">{s_content}</div>
            </div>''')
            body_content = f'<div class="discussion-agenda-container">{"".join(secs_list)}\n          </div>'

        elif layout == "table":
            tbl = slide.get("table", {})
            headers = tbl.get("headers", [])
            rows = tbl.get("rows", [])
            
            th_cells = "".join(f'<th>{html_escape(h)}</th>' for h in headers)
            thead_html = f'<thead><tr>{th_cells}</tr></thead>' if headers else ""
            
            tr_rows = []
            for r in rows:
                td_cells = []
                for c_idx, cell in enumerate(r):
                    if c_idx == 0:
                        td_cells.append(f'<td style="font-weight: 600;">{html_escape(cell)}</td>')
                    else:
                        td_cells.append(f'<td>{html_escape(cell)}</td>')
                tr_rows.append(f'<tr>{"".join(td_cells)}</tr>')
            tbody_html = f'<tbody>{"".join(tr_rows)}</tbody>'
            
            body_content = f'''<div class="discussion-table-wrapper">
            <table class="discussion-matrix-table">
              {thead_html}
              {tbody_html}
            </table>
          </div>'''

        elif layout == "custom":
            body_content = f'<div style="flex: 1; overflow-y: auto;">{slide.get("html", "")}</div>'

        # Conclusion box (optional)
        conclusion = slide.get("conclusion")
        conclusion_html = ""
        if conclusion:
            if isinstance(conclusion, dict):
                c_badge = html_escape(conclusion.get("badge", "周会决议 / 待决策项"))
                c_text = html_escape(conclusion.get("text", ""))
            else:
                c_badge = "周会决议 / 待决策项"
                c_text = html_escape(str(conclusion))
            
            conclusion_html = f'''
        <div class="discussion-conclusion-box">
          <div class="conclusion-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
            </svg>
            <span>{c_badge}</span>
          </div>
          <div class="conclusion-text">{c_text}</div>
        </div>'''

        slide_block = f'''
    <!-- ====================================================================
         PAGE {page_num}: 方案研讨与议题讨论 (Discussion & Proposal)
         ==================================================================== -->
    <section class="slide slide-discussion" id="slide{page_num}">
      <div class="slide-header" style="align-items: center;">
        <div class="slide-title-group">
          <h2 class="slide-title">{title}</h2>
          <div class="slide-subtitle" style="font-size: 14px; margin-top: 2px;">{subtitle}</div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          {cat_html}
          {badge_html}
        </div>
      </div>

      <div class="discussion-body">
        {body_content}
      </div>
      {conclusion_html}

      <div class="slide-footer-num">{page_num}</div>
    </section>'''
        slides_html.append(slide_block)

    return "\n".join(slides_html)

def generate_report(data_path, output_path, theme="classic-navy", auto_fix_dates=False, strict_dates=False):
    base_dir = Path(__file__).resolve().parent.parent
    template_path = base_dir / "templates" / "weekly_report_template.html"
    
    data = load_json(data_path)
    if not theme:
        theme = data.get("theme", "astrazeneca")
    data["theme"] = theme

    # Get sub-sections
    company = data.get("company", {})
    project = data.get("project", {})
    timeline = data.get("timeline", data.get("slide2_plan", {}))
    deliverables = data.get("deliverables", data.get("slide3_deliverables", {}))
    this_week = data.get("thisWeek", data.get("slide4_tasks", {}))

    # Validate work plan timeline dates
    validate_timeline_dates(timeline, project, auto_fix=auto_fix_dates, strict=strict_dates)

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Apply theme to body and select
    html = html.replace('body data-theme="classic-navy"', f'body data-theme="{theme}"')
    html = html.replace('body data-theme="astrazeneca"', f'body data-theme="{theme}"')
    html = re.sub(r'<option value="' + re.escape(theme) + r'">', f'<option value="{theme}" selected>', html)

    # 1. Slide 1 (Cover) replacements
    html = html.replace("AstraZeneca / 数字化交付中心", company.get("name", "企业数字化创新交付中心"))
    html = html.replace("商业技术交付团队", company.get("department", "技术交付团队"))
    html = html.replace(">AZ<", f">{company.get('logoText', 'TECH')}<")
    html = html.replace("手机端搭建与 Web 端优化项目", project.get("title", "核心系统升级与交付项目"))
    html = html.replace("Weekly Report", project.get("reportTitle", "Weekly Report"))
    html = html.replace("PRJ-2024-AZ-Q1", project.get("projectCode", "PRJ-2024-001"))
    html = html.replace("汇报周期：Week 16（2024.04.01 ～ 2024.04.03）", f"汇报周期：{project.get('period', 'Week 16')}")
    html = html.replace("2024-04-03", project.get("reportDate", "2024-04-03"))
    html = html.replace("项目交付组 (AZ Team)", project.get("reporter", "项目交付团队"))

    # Status badge in Slide 1
    overall_status = project.get("overallStatus", this_week.get("overallStatus", "caution"))
    overall_text = project.get("overallStatusText", "受控推进中" if overall_status == "caution" else ("如期进行" if overall_status == "good" else "存在风险"))
    dot_class = "dot-good" if overall_status == "good" else ("dot-risk" if overall_status == "risk" else "dot-caution")
    dot_color = "#059669" if overall_status == "good" else ("#dc2626" if overall_status == "risk" else "#d97706")

    # 2. Slide 2 (Timeline Gantt) generation
    timeline_title = timeline.get("title", "Work Plan —Overview")
    weeks = timeline.get("weeks", [])
    if weeks:
        w_first = weeks[0].get("name", weeks[0].get("id", ""))
        w_last = weeks[-1].get("name", weeks[-1].get("id", ""))
        auto_range = f"({w_first} - {w_last})" if w_first and w_last else ""
    else:
        auto_range = ""

    raw_tl_sub = timeline.get("subtitle", "")
    if not raw_tl_sub:
        timeline_subtitle = f"端到端执行计划及进度跟踪 {auto_range}".strip() if auto_range else "端到端执行计划及进度跟踪"
    elif "(W6 - W20)" in raw_tl_sub and auto_range and auto_range != "(W6 - W20)":
        timeline_subtitle = raw_tl_sub.replace("(W6 - W20)", auto_range)
    else:
        timeline_subtitle = raw_tl_sub

    # Replace title & subtitle in Slide 2
    html = re.sub(
        r'(<section class="slide" id="slide2">.*?<h2 class="slide-title">).*?(</h2>)',
        f'\\1{timeline_title}\\2',
        html,
        flags=re.DOTALL
    )
    html = re.sub(
        r'(<section class="slide" id="slide2">.*?<span class="slide-subtitle"[^>]*>).*?(</span>)',
        f'\\1{timeline_subtitle}\\2',
        html,
        flags=re.DOTALL
    )

    gantt_thead = build_gantt_thead_html(timeline)
    gantt_tbody = build_gantt_rows_html(timeline)
    
    # Replace the thead and tbody in slide 2
    html = re.sub(
        r'<table class="gantt-table">\s*<thead>.*?</thead>\s*<tbody>.*?</tbody>\s*</table>',
        f'<table class="gantt-table">\n        <thead>{gantt_thead}\n        </thead>\n        <tbody>\n{gantt_tbody}\n        </tbody>\n      </table>',
        html,
        flags=re.DOTALL
    )

    # 3. Slide 3 (Deliverables) generation
    deliv_title = deliverables.get("title", "Deliverables / Output Status")
    deliv_subtitle = deliverables.get("subtitle", "关键交付节点与成果物健康度评估")

    # Replace title & subtitle in Slide 3
    html = re.sub(
        r'(<section class="slide" id="slide3">.*?<h2 class="slide-title">).*?(</h2>)',
        f'\\1{deliv_title}\\2',
        html,
        flags=re.DOTALL
    )
    html = re.sub(
        r'(<section class="slide" id="slide3">.*?<span class="slide-subtitle"[^>]*>).*?(</span>)',
        f'\\1{deliv_subtitle}\\2',
        html,
        flags=re.DOTALL
    )

    deliv_tbody = build_deliverables_tbody_html(deliverables)
    html = re.sub(
        r'<table class="deliverables-table">\s*<thead>.*?</thead>\s*<tbody>.*?</tbody>\s*</table>',
        f'<table class="deliverables-table">\n          <thead>\n            <tr>\n              <th class="col-m-name">Milestone</th>\n              <th class="col-m-prog">Progress</th>\n              <th class="col-m-date">Date</th>\n              <th class="col-m-stat">Status</th>\n              <th class="col-m-indi">Indicator</th>\n            </tr>\n          </thead>\n          <tbody>\n{deliv_tbody}\n          </tbody>\n        </table>',
        html,
        flags=re.DOTALL
    )

    # 4. Slide 4 (This week / Task Management) generation
    tm_comps = build_task_mgmt_components(this_week)
    
    tw_title = this_week.get("title", "Task Management")
    tw_subtitle = this_week.get("subtitle", "Week 16")

    # Replace title & subtitle in Slide 4
    html = re.sub(
        r'(<section [^>]*id="slide4"[^>]*>.*?<h2 class="slide-title"[^>]*>).*?(</h2>)',
        f'\\1{tw_title}\\2',
        html,
        flags=re.DOTALL
    )
    html = re.sub(
        r'(<section [^>]*id="slide4"[^>]*>.*?<div class="slide-subtitle"[^>]*>).*?(</div>)',
        f'\\1{tw_subtitle}\\2',
        html,
        flags=re.DOTALL
    )

    # Status circle color
    circle_color = "#00B050" if overall_status == "good" else ("#FF0000" if overall_status == "risk" else "#ED7D31")
    html = re.sub(
        r'<div class="ppt-status-circle"[^>]*></div>',
        f'<div class="ppt-status-circle" style="background-color: {circle_color};"></div>',
        html
    )

    # Card bodies
    html = re.sub(
        r'(<div class="ppt-card-header">Key tasks from previous weeks</div>\s*<div class="ppt-card-body">).*?(</div>\s*</div>\s*<!-- Card 2: Key next steps)',
        f'\\1\n{tm_comps["prev_html"]}\n            \\2',
        html,
        flags=re.DOTALL
    )
    html = re.sub(
        r'(<div class="ppt-card-header">Key next steps for next week</div>\s*<div class="ppt-card-body">).*?(</div>\s*</div>\s*</div>\s*<!-- Right Column)',
        f'\\1\n{tm_comps["next_html"]}\n            \\2',
        html,
        flags=re.DOTALL
    )
    html = re.sub(
        r'(<div class="ppt-card-header">Risk Management</div>\s*<div class="ppt-card-body">).*?(</div>\s*</div>\s*<!-- Card 2: Key Milestones)',
        f'\\1\n{tm_comps["risk_html"]}\n            \\2',
        html,
        flags=re.DOTALL
    )
    html = re.sub(
        r'(<table class="milestones-table">.*?<tbody>).*?(</tbody>\s*</table>)',
        f'\\1\n{tm_comps["ms_html"]}\n              \\2',
        html,
        flags=re.DOTALL
    )

    # 5. Slide 5+ (Discussion / Proposal Slides) generation & injection
    discussion_slides = data.get("discussionSlides", data.get("appendixSlides", []))
    if discussion_slides:
        disc_slides_html = build_discussion_slides_html(discussion_slides, start_page_num=5)
        # Remove any existing discussion slides in template first
        html = re.sub(r'<!-- ===+\s*PAGE \d+: 方案研讨与议题讨论.*?<div class="slide-footer-num">\d+</div>\s*</section>', '', html, flags=re.DOTALL)
        html = re.sub(r'<section class="slide slide-discussion".*?</section>', '', html, flags=re.DOTALL)
        
        # Insert after slide 4
        html = re.sub(
            r'(<div class="slide-footer-num">4</div>\s*</section>)',
            f'\\1\n\n{disc_slides_html}',
            html,
            flags=re.DOTALL
        )

    # 6. Embed the clean data JSON into script tag for browser dynamic editing
    data_json_str = json.dumps(data, ensure_ascii=False, indent=2)
    # Remove existing script if any
    html = re.sub(r'<script id="weekly-report-data" type="application/json">.*?</script>', '', html, flags=re.DOTALL)
    script_injection = f'''
  <script id="weekly-report-data" type="application/json">
{data_json_str}
  </script>
'''
    html = html.replace("</body>", f"{script_injection}\n</body>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Successfully compiled weekly report HTML: {output_path} (Theme: {theme})")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Weekly Report HTML")
    parser.add_argument("--data", default=None, help="Path to JSON data file")
    parser.add_argument("--output", default="weekly-report.html", help="Path to output HTML file")
    parser.add_argument("--theme", default=None, help="Theme ID (astrazeneca, novartis, bayer, jnj, novo-nordisk, vercel-minimal)")
    parser.add_argument("--check-dates", action="store_true", help="Only validate timeline dates and report issues without generating HTML")
    parser.add_argument("--fix-dates", action="store_true", help="Auto-adjust non-holiday timeline dates to exact Monday-to-Friday")
    parser.add_argument("--strict-dates", action="store_true", help="Fail with non-zero exit code if timeline date validation finds any issue")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    data_file = args.data if args.data else str(base_dir / "examples" / "sample_data.json")
    
    if args.check_dates:
        data = load_json(data_file)
        timeline = data.get("timeline", data.get("slide2_plan", {}))
        project = data.get("project", {})
        issues = validate_timeline_dates(timeline, project, auto_fix=args.fix_dates, strict=args.strict_dates)
        if not issues:
            print("✅ All Work Plan timeline dates strictly conform to Monday-to-Friday and statutory holiday rules.")
        sys.exit(1 if issues and not args.fix_dates else 0)

    generate_report(data_file, args.output, args.theme, auto_fix_dates=args.fix_dates, strict_dates=args.strict_dates)
