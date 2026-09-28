import contextlib
import io
import unittest

import helpers  # noqa: F401  (adds scripts/ to sys.path)
from generate_report import validate_timeline_dates


def check(weeks, report_date="2024-04-03", **kwargs):
    timeline = {"weeks": weeks}
    with contextlib.redirect_stdout(io.StringIO()):
        issues = validate_timeline_dates(timeline, {"reportDate": report_date}, verbose=False, **kwargs)
    return issues, timeline["weeks"]


class TimelineDateTests(unittest.TestCase):
    def test_monday_to_friday_passes(self):
        issues, _ = check([{"id": "W1", "dates": "1.29-2.2"}, {"id": "W2", "dates": "4.1-4.5"}])
        self.assertEqual(issues, [])

    def test_wrong_weekdays_reported_with_suggestion(self):
        issues, _ = check([{"id": "W7", "dates": "1.30-2.3"}])
        self.assertEqual(len(issues), 1)
        self.assertIn("Suggested: '1.29-2.2'", issues[0])

    def test_auto_fix_aligns_to_start_week(self):
        _, weeks = check([{"id": "W7", "dates": "1.30-2.3"}], auto_fix=True)
        self.assertEqual(weeks[0]["dates"], "1.29-2.2")

    def test_auto_fix_keeps_friday_end(self):
        _, weeks = check([{"id": "W", "dates": "3.27-3.29"}], auto_fix=True)  # Wed-Fri
        self.assertEqual(weeks[0]["dates"], "3.25-3.29")

    def test_auto_fix_sunday_start_moves_to_monday(self):
        _, weeks = check([{"id": "W", "dates": "3.31-4.4"}], auto_fix=True)  # Sun-Thu
        self.assertEqual(weeks[0]["dates"], "4.1-4.5")

    def test_year_comes_from_report_date(self):
        weeks = [{"id": "W", "dates": "9.14-9.18"}]
        self.assertEqual(check(weeks, report_date="2026-09-18")[0], [])
        self.assertEqual(len(check(weeks, report_date="2025-09-18")[0]), 1)  # 2025-09-14 is a Sunday

    def test_week_crossing_year_boundary(self):
        issues, _ = check([{"id": "W", "dates": "12.29-1.2"}], report_date="2025-12-30")
        self.assertEqual(issues, [])

    def test_explicit_years_and_chinese_format(self):
        issues, _ = check([{"id": "A", "dates": "2025.12.29-2026.1.2"}, {"id": "B", "dates": "4月1日至4月5日"}])
        self.assertEqual(issues, [])

    def test_holiday_needs_name_but_not_weekdays(self):
        issues, _ = check([{"id": "H", "dates": "10.1-10.7", "isHoliday": True}])
        self.assertEqual(len(issues), 1)
        self.assertIn("holidayName", issues[0])
        issues, _ = check([{"id": "H", "dates": "10.1-10.7", "isHoliday": True, "holidayName": "国庆假期"}])
        self.assertEqual(issues, [])

    def test_unparseable_and_invalid_dates(self):
        issues, _ = check([{"id": "A", "dates": "next week"}, {"id": "B", "dates": "2.30-3.3"}, {"id": "C", "dates": ""}])
        self.assertEqual(len(issues), 3)

    def test_strict_raises(self):
        with self.assertRaises(ValueError):
            check([{"id": "W7", "dates": "1.30-2.3"}], strict=True)


if __name__ == "__main__":
    unittest.main()
