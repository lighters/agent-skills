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

try:
    from pptx_extractor import extract_pptx_template, build_pptx_css_override
except ImportError:
    from .pptx_extractor import extract_pptx_template, build_pptx_css_override

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

def load_theme_ids(template_html):
    """Theme ids that have a [data-theme="..."] CSS block in the template."""
    return list(dict.fromkeys(re.findall(r'\[data-theme="([\w-]+)"\]', template_html)))

def generate_report(data_path, output_path, theme=None, pptx_path=None, auto_fix_dates=False, strict_dates=False):
    """
    Builds the standalone report HTML. All slide content is rendered client-side by the
    template's renderAll() from the embedded #weekly-report-data JSON (also used by headless
    Chrome for PDF export), so this only validates data, applies theme/PPTX styling and
    embeds the JSON.
    """
    base_dir = Path(__file__).resolve().parent.parent
    template_path = base_dir / "templates" / "weekly_report_template.html"

    data = load_json(data_path)
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    theme = theme or data.get("theme") or "astrazeneca"
    theme_ids = load_theme_ids(html)
    if theme not in theme_ids:
        raise ValueError(f"Unknown theme '{theme}'. Available: {', '.join(theme_ids)}")
    data["theme"] = theme

    # Validate work plan timeline dates
    timeline = data.get("timeline", data.get("slide2_plan", {}))
    validate_timeline_dates(timeline, data.get("project", {}), auto_fix=auto_fix_dates, strict=strict_dates)

    # Apply PPTX custom template override if provided
    if pptx_path and not os.path.isfile(pptx_path):
        raise FileNotFoundError(f"PPTX template not found: {pptx_path}")
    if pptx_path:
        print(f"📦 Extracting corporate template assets from PPTX: {pptx_path}...")
        pptx_data = extract_pptx_template(pptx_path)
        pptx_css = build_pptx_css_override(pptx_data)
        html = html.replace("</head>", f"{pptx_css}\n</head>", 1)

        company = data.setdefault("company", {})
        if pptx_data.get("logo_data_url"):
            company["logoDataUrl"] = pptx_data["logo_data_url"]
        # Company name / slogan from PPTX only when not set in JSON
        if pptx_data.get("company_name") and not company.get("name"):
            company["name"] = pptx_data["company_name"]
        if pptx_data.get("slogan") and not company.get("department"):
            company["department"] = pptx_data["slogan"]

        # Stored in data so client-side re-rendering retains customPptx info
        data["customPptx"] = {
            "colors": pptx_data.get("colors", {}),
            "coverBgDataUrl": pptx_data.get("cover_bg_data_url"),
            "contentBgDataUrl": pptx_data.get("content_bg_data_url"),
            "logoDataUrl": pptx_data.get("logo_data_url"),
            "companyName": pptx_data.get("company_name", ""),
            "slogan": pptx_data.get("slogan", ""),
            "isLightCover": pptx_data.get("is_light_cover", False),
            "coverHasLogoTopLeft": pptx_data.get("cover_has_logo_top_left", False),
            "contentHasLogoTopRight": pptx_data.get("content_has_logo_top_right", False)
        }

    # Initial theme on <body> and the theme <select> (avoids a flash before JS runs)
    html = re.sub(r'<body data-theme="[\w-]+"', f'<body data-theme="{theme}"', html, count=1)
    html = html.replace(f'<option value="{theme}">', f'<option value="{theme}" selected>', 1)

    # Embed the data JSON; escape "</" so values like "</script>" cannot terminate the block early
    data_json_str = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    html = re.sub(r'<script id="weekly-report-data" type="application/json">.*?</script>', '', html, flags=re.DOTALL)
    script_injection = f'''
  <script id="weekly-report-data" type="application/json">
{data_json_str}
  </script>
'''
    head, body_close, tail = html.rpartition("</body>")
    html = head + script_injection + "\n" + body_close + tail

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Successfully compiled weekly report HTML: {output_path} (Theme: {theme})")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Weekly Report HTML")
    parser.add_argument("--data", default=None, help="Path to JSON data file")
    parser.add_argument("--output", default="weekly-report.html", help="Path to output HTML file")
    parser.add_argument("--theme", default=None, help="Theme ID (astrazeneca/classic-navy, novartis, bayer, jnj, novo-nordisk, wukong-green, vercel-minimal); defaults to the JSON 'theme' field")
    parser.add_argument("--pptx", "--pptx-template", dest="pptx", default=None, help="Path to PowerPoint (.pptx) template file to extract backgrounds, theme colors, and logo from")
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

    try:
        generate_report(data_file, args.output, args.theme, pptx_path=args.pptx, auto_fix_dates=args.fix_dates, strict_dates=args.strict_dates)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
