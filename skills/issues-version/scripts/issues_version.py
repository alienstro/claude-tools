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

The script reads releases, PRs and issue links with GraphQL. When GraphQL is rate limited
(the hourly budget is used up, or the per-minute limit stays after one wait), it reads them
with REST endpoints, which use the separate core budget.
The board always uses the Projects REST API.

Needs: the `gh` CLI with the `project` scope (`gh auth refresh -s project`), and a clone
of the repository as the working directory, for the git history.
"""

import argparse
import json
import re
import subprocess
import sys
import time

PR_SUFFIX = re.compile(r"\(#(\d+)\)\s*$")
MERGE_LINE = re.compile(r"^Merge pull request #(\d+)")
REST_VERSION = ("-H", "X-GitHub-Api-Version: 2022-11-28")
# Below this number of GraphQL points, the script starts with REST.
GRAPHQL_RESERVE = 100


class GraphQLDepleted(Exception):
    """GraphQL cannot answer now: the hourly budget is used up, or the per-minute limit stays."""


USE_REST = False


def graphql_remaining():
    out = subprocess.run(["gh", "api", "rate_limit", "-q", ".resources.graphql.remaining"],
                         capture_output=True, text=True)
    return int(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip().isdigit() else 0


def run_gh(args, graphql=False):
    """Run gh, and wait and try again when GitHub sends a rate limit.

    The script sends many queries in a short time. GitHub then can send its secondary rate
    limit, even when the hourly points are not used up. The limit stops after about a minute.
    A GraphQL call raises GraphQLDepleted, and the caller changes to REST, in two cases:
    the hourly budget is used up, or the per-minute limit stays after one wait. Other
    sessions on the same account can keep the per-minute limit on for a long time.
    """
    for attempt, wait in enumerate((60, 120, 240, None)):
        out = subprocess.run(["gh", *args], capture_output=True, text=True)
        if out.returncode == 0 or "rate limit" not in out.stderr.lower():
            return out
        if graphql and (attempt >= 1 or graphql_remaining() < GRAPHQL_RESERVE):
            raise GraphQLDepleted()
        if wait is None:
            return out
        print(f"rate limit from GitHub; waiting {wait} s, then trying again", flush=True)
        time.sleep(wait)


def gh(*args, graphql=False):
    out = run_gh(args, graphql)
    if out.returncode:
        sys.exit(f"gh {' '.join(args[:3])} failed: {out.stderr.strip()}")
    return out.stdout


def via(graphql_way, rest_way, *args):
    """Use GraphQL, and use REST when the GraphQL budget is used up."""
    global USE_REST
    if not USE_REST:
        try:
            return graphql_way(*args)
        except GraphQLDepleted:
            USE_REST = True
            print("GraphQL is rate limited. The script uses REST from here.", flush=True)
    return rest_way(*args)


# --- GraphQL ---------------------------------------------------------------------------


def gql(query):
    return json.loads(gh("api", "graphql", "-f", "query=" + query, graphql=True))["data"]


def repo_block(repo, body):
    owner, name = repo.split("/")
    return gql('{repository(owner:"%s",name:"%s"){%s}}' % (owner, name, body))["repository"]


def releases_gql(repo):
    rows = json.loads(gh("release", "list", "--repo", repo, "--limit", "100",
                         "--json", "tagName,publishedAt,isDraft", graphql=True))
    return [(r["tagName"], r["publishedAt"]) for r in rows if not r["isDraft"]]


def release_pr_gql(repo, tag, base_branch):
    data = repo_block(repo, 'object(expression:"%s"){... on Commit{associatedPullRequests'
                      '(first:5){nodes{number baseRefName headRefOid baseRefOid}}}}' % tag)
    nodes = ((data.get("object") or {}).get("associatedPullRequests") or {}).get("nodes", [])
    nodes = [n for n in nodes if n["baseRefName"] == base_branch] or nodes
    if not nodes:
        return None, None, None
    return nodes[0]["number"], nodes[0]["headRefOid"], nodes[0]["baseRefOid"]


def pr_numbers_gql(repo, number, base_sha, head_sha):
    found, after = set(), None
    while True:
        cursor = ',after:"%s"' % after if after else ""
        data = repo_block(repo, "pullRequest(number:%d){commits(first:100%s){"
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


def closing_issues_gql(repo, prs):
    result = {}
    prs = sorted(prs)
    for start in range(0, len(prs), 40):
        body = "".join("p%d:pullRequest(number:%d){number closingIssuesReferences(first:20)"
                       "{nodes{number}}} " % (n, n) for n in prs[start:start + 40])
        for value in repo_block(repo, body).values():
            if value:
                result[value["number"]] = [i["number"] for i in value["closingIssuesReferences"]["nodes"]]
    return result


PR_FIELDS = "number merged baseRefName mergeCommit{oid}"


def issue_links_gql(repo, numbers):
    """Return {issue: {"prs": [merged PR numbers], "detail": {...}, "commit": None}}."""
    result = {}
    numbers = sorted(numbers)
    for start in range(0, len(numbers), 30):
        body = "".join(
            "i%d:issue(number:%d){number "
            "closedByPullRequestsReferences(first:20,includeClosedPrs:true){nodes{%s}} "
            "timelineItems(first:50,itemTypes:[CROSS_REFERENCED_EVENT,CONNECTED_EVENT]){nodes{"
            "... on CrossReferencedEvent{source{... on PullRequest{%s}}} "
            "... on ConnectedEvent{subject{... on PullRequest{%s}}}}}} " % (n, n, PR_FIELDS, PR_FIELDS, PR_FIELDS)
            for n in numbers[start:start + 30])
        for value in repo_block(repo, body).values():
            # A closing PR is the fix. A PR that only mentions the issue can be a later
            # follow-up, and it must not move the issue to a later release. So use the
            # mentions only when no merged PR closes the issue.
            closing = {p["number"]: p for p in value["closedByPullRequestsReferences"]["nodes"]
                       if p.get("merged")}
            mentions = [e.get("source") or e.get("subject") or {} for e in value["timelineItems"]["nodes"]]
            prs = closing or {p["number"]: p for p in mentions if p.get("merged")}
            result[value["number"]] = {"prs": sorted(prs), "detail": prs, "commit": None}
    return result


def merged_branch_pr_gql(repo, branch):
    rows = json.loads(gh("pr", "list", "--repo", repo, "--head", branch, "--state", "merged",
                         "--json", "number,baseRefName,mergeCommit", "--limit", "1", graphql=True))
    return rows[0] if rows else None


def pr_gql(repo, number):
    return repo_block(repo, "pullRequest(number:%d){%s}" % (number, PR_FIELDS))["pullRequest"]


# --- REST, when the GraphQL budget is used up -----------------------------------------


def rest(*args):
    return json.loads(gh("api", *REST_VERSION, *args))


def rest_pages(path):
    """Read every page of a REST list. The REST calls use the core budget, not GraphQL points."""
    pages = json.loads(gh("api", *REST_VERSION, "--paginate", "--slurp", path))
    return [row for page in pages for row in page]


def releases_rest(repo):
    rows = rest_pages(f"/repos/{repo}/releases?per_page=100")
    return [(r["tag_name"], r["published_at"]) for r in rows if not r["draft"]]


def release_pr_rest(repo, tag, base_branch):
    sha = rest(f"/repos/{repo}/commits/{tag}")["sha"]
    prs = rest(f"/repos/{repo}/commits/{sha}/pulls")
    prs = [p for p in prs if p["base"]["ref"] == base_branch] or prs
    if not prs:
        return None, None, None
    return prs[0]["number"], prs[0]["head"]["sha"], prs[0]["base"]["sha"]


def pr_numbers_rest(repo, number, base_sha, head_sha):
    """Read the PR numbers from the commit titles of a release PR, with the local git.

    The REST list of PR commits stops at 250 commits, and a release PR can have more. The
    commits of a PR are the commits of its head that its base does not hold.
    """
    if not (have_commit(base_sha) and have_commit(head_sha)):
        sys.exit(f"git cannot find {base_sha[:8]} or {head_sha[:8]}. Run the script in a clone.")
    found = set()
    for line in git("log", "--format=%s", f"{base_sha}..{head_sha}").stdout.splitlines():
        match = PR_SUFFIX.search(line) or MERGE_LINE.match(line)
        if match:
            found.add(int(match.group(1)))
    return found


def closing_issues_rest(repo, prs):
    # REST has no list of the issues that a PR closes. issue_links_rest reads the same
    # links from the side of each issue, so this step has nothing to add.
    return {}


CLOSING_WORDS = r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)"


def issue_links_rest(repo, numbers):
    """Return {issue: {"prs": [...], "detail": {}, "commit": sha or None}} from the timeline.

    A PR that names the issue after a closing word (such as "Closes #12") is the fix. Use
    the PRs that only mention the issue only when no merged PR closes it. The "commit" is
    the commit that closed the issue, for an issue with no PR.
    """
    result = {}
    for number in sorted(numbers):
        events = rest_pages(f"/repos/{repo}/issues/{number}/timeline?per_page=100")
        closes = re.compile(r"\b%s\b[:\s]+(?:%s)?#%d\b|%s\b[:\s]+https://github\.com/%s/issues/%d\b"
                            % (CLOSING_WORDS, re.escape(repo), number, CLOSING_WORDS, re.escape(repo), number),
                            re.IGNORECASE)
        closing, mentions, commit = set(), set(), None
        for event in events:
            if event.get("event") == "closed" and event.get("commit_id"):
                commit = event["commit_id"]
            source = (event.get("source") or {}).get("issue") or {}
            if event.get("event") != "cross-referenced" or not (source.get("pull_request") or {}).get("merged_at"):
                continue
            if not source.get("repository_url", "").lower().endswith("/repos/" + repo.lower()):
                continue
            text = f"{source.get('title') or ''}\n{source.get('body') or ''}"
            (closing if closes.search(text) else mentions).add(source["number"])
        result[number] = {"prs": sorted(closing or mentions), "detail": {}, "commit": commit}
    return result


def merged_branch_pr_rest(repo, branch):
    owner = repo.split("/")[0]
    rows = rest(f"/repos/{repo}/pulls?state=closed&per_page=10&head={owner}:{branch}")
    return next((r for r in rows if r.get("merged_at")), None)


def pr_rest(repo, number):
    return rest(f"/repos/{repo}/pulls/{number}")


# --- One way for both ------------------------------------------------------------------


def releases(repo, count):
    rows = sorted(via(releases_gql, releases_rest, repo), key=lambda r: r[1])
    tags = [tag for tag, _ in rows]
    # The second value is true when the window starts at the first release of all.
    return tags[-count:], count >= len(tags)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def have_commit(sha):
    if git("cat-file", "-e", f"{sha}^{{commit}}").returncode:
        git("fetch", "-q", "origin", sha)
    return git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def is_ancestor(commit, tip):
    """Return true when `commit` is in the history of `tip`."""
    if not have_commit(commit):
        return False
    if git("rev-parse", "-q", "--verify", f"{tip}^{{commit}}").returncode and not have_commit(tip):
        return False
    return git("merge-base", "--is-ancestor", commit, tip).returncode == 0


def merge_facts(pr):
    """Return the merge commit, the base branch and the merged flag of a GraphQL or REST PR."""
    if "mergeCommit" in pr or "baseRefName" in pr:
        return (pr.get("mergeCommit") or {}).get("oid"), pr.get("baseRefName"), pr.get("merged", True)
    return pr.get("merge_commit_sha"), (pr.get("base") or {}).get("ref"), bool(pr.get("merged_at"))


def release_of_commit(sha, heads, order, on_base):
    """Return the first release that holds a commit, or None."""
    for tag in order:
        tip = tag if on_base else heads.get(tag)
        if tip and is_ancestor(sha, tip):
            return tag
    return None


def release_by_ancestry(repo, pr, heads, order, base_branch, depth=0):
    """Find the first release that holds a PR that the release PR titles do not name.

    A PR into the base branch ships in the first tag that holds its merge commit. A PR into
    any other branch ships in the first release whose release PR head holds its merge
    commit. A PR into a feature branch that later got a squash merge follows that branch.
    """
    if isinstance(pr, int):
        pr = via(pr_gql, pr_rest, repo, pr)
    sha, base, merged = merge_facts(pr)
    if not (sha and merged):
        return None
    tag = release_of_commit(sha, heads, order, base == base_branch)
    if tag or depth >= 3 or base in (base_branch, "dev"):
        return tag
    parent = via(merged_branch_pr_gql, merged_branch_pr_rest, repo, base)
    return release_by_ancestry(repo, parent, heads, order, base_branch, depth + 1) if parent else None


# --- The board (Projects REST API) -------------------------------------------------------


def project_path(owner, project):
    """Return the REST path of the board. The path differs for an organization and a user."""
    kind = "orgs" if rest(f"/users/{owner}")["type"] == "Organization" else "users"
    return f"/{kind}/{owner}/projectsV2/{project}"


def option_name(value):
    # REST gives a select option name as {"raw": ..., "html": ...}.
    name = (value or {}).get("name")
    return name.get("raw") if isinstance(name, dict) else name


def board(path, repo, status_field, version_field):
    """Read the board with the Projects REST API. It uses the core budget, not GraphQL points."""
    fields = rest(f"{path}/fields?per_page=100")
    by_name = {f["name"]: f for f in fields}
    for needed in (status_field, version_field):
        if needed not in by_name:
            sys.exit(f"The project has no field named {needed!r}. Fields: {sorted(by_name)}")
    status_f, version_f = by_name[status_field], by_name[version_field]
    for option in status_f.get("options", []):
        option["name"] = option_name(option)
    query = f"{path}/items?per_page=100&fields[]={status_f['id']}&fields[]={version_f['id']}"
    repo_url = f"https://api.github.com/repos/{repo}"
    issues = {}
    for item in rest_pages(query):
        content = item.get("content") or {}
        if item.get("content_type") != "Issue" or content.get("repository_url", "").lower() != repo_url.lower():
            continue
        values = {f["id"]: f.get("value") for f in item.get("fields", [])}
        version = values.get(version_f["id"])
        issues[content["number"]] = {
            "id": item["id"], "title": content.get("title", ""), "state": content.get("state"),
            "status": option_name(values.get(status_f["id"])),
            "version": version.get("raw") if isinstance(version, dict) else version,
        }
    return status_f, version_f, issues


def set_field(path, item_id, field_id, value):
    # -F sends the id as a number. -f keeps an option id such as "98236657" a string.
    return run_gh(["api", *REST_VERSION, "-X", "PATCH", f"{path}/items/{item_id}",
                   "-F", f"fields[][id]={field_id}", "-f", f"fields[][value]={value}"])


def main():
    global USE_REST
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
    ap.add_argument("--base-branch", default="main", help="the branch that release tags are on")
    ap.add_argument("--status-field", default="Status")
    ap.add_argument("--version-field", default="Release Version")
    ap.add_argument("--manual", default="",
                    help="versions that you found by hand, such as 630=1.5.0,852=1.6.0")
    ap.add_argument("--plan-out", help="write the plan as JSON to this path")
    ap.add_argument("--recheck", action="store_true",
                    help="also check the done issues that have a version, and correct a wrong one")
    ap.add_argument("--apply", action="store_true", help="change the board (default: dry run)")
    args = ap.parse_args()

    move = {s.strip() for s in args.move.split(",") if s.strip()}
    keep = {s.strip() for s in args.keep.split(",") if s.strip()}
    manual = dict(pair.split("=") for pair in args.manual.split(",") if pair)
    manual = {int(k): v for k, v in manual.items()}

    remaining = graphql_remaining()
    if remaining < GRAPHQL_RESERVE:
        USE_REST = True
        print(f"The GraphQL budget has {remaining} points left. The script uses REST.", flush=True)

    git("fetch", "-q", "--tags", "origin")
    tags, from_first = releases(args.repo, args.releases)
    if len(tags) < 2 and not from_first:
        sys.exit("Need at least two releases: the oldest one is only the floor.")
    # No release comes before the first release, so its version is sure.
    floor, order = (None if from_first else tags[0]), tags
    first, heads = {}, {}
    for tag in tags:
        number, heads[tag], base_sha = via(release_pr_gql, release_pr_rest, args.repo, tag, args.base_branch)
        if number is None:
            print(f"warning: no release PR for tag {tag}; its PRs count for the next release")
            continue
        prs = via(pr_numbers_gql, pr_numbers_rest, args.repo, number, base_sha, heads[tag])
        new = [p for p in prs if p not in first]
        for p in new:
            first[p] = tag
        print(f"{tag}: release PR #{number}, {len(new)} new PRs" + ("  (floor)" if tag == floor else ""))

    path = project_path(args.owner, args.project)
    status_f, version_f, issues = board(path, args.repo, args.status_field, args.version_field)
    done_option = next((o["id"] for o in status_f.get("options", []) if o["name"] == args.done), None)
    if done_option is None:
        sys.exit(f"The {args.status_field} field has no option {args.done!r}.")

    found = {}

    def add(issue, tag):
        found[issue] = max(found.get(issue, tag), tag, key=order.index)

    for pr, closed in via(closing_issues_gql, closing_issues_rest, args.repo, set(first)).items():
        for issue in closed:
            add(issue, first[pr])
    # Read the linked PRs of each issue in a testing status, and of each done issue
    # with no version, because a PR that only mentions the issue does not close it.
    watched = {n for n, i in issues.items()
               if i["status"] in move | keep
               or (i["status"] == args.done and (args.recheck or not i["version"]))}
    links = via(issue_links_gql, issue_links_rest, args.repo, watched)
    for issue, info in links.items():
        for pr in info["prs"]:
            if pr in first:
                add(issue, first[pr])
    # Old release PRs and direct PRs into the base branch do not name each PR in a commit
    # title. For an issue with no version yet, place its linked PRs by the git history.
    # Only fill a gap: a later PR that only mentions an old issue must not move its version.
    by_history = set()
    for issue, info in links.items():
        if issue in found:
            continue
        for pr in info["prs"]:
            tag = release_by_ancestry(args.repo, info["detail"].get(pr) or pr, heads, order, args.base_branch)
            if tag:
                add(issue, tag)
                by_history.add(issue)
        # An issue that a direct commit closed has no PR. Place that commit.
        if issue not in found and info["commit"]:
            tag = (release_of_commit(info["commit"], heads, order, True)
                   or release_of_commit(info["commit"], heads, order, False))
            if tag:
                add(issue, tag)
                by_history.add(issue)
    for issue, tag in manual.items():
        found[issue] = tag

    plan, floor_only, unlinked, unreleased = [], [], [], []
    for number, item in sorted(issues.items()):
        tag = found.get(number)
        in_testing = number in watched
        if tag is None:
            if in_testing:
                info = links.get(number, {})
                (unlinked if item.get("state") == "closed" and not info.get("prs") else unreleased).append(number)
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
        elif row["issue"] in by_history:
            version += " (history)"
        print(f"#{row['issue']:>5}  {str(row['status']):<15} "
              f"{args.done if row['to_done'] else '(keep)':<11} {version:<16} {row['title']}")
    print(f"\n{len(plan)} changes: {sum(r['to_done'] for r in plan)} to {args.done}.")
    print("closed, no linked PR (find the version by hand, then use --manual):", unlinked)
    print("no released fix yet (leave as is):", unreleased)
    print(f"version not sure, release {floor} or earlier (not set):", floor_only)
    print("read with:", "REST (GraphQL was rate limited)" if USE_REST else "GraphQL")
    if args.plan_out:
        with open(args.plan_out, "w") as handle:
            json.dump(plan, handle, indent=1)

    if not args.apply:
        print("\nDry run. Run again with --apply to change the board.")
        return
    failures = []
    for row in plan:
        if row["old_version"] != row["version"]:
            out = set_field(path, row["id"], version_f["id"], row["version"])
            if out.returncode:
                failures.append((row["issue"], "version", out.stderr.strip()))
        if row["to_done"]:
            out = set_field(path, row["id"], status_f["id"], done_option)
            if out.returncode:
                failures.append((row["issue"], "status", out.stderr.strip()))

    _, _, after = board(path, args.repo, args.status_field, args.version_field)
    mismatches = []
    for row in plan:
        item = after.get(row["issue"], {})
        want = args.done if row["to_done"] else row["status"]
        if item.get("status") != want or item.get("version") != row["version"]:
            mismatches.append((row["issue"], item.get("status"), item.get("version")))
    print(f"\nApplied. Failures: {failures}. Mismatches after a new read: {mismatches}.")


if __name__ == "__main__":
    main()
