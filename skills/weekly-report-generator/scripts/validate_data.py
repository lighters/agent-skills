#!/usr/bin/env python3
"""
Weekly Report Data Validator
Checks report JSON against references/schema.json plus cross-field rules the schema
cannot express (week id references, adjacency of merged Gantt cells, layout payloads).
Standard library only: implements the JSON Schema subset used by schema.json
($ref, type, enum, required, properties, additionalProperties, items).
"""

import difflib
import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "references" / "schema.json"

_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "null": lambda v: v is None,
}

LEGACY_ALIASES = {
    "slide2_plan": "timeline",
    "slide3_deliverables": "deliverables",
    "slide4_tasks": "thisWeek",
    "appendixSlides": "discussionSlides",
}


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve(schema, root):
    while "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"Unsupported $ref: {ref}")
        node = root
        for part in ref[2:].split("/"):
            node = node[part]
        schema = node
    return schema


def _check(value, schema, path, root, errors, warnings):
    schema = _resolve(schema, root)
    where = path or "(root)"

    types = schema.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        if not any(_TYPE_CHECKS[t](value) for t in types):
            errors.append(f"{where}: expected {' or '.join(types)}, got {type(value).__name__}")
            return

    if "enum" in schema:
        # bool is an int subclass in Python: keep True from matching 1
        if not any(value == e and type(value) is type(e) for e in schema["enum"]):
            allowed = ", ".join(json.dumps(e, ensure_ascii=False) for e in schema["enum"])
            errors.append(f"{where}: {json.dumps(value, ensure_ascii=False)} is not one of {allowed}")
            return

    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{where}: missing required field '{key}'")
        for key, sub in value.items():
            sub_path = f"{path}.{key}" if path else key
            if key in props:
                _check(sub, props[key], sub_path, root, errors, warnings)
            elif schema.get("additionalProperties") is False:
                hint = difflib.get_close_matches(key, list(props), n=1)
                suggestion = f" (did you mean '{hint[0]}'?)" if hint else ""
                warnings.append(f"{sub_path}: unknown field, ignored by the renderer{suggestion}")

    if isinstance(value, list) and "items" in schema:
        for idx, item in enumerate(value):
            _check(item, schema["items"], f"{path}[{idx}]", root, errors, warnings)


def _pick(data, key, alias):
    """Return (path, value) for a canonical key, falling back to its legacy alias."""
    if key in data:
        return key, data[key]
    if alias in data:
        return alias, data[alias]
    return key, None


def _check_semantics(data, errors, warnings):
    for alias, key in LEGACY_ALIASES.items():
        if alias in data and key in data:
            warnings.append(f"{alias}: ignored because '{key}' is also present")
        elif alias in data:
            warnings.append(f"{alias}: deprecated, rename to '{key}'")

    tl_path, timeline = _pick(data, "timeline", "slide2_plan")
    if isinstance(timeline, dict):
        weeks = [w for w in timeline.get("weeks", []) if isinstance(w, dict)]
        week_ids = [w.get("id") for w in weeks]
        index = {}
        for i, wid in enumerate(week_ids):
            if wid in index:
                errors.append(f"{tl_path}.weeks[{i}].id: duplicate week id '{wid}'")
            else:
                index[wid] = i

        def ref_ok(ref, where):
            if ref not in index:
                errors.append(f"{where}: '{ref}' is not a week id in {tl_path}.weeks")
                return False
            return True

        current = timeline.get("currentWeek")
        if current is not None and weeks:
            ref_ok(current, f"{tl_path}.currentWeek")

        tasks_key = "tasks" if "tasks" in timeline else "rows"
        tasks = [t for t in timeline.get(tasks_key, []) if isinstance(t, dict)]
        seen_ws, seen_cat = set(), set()
        prev_ws = prev_cat = None
        for i, t in enumerate(tasks):
            where = f"{tl_path}.{tasks_key}[{i}]"
            spans = t.get("spans") or []
            if not spans and "start" in t and "end" in t:
                spans = [{"start": t["start"], "end": t["end"]}]
            for j, s in enumerate(spans):
                if not isinstance(s, dict):
                    continue
                s_where = where if not t.get("spans") else f"{where}.spans[{j}]"
                start, end = s.get("start"), s.get("end")
                if ref_ok(start, f"{s_where}.start") & ref_ok(end, f"{s_where}.end") and index[start] > index[end]:
                    errors.append(f"{s_where}: start '{start}' is after end '{end}'")
            milestone = t.get("milestone")
            if isinstance(milestone, str):
                ref_ok(milestone, f"{where}.milestone")
            for k, star in enumerate(t.get("stars") or []):
                ref_ok(star, f"{where}.stars[{k}]")

            # Merged Gantt cells (rowspan) only render correctly for adjacent rows
            ws = t.get("workstream", "默认工作流")
            cat = (ws, t.get("category", "通用"))
            if ws != prev_ws and ws in seen_ws:
                errors.append(f"{where}.workstream: '{ws}' also appears earlier but not adjacent; group its tasks together")
            if cat != prev_cat and cat in seen_cat:
                errors.append(f"{where}.category: '{cat[1]}' in '{ws}' also appears earlier but not adjacent; group its tasks together")
            seen_ws.add(ws)
            seen_cat.add(cat)
            prev_ws, prev_cat = ws, cat

    ds_path, slides = _pick(data, "discussionSlides", "appendixSlides")
    if isinstance(slides, list):
        required_payload = {
            "comparison": "cards", "cards": "cards",
            "agenda": "sections", "deep-dive": "sections",
            "table": "table", "custom": "html",
        }
        for i, slide in enumerate(slides):
            if not isinstance(slide, dict):
                continue
            layout = slide.get("layout", "comparison")
            payload = required_payload.get(layout)
            if payload and not slide.get(payload):
                warnings.append(f"{ds_path}[{i}]: layout '{layout}' needs '{payload}', the slide body will be empty")


def validate_data(data, theme_ids=None):
    """Returns (errors, warnings) as lists of human-readable strings."""
    errors, warnings = [], []
    root = load_schema()
    _check(data, root, "", root, errors, warnings)
    if isinstance(data, dict):
        _check_semantics(data, errors, warnings)
        theme = data.get("theme")
        if theme_ids and isinstance(theme, str) and theme not in theme_ids:
            errors.append(f"theme: unknown theme '{theme}'. Available: {', '.join(theme_ids)}")
    return errors, warnings


def print_report(errors, warnings, file):
    for w in warnings:
        print(f"   ⚠️  {w}", file=file)
    for e in errors:
        print(f"   ❌ {e}", file=file)
