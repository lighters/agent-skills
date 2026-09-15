#!/usr/bin/env python3
"""
Weekly Report PDF Exporter
Uses Google Chrome headless mode to export weekly report HTML to presentation landscape PDF.
Part of the weekly-report-generator Antigravity skill.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def find_chrome_binary():
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "google-chrome",
        "chromium",
        "google-chrome-stable"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        # check if in PATH
        result = subprocess.run(f"which {c} 2>/dev/null", shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return None

def export_to_pdf(html_path, pdf_path):
    chrome_bin = find_chrome_binary()
    if not chrome_bin:
        raise RuntimeError("Google Chrome binary not found. Please ensure Chrome is installed.")
        
    html_abs = str(Path(html_path).resolve())
    pdf_abs = str(Path(pdf_path).resolve())

    cmd = [
        chrome_bin,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_abs}",
        html_abs
    ]
    
    print(f"📄 Exporting {html_abs} to {pdf_abs} using Chrome headless...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Warning: Chrome returned code {res.returncode}: {res.stderr}")
        
    if os.path.exists(pdf_abs) and os.path.getsize(pdf_abs) > 0:
        size_kb = os.path.getsize(pdf_abs) / 1024
        print(f"✅ Successfully exported PDF: {pdf_abs} ({size_kb:.1f} KB)")
        return pdf_abs
    else:
        raise RuntimeError(f"Failed to generate PDF at {pdf_abs}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Weekly Report HTML to PDF")
    parser.add_argument("--input", default="weekly-report.html", help="Path to input HTML file")
    parser.add_argument("--output", default="weekly-report.pdf", help="Path to output PDF file")
    args = parser.parse_args()

    export_to_pdf(args.input, args.output)
