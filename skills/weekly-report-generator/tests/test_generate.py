import contextlib
import io
import json
import re
import subprocess
import sys
import unittest
from unittest import mock

from helpers import SCRIPTS_DIR, TempDirMixin, build_pptx, minimal_data
import generate_report
import pptx_extractor


def embedded_data(html):
    m = re.search(r'<script id="weekly-report-data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1))


class GenerateTests(TempDirMixin, unittest.TestCase):
    def generate(self, data, **kwargs):
        out = self.tmp / "out.html"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            generate_report.generate_report(str(self.write_json(data)), str(out), **kwargs)
        return out.read_text(encoding="utf-8")

    def test_embeds_data_once_and_sets_theme(self):
        html = self.generate(minimal_data(theme="novartis"))
        self.assertEqual(html.count('id="weekly-report-data"'), 1)
        self.assertIn('<body data-theme="novartis"', html)
        self.assertIn('<option value="novartis" selected>', html)
        self.assertEqual(embedded_data(html)["project"]["title"], "Test Project")

    def test_cli_theme_overrides_data(self):
        html = self.generate(minimal_data(theme="novartis"), theme="bayer")
        self.assertEqual(embedded_data(html)["theme"], "bayer")

    def test_script_breakout_is_escaped(self):
        data = minimal_data()
        data["thisWeek"]["previousTasks"][0]["content"] = '</script><script>alert(1)</script> \\1'
        html = self.generate(data)
        self.assertNotIn("</script><script>alert(1)", html)
        self.assertEqual(embedded_data(html)["thisWeek"]["previousTasks"][0]["content"],
                         '</script><script>alert(1)</script> \\1')

    def test_template_sample_data_is_untouched(self):
        html = self.generate(minimal_data())
        default_sample = html[html.index("const DEFAULT_SAMPLE_DATA"):]
        self.assertIn('"name": "AstraZeneca / 数字化交付中心"', default_sample)

    def test_invalid_data_is_rejected(self):
        data = minimal_data()
        data["timeline"]["currentWeek"] = "W99"
        with self.assertRaises(ValueError):
            self.generate(data)
        self.assertFalse((self.tmp / "out.html").exists())

    def test_unknown_theme_and_missing_pptx(self):
        with self.assertRaises(ValueError):
            self.generate(minimal_data(), theme="tech-blue")
        with self.assertRaises(FileNotFoundError):
            self.generate(minimal_data(), pptx_path=str(self.tmp / "missing.pptx"))

    def test_fix_dates_writes_back(self):
        data = minimal_data()
        data["timeline"]["weeks"][0]["dates"] = "9.8-9.12"  # Tue-Sat
        path = self.write_json(data)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            generate_report.generate_report(str(path), str(self.tmp / "out.html"), auto_fix_dates=True)
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["timeline"]["weeks"][0]["dates"], "9.7-9.11")
        self.assertNotIn("theme", saved)

    def test_pptx_assets_go_into_data_not_css(self):
        pptx = build_pptx(self.tmp / "t.pptx")
        with mock.patch.object(pptx_extractor, "render_pptx_clean_slide", return_value=(None, None)):
            html = self.generate(minimal_data(company={"name": "Keep Me"}), pptx_path=str(pptx))
        data = embedded_data(html)
        self.assertEqual(data["company"]["name"], "Keep Me")
        self.assertTrue(data["company"]["logoDataUrl"].startswith("data:image/png;base64,"))
        self.assertEqual(data["customPptx"]["colors"]["primary"], "#112233")
        self.assertNotIn('<style id="pptx-template-override">', html)


class CliTests(TempDirMixin, unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS_DIR / "generate_report.py"), *args],
                              capture_output=True, text=True, cwd=self.tmp)

    def test_validate_exit_codes(self):
        good = self.write_json(minimal_data(), "good.json")
        self.assertEqual(self.cli("--data", str(good), "--validate").returncode, 0)

        bad_data = minimal_data()
        bad_data["timeline"]["tasks"][0]["end"] = "W9"
        bad = self.write_json(bad_data, "bad.json")
        res = self.cli("--data", str(bad), "--validate")
        self.assertEqual(res.returncode, 1)
        self.assertIn("'W9' is not a week id", res.stderr)

        warn_data = minimal_data()
        warn_data["project"]["typo"] = 1
        warn = self.write_json(warn_data, "warn.json")
        self.assertEqual(self.cli("--data", str(warn), "--validate").returncode, 0)

    def test_check_dates_with_fix_exits_zero_once_fixed(self):
        data = minimal_data()
        data["timeline"]["weeks"][0]["dates"] = "9.8-9.12"
        path = self.write_json(data)
        self.assertEqual(self.cli("--data", str(path), "--check-dates").returncode, 1)
        self.assertEqual(self.cli("--data", str(path), "--check-dates", "--fix-dates").returncode, 0)
        self.assertEqual(self.cli("--data", str(path), "--check-dates").returncode, 0)

    def test_generation_errors_exit_nonzero(self):
        path = self.write_json(minimal_data())
        res = self.cli("--data", str(path), "--pptx", "missing.pptx")
        self.assertEqual(res.returncode, 1)
        self.assertIn("PPTX template not found", res.stderr)


if __name__ == "__main__":
    unittest.main()
