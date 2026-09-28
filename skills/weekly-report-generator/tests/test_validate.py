import unittest

from helpers import load_example, minimal_data
from validate_data import validate_data

THEMES = ["classic-navy", "astrazeneca", "vercel-minimal"]


def run(data):
    return validate_data(data, THEMES)


class ExampleDataTests(unittest.TestCase):
    def test_examples_are_valid(self):
        for name in ("sample_data", "vercel_sample_data"):
            with self.subTest(name=name):
                self.assertEqual(run(load_example(name)), ([], []))

    def test_minimal_data_is_valid(self):
        self.assertEqual(run(minimal_data()), ([], []))


class SchemaTests(unittest.TestCase):
    def assertError(self, data, fragment):
        errors, _ = run(data)
        self.assertTrue(any(fragment in e for e in errors), f"{fragment!r} not in {errors}")

    def test_wrong_type(self):
        self.assertError(minimal_data(project="x"), "project: expected object")

    def test_enum_violations(self):
        data = minimal_data()
        data["timeline"]["tasks"][0]["status"] = "doing"
        data["deliverables"]["items"][0]["risk"] = "red"
        data["thisWeek"]["overallStatus"] = "ok"
        errors, _ = run(data)
        self.assertEqual(len(errors), 3, errors)

    def test_bool_is_not_an_enum_integer(self):
        self.assertError(minimal_data(discussionSlides=[{"layout": "cards", "cards": [{}], "columns": True}]),
                         "columns")

    def test_required_field(self):
        data = minimal_data()
        data["thisWeek"]["risks"] = [{"text": "oops"}]
        self.assertError(data, "thisWeek.risks[0]: missing required field 'content'")

    def test_unknown_field_warns_with_suggestion(self):
        data = minimal_data()
        data["timeline"]["weAreHereLabel"] = "Now"
        errors, warnings = run(data)
        self.assertEqual(errors, [])
        self.assertIn("did you mean 'weAreHereText'", warnings[0])

    def test_conclusion_accepts_string_or_object(self):
        for conclusion in ("decided", {"badge": "决议", "text": "decided"}):
            data = minimal_data(discussionSlides=[{"layout": "agenda", "sections": [{"title": "t"}], "conclusion": conclusion}])
            self.assertEqual(run(data), ([], []))

    def test_unknown_theme(self):
        self.assertError(minimal_data(theme="tech-blue"), "unknown theme 'tech-blue'")


class SemanticTests(unittest.TestCase):
    def errors_for(self, mutate):
        data = minimal_data()
        mutate(data["timeline"])
        return run(data)[0]

    def test_unknown_week_references(self):
        def mutate(tl):
            tl["currentWeek"] = "W9"
            tl["tasks"][0].update(end="W4", milestone="W5", stars=["W6"])
        errors = self.errors_for(mutate)
        for ref in ("W9", "W4", "W5", "W6"):
            self.assertTrue(any(f"'{ref}' is not a week id" in e for e in errors), errors)

    def test_start_after_end(self):
        errors = self.errors_for(lambda tl: tl["tasks"][0].update(start="W3", end="W1"))
        self.assertTrue(any("start 'W3' is after end 'W1'" in e for e in errors), errors)

    def test_span_references(self):
        def mutate(tl):
            del tl["tasks"][0]["start"], tl["tasks"][0]["end"]
            tl["tasks"][0]["spans"] = [{"start": "W1", "end": "W2"}, {"start": "W3", "end": "W8"}]
        errors = self.errors_for(mutate)
        self.assertEqual(len(errors), 1)
        self.assertIn("spans[1].end", errors[0])

    def test_duplicate_week_ids(self):
        errors = self.errors_for(lambda tl: tl["weeks"].append({"id": "W1", "dates": "9.28-10.2"}))
        self.assertTrue(any("duplicate week id 'W1'" in e for e in errors), errors)

    def test_non_adjacent_workstream_and_category(self):
        def mutate(tl):
            tl["tasks"] += [
                {"workstream": "Other", "category": "X", "task": "b", "start": "W1", "end": "W1"},
                {"workstream": "WS", "category": "C", "task": "c", "start": "W2", "end": "W2"},
            ]
        errors = self.errors_for(mutate)
        self.assertEqual(len(errors), 2, errors)

    def test_adjacent_rows_and_barless_tasks_are_fine(self):
        def mutate(tl):
            tl["tasks"] += [
                {"workstream": "WS", "category": "C", "task": "header only"},
                {"workstream": "WS", "category": "D", "task": "milestone", "milestone": "W3"},
            ]
        self.assertEqual(self.errors_for(mutate), [])

    def test_layout_without_payload_warns(self):
        _, warnings = run(minimal_data(discussionSlides=[{"layout": "table"}]))
        self.assertIn("needs 'table'", warnings[0])

    def test_legacy_aliases(self):
        data = minimal_data()
        data["slide2_plan"] = data.pop("timeline")
        data["slide2_plan"]["currentWeek"] = "W9"
        errors, warnings = run(data)
        self.assertTrue(any(e.startswith("slide2_plan.currentWeek") for e in errors), errors)
        self.assertTrue(any("deprecated" in w for w in warnings), warnings)


if __name__ == "__main__":
    unittest.main()
