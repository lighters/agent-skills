import base64
import unittest
from unittest import mock

from helpers import TempDirMixin, build_pptx, tiny_png
import pptx_extractor


def extract(path):
    # Slide rendering needs macOS qlmanage; force the portable layout-image fallback
    with mock.patch.object(pptx_extractor, "render_pptx_clean_slide", return_value=(None, None)), \
         mock.patch.object(pptx_extractor, "optimize_image_if_possible", side_effect=lambda b, fn, **kw: (b, "image/png")):
        return pptx_extractor.extract_pptx_template(str(path))


class PptxExtractorTests(TempDirMixin, unittest.TestCase):
    def test_theme_palette(self):
        res = extract(build_pptx(self.tmp / "t.pptx"))
        self.assertEqual(res["colors"], {
            "primary": "#112233", "primaryDark": "#0A0B0C", "accent": "#445566", "accentWarm": "#778899",
        })

    def test_logo_is_the_repeated_small_layout_picture(self):
        res = extract(build_pptx(self.tmp / "t.pptx"))
        self.assertEqual(res["logo_data_url"], "data:image/png;base64," + base64.b64encode(tiny_png((0, 0, 255))).decode())

    def test_layout_backgrounds_fallback(self):
        res = extract(build_pptx(self.tmp / "t.pptx"))
        self.assertIsNotNone(res["cover_bg_data_url"])
        self.assertEqual(res["content_bg_data_url"],
                         "data:image/png;base64," + base64.b64encode(tiny_png((255, 255, 0))).decode())
        self.assertTrue(res["has_custom_pptx"])

    def test_company_detection_needs_standalone_az(self):
        for text, expected in [("掌上AZ 项目周报", "AstraZeneca / 阿斯利康"),
                               ("AstraZeneca Weekly", "AstraZeneca / 阿斯利康"),
                               ("AZURE Migration Weekly", ""),
                               ("Hazard review", "")]:
            with self.subTest(text=text):
                res = extract(build_pptx(self.tmp / "t.pptx", slide1_text=text))
                self.assertEqual(res["company_name"], expected)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            pptx_extractor.extract_pptx_template(str(self.tmp / "missing.pptx"))


if __name__ == "__main__":
    unittest.main()
