import copy
import json
import struct
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
EXAMPLES_DIR = SKILL_DIR / "examples"
sys.path.insert(0, str(SCRIPTS_DIR))


def load_example(name="sample_data"):
    with open(EXAMPLES_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def minimal_data(**overrides):
    data = {
        "project": {"title": "Test Project", "reportDate": "2026-09-18"},
        "timeline": {
            "currentWeek": "W2",
            "weeks": [
                {"id": "W1", "dates": "9.7-9.11"},
                {"id": "W2", "dates": "9.14-9.18"},
                {"id": "W3", "dates": "9.21-9.25"},
            ],
            "tasks": [
                {"workstream": "WS", "category": "C", "task": "Build", "start": "W1", "end": "W2", "status": "active"},
            ],
        },
        "deliverables": {"items": [{"milestone": "Go-live", "status": "未开始", "risk": "none"}]},
        "thisWeek": {"previousTasks": [{"content": "done"}]},
    }
    data.update(copy.deepcopy(overrides))
    return data


class TempDirMixin:
    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()
        super().tearDown()

    def write_json(self, data, name="data.json"):
        path = self.tmp / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path


def tiny_png(color=(255, 0, 0)):
    """A valid 1x1 RGB PNG."""
    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    raw = b"\x00" + bytes(color)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def _pic(rid, x, y, cx, cy):
    return (f'<p:pic><p:blipFill><a:blip r:embed="{rid}"/></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm></p:spPr></p:pic>')


def _rels(targets):
    rels = "".join(f'<Relationship Id="{rid}" Target="{t}"/>' for rid, t in targets)
    return f'<?xml version="1.0"?><Relationships>{rels}</Relationships>'


def build_pptx(path, slide1_text="Quarterly Review", accent1="112233", dk2="0A0B0C", accent5="445566"):
    """
    Writes a minimal PPTX with a theme palette, a small logo and a large cover picture on
    layout 1, and a large decorative picture on layout 2 (the content background).
    """
    theme = (f'<a:theme><a:clrScheme>'
             f'<a:dk2><a:srgbClr val="{dk2}"/></a:dk2>'
             f'<a:accent1><a:srgbClr val="{accent1}"/></a:accent1>'
             f'<a:accent2><a:srgbClr val="778899"/></a:accent2>'
             f'<a:accent5><a:srgbClr val="{accent5}"/></a:accent5>'
             f'</a:clrScheme></a:theme>')
    layout1 = ('<p:sldLayout><p:cSld name="Cover"><p:spTree>'
               + _pic("rId1", 100000, 100000, 900000, 400000)      # logo
               + _pic("rId2", 0, 0, 12192000, 6858000)             # cover background
               + '</p:spTree></p:cSld></p:sldLayout>')
    layout2 = ('<p:sldLayout><p:cSld name="Title Only"><p:spTree>'
               + _pic("rId1", 100000, 100000, 900000, 400000)      # same logo again
               + _pic("rId3", 0, 6000000, 12192000, 858000)        # footer wave
               + '</p:spTree></p:cSld></p:sldLayout>')
    slide1 = f'<p:sld><p:cSld><p:spTree><p:sp><a:t>{slide1_text}</a:t></p:sp></p:spTree></p:cSld></p:sld>'
    slide2 = '<p:sld><p:cSld><p:spTree><p:sp><a:t>Status</a:t></p:sp></p:spTree></p:cSld></p:sld>'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/theme/theme1.xml", theme)
        z.writestr("ppt/media/logo.png", tiny_png((0, 0, 255)))
        z.writestr("ppt/media/cover.png", tiny_png((0, 255, 0)) + b"\0" * 120000)
        z.writestr("ppt/media/wave.png", tiny_png((255, 255, 0)))
        z.writestr("ppt/slideLayouts/slideLayout1.xml", layout1)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
                   _rels([("rId1", "../media/logo.png"), ("rId2", "../media/cover.png")]))
        z.writestr("ppt/slideLayouts/slideLayout2.xml", layout2)
        z.writestr("ppt/slideLayouts/_rels/slideLayout2.xml.rels",
                   _rels([("rId1", "../media/logo.png"), ("rId3", "../media/wave.png")]))
        z.writestr("ppt/slides/slide1.xml", slide1)
        z.writestr("ppt/slides/_rels/slide1.xml.rels", _rels([("rId1", "../slideLayouts/slideLayout1.xml")]))
        z.writestr("ppt/slides/slide2.xml", slide2)
        z.writestr("ppt/slides/_rels/slide2.xml.rels", _rels([("rId1", "../slideLayouts/slideLayout2.xml")]))
    return path
