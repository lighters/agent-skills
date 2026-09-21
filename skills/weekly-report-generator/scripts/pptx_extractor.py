#!/usr/bin/env python3
"""
PPTX Template Background & Asset Extractor
Extracts slide backgrounds, logos, and corporate color palettes from Microsoft PowerPoint (.pptx) templates.
Part of the weekly-report-generator skill.

Zero third-party pip dependencies (uses Python standard library zipfile, re, xml, base64).
"""

import os
import re
import sys
import base64
import zipfile
import subprocess
import tempfile
from pathlib import Path

def optimize_image_if_possible(img_bytes, filename, max_dim=1920):
    """
    Optimizes large background images (> 1MB) using macOS sips if available.
    Falls back gracefully to raw bytes if sips is not installed.
    """
    if len(img_bytes) < 1024 * 1024:
        return img_bytes, filename

    # Check if sips is available (macOS standard utility)
    try:
        with tempfile.NamedTemporaryFile(suffix='_' + filename, delete=False) as tmp_in:
            tmp_in.write(img_bytes)
            tmp_in_path = tmp_in.name

        tmp_out_path = tmp_in_path + '_opt.jpg'
        cmd = ['sips', '-Z', str(max_dim), tmp_in_path, '-s', 'format', 'jpeg', '-s', 'formatOptions', '88', '--out', tmp_out_path]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and os.path.exists(tmp_out_path) and os.path.getsize(tmp_out_path) > 0:
            with open(tmp_out_path, 'rb') as f:
                opt_bytes = f.read()
            os.remove(tmp_in_path)
            os.remove(tmp_out_path)
            return opt_bytes, 'optimized.jpg'
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.remove(tmp_out_path)
    except Exception:
        pass

    return img_bytes, filename

def extract_pptx_template(pptx_path):
    """
    Parses a .pptx file and extracts:
    - Cover slide background image
    - Content slide background image (e.g. corporate wave/header/footer)
    - Corporate logo
    - Brand color palette (primary, accent, text)
    - Company name / slogan strings
    """
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PPTX file not found: {pptx_path}")

    template_data = {
        "cover_bg_data_url": None,
        "content_bg_data_url": None,
        "logo_data_url": None,
        "colors": {
            "primary": "#0E7CEA",
            "primaryDark": "#0B1411",
            "accent": "#0099FF",
            "accentWarm": "#ED7D31"
        },
        "company_name": "",
        "slogan": "",
        "has_custom_pptx": False
    }

    with zipfile.ZipFile(pptx_path, 'r') as z:
        names = z.namelist()

        # 1. Extract theme color palette from ppt/theme/theme1.xml
        for n in names:
            if n.startswith('ppt/theme/theme') and n.endswith('.xml'):
                xml_text = z.read(n).decode('utf-8', errors='ignore')
                # Find color scheme
                accent1 = re.search(r'<a:accent1>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', xml_text)
                if accent1:
                    template_data["colors"]["primary"] = '#' + accent1.group(1)
                accent2 = re.search(r'<a:accent2>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', xml_text)
                if accent2:
                    template_data["colors"]["accentWarm"] = '#' + accent2.group(1)
                accent5 = re.search(r'<a:accent5>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', xml_text)
                if accent5:
                    template_data["colors"]["accent"] = '#' + accent5.group(1)
                dk2 = re.search(r'<a:dk2>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', xml_text)
                if dk2:
                    template_data["colors"]["primaryDark"] = '#' + dk2.group(1)
                break

        VALID_WEB_IMG_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif')

        def get_img_mime(fn):
            l = fn.lower()
            if l.endswith(('.jpg', '.jpeg')): return 'image/jpeg'
            if l.endswith('.png'): return 'image/png'
            if l.endswith('.svg'): return 'image/svg+xml'
            if l.endswith('.webp'): return 'image/webp'
            if l.endswith('.gif'): return 'image/gif'
            return 'image/png'

        # 2. Map media files and their sizes (only web-compatible raster & vector formats)
        media_files = {}
        for n in names:
            if n.startswith('ppt/media/'):
                base = os.path.basename(n)
                if any(base.lower().endswith(ext) for ext in VALID_WEB_IMG_EXTS):
                    info = z.getinfo(n)
                    if info.file_size > 0:
                        media_files[base] = (n, info.file_size)

        # 3. Parse slideLayouts and rels to identify pictures with precise coordinates
        layout_pics = []
        for n in names:
            if n.startswith('ppt/slideLayouts/slideLayout') and n.endswith('.xml'):
                rels_name = n.replace('ppt/slideLayouts/', 'ppt/slideLayouts/_rels/') + '.rels'
                rels = {}
                if rels_name in names:
                    rel_xml = z.read(rels_name).decode('utf-8', errors='ignore')
                    for m in re.finditer(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rel_xml):
                        rels[m.group(1)] = os.path.basename(m.group(2))

                layout_xml = z.read(n).decode('utf-8', errors='ignore')
                layout_num = int(re.search(r'slideLayout(\d+)\.xml', n).group(1))

                for pic in re.finditer(r'<p:pic>(.*?)</p:pic>', layout_xml):
                    p_txt = pic.group(1)
                    rId = re.findall(r'r:embed="([^"]+)"', p_txt)
                    off_m = re.search(r'<a:off x="(\d+)" y="(\d+)"', p_txt)
                    ext_m = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', p_txt)
                    off = (int(off_m.group(1)), int(off_m.group(2))) if off_m else (0, 0)
                    ext = (int(ext_m.group(1)), int(ext_m.group(2))) if ext_m else (0, 0)

                    for r in rId:
                        target_file = rels.get(r)
                        if target_file and target_file in media_files:
                            layout_pics.append({
                                "layout": layout_num,
                                "file": target_file,
                                "zip_path": media_files[target_file][0],
                                "size": media_files[target_file][1],
                                "off": off,
                                "ext": ext
                            })

        # 4. Identify Corporate Logo:
        # Prioritize SVG vector logos if available (e.g. AstraZeneca Spark)
        svg_logos = [f for f in media_files if f.lower().endswith('.svg')]
        logo_file = None
        if svg_logos:
            logo_file = svg_logos[0]
        else:
            # Score logo candidates by layout recurrence and small dimensions
            logo_cands = [p for p in layout_pics if (0 < p["ext"][0] < 2500000 and 0 < p["ext"][1] < 2500000) or p["size"] < 70000]
            if logo_cands:
                # Count frequency of each file across layouts
                freq = {}
                for p in logo_cands:
                    freq[p["file"]] = freq.get(p["file"], 0) + 1
                # Sort primarily by frequency (most repeated across layouts), then smallest size
                sorted_by_freq = sorted(logo_cands, key=lambda p: (-freq[p["file"]], p["size"]))
                logo_file = sorted_by_freq[0]["file"]
            else:
                pngs = sorted([(b, sz) for b, (zp, sz) in media_files.items() if b.lower().endswith('.png') and sz < 80000], key=lambda x: x[1])
                if pngs:
                    logo_file = pngs[0][0]

        if logo_file and logo_file in media_files:
            logo_bytes = z.read(media_files[logo_file][0])
            mime = get_img_mime(logo_file)
            template_data["logo_data_url"] = f"data:{mime};base64,{base64.b64encode(logo_bytes).decode()}"

        # 5. Identify Cover Background:
        cover_cands = [p for p in layout_pics if p["layout"] == 1 and (p["ext"][0] > 4000000 or p["size"] > 100000) and p["file"] != logo_file]
        if cover_cands:
            cover_cands.sort(key=lambda x: x["size"], reverse=True)
            cover_file = cover_cands[0]["file"]
        else:
            # Check layouts with full slide width (cx >= 8,000,000)
            wide_pics = [p for p in layout_pics if p["ext"][0] >= 8000000 and p["file"] != logo_file]
            if wide_pics:
                wide_pics.sort(key=lambda x: x["size"], reverse=True)
                cover_file = wide_pics[0]["file"]
            else:
                # Fallback to the largest media file excluding logo
                sorted_media = sorted([item for item in media_files.items() if item[0] != logo_file], key=lambda x: x[1][1], reverse=True)
                cover_file = sorted_media[0][0] if sorted_media else None

        if cover_file and cover_file in media_files:
            c_bytes = z.read(media_files[cover_file][0])
            c_bytes, c_filename = optimize_image_if_possible(c_bytes, cover_file)
            mime = get_img_mime(c_filename)
            template_data["cover_bg_data_url"] = f"data:{mime};base64,{base64.b64encode(c_bytes).decode()}"

        # 6. Identify Content Slide Background Graphic:
        content_cands = [
            p for p in layout_pics 
            if p["layout"] > 1 and p["ext"][0] > 7000000 and p["file"] not in [cover_file, logo_file]
        ]
        if content_cands:
            content_cands.sort(key=lambda x: x["size"], reverse=True)
            content_file = content_cands[0]["file"]
        else:
            # Search media files for images between 40KB and 2MB that aren't cover or logo
            candidates = [
                base for base, (zp, sz) in media_files.items()
                if base not in [cover_file, logo_file] and 40000 < sz < 2000000
            ]
            content_file = candidates[0] if candidates else None

        if content_file and content_file in media_files:
            cnt_bytes = z.read(media_files[content_file][0])
            mime = get_img_mime(content_file)
            template_data["content_bg_data_url"] = f"data:{mime};base64,{base64.b64encode(cnt_bytes).decode()}"

        # 7. Extract texts (Company / Slogans)
        for s in ['ppt/slides/slide1.xml', 'ppt/slideLayouts/slideLayout1.xml', 'ppt/slideLayouts/slideLayout3.xml']:
            if s in names:
                txt = z.read(s).decode('utf-8', errors='ignore')
                texts = re.findall(r'<a:t>([^<]+)</a:t>', txt)
                full_str = ' '.join(texts)
                if 'SINOPHARM' in full_str or '国药' in full_str:
                    template_data["company_name"] = "国药控股 / 国药集团"
                elif 'J&J' in full_str or 'Johnson' in full_str or 'JJMT' in full_str:
                    template_data["company_name"] = "Johnson & Johnson / 强生医疗科技"
                elif 'AstraZeneca' in full_str or 'AZ' in full_str:
                    template_data["company_name"] = "AstraZeneca / 阿斯利康"
                for t in texts:
                    if any(w in t for w in ['关爱生命', '呵护健康', '科技引领', '持续创新', '客户至上', '医者智库']):
                        template_data["slogan"] = t.strip()

    template_data["has_custom_pptx"] = bool(template_data["cover_bg_data_url"] or template_data["content_bg_data_url"])
    return template_data

def build_pptx_css_override(template_data):
    """
    Generates CSS overrides to apply the extracted PPTX backgrounds and color palette.
    Ensures high contrast, vector rendering, and clean presentation on custom slides.
    """
    css_rules = []
    colors = template_data.get("colors", {})

    # Brand colors
    if colors.get("primary"):
        css_rules.append(f"--brand-primary: {colors['primary']} !important;")
        css_rules.append(f"--brand-border: {colors['primary']} !important;")
        css_rules.append(f"--brand-table-header: {colors['primary']} !important;")
        css_rules.append(f"--brand-gantt-header: {colors['primary']} !important;")
        css_rules.append(f"--brand-status-header: {colors['primary']} !important;")
    if colors.get("primaryDark"):
        css_rules.append(f"--brand-primary-dark: {colors['primaryDark']} !important;")
        css_rules.append(f"--brand-text-main: {colors['primaryDark']} !important;")
    if colors.get("accent"):
        css_rules.append(f"--brand-accent: {colors['accent']} !important;")
        css_rules.append(f"--brand-accent-sec: {colors['accent']} !important;")
    if colors.get("accentWarm"):
        css_rules.append(f"--brand-holiday: {colors['accentWarm']} !important;")

    # Cover Slide Background
    cover_bg = template_data.get("cover_bg_data_url")
    cover_css = ""
    if cover_bg:
        cover_css = f"""
    body .slide-cover {{
      background-image: linear-gradient(135deg, rgba(8, 20, 36, 0.78) 0%, rgba(14, 40, 70, 0.68) 100%), url('{cover_bg}') !important;
      background-size: cover !important;
      background-position: center !important;
      background-repeat: no-repeat !important;
    }}
    body .slide-cover::before, body .slide-cover::after {{
      display: none !important;
    }}
"""

    # Content Slide Background (Slides 2, 3, 4, 5+)
    content_bg = template_data.get("content_bg_data_url")
    content_css = ""
    if content_bg:
        content_css = f"""
    body .slide:not(.slide-cover) {{
      background-image: url('{content_bg}') !important;
      background-size: 100% 100% !important;
      background-position: center bottom !important;
      background-repeat: no-repeat !important;
      background-color: #ffffff !important;
    }}
    body .slide:not(.slide-cover)::before {{
      display: none !important;
    }}
    body .gantt-container,
    body .deliverables-table-wrapper,
    body .ppt-card,
    body .discussion-card {{
      background: rgba(255, 255, 255, 0.94) !important;
      backdrop-filter: blur(10px) !important;
      -webkit-backdrop-filter: blur(10px) !important;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.05) !important;
    }}
"""

    # Logo Styling
    logo_data = template_data.get("logo_data_url")
    logo_css = ""
    if logo_data:
        logo_css = f"""
    .company-logo-icon, .cover-logo-badge {{
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: transparent !important;
      font-size: 0 !important;
      line-height: 0 !important;
    }}
    .company-logo-icon::before, .cover-logo-badge::before {{
      content: '' !important;
      display: inline-block !important;
      width: 44px !important;
      height: 44px !important;
      background-image: url('{logo_data}') !important;
      background-size: contain !important;
      background-repeat: no-repeat !important;
      background-position: center !important;
    }}
    .cover-logo-badge::before {{
      width: 48px !important;
      height: 48px !important;
    }}
    .company-logo-icon span, .cover-logo-text {{
      display: none !important;
    }}
"""

    style_block = f"""
  <!-- Auto-generated PPTX Custom Template Override -->
  <style id="pptx-template-override">
    :root, body {{
      {chr(10).join('      ' + r for r in css_rules)}
    }}
{cover_css}
{content_css}
{logo_css}
  </style>
"""
    return style_block

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pptx_extractor.py <path_to_template.pptx>")
        sys.exit(1)

    path = sys.argv[1]
    res = extract_pptx_template(path)
    print("✅ Extracted PPTX Template Assets:")
    print(f"  • Brand Colors: {res['colors']}")
    print(f"  • Logo: {'Found (' + str(len(res['logo_data_url'])) + ' chars)' if res['logo_data_url'] else 'None'}")
    print(f"  • Cover Background: {'Found (' + str(len(res['cover_bg_data_url'])) + ' chars)' if res['cover_bg_data_url'] else 'None'}")
    print(f"  • Content Background: {'Found (' + str(len(res['content_bg_data_url'])) + ' chars)' if res['content_bg_data_url'] else 'None'}")
    if res['company_name']:
        print(f"  • Company Name: {res['company_name']}")
    if res['slogan']:
        print(f"  • Corporate Slogan: {res['slogan']}")
