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
import argparse
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

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
    holiday_week_id = next((w["id"] for w in weeks if w.get("isHoliday")), None)
    holiday_name = next((w.get("holidayName", "假期") for w in weeks if w.get("isHoliday")), "假期")
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
            if w_id == holiday_week_id:
                if row_idx == 0:
                    row_cells.append(f'<td rowspan="{len(tasks)}" class="cell-holiday"><div class="holiday-col-text">{holiday_name}</div></td>')
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
            
            # Check "We are here" indicator (positioned on the last row under current week)
            if row_idx == len(tasks) - 1 and w_id == current_week_id:
                cell_content += f'''
                <div class="we-are-here-indicator" style="left: -140px; bottom: 2px;">
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
    for w in weeks:
        w_id = w.get("id", "")
        w_name = w.get("name", w_id)
        w_date = w.get("dates", "")
        extra_style = ""
        if w.get("isHoliday"):
            extra_style = ' style="background-color: #d97706;"'
        elif w.get("isCurrent"):
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

def generate_report(data_path, output_path, theme="classic-navy"):
    base_dir = Path(__file__).resolve().parent.parent
    template_path = base_dir / "templates" / "weekly_report_template.html"
    
    data = load_json(data_path)
    if not theme:
        theme = data.get("theme", "astrazeneca")
    data["theme"] = theme

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Apply theme to body and select
    html = html.replace('body data-theme="classic-navy"', f'body data-theme="{theme}"')
    html = html.replace('body data-theme="astrazeneca"', f'body data-theme="{theme}"')
    html = re.sub(r'<option value="' + re.escape(theme) + r'">', f'<option value="{theme}" selected>', html)

    # Get sub-sections
    company = data.get("company", {})
    project = data.get("project", {})
    timeline = data.get("timeline", data.get("slide2_plan", {}))
    deliverables = data.get("deliverables", data.get("slide3_deliverables", {}))
    this_week = data.get("thisWeek", data.get("slide4_tasks", {}))

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
    deliv_tbody = build_deliverables_tbody_html(deliverables)
    html = re.sub(
        r'<table class="deliverables-table">\s*<thead>.*?</thead>\s*<tbody>.*?</tbody>\s*</table>',
        f'<table class="deliverables-table">\n          <thead>\n            <tr>\n              <th class="col-m-name">Milestone</th>\n              <th class="col-m-prog">Progress</th>\n              <th class="col-m-date">Date</th>\n              <th class="col-m-stat">Status</th>\n              <th class="col-m-indi">Indicator</th>\n            </tr>\n          </thead>\n          <tbody>\n{deliv_tbody}\n          </tbody>\n        </table>',
        html,
        flags=re.DOTALL
    )

    # 4. Slide 4 (This week / Task Management) generation
    tm_comps = build_task_mgmt_components(this_week)
    
    # Subtitle
    html = re.sub(
        r'<div class="slide-subtitle" style="font-size: 18px; margin-top: 2px;">.*?</div>',
        f'<div class="slide-subtitle" style="font-size: 18px; margin-top: 2px;">{this_week.get("subtitle", "Week 16")}</div>',
        html
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

    # 5. Embed the clean data JSON into script tag for browser dynamic editing
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
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    data_file = args.data if args.data else str(base_dir / "examples" / "sample_data.json")
    
    generate_report(data_file, args.output, args.theme)
