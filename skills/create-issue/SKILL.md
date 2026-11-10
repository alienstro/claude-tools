---
name: create-issue
description: Use when the user wants to open a GitHub issue, or to fill the missing parts of an issue that already exists. Writes the title and the description in the team format, and sets every part that the team reads on the board: the area label, the project label (the product that the work is for, found from the repository), the issue type (Bug, Feature, Task), and the project fields Status, Priority, Estimate Effort (in hours) and Week. It sets an assignee only when the user names one. Use it when the user says "/create-issue", "open an issue", "file a bug", "make a ticket for this", "log this for QA", "add this to the board", or "my issue has no type or priority", even if they do not name the fields.
user-invocable: true
allowed-tools: Bash, Read
---

# Create issue

Open an issue that the team can sort, plan and test without more edits. An issue with no
type, no area, no priority, no estimate or no week does not show in the board views and
the weekly plan, so somebody must fix it by hand later. This skill sets all of these parts
when it creates the issue.

## Team values

Read `team.local.md` in this skill folder first, if it exists. It has a `Shared` section
for the whole org, and one `Repo:` section for each repository. A repo section holds the
owner, the project, the area labels, the title examples and the ids of that repository.
A value in `team.local.md` wins over an example in this file. Keep `team.local.md` out of
a public repository.

To find the repo section:

1. Use the repository that the user names.
2. If the user names no repository, use the repository of the current directory:
   `gh repo view --json nameWithOwner --jq .nameWithOwner`.
3. Read the `Shared` section and the `Repo: <owner>/<repo>` section only. Do not use the
   values of a different repository, because each project has its own field ids.

When `team.local.md` or the repo section does not exist, ask the user for these values.
Then read the ids with the commands in `## Commands`, and add a new `Repo:` section to
`team.local.md` so that the next run does not ask again:

| Placeholder | Meaning |
|---|---|
| `<owner>` | The GitHub org or user that owns the repository and the project |
| `<repo>` | The repository name |
| `<project>` | The number of the GitHub Project board that the team plans from |

An auto-add workflow can put each new issue on a different project. That workflow does not
add it to `<project>`, so this skill adds it.

## The parts of an issue

| Part | Where it lives | Value |
|---|---|---|
| Title | issue | The format below |
| Description | issue | The format below |
| Assignee | issue | Empty. Set it only when the user names a person, such as "assign it to me" |
| Type | issue (org type) | `Bug`, `Feature` or `Task`, from the title prefix |
| Area label | issue | One `area:*` label, from the part of the product |
| Project label | issue | One label that names the product the work is for. See `### Project label` |
| `qa-reported` label | issue | Only when QA found the problem |
| Status | project | `Backlog`, unless the user says that work started |
| Priority | project | `P0` to `P4`. Default `P2` |
| Estimate Effort (in hours) | project | A number, such as `0.5`, `2` or `8` |
| Week | project | The current week iteration, unless the user names a week |
| Release Version | project | Leave empty. `/issues-version` sets it after the release |

Keep each value in one place only. If the org also has issue fields or labels for the
priority or the effort, leave them empty. The team reads the priority and the effort only
from the project fields. Two places for one value go out of step.

### Type from the title prefix

| Prefix | Type |
|---|---|
| `fix` | Bug |
| `feat` | Feature |
| `refactor`, `perf`, `chore`, `docs`, `test`, `build`, `ci` | Task |

### Area label

Use the `area:*` labels of the repository. Read them with
`gh label list --repo <owner>/<repo> --search area:`. This is an example set:

| Label | Use it for |
|---|---|
| `area:backend` | The server, the API and the jobs |
| `area:frontend` | The web and mobile screens |
| `area:data` | The schema, the migrations and the stores |
| `area:ops` | The admin tools and the scripts that run production |
| `area:infra` | Deploy, CI, cost, security and observability |
| `area:product` | What the user experiences, and decisions about it |

Pick the one area where the fix goes. If the fix goes in two areas, pick the area of the
largest change.

### Project label

Each issue gets one project label. The label names the product that the work is for, so the
team can filter the issues of one product across all repositories. The user does not name it.
Find it in this order:

1. The user names a product. Use the label of that product.
2. The request comes from the repository of a product, such as the current directory. Use
   the label of that product, also when the issue goes to a shared backend repository.
3. Else, use the label of the target repository.

`team.local.md` maps each repository to its project label, in the `Shared` section. If it
has no map, use the repository name as the label, and add the map to `team.local.md`. If the
label does not exist in the target repository, create it with the same name and the same
description. Show the new label in the block of step 3 before you create it.

### Priority

| Value | Use it when |
|---|---|
| `P0` | Real users are blocked, money is wrong, or data leaks. Fix now |
| `P1` | A main flow is broken or wrong for many users. Fix in this week |
| `P2` | A normal bug or feature. Plan it |
| `P3` | A small problem with an easy workaround |
| `P4` | A good idea for later |

### Estimate

The team builds with AI coding agents. An agent writes most of the code, so an issue takes
about half of the time that the same work takes by hand. Estimate the hours for the work
by hand, then divide by two. Do not add hours for each risk. One small buffer is enough.

| Size of the work | Estimate |
|---|---|
| A copy change, a label or a small style fix | `0.5` |
| A small fix or a change in one or two files | `1` |
| A normal feature or bug in one area | `2` to `4` |
| A feature that touches the contract, a store or two repositories | `6` to `8` |
| More than `8` hours | Split the issue into a main issue and sub-issues. See `### Split a large issue` |

- Estimate each part of the work, then add the parts. Do not guess one number for the
  full feature. Show the parts to the user with the total.
- Use `0.5` steps up to `2` hours, and whole hours after that.
- An issue that you split into two repositories gets two estimates. Their sum must not be
  more than the estimate for the full work. Lower the estimate of the first issue if you
  need to.
- Do not round up to a "safe" number. A large estimate fills the week and hides space for
  other work.

### Split a large issue

When the sum of the parts is more than `8` hours, do not create one large issue. Create a
main issue and one sub-issue for each part.

- **Main issue:** it keeps the full Summary, Problem, Goal and Scope. Its `Done when` lists
  the sub-issues. Set the type, the area, the Status, the Priority and the Week. Leave the
  estimate empty, because the board adds the estimates, and a total on the main issue
  counts the same hours two times.
- **Sub-issue:** one part that a developer can merge and QA can test alone. Give it its own
  title, a short description, its own `Done when`, an area and an estimate of `8` hours or
  less. Use the same type and Priority as the main issue, unless the user says different.
- Make each sub-issue a real GitHub sub-issue of the main issue, not only a task list
  item. Then the main issue shows the progress of each part.
- Show the user the main issue and the list of sub-issues, with each estimate and the
  total, in the same block. Create all of them only after the user says yes.

## Title format

```
<prefix>(<area>): <the problem, as a fact that a user or an operator sees>
```

- Use the prefix from the type table, and the area name without `area:`.
- Write the problem, not the fix. The fix can change. The problem stays true until the
  issue closes.
- Use lowercase after the colon, the present tense, and no full stop.
- Keep the title to about 80 characters or less.

Examples:

- `fix(frontend): the price list draws its note over the product names`
- `feat(ops): admins can only add a team member through the server config`
- `fix(data): orders from before the currency column show no total`

Bad: `Fix total bug` (no area, no fact). Bad: `fix(data): add a script to backfill the
currency` (this is the fix, not the problem).

## Description format

Write in ASD-STE100 Simplified Technical English: short sentences, the active voice, one
word for one meaning. Write for a reader who knows the product but not this problem.

A good description lets a new developer start the work, and lets QA test the result,
without a question to the reporter. A short report hides facts that the team then finds
again later. So give the context, the exact words and the evidence, even when a section
takes only one line. When you do not know a fact, write "Not known yet" and say what you
checked. Do not delete the section, because an empty gap is a fact too.

- Quote the exact words of the app, an error or a log line, in a code block or quotes.
- Name each file with a repo path and a line number, such as `src/api/orders.ts:52`, and
  each issue or PR with `#<number>`.
- Give numbers: how many users, how often, how long, how much money.

### Bug

```markdown
## Summary
<Two or three sentences: what goes wrong, who sees it, and why it matters.>

## Background
<How this part of the product works now, and how it works on the other platform or in the
last release. Give the reader the context to understand the problem.>

## Steps to reproduce
1. <step, with the exact input that the user gives>
2. <step>
3. <step>

## Expected
<What must happen. Name the reference behaviour, such as "as it does on the web app".>

## Actual
<What happens. Quote the exact message or error:>
> <the exact words>

## Environment
- **Where:** <prod or staging>
- **Platform:** <web, mobile, the API or the admin tools>
- **Version:** <release, such as 1.6.0, or the dev date>
- **When:** <date and time, with the time zone>
- **Account:** <user or account handle, if it is safe to share>

## Impact
- **Who:** <all users, mobile users, admins, one customer>
- **How often:** <each time, sometimes, one time>
- **Workaround:** <what the user can do now, or "None">

## Evidence
<Screenshots, links, trace ids, log lines. Put the error text in a code block.>

## Done when
- [ ] <a check that QA can do, with the expected result>
- [ ] <a check for an edge case, such as a large file or an expired session>
- [ ] <a check that the old behaviour on the other platform still works>

## Related
- <issues and PRs, such as #42, #57>
```

### Feature or task

```markdown
## Summary
<Two or three sentences: what the issue adds or changes, and for whom.>

## Problem
<What the user, the operator or the team cannot do now. Say what they do instead today,
and what that costs: time, money, errors, support messages.>

## Background
<How the product works now in this area. Name the files, the tables and the past issues.>

## Goal
<The result that the user or the team gets. One or two sentences.>

## Scope
**In scope**
- <change>
- <change>

**Out of scope**
- <a thing that a reader can expect but this issue does not do>

## Proposed approach
<How to build it: the parts that change, the new data, the new settings. Give the other
options and why this issue does not use them.>

## Open questions
- <a decision that the team must make before or during the work, or "None">

## Done when
- [ ] <a check that QA can do, with the expected result>
- [ ] <a check for a permission, a limit or an error case>

## Related
- <issues and PRs>
```

For a `qa-reported` bug, keep the QA words in **Steps to reproduce**, **Expected** and
**Actual**. Add the screenshot or the link that QA gave under **Evidence**, and the name
of the tester at the end: `Reported by: <name> (QA)`.

## Steps

1. Read what the user gave: the bug report, the chat or the screenshot. Search the issues
   and PRs for related work. A bug issue states the problem only. Do not write a cause or
   a fix in it, even when you know one. The developer who takes the issue finds the cause
   and chooses the fix. If you know a cause, tell the user in the chat, not in the issue.
2. Write the title and the description in the formats above. Choose the type, the area,
   the priority and the estimate. Estimate each part of the work. If the sum is more than
   `8` hours, split the issue. See `### Split a large issue`.
3. Show the user one block with the title, the description and each part from the table.
   Wait for a yes before you create the issue. The issue is public to the whole team.
4. Create the issue, then set the type and the project fields. See `## Commands`.
5. Read the issue again and check each part. Give the user the issue link and the parts
   that you set.

### Fill an issue that already exists

When the user gives an issue number, or asks to fix the issues that have no type or no
priority, do not create a new issue. Read the issue, find the parts that are missing, and
show the user the values that you want to set. Change the title or the description only if
the user asks. Then run the commands for the missing parts only.

To find the user's issues with missing parts, look for an open issue with no `issueType`, no
`area:*` label, or no `Priority` on the project.

To find the issues that are not on the board, compare the issue numbers of the repository
with the issue numbers of the project items.

A closed issue keeps its history. Do not change its title, its description or its
assignee. Set the Week iteration that holds the close date. Set the Status `Won't Do` for
the reason `NOT_PLANNED`. For the reason `COMPLETED`, use the status that the board sets
when an issue closes, such as `For Testing`. Read the statuses of other closed items to
find it. If the board has no such rule, use `Done`.

## Commands

Take the ids from the repo section of `team.local.md`. If it has no ids, or a command fails with "not found",
read the ids again:

```bash
# The project id, and the field ids and option ids of Status, Priority, Estimate Effort and Week.
gh project view <project> --owner <owner> --format json --jq .id
gh project field-list <project> --owner <owner> --format json

# The org issue type ids (Bug, Feature, Task).
gh api graphql -f query='{organization(login:"<owner>"){issueTypes(first:20){nodes{id name}}}}'
```

Then create the issue and set its parts:

```bash
# 1. Create the issue.
gh issue create --repo <owner>/<repo> --title "<title>" --body-file <file> \
  --label area:<area> --label <project label> [--label qa-reported] [--assignee <login>]
# If the project label is missing in the target repository, create it first:
#   gh label create <project label> --repo <owner>/<repo> --description "<description>"
# Add --assignee only when the user names a person. "me" means @me.

# 2. Set the issue type.
gh api graphql -f query='mutation{updateIssueIssueType(input:{issueId:"<issue node id>",issueTypeId:"<type id>"}){issue{number}}}'

# 3. Add the issue to the project and keep the item id.
gh project item-add <project> --owner <owner> --url <issue url> --format json --jq .id

# 4. Set the project fields.
gh project item-edit --project-id <project id> --id <item id> \
  --field-id <Status field id> --single-select-option-id <status option id>
gh project item-edit ... --field-id <Priority field id> --single-select-option-id <priority option id>
gh project item-edit ... --field-id <Estimate Effort field id> --number <hours>

# 5. For a split issue: create each sub-issue with steps 1 to 4, then link it to the main issue.
gh api graphql -f query='mutation{addSubIssue(input:{issueId:"<main issue node id>",subIssueId:"<sub-issue node id>"}){issue{number}}}'
gh project item-edit ... --field-id <Week field id> --iteration-id <week id>
```

Week: take the iteration whose dates hold today from the `Week` field configuration.
