#!/usr/bin/env python3
"""Refuse a PASS or FAIL comment whose case matrix misses the counts of test-cases.md section 6.

Usage: check_coverage.py <comment.md> [test-cases.md]
The edge areas come from the section 2 table of test-cases.md, so a new area there applies here.
Prints the Coverage line that the tables give. Exit 0: OK or verdict not checked. Exit 1: gaps.
"""
import os
import re
import sys
from pathlib import Path

MIN_EDGE_LIVE = 3
MIN_EDGE_AREAS = 3
MUST_AREAS = ("Errors", "Lifecycle")
CHECKED = ("PASS", "FAIL")
LIVE, PASSED, NOT_RUN = ("✅", "❌", "⚠️"), "✅", "⏭️"


def areas_from(path):
    text = Path(path).read_text(encoding="utf-8")
    sec = re.search(r"^## 2\..*?\n(.*?)(?=^## )", text, re.S | re.M)
    if not sec:
        sys.exit(f"no section 2 table in {path}")
    rows = [r for r in sec.group(1).splitlines() if r.startswith("|")][2:]
    return [r.split("|")[1].strip() for r in rows]


def table(text, heading):
    """Rows under a '### <heading>' table, as dicts keyed by the lower-case header names."""
    m = re.search(rf"^### {heading}\s*\n((?:\|.*\n?)+)", text, re.M)
    if not m:
        return None
    lines = m.group(1).strip().splitlines()
    head = [c.strip().lower() for c in lines[0].strip("|").split("|")]
    return [dict(zip(head, (c.strip() for c in ln.strip().strip("|").split("|"))))
            for ln in lines[2:] if re.match(r"\|\s*\d+\s*\|", ln)]


def mark(row):
    r = row.get("result", "")
    return next((m for m in LIVE + (NOT_RUN,) if m in r), "")


def main(comment_path, cases_path):
    text = Path(comment_path).read_text(encoding="utf-8")
    head = re.search(r"^## QA result:\s*([A-Z][A-Z ]*?)\s*(?:—|-|$)", text, re.M)
    if not head:
        return ["no '## QA result: <verdict>' heading"], None
    verdict = head.group(1).strip()
    if verdict not in CHECKED:
        print(f"skip: verdict {verdict} has no count rule")
        return [], None

    areas = areas_from(cases_path)
    missing_must = [a for a in MUST_AREAS if a not in areas]
    if missing_must:
        sys.exit(f"test-cases.md section 2 has no area {missing_must}")

    errs = []
    happy, edge = table(text, "Happy path"), table(text, "Edge cases")
    if happy is None or edge is None:
        return ["the comment needs a '### Happy path' and a '### Edge cases' table"], None

    for name, rows in (("Happy path", happy), ("Edge cases", edge)):
        for r in rows:
            m, n = mark(r), r.get("#", "?")
            if not m:
                errs.append(f"row {n}: Result needs one of {' '.join(LIVE + (NOT_RUN,))}")
            elif m in LIVE and r.get("proof", "-") in ("", "-"):
                errs.append(f"row {n}: a live row needs proof (a screenshot file, or 'text: <reason>')")
            elif m == NOT_RUN:
                if name == "Happy path":
                    errs.append(f"row {n}: a {r.get('kind', 'happy')} row did not run live; the verdict is BLOCKED")
                elif not re.search(r"not run:\s*\S.*tried:\s*\S", r.get("actual", "")):
                    errs.append(f"row {n}: write 'not run: <reason>; tried: <emulation method, or none possible>'")
            if verdict == "PASS" and m in ("❌", "⚠️"):
                errs.append(f"row {n}: a PASS has no failed or flaky row")

    for p in ("new", "power"):
        if not any(r.get("kind") == "happy" and r.get("persona") == p and mark(r) in LIVE for r in happy):
            errs.append(f"no live happy row as the {p} persona")

    for r in edge:
        if r.get("area") not in areas:
            errs.append(f"row {r.get('#')}: unknown area '{r.get('area')}'; use one of: {', '.join(areas)}")

    na = {}
    m = re.search(r"^\*\*Not applicable:\*\*(.*)$", text, re.M)
    for part in (m.group(1).split(";") if m else []):
        a, _, why = part.partition(":")
        if a.strip():
            na[a.strip()] = why.strip()
    for a, why in na.items():
        if not why:
            errs.append(f"Not applicable '{a}' needs a reason")

    live = [r for r in edge if mark(r) in LIVE]
    live_areas = [a for a in areas if any(r.get("area") == a for r in live)]
    if len(live) < MIN_EDGE_LIVE:
        errs.append(f"{len(live)} edge rows ran live; need {MIN_EDGE_LIVE} or more")
    if len(live_areas) < MIN_EDGE_AREAS:
        errs.append(f"live edge rows cover {len(live_areas)} areas; need {MIN_EDGE_AREAS} or more")
    for a in MUST_AREAS:
        if a not in live_areas and a not in na and not any(r.get("area") == a for r in edge):
            errs.append(f"no {a} row: run one, or give the reason under Not applicable")
    for a in areas:
        if a not in na and not any(r.get("area") == a for r in edge):
            errs.append(f"area '{a}' has no row and no 'Not applicable' reason")

    hl = [r for r in happy if mark(r) in LIVE]
    cov = (f"**Coverage:** happy path {sum(mark(r) == PASSED for r in hl)}/{len(hl)}"
           f" · edge cases {sum(mark(r) == PASSED for r in live)}/{len(live)} live,"
           f" {sum(mark(r) == NOT_RUN for r in edge)} not run · edge areas: {', '.join(live_areas)}")
    if cov not in text:
        errs.append(f"the Coverage line does not match the tables; use:\n  {cov}")
    return errs, cov


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "test-cases.md")
    errs, cov = main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else default)
    for e in errs:
        print("✗", e)
    if errs:
        sys.exit(1)
    if cov:
        print("✓", cov)
