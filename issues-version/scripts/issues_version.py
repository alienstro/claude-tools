#!/usr/bin/env python3
"""Plan, and optionally apply, the release version and Done status of board issues.

This script finds the release that shipped each issue. It reads the release PR into the
base branch of each GitHub release, takes the feature PRs from the commit titles of that
release PR, and finds the issues that each feature PR closes. It then compares the result
with the GitHub Project board and prints a plan. It changes the board only with --apply.

The commit list of a release PR can hold the PRs of earlier releases too, because the base
branch gets squash merges. The first release that lists a PR is the release that shipped it.
The oldest release that the script reads is the "floor": a PR that it lists can come from
that release or from an earlier one, so the script does not set a version from the floor.

Needs: the `gh` CLI with the `project` scope (`gh auth refresh -s project`).
"""

import argparse
import json
import re
import subprocess
import sys

PR_SUFFIX = re.compile(r"\(#(\d+)\)\s*$")
MERGE_LINE = re.compile(r"^Merge pull request #(\d+)")


def gh(*args):
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"gh {' '.join(args[:3])} failed: {out.stderr.strip()}")
    return out.stdout


def gql(query):
    return json.loads(gh("api", "graphql", "-f", "query=" + query))["data"]


def repo_block(owner, name, body):
    return gql('{repository(owner:"%s",name:"%s"){%s}}' % (owner, name, body))["repository"]


def releases(repo, count):
    rows = json.loads(gh("release", "list", "--repo", repo, "--limit", "100",
                         "--json", "tagName,publishedAt,isDraft"))
    rows = sorted((r for r in rows if not r["isDraft"]), key=lambda r: r["publishedAt"])
    tags = [r["tagName"] for r in rows]
    # The second value is true when the window starts at the first release of all.
    return tags[-count:], count >= len(tags)


def release_pr(owner, name, tag):
    data = repo_block(owner, name, 'object(expression:"%s"){... on Commit{'
                      'associatedPullRequests(first:5){nodes{number baseRefName}}}}' % tag)
    nodes = ((data.get("object") or {}).get("associatedPullRequests") or {}).get("nodes", [])
    return nodes[0]["number"] if nodes else None


def pr_numbers_in(owner, name, number):
    found, after = set(), None
    while True:
        cursor = ',after:"%s"' % after if after else ""
        data = repo_block(owner, name, "pullRequest(number:%d){commits(first:100%s){"
                          "pageInfo{hasNextPage endCursor} nodes{commit{message}}}}"
                          % (number, cursor))["pullRequest"]["commits"]
        for node in data["nodes"]:
            line = node["commit"]["message"].split("\n")[0]
            match = PR_SUFFIX.search(line) or MERGE_LINE.match(line)
            if match:
                found.add(int(match.group(1)))
        if not data["pageInfo"]["hasNextPage"]:
            return found
        after = data["pageInfo"]["endCursor"]


def closing_issues(owner, name, prs):
    result = {}
    prs = sorted(prs)
    for start in range(0, len(prs), 40):
        body = "".join("p%d:pullRequest(number:%d){number closingIssuesReferences(first:20)"
                       "{nodes{number}}} " % (n, n) for n in prs[start:start + 40])
        for value in repo_block(owner, name, body).values():
            if value:
                result[value["number"]] = [i["number"] for i in value["closingIssuesReferences"]["nodes"]]
    return result


def issue_links(owner, name, numbers):
    """Return {issue: {"state": ..., "prs": [merged PR numbers]}} from both link kinds."""
    result = {}
    numbers = sorted(numbers)
    for start in range(0, len(numbers), 30):
        body = "".join(
            "i%d:issue(number:%d){number state "
            "closedByPullRequestsReferences(first:20,includeClosedPrs:true){nodes{number merged}} "
            "timelineItems(first:50,itemTypes:[CROSS_REFERENCED_EVENT,CONNECTED_EVENT]){nodes{"
            "... on CrossReferencedEvent{source{... on PullRequest{number merged}}} "
            "... on ConnectedEvent{subject{... on PullRequest{number merged}}}}}} " % (n, n)
            for n in numbers[start:start + 30])
        for value in repo_block(owner, name, body).values():
            prs = {p["number"] for p in value["closedByPullRequestsReferences"]["nodes"] if p["merged"]}
            for event in value["timelineItems"]["nodes"]:
                source = event.get("source") or event.get("subject") or {}
                if source.get("merged"):
                    prs.add(source["number"])
            result[value["number"]] = {"state": value["state"], "prs": sorted(prs)}
    return result


def board(owner, project, repo, status_field, version_field):
    fields = json.loads(gh("project", "field-list", str(project), "--owner", owner,
                           "--format", "json", "--limit", "100"))["fields"]
    by_name = {f["name"]: f for f in fields}
    for needed in (status_field, version_field):
        if needed not in by_name:
            sys.exit(f"The project has no field named {needed!r}. Fields: {sorted(by_name)}")
    project_id = json.loads(gh("project", "view", str(project), "--owner", owner,
                               "--format", "json"))["id"]
    items = json.loads(gh("project", "item-list", str(project), "--owner", owner,
                          "--format", "json", "--limit", "3000"))["items"]
    # gh writes a custom field key with a lowercase first letter, such as "release Version".
    version_key = version_field[0].lower() + version_field[1:]
    issues = {}
    for item in items:
        content = item.get("content") or {}
        if content.get("type") == "Issue" and content.get("repository") == repo:
            issues[content["number"]] = {
                "id": item["id"], "title": content.get("title", ""),
                "status": item.get("status"), "version": item.get(version_key),
            }
    return project_id, by_name[status_field], by_name[version_field], issues


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True, help="the repository, such as my-org/my-app")
    ap.add_argument("--owner", required=True, help="owner of the project board")
    ap.add_argument("--project", type=int, required=True, help="number of the project board")
    ap.add_argument("--releases", type=int, default=6,
                    help="number of recent releases to read; the oldest one is the floor")
    ap.add_argument("--move", default="For Testing,In Testing,For Release",
                    help="statuses that go to the done status after a release")
    ap.add_argument("--keep", default="Failed Testing",
                    help="statuses that get the version but keep their status")
    ap.add_argument("--done", default="Done")
    ap.add_argument("--status-field", default="Status")
    ap.add_argument("--version-field", default="Release Version")
    ap.add_argument("--manual", default="",
                    help="versions that you found by hand, such as 630=1.5.0,852=1.6.0")
    ap.add_argument("--plan-out", help="write the plan as JSON to this path")
    ap.add_argument("--apply", action="store_true", help="change the board (default: dry run)")
    args = ap.parse_args()

    owner, name = args.repo.split("/")
    move = {s.strip() for s in args.move.split(",") if s.strip()}
    keep = {s.strip() for s in args.keep.split(",") if s.strip()}
    manual = dict(pair.split("=") for pair in args.manual.split(",") if pair)
    manual = {int(k): v for k, v in manual.items()}

    tags, from_first = releases(args.repo, args.releases)
    if len(tags) < 2 and not from_first:
        sys.exit("Need at least two releases: the oldest one is only the floor.")
    # No release comes before the first release, so its version is sure.
    floor, order = (None if from_first else tags[0]), tags
    first = {}
    for tag in tags:
        number = release_pr(owner, name, tag)
        if number is None:
            print(f"warning: no release PR for tag {tag}; its PRs count for the next release")
            continue
        new = [p for p in pr_numbers_in(owner, name, number) if p not in first]
        for p in new:
            first[p] = tag
        print(f"{tag}: release PR #{number}, {len(new)} new PRs" + ("  (floor)" if tag == floor else ""))

    project_id, status_f, version_f, issues = board(
        args.owner, args.project, args.repo, args.status_field, args.version_field)
    done_option = next((o["id"] for o in status_f.get("options", []) if o["name"] == args.done), None)
    if done_option is None:
        sys.exit(f"The {args.status_field} field has no option {args.done!r}.")

    found = {}

    def add(issue, tag):
        found[issue] = max(found.get(issue, tag), tag, key=order.index)

    for pr, closed in closing_issues(owner, name, set(first)).items():
        for issue in closed:
            add(issue, first[pr])
    # Read the linked PRs of each issue in a testing status, and of each done issue
    # with no version, because a PR that only mentions the issue does not close it.
    watched = {n for n, i in issues.items()
               if i["status"] in move | keep or (i["status"] == args.done and not i["version"])}
    links = issue_links(owner, name, watched)
    for issue, info in links.items():
        for pr in info["prs"]:
            if pr in first:
                add(issue, first[pr])
    for issue, tag in manual.items():
        found[issue] = tag

    plan, floor_only, unlinked, unreleased = [], [], [], []
    for number, item in sorted(issues.items()):
        tag = found.get(number)
        in_testing = number in watched
        if tag is None:
            if in_testing:
                info = links.get(number, {})
                (unlinked if info.get("state") == "CLOSED" and not info.get("prs") else unreleased).append(number)
            continue
        if tag == floor and number not in manual:
            if in_testing:
                floor_only.append(number)
            continue
        to_done = item["status"] in move
        if item["version"] == tag and not to_done:
            continue
        plan.append({"issue": number, "id": item["id"], "title": item["title"][:60],
                     "status": item["status"], "to_done": to_done,
                     "old_version": item["version"], "version": tag,
                     "manual": number in manual})

    print(f"\n{'issue':>6}  {'status now':<15} {'new status':<11} {'version':<16} title")
    for row in plan:
        version = row["version"] if row["old_version"] in (None, row["version"]) \
            else f"{row['old_version']} -> {row['version']}"
        if row["manual"]:
            version += " (manual)"
        print(f"#{row['issue']:>5}  {str(row['status']):<15} "
              f"{args.done if row['to_done'] else '(keep)':<11} {version:<16} {row['title']}")
    print(f"\n{len(plan)} changes: {sum(r['to_done'] for r in plan)} to {args.done}.")
    print("closed, no linked PR (find the version by hand, then use --manual):", unlinked)
    print("no released fix yet (leave as is):", unreleased)
    print(f"version not sure, release {floor} or earlier (not set):", floor_only)
    if args.plan_out:
        with open(args.plan_out, "w") as handle:
            json.dump(plan, handle, indent=1)

    if not args.apply:
        print("\nDry run. Run again with --apply to change the board.")
        return
    failures = []
    for row in plan:
        if row["old_version"] != row["version"]:
            out = subprocess.run(["gh", "project", "item-edit", "--project-id", project_id,
                                  "--id", row["id"], "--field-id", version_f["id"],
                                  "--text", row["version"]], capture_output=True, text=True)
            if out.returncode:
                failures.append((row["issue"], "version", out.stderr.strip()))
        if row["to_done"]:
            out = subprocess.run(["gh", "project", "item-edit", "--project-id", project_id,
                                  "--id", row["id"], "--field-id", status_f["id"],
                                  "--single-select-option-id", done_option],
                                 capture_output=True, text=True)
            if out.returncode:
                failures.append((row["issue"], "status", out.stderr.strip()))

    _, _, _, after = board(args.owner, args.project, args.repo, args.status_field, args.version_field)
    mismatches = []
    for row in plan:
        item = after.get(row["issue"], {})
        want = args.done if row["to_done"] else row["status"]
        if item.get("status") != want or item.get("version") != row["version"]:
            mismatches.append((row["issue"], item.get("status"), item.get("version")))
    print(f"\nApplied. Failures: {failures}. Mismatches after a new read: {mismatches}.")


if __name__ == "__main__":
    main()
