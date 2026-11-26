"""Self-test for check_coverage.py. Run: python3 -m unittest <this file>."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_coverage.py")

AREAS = """## 2. Edge-case list

| Area | Cases to try |
|---|---|
| Data | x |
| Timing | x |
| Lifecycle | x |
| Errors | x |
| Roles and plans | x |

## 3. Next
"""

HAPPY = """### Happy path
| # | Kind | Persona | Screen | Step | Expected | Actual | Proof | Result |
|---|---|---|---|---|---|---|---|---|
| 1 | happy | new | Home | a | b | b | Playwright: 1-a.png | ✅ |
| 2 | happy | power | Home | a | b | b | Playwright: 1-b.png | ✅ |
"""

EDGE = """### Edge cases
| # | Area | Persona | Screen | Step | Expected | Actual | Proof | Result |
|---|---|---|---|---|---|---|---|---|
| 3 | Data | new | Home | a | b | b | Playwright: 1-c.png | ✅ |
| 4 | Errors | - | Home | a | b | b | Playwright: 1-d.png | ✅ |
| 5 | Lifecycle | power | Home | a | b | b | text: list is empty before and after | ✅ |
| 6 | Timing | - | Home | a | b | not run: needs a real device; tried: none possible | - | ⏭️ |
"""

NA = "**Not applicable:** Roles and plans: the page has one role\n"
COVERAGE = ("**Coverage:** happy path 2/2 · edge cases 3/3 live, 1 not run"
            " · edge areas: Data, Lifecycle, Errors\n")


def comment(verdict="PASS", coverage=COVERAGE, na=NA, happy=HAPPY, edge=EDGE):
    return f"## QA result: {verdict} — test `abc123`\n\n{coverage}{na}\n{happy}\n{edge}"


class CheckCoverage(unittest.TestCase):
    def run_check(self, text):
        with tempfile.TemporaryDirectory() as d:
            c, a = os.path.join(d, "c.md"), os.path.join(d, "areas.md")
            Path(c).write_text(text, encoding="utf-8")
            Path(a).write_text(AREAS, encoding="utf-8")
            p = subprocess.run([sys.executable, SCRIPT, c, a], capture_output=True, text=True)
            return p.returncode, p.stdout + p.stderr

    def test_full_comment_passes(self):
        code, out = self.run_check(comment())
        self.assertEqual(code, 0, out)

    def test_blocked_and_not_deployed_skip(self):
        for v in ("BLOCKED", "NOT DEPLOYED"):
            code, out = self.run_check(f"## QA result: {v} — test `abc`\n")
            self.assertEqual(code, 0, out)

    def test_missing_power_persona_fails(self):
        code, out = self.run_check(comment(happy=HAPPY.replace("| power |", "| new |")))
        self.assertEqual(code, 1)
        self.assertIn("power", out)

    def test_too_few_live_edge_rows_fails(self):
        edge = EDGE.replace("| 3 | Data | new | Home | a | b | b | Playwright: 1-c.png | ✅ |\n", "")
        na = "**Not applicable:** Roles and plans: one role; Data: no input\n"
        code, out = self.run_check(comment(edge=edge, na=na))
        self.assertEqual(code, 1)
        self.assertIn("3 or more", out)

    def test_area_with_no_row_and_no_reason_fails(self):
        code, out = self.run_check(comment(na=""))
        self.assertEqual(code, 1)
        self.assertIn("Roles and plans", out)

    def test_unknown_area_fails(self):
        code, out = self.run_check(comment(edge=EDGE.replace("| Data |", "| Dataa |")))
        self.assertEqual(code, 1)
        self.assertIn("Dataa", out)

    def test_not_run_without_tried_fails(self):
        code, out = self.run_check(comment(edge=EDGE.replace("; tried: none possible", "")))
        self.assertEqual(code, 1)
        self.assertIn("tried:", out)

    def test_live_row_without_proof_fails(self):
        code, out = self.run_check(comment(edge=EDGE.replace("Playwright: 1-c.png", "-")))
        self.assertEqual(code, 1)
        self.assertIn("proof", out.lower())

    def test_pass_with_flaky_row_fails(self):
        code, out = self.run_check(comment(edge=EDGE.replace("1-d.png | ✅", "1-d.png | ⚠️")))
        self.assertEqual(code, 1)
        self.assertIn("PASS", out)

    def test_fail_verdict_may_have_failed_rows(self):
        edge = EDGE.replace("1-d.png | ✅", "1-d.png | ❌")
        cov = COVERAGE.replace("edge cases 3/3", "edge cases 2/3")
        code, out = self.run_check(comment(verdict="FAIL", edge=edge, coverage=cov))
        self.assertEqual(code, 0, out)

    def test_wrong_coverage_line_fails_and_prints_the_right_one(self):
        code, out = self.run_check(comment(coverage=COVERAGE.replace("2/2", "5/5")))
        self.assertEqual(code, 1)
        self.assertIn("happy path 2/2", out)


if __name__ == "__main__":
    unittest.main()
