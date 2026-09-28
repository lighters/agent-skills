"""
End-to-end check of the client-side renderer: generate a report, let headless Chrome run
the template JS, and inspect the resulting DOM. Skipped when no Chrome/Chromium is found.
"""
import contextlib
import io
import re
import subprocess
import sys
import unittest

from helpers import TempDirMixin, minimal_data
import generate_report
from export_pdf import find_chrome_binary

CHROME = find_chrome_binary()
XSS = '<img src=x onerror=alert(1)></td></tr>'


def slide(dom, n):
    m = re.search(rf'<section[^>]*id="slide{n}".*?</section>', dom, re.S)
    return m.group(0) if m else ""


@unittest.skipUnless(CHROME, "Chrome/Chromium not installed")
class RenderTests(TempDirMixin, unittest.TestCase):
    def render(self, data):
        html = self.tmp / "report.html"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            generate_report.generate_report(str(self.write_json(data)), str(html))
        cmd = [CHROME, "--headless", "--disable-gpu", "--virtual-time-budget=3000", "--dump-dom", html.as_uri()]
        if sys.platform.startswith("linux"):
            cmd.insert(1, "--no-sandbox")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def test_renders_data_with_defaults_instead_of_sample(self):
        data = minimal_data()
        data["project"].update(overallStatus="good", confidential="INTERNAL ONLY", projectCode="P-1")
        dom = self.render(data)
        cover = slide(dom, 1)
        self.assertIn("Test Project", cover)
        self.assertIn("INTERNAL ONLY", cover)
        self.assertIn("如期进行", cover)
        self.assertIn("P-1", cover)
        self.assertIn("企业数字化创新交付中心", cover)  # neutral default, not the template sample
        for n in (1, 2, 3, 4):
            self.assertNotIn("AstraZeneca", slide(dom, n))
        self.assertIn('class="col-task">Build</td>', slide(dom, 2))
        self.assertIn('<title>项目周报 | Weekly Report</title>', dom)

    def test_user_content_is_escaped(self):
        data = minimal_data()
        data["timeline"]["tasks"][0]["task"] = XSS
        data["deliverables"]["items"][0]["milestone"] = XSS
        data["thisWeek"]["previousTasks"][0]["content"] = XSS
        data["project"]["title"] = XSS
        dom = self.render(data)
        slides = "".join(slide(dom, n) for n in (1, 2, 3, 4))
        self.assertNotIn("<img src=", slides)
        self.assertEqual(slides.count("&lt;img src=x onerror=alert(1)&gt;"), 4)

    def test_status_aliases_and_discussion_slides(self):
        data = minimal_data(discussionSlides=[
            {"title": "Option review", "layout": "table", "table": {"headers": ["A"], "rows": [["1"]]}},
            {"title": "Agenda", "layout": "agenda", "sections": [{"title": "S", "content": "C"}]},
        ])
        data["deliverables"]["items"][0].update(status="active", risk="high")
        dom = self.render(data)
        self.assertIn('status-pill ongoing">active</span>', slide(dom, 3))
        self.assertIn("dot-risk", slide(dom, 3))
        self.assertIn("Option review", slide(dom, 5))
        self.assertIn("Agenda", slide(dom, 6))


if __name__ == "__main__":
    unittest.main()
