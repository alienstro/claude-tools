#!/usr/bin/env python3
"""Set the Status of an issue on each project board that holds it.

Usage:
  set_board_status.py --repo OWNER/NAME --issue N --status "For Testing" [--dry-run]

The script prints one JSON line for each board: the board title, the old status, the new
status, and the result. A board with no option that matches the status keeps its card as it
is. The match ignores the letter case, the spaces, the hyphens and the underscores, so
"for-testing" matches "For Testing".
"""
import argparse
import json
import re
import subprocess
import sys

QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      projectItems(first: 20) {
        nodes {
          id
          project {
            id
            title
            number
            field(name: "Status") {
              ... on ProjectV2SingleSelectField { id options { id name } }
            }
          }
          fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue { name }
          }
        }
      }
    }
  }
}
"""

MUTATION = """
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $project, itemId: $item, fieldId: $field,
    value: { singleSelectOptionId: $option }
  }) { projectV2Item { id } }
}
"""


def graphql(query, **variables):
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        flag = "-F" if isinstance(value, int) else "-f"
        args += [flag, f"{key}={value}"]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"gh api graphql failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def normalize(name):
    return re.sub(r"[\s_-]+", "", name).lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--issue", required=True, type=int)
    parser.add_argument("--status", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    owner, name = args.repo.split("/", 1)
    data = graphql(QUERY, owner=owner, name=name, number=args.issue)
    issue = data["data"]["repository"]["issue"]
    items = issue["projectItems"]["nodes"] if issue else []
    if not items:
        print(json.dumps({"board": None, "result": "issue is on no project board"}))
        return

    wanted = normalize(args.status)
    for item in items:
        project = item["project"]
        field = project.get("field") or {}
        old = (item.get("fieldValueByName") or {}).get("name")
        report = {"board": f"{project['title']} (#{project['number']})", "old": old}
        option = next((o for o in field.get("options", []) if normalize(o["name"]) == wanted), None)
        if not field:
            report["result"] = "board has no Status field"
        elif option is None:
            names = [o["name"] for o in field["options"]]
            report["result"] = f"no status named {args.status!r}; options: {names}"
        elif old == option["name"]:
            report.update(new=old, result="already set")
        elif args.dry_run:
            report.update(new=option["name"], result="dry run, not changed")
        else:
            graphql(MUTATION, project=project["id"], item=item["id"], field=field["id"],
                    option=option["id"])
            report.update(new=option["name"], result="changed")
        print(json.dumps(report))


if __name__ == "__main__":
    main()
