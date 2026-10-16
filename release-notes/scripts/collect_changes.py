#!/usr/bin/env python3
"""Collect the pull requests, commits and migrations between two refs for release notes.

Usage:
  collect_changes.py [--from <tag>] [--to <ref>] [--repo <owner/name>] [--json]

Defaults: --from is the newest GitHub release tag, --to is origin/dev.
The script calls git and gh directly, so a shell hook cannot shorten the output.
"""

import argparse
import json
import re
import subprocess
import sys

BODY_LIMIT = 1500
PR_SUBJECT = re.compile(r"\(#(\d+)\)\s*$")
PR_MERGE = re.compile(r"^Merge pull request #(\d+)")
PR_ANY = re.compile(r"#(\d+)\b")
CONVENTIONAL = re.compile(r"^(\w+)(?:\([^)]*\))?!?:")
GRAPHQL_BATCH = 25


def run(args, check=True):
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(f"error: {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout


def newest_release_tag():
    out = run(["gh", "release", "list", "--limit", "1", "--json", "tagName", "-q", ".[0].tagName"])
    tag = out.strip()
    if not tag:
        sys.exit("error: the repository has no GitHub release. Pass --from <tag>.")
    return tag


def release_body(tag):
    out = run(["gh", "release", "view", tag, "--json", "body", "-q", ".body"], check=False)
    return out


def commits(base, head):
    # %x1f separates fields and %x1e separates records, so a subject can hold any text.
    out = run(["git", "log", "--format=%h%x1f%s%x1f%P%x1e", f"{base}..{head}"])
    rows = []
    for record in out.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        sha, subject, parents = record.split("\x1f")
        rows.append({"sha": sha, "subject": subject, "merge": len(parents.split()) > 1})
    return rows


def mainline(base, head):
    # A commit off the first-parent line came in with a merged PR branch, so its PR covers it.
    out = run(["git", "log", "--first-parent", "--format=%h", f"{base}..{head}"])
    return set(out.split())


def pr_number(subject):
    for pattern in (PR_SUBJECT, PR_MERGE):
        match = pattern.search(subject)
        if match:
            return int(match.group(1))
    return None


def commit_type(subject):
    match = CONVENTIONAL.match(subject)
    return match.group(1).lower() if match else None


def fetch_prs(repo, numbers):
    owner, name = repo.split("/")
    prs = {}
    for start in range(0, len(numbers), GRAPHQL_BATCH):
        chunk = numbers[start:start + GRAPHQL_BATCH]
        fields = (
            "number title body state mergedAt baseRefName headRefName url "
            "labels(first:10){nodes{name}} "
            "closingIssuesReferences(first:5){nodes{number title}}"
        )
        parts = [f"p{n}: pullRequest(number:{n}){{{fields}}}" for n in chunk]
        query = f'query{{repository(owner:"{owner}",name:"{name}"){{{" ".join(parts)}}}}}'
        out = run(["gh", "api", "graphql", "-f", f"query={query}"], check=False)
        try:
            data = json.loads(out)["data"]["repository"]
        except (ValueError, KeyError, TypeError):
            data = {}
        for n in chunk:
            node = data.get(f"p{n}")
            if node:
                prs[n] = node
    return prs


def migrations(base, head):
    out = run(["git", "diff", "--name-only", "--diff-filter=A", base, head])
    return sorted({line for line in out.splitlines() if "/migrations/" in line})


def next_version(tag, has_feature):
    match = re.match(r"^(v?)(\d+)\.(\d+)\.(\d+)$", tag)
    if not match:
        return None
    prefix, major, minor, patch = match.group(1), *map(int, match.groups()[1:])
    if has_feature:
        return f"{prefix}{major}.{minor + 1}.0"
    return f"{prefix}{major}.{minor}.{patch + 1}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="base")
    parser.add_argument("--to", dest="head", default="origin/dev")
    parser.add_argument("--repo")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    run(["git", "fetch", "--quiet", "--tags", "origin"], check=False)
    repo = args.repo or run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]).strip()
    base = args.base or newest_release_tag()
    head = args.head

    rows = commits(base, head)
    direct = mainline(base, head)
    shipped = {int(n) for n in PR_ANY.findall(release_body(base))}

    numbers, loose = [], []
    for row in rows:
        number = pr_number(row["subject"])
        row["pr"] = number
        row["type"] = commit_type(row["subject"])
        if number is None:
            if not row["merge"] and row["sha"] in direct:
                loose.append(row)
        elif number not in numbers:
            numbers.append(number)

    details = fetch_prs(repo, numbers)
    prs = []
    for number in numbers:
        node = details.get(number, {})
        if node.get("baseRefName") == "main" and node.get("headRefName") == "dev":
            continue  # an earlier release PR, not a change
        subject = next((r["subject"] for r in rows if r["pr"] == number), "")
        body = (node.get("body") or "").strip()
        prs.append({
            "number": number,
            "title": node.get("title") or subject,
            "type": commit_type(node.get("title") or "") or commit_type(subject),
            "base": node.get("baseRefName"),
            "head": node.get("headRefName"),
            "merged_at": node.get("mergedAt"),
            "labels": [l["name"] for l in (node.get("labels") or {}).get("nodes", [])],
            "closes": [f"#{i['number']} {i['title']}" for i in (node.get("closingIssuesReferences") or {}).get("nodes", [])],
            "in_previous_notes": number in shipped,
            "body": body[:BODY_LIMIT] + ("\n[...cut]" if len(body) > BODY_LIMIT else ""),
            "found": bool(node),
        })

    has_feature = any(p["type"] == "feat" for p in prs) or any(r["type"] == "feat" for r in loose)
    report = {
        "repo": repo,
        "from": base,
        "to": head,
        "suggested_version": next_version(base, has_feature),
        "commit_count": len(rows),
        "prs": prs,
        "commits_without_pr": [{"sha": r["sha"], "subject": r["subject"]} for r in loose],
        "new_migrations": migrations(base, head),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"# Changes {base}..{head} in {repo}")
    print(f"commits: {report['commit_count']}  prs: {len(prs)}  suggested version: {report['suggested_version']}\n")
    for p in prs:
        flags = []
        if p["base"] and p["base"] not in ("dev", "main"):
            flags.append(f"merged into {p['base']}, part of a larger PR")
        if p["base"] == "main":
            flags.append("merged into main directly: check if it already shipped")
        if p["in_previous_notes"]:
            flags.append(f"named in the {base} notes: probably shipped already")
        if not p["found"]:
            flags.append("gh could not read this PR")
        print(f"## #{p['number']} [{p['type'] or '?'}] {p['title']}")
        print(f"base: {p['base']}  head: {p['head']}  merged: {p['merged_at']}")
        if p["labels"]:
            print(f"labels: {', '.join(p['labels'])}")
        if p["closes"]:
            print(f"closes: {'; '.join(p['closes'])}")
        for flag in flags:
            print(f"FLAG: {flag}")
        if p["body"]:
            print(p["body"])
        print()
    if loose:
        print("## Direct pushes with no PR number")
        for r in loose:
            print(f"- {r['sha']} {r['subject']}")
        print()
    print("## New migrations")
    for path in report["new_migrations"] or ["(none)"]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
