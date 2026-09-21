#!/usr/bin/env python3
"""
PPTX Template Background & Asset Extractor
Extracts slide backgrounds, logos, and corporate color palettes from Microsoft PowerPoint (.pptx) templates.
Part of the weekly-report-generator skill.

Features:
- Cover slide extraction with slide body text stripped out (retains authentic brand backgrounds, shapes, logos).
- Intelligent content slide identification: finds pure/solid content layouts (e.g. JNJ slides 24/25, AZ slide 3, 国控 slide 5).
- Automatic lightness detection for covers (light vs. dark/vibrant cover typography).
- Zero third-party pip dependencies (uses Python standard library zipfile, re, xml, base64, struct, subprocess).
"""

import os
import re
import sys
import base64
import zipfile
import subprocess
import tempfile
import struct
from pathlib import Path

def optimize_image_if_possible(img_bytes, filename, max_dim=1920, target_format='jpeg', quality='90'):
    """
    Optimizes background images using macOS sips if available.
    Converts to high-quality compressed JPEG (or PNG) to keep HTML files light and responsive.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='_' + filename, delete=False) as tmp_in:
            tmp_in.write(img_bytes)
            tmp_in_path = tmp_in.name

        ext = '.jpg' if target_format == 'jpeg' else '.png'
        tmp_out_path = tmp_in_path + '_opt' + ext
        cmd = ['sips', '-Z', str(max_dim), tmp_in_path, '-s', 'format', target_format]
        if target_format == 'jpeg':
            cmd.extend(['-s', 'formatOptions', str(quality)])
        cmd.extend(['--out', tmp_out_path])

        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and os.path.exists(tmp_out_path) and os.path.getsize(tmp_out_path) > 0:
            with open(tmp_out_path, 'rb') as f:
                opt_bytes = f.read()
            os.remove(tmp_in_path)
            os.remove(tmp_out_path)
            mime = 'image/jpeg' if target_format == 'jpeg' else 'image/png'
            return opt_bytes, mime
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.remove(tmp_out_path)
    except Exception:
        pass

    mime = 'image/png' if filename.lower().endswith('.png') else 'image/jpeg'
    return img_bytes, mime

def detect_image_brightness(img_bytes):
    """
    Samples brightness of the title area (around x=20%, y=35%).
    Returns perceived brightness (0.0 to 255.0).
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp_in:
            tmp_in.write(img_bytes)
            tmp_in_path = tmp_in.name
        tmp_bmp = tmp_in_path + '.bmp'
        subprocess.run(['sips', '-z', '20', '20', '-s', 'format', 'bmp', tmp_in_path, '--out', tmp_bmp], capture_output=True)
        if os.path.exists(tmp_bmp) and os.path.getsize(tmp_bmp) > 0:
            with open(tmp_bmp, 'rb') as f:
                data = f.read()
            os.remove(tmp_in_path)
            os.remove(tmp_bmp)
            offset = struct.unpack_from('<I', data, 10)[0]
            # Sample around left-center (row 10, col 4 of 20x20)
            idx = offset + (10 * 20 + 4) * 3
            if idx + 2 < len(data):
                b, g, r = data[idx], data[idx+1], data[idx+2]
                return 0.299 * r + 0.587 * g + 0.114 * b
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)
    except Exception:
        pass
    return 128.0

def render_pptx_clean_slide(pptx_path, target_slide_num=1, strip_text=True):
    """
    Renders a specific slide from PPTX with slide body text stripped out,
    leaving clean background, layout shapes, branding elements.
    Uses macOS qlmanage if available.
    """
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_pptx = os.path.join(tmp_dir, 'slide.pptx')
            with zipfile.ZipFile(pptx_path, 'r') as zin:
                entries = {item.filename: zin.read(item.filename) for item in zin.infolist()}

            target_slide_name = f'ppt/slides/slide{target_slide_num}.xml'
            target_rels_name = f'ppt/slides/_rels/slide{target_slide_num}.xml.rels'

            if target_slide_name in entries:
                xml = entries[target_slide_name].decode('utf-8', errors='ignore')
                if strip_text:
                    # Strip shapes with <a:t> (body/title text) while preserving non-text graphics
                    clean_xml = re.sub(r'<p:sp\b[^>]*>.*?</p:sp>', lambda m: '' if '<a:t>' in m.group(0) else m.group(0), xml, flags=re.DOTALL)
                    entries['ppt/slides/slide1.xml'] = clean_xml.encode('utf-8')
                else:
                    entries['ppt/slides/slide1.xml'] = entries[target_slide_name]

            if target_rels_name in entries:
                entries['ppt/slides/_rels/slide1.xml.rels'] = entries[target_rels_name]

            if strip_text:
                for k, v in list(entries.items()):
                    if k.startswith('ppt/slideLayouts/slideLayout') and k.endswith('.xml'):
                        l_xml = v.decode('utf-8', errors='ignore')
                        l_clean = re.sub(r'<p:sp\b[^>]*>.*?</p:sp>', lambda m: '' if '<a:t>' in m.group(0) else m.group(0), l_xml, flags=re.DOTALL)
                        entries[k] = l_clean.encode('utf-8')

            with zipfile.ZipFile(tmp_pptx, 'w') as zout:
                for fname, data in entries.items():
                    zout.writestr(fname, data)

            res = subprocess.run(['qlmanage', '-t', '-s', '1920', '-o', tmp_dir, tmp_pptx], capture_output=True)
            out_png = os.path.join(tmp_dir, 'slide.pptx.png')
            if os.path.exists(out_png) and os.path.getsize(out_png) > 0:
                with open(out_png, 'rb') as f:
                    raw_bytes = f.read()
                opt_bytes, mime = optimize_image_if_possible(raw_bytes, 'slide.png', max_dim=1920, target_format='jpeg', quality='90')
                return opt_bytes, mime
    except Exception as e:
        pass
    return None, None

def find_best_content_slide_num(pptx_path):
    """
    Identifies the ideal clean/solid content slide from PPTX.
    Looks for standard content layouts (body, title only, columns, wht) without inserted photos or section breaks.
    Returns the 1-indexed slide number.
    """
    with zipfile.ZipFile(pptx_path, 'r') as z:
        slides = sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml', n)],
                        key=lambda x: int(re.search(r'\d+', x).group(0)))
        candidates = []
        for s in slides:
            s_num = int(re.search(r'\d+', s).group(0))
            if s_num == 1:
                continue

            s_xml = z.read(s).decode('utf-8', errors='ignore')
            pics = re.findall(r'<p:pic>.*?</p:pic>', s_xml)
            if len(pics) > 0:
                # Skip slides with inserted user photos or charts
                continue

            rels_name = f'ppt/slides/_rels/slide{s_num}.xml.rels'
            if rels_name not in z.namelist():
                continue
            rel_xml = z.read(rels_name).decode('utf-8', errors='ignore')
            l_m = re.search(r'Target=\"\.\./slideLayouts/(slideLayout\d+\.xml)\"', rel_xml)
            if not l_m:
                continue
            layout_file = 'ppt/slideLayouts/' + l_m.group(1)
            if layout_file not in z.namelist():
                continue
            layout_xml = z.read(layout_file).decode('utf-8', errors='ignore')
            name_m = re.search(r'<p:cSld[^>]*name=\"([^\"]+)\"', layout_xml)
            layout_name = name_m.group(1).lower() if name_m else ''

            texts = [t.lower() for t in re.findall(r'<a:t>([^<]+)</a:t>', s_xml)]
            full_text = ' '.join(texts)

            # Skip table of contents, agendas, section dividers, thank you slides
            if any(w in full_text for w in ['目录', 'contents', 'thanks', 'thank you', 'end', 'agenda', 'appendix']):
                continue
            if any(w in layout_name for w in ['divider', 'section', 'end', 'quote', 'cover', 'dark', 'mulberry']):
                continue
            if re.search(r'0\d\s*/\s*0\d', full_text):
                continue

            score = 0
            if any(w in layout_name for w in ['wht', 'white', 'columns', 'title only', 'content', 'body']):
                score += 50
            if '自定义' in layout_name:
                score += 30
            # Prefer layouts with decorative master graphics (e.g. bottom waves)
            l_pics = re.findall(r'<p:pic>.*?</p:pic>', layout_xml)
            score += len(l_pics) * 10

            candidates.append((s_num, score, layout_name))

        candidates.sort(key=lambda x: -x[1])
        return candidates[0][0] if candidates else 2

def detect_layout_logo_positions(pptx_path, content_slide_num=None):
    """
    Detects if logos or brand emblems are embedded in layout margins
    so that HTML content can avoid colliding with them.
    - cover_has_logo_top_left: True if cover has logo/emblem at top-left
    - content_has_logo_top_right: True if content slide has logo at top-right
    """
    cover_has_logo_top_left = False
    content_has_logo_top_right = False
    try:
        with zipfile.ZipFile(pptx_path, 'r') as z:
            names = z.namelist()
            # Check cover slide & layout
            for s in ['ppt/slides/slide1.xml', 'ppt/slideLayouts/slideLayout1.xml']:
                if s in names:
                    txt = z.read(s).decode('utf-8', errors='ignore')
                    for pic in re.finditer(r'<p:pic>.*?</p:pic>', txt, flags=re.DOTALL):
                        p = pic.group(0)
                        off_m = re.search(r'<a:off x="(\d+)" y="(\d+)"', p)
                        ext_m = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', p)
                        if off_m and ext_m:
                            x, y = int(off_m.group(1)) // 9525, int(off_m.group(2)) // 9525
                            cx, cy = int(ext_m.group(1)) // 9525, int(ext_m.group(2)) // 9525
                            if x < 150 and y < 150 and cx < 400 and cy < 200:
                                cover_has_logo_top_left = True

            # Check content slide & layout
            if content_slide_num:
                targets = [f'ppt/slides/slide{content_slide_num}.xml']
                rels_name = f'ppt/slides/_rels/slide{content_slide_num}.xml.rels'
                if rels_name in names:
                    rel_xml = z.read(rels_name).decode('utf-8', errors='ignore')
                    l_m = re.search(r'Target="\.\./slideLayouts/(slideLayout\d+\.xml)"', rel_xml)
                    if l_m:
                        targets.append('ppt/slideLayouts/' + l_m.group(1))
                for s in targets:
                    if s in names:
                        txt = z.read(s).decode('utf-8', errors='ignore')
                        for pic in re.finditer(r'<p:pic>.*?</p:pic>', txt, flags=re.DOTALL):
                            p = pic.group(0)
                            off_m = re.search(r'<a:off x="(\d+)" y="(\d+)"', p)
                            ext_m = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', p)
                            if off_m and ext_m:
                                x, y = int(off_m.group(1)) // 9525, int(off_m.group(2)) // 9525
                                cx, cy = int(ext_m.group(1)) // 9525, int(ext_m.group(2)) // 9525
                                if x > 900 and y < 150 and cx < 300 and cy < 200:
                                    content_has_logo_top_right = True
    except Exception:
        pass
    return cover_has_logo_top_left, content_has_logo_top_right

def extract_pptx_template(pptx_path):
    """
    Parses a .pptx file and extracts:
    - Cover slide background image (clean render or layout background)
    - Content slide background image (clean render of solid content slide or layout wave)
    - Corporate logo
    - Brand color palette (primary, accent, text)
    - Company name / slogan strings
    - Brightness metadata for cover typography
    """
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PPTX file not found: {pptx_path}")

    template_data = {
        "cover_bg_data_url": None,
        "content_bg_data_url": None,
        "logo_data_url": None,
        "is_light_cover": False,
        "cover_has_logo_top_left": False,
        "content_has_logo_top_right": False,
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

        # 1. Extract theme color palette from ppt/theme/theme*.xml
        for n in names:
            if n.startswith('ppt/theme/theme') and n.endswith('.xml'):
                xml_text = z.read(n).decode('utf-8', errors='ignore')
                accent1 = re.search(r'<a:accent1>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', xml_text)
                if accent1:
                    template_data["colors"]["primary"] = '#' + accent1.group(1)
                accent2 = re.search(r'<a:accent2>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', xml_text)
                if accent2:
                    template_data["colors"]["accentWarm"] = '#' + accent2.group(1)
                accent3 = re.search(r'<a:accent3>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', xml_text)
                accent5 = re.search(r'<a:accent5>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', xml_text)
                if accent5:
                    template_data["colors"]["accent"] = '#' + accent5.group(1)
                elif accent2:
                    template_data["colors"]["accent"] = '#' + accent2.group(1)
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

        # 2. Map media files
        media_files = {}
        for n in names:
            if n.startswith('ppt/media/'):
                base = os.path.basename(n)
                if any(base.lower().endswith(ext) for ext in VALID_WEB_IMG_EXTS):
                    info = z.getinfo(n)
                    if info.file_size > 0:
                        media_files[base] = (n, info.file_size)

        # 3. Parse slideLayouts and rels
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

        # 4. Identify Corporate Logo (prioritize SVG vector logos like AstraZeneca Spark)
        svg_logos = [f for f in media_files if f.lower().endswith('.svg')]
        logo_file = None
        if svg_logos:
            logo_file = svg_logos[0]
        else:
            logo_cands = [p for p in layout_pics if (0 < p["ext"][0] < 2500000 and 0 < p["ext"][1] < 2500000) or p["size"] < 70000]
            if logo_cands:
                freq = {}
                for p in logo_cands:
                    freq[p["file"]] = freq.get(p["file"], 0) + 1
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

        # 5. Extract Cover Slide Background:
        # First attempt high-fidelity clean slide 1 rendering (with slide body text stripped out)
        cov_bytes, cov_mime = render_pptx_clean_slide(pptx_path, 1, strip_text=True)
        if cov_bytes:
            template_data["cover_bg_data_url"] = f"data:{cov_mime};base64,{base64.b64encode(cov_bytes).decode()}"
            bri = detect_image_brightness(cov_bytes)
            template_data["is_light_cover"] = (bri > 180.0)
        else:
            # Fallback: identify cover image from layout
            cover_cands = [p for p in layout_pics if p["layout"] == 1 and (p["ext"][0] > 4000000 or p["size"] > 100000) and p["file"] != logo_file]
            cover_file = cover_cands[0]["file"] if cover_cands else None
            if cover_file and cover_file in media_files:
                c_bytes = z.read(media_files[cover_file][0])
                c_bytes, c_mime = optimize_image_if_possible(c_bytes, cover_file)
                template_data["cover_bg_data_url"] = f"data:{c_mime};base64,{base64.b64encode(c_bytes).decode()}"

        # 6. Extract Content Slide Background:
        # Identify the best clean solid content slide (e.g. JNJ 24/25, AZ 3, 国控 5)
        best_content_num = find_best_content_slide_num(pptx_path)
        cov_tl, cnt_tr = detect_layout_logo_positions(pptx_path, best_content_num)
        template_data["cover_has_logo_top_left"] = cov_tl
        template_data["content_has_logo_top_right"] = cnt_tr

        cnt_bytes, cnt_mime = render_pptx_clean_slide(pptx_path, best_content_num, strip_text=True)
        if cnt_bytes:
            template_data["content_bg_data_url"] = f"data:{cnt_mime};base64,{base64.b64encode(cnt_bytes).decode()}"
        else:
            # Fallback: check if content layout contains decorative footer picture
            content_cands = [
                p for p in layout_pics 
                if p["layout"] > 1 and p["ext"][0] > 7000000 and p["file"] not in [logo_file]
            ]
            if content_cands:
                content_cands.sort(key=lambda x: x["size"], reverse=True)
                content_file = content_cands[0]["file"]
                cnt_bytes = z.read(media_files[content_file][0])
                cnt_mime = get_img_mime(content_file)
                template_data["content_bg_data_url"] = f"data:{cnt_mime};base64,{base64.b64encode(cnt_bytes).decode()}"
            else:
                template_data["content_bg_data_url"] = None

        # 7. Extract texts (Company / Slogans)
        for s in ['ppt/slides/slide1.xml', 'ppt/slideLayouts/slideLayout1.xml', 'ppt/slideLayouts/slideLayout3.xml']:
            if s in names:
                txt = z.read(s).decode('utf-8', errors='ignore')
                texts = re.findall(r'<a:t>([^<]+)</a:t>', txt)
                full_str = ' '.join(texts)
                if 'SINOPHARM' in full_str or '国药' in full_str:
                    template_data["company_name"] = "国药控股 / 国药集团"
                    template_data["colors"]["primary"] = "#004ea2"
                    template_data["colors"]["primaryDark"] = "#002b66"
                    template_data["colors"]["accent"] = "#0092EE"
                elif 'J&J' in full_str or 'Johnson' in full_str or 'JJMT' in full_str:
                    template_data["company_name"] = "Johnson & Johnson / 强生医疗科技"
                    template_data["colors"]["primary"] = "#C8102E"
                    template_data["colors"]["primaryDark"] = "#A00D1E"
                    template_data["colors"]["accent"] = "#FF8200"
                    template_data["colors"]["accentWarm"] = "#1E22AA"
                elif 'AstraZeneca' in full_str or 'AZ' in full_str:
                    template_data["company_name"] = "AstraZeneca / 阿斯利康"
                    template_data["colors"]["primary"] = "#830051"
                    template_data["colors"]["primaryDark"] = "#003865"
                    template_data["colors"]["accent"] = "#F0AB00"
                    template_data["colors"]["accentWarm"] = "#D0006F"

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

    # Cover Slide Background & Typography Handling
    cover_bg = template_data.get("cover_bg_data_url")
    is_light = template_data.get("is_light_cover", False)
    cov_has_logo_tl = template_data.get("cover_has_logo_top_left", False)
    cnt_has_logo_tr = template_data.get("content_has_logo_top_right", False)
    cover_css = ""

    if cover_bg:
        if is_light:
            # Light cover (e.g. AstraZeneca white cover): Dark plum/navy typography, translucent light cards
            primary_col = colors.get('primary', '#830051')
            dark_col = colors.get('primaryDark', '#003865')
            logo_tl_css = """
    body .slide-cover .company-badge {
      visibility: hidden !important;
    }
    body .slide-cover .cover-center-content {
      margin-top: 56px !important;
    }
""" if cov_has_logo_tl else ""
            cover_css = f"""
    body .slide-cover {{
      background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0) 100%), url('{cover_bg}') !important;
      background-size: cover !important;
      background-position: center !important;
      background-repeat: no-repeat !important;
      color: {dark_col} !important;
    }}
    body .slide-cover::before, body .slide-cover::after {{
      display: none !important;
    }}
    body .slide-cover .company-name,
    body .slide-cover .company-dept,
    body .slide-cover .cover-sub-title,
    body .slide-cover .cover-project-title {{
      color: {dark_col} !important;
      -webkit-text-fill-color: {dark_col} !important;
    }}
    body .slide-cover .cover-main-title {{
      color: {primary_col} !important;
      background: transparent !important;
      -webkit-background-clip: border-box !important;
      background-clip: border-box !important;
      -webkit-text-fill-color: {primary_col} !important;
      text-shadow: none !important;
    }}
    body .slide-cover .cover-tag {{
      background: rgba(131, 0, 81, 0.08) !important;
      color: {primary_col} !important;
      border-color: rgba(131, 0, 81, 0.25) !important;
    }}
    body .slide-cover .cover-period-pill {{
      background: rgba(0, 56, 101, 0.08) !important;
      color: {dark_col} !important;
      border-color: rgba(0, 56, 101, 0.2) !important;
    }}
    body .slide-cover .meta-card,
    body .slide-cover .cover-stat-card {{
      background: rgba(255, 255, 255, 0.90) !important;
      border: 1px solid rgba(0, 56, 101, 0.15) !important;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.06) !important;
      backdrop-filter: blur(10px) !important;
    }}
    body .slide-cover .meta-value,
    body .slide-cover .stat-card-val {{
      color: {dark_col} !important;
    }}
    body .slide-cover .meta-label,
    body .slide-cover .stat-card-label {{
      color: #64748b !important;
    }}
{logo_tl_css}"""
        else:
            # Dark/Vibrant cover (e.g. JNJ bold red, Sinopharm blue): Minimal neutral darkening vignette
            logo_tl_css = """
    body .slide-cover .company-logo-icon {
      display: none !important;
    }
    body .slide-cover .company-info-text {
      margin-left: 55px !important;
    }
""" if cov_has_logo_tl else ""
            cover_css = f"""
    body .slide-cover {{
      background-image: linear-gradient(135deg, rgba(0, 0, 0, 0.04) 0%, rgba(0, 0, 0, 0.12) 100%), url('{cover_bg}') !important;
      background-size: cover !important;
      background-position: center !important;
      background-repeat: no-repeat !important;
      color: #ffffff !important;
    }}
    body .slide-cover::before, body .slide-cover::after {{
      display: none !important;
    }}
    body .slide-cover .cover-main-title {{
      color: #ffffff !important;
      background: none !important;
      -webkit-background-clip: border-box !important;
      background-clip: border-box !important;
      -webkit-text-fill-color: #ffffff !important;
    }}
    body .slide-cover .cover-sub-title {{
      color: rgba(255, 255, 255, 0.95) !important;
    }}
    body .slide-cover .meta-card,
    body .slide-cover .cover-stat-card {{
      background: rgba(0, 0, 0, 0.24) !important;
      border: 1px solid rgba(255, 255, 255, 0.25) !important;
      backdrop-filter: blur(10px) !important;
    }}
    body .slide-cover .meta-value,
    body .slide-cover .stat-card-val {{
      color: #ffffff !important;
    }}
    body .slide-cover .meta-label,
    body .slide-cover .stat-card-label {{
      color: rgba(255, 255, 255, 0.82) !important;
    }}
{logo_tl_css}"""

    # Content Slide Background (Slides 2, 3, 4, 5+)
    content_bg = template_data.get("content_bg_data_url")
    cnt_logo_tr_css = """
    body .slide:not(.slide-cover) .slide-header {
      padding-right: 90px !important;
    }
    body .slide:not(.slide-cover) .gantt-legend,
    body .slide:not(.slide-cover) .status-summary-pills {
      margin-right: 90px !important;
    }
""" if cnt_has_logo_tr else ""
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
{cnt_logo_tr_css}"""
    else:
        content_css = f"""
    body .slide:not(.slide-cover) {{
      background-color: #ffffff !important;
      background-image: none !important;
    }}
    body .slide:not(.slide-cover)::before {{
      display: none !important;
    }}
{cnt_logo_tr_css}"""

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
    print(f"  • Is Light Cover: {res['is_light_cover']}")
    print(f"  • Cover Logo Top-Left: {res.get('cover_has_logo_top_left', False)}")
    print(f"  • Content Logo Top-Right: {res.get('content_has_logo_top_right', False)}")
    print(f"  • Logo: {'Found (' + str(len(res['logo_data_url'])) + ' chars)' if res['logo_data_url'] else 'None'}")
    print(f"  • Cover Background: {'Found (' + str(len(res['cover_bg_data_url'])) + ' chars)' if res['cover_bg_data_url'] else 'None'}")
    print(f"  • Content Background: {'Found (' + str(len(res['content_bg_data_url'])) + ' chars)' if res['content_bg_data_url'] else 'None'}")
    if res['company_name']:
        print(f"  • Company Name: {res['company_name']}")
    if res['slogan']:
        print(f"  • Corporate Slogan: {res['slogan']}")
