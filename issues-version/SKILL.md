---
name: issues-version
description: Use when the user wants to tag GitHub issues with the release that shipped them, or to move released issues out of the testing columns of a GitHub Project board. Finds the release of each issue from the release PRs, sets the "Release Version" field so QA can filter by version, and moves released "For Testing", "In Testing" and "For Release" issues to Done. Use it after a release, or when the user says "/issues-version", "add the release version to the issues", "which issues shipped in 1.6.0", "move the released issues to done", "clean up the testing column", or "tag the issues for QA", even if they do not name the board or the field.
user-invocable: true
allowed-tools: Bash, Read
---

# Issues version

Give each released issue on the project board the version that shipped it. QA then filters
the board by `Release Version` and tests the issues of one release. Move the released issues
out of the testing columns, so that those columns show only work that waits for a release.

Read `team.local.md` in this skill folder first, if it exists. It holds the values of your
team for `--repo`, `--owner` and `--project`. Keep `team.local.md` out of a public
repository. When it does not exist, ask the user for the repository, the owner of the board
and the project number. The commands below show these values as `<team flags>`:

```
--repo <owner>/<repo> --owner <owner> --project <project number>
```

## How the script finds a version

`scripts/issues_version.py` does the repeated work. Know how it works, so that you can
explain a strange result:

1. It reads the most recent GitHub releases (`--releases`, default 6). For each tag, it finds
   the release PR into `main`.
2. It reads the commits of each release PR and takes the PR number from each commit title,
   such as `fix: ... (#88)` or `Merge pull request #88`.
3. The commit list of a release PR also holds the PRs of earlier releases, because `main`
   gets squash merges. So the **first** release that lists a PR is the release that shipped it.
4. The oldest release that the script reads is the **floor**. A PR in the floor can come from
   that release or an earlier one, so the script never sets a version from the floor.
5. It finds the issues that each PR closes, and also the PRs that link to each issue in a
   testing status. An issue with fixes in two releases gets the **later** release.

## Steps

1. Run a dry run. The dry run reads only, and it prints the plan:

   ```bash
   python3 ~/.claude/skills/issues-version/scripts/issues_version.py <team flags>
   ```

   The run takes about one minute. Add `--plan-out <scratchpad>/plan.json` to keep the plan.

2. Look at the list `closed, no linked PR`. These issues were closed, but no PR links to them.
   Some fixes go to `dev` as direct commits with no PR number. For each issue:
   - Read the issue comments. A comment often names the PR, such as "Merged into dev in #57".
     `gh issue view <n> --json comments`
   - Search the commit messages for the issue number:
     `git log --all --format='%h %ad %s' --date=short -E --grep='#<n>([^0-9]|$)'`
   - If that finds nothing, match the issue title to a commit title near the close date.

   If a shell hook such as RTK shortens the output of `git log`, run the raw command (for
   RTK, `rtk proxy git log`). A cut title hides the `(#N)` at its end.

   When you find a commit, find the first release whose release PR lists that commit title.
   Then run the dry run again with `--manual 690=1.5.0,852=1.6.0`. Tell the user which
   versions are guesses from a commit title and which come from a link.

3. Show the plan to the user before you change the board. The board is shared, and QA and the
   team see each change at once. Show:
   - The number of issues for each version, and the number that move to Done.
   - Each version that changes from an old value (such as `1.6.0 -> 1.6.1`), with the reason.
   - The issues in a testing status with no released fix. The script leaves them as they are.

   Tell the user the correct practice when you show the plan. An issue normally goes to Done
   only after QA passes it. If the team moves an issue to Done at release time, QA uses the
   `Release Version` filter, and QA reopens an issue that fails. Let the user choose which
   statuses move with `--move`. The default moves `For Testing`, `In Testing` and
   `For Release`. Issues in `Failed Testing` get the version but keep their status (`--keep`).

4. After the user agrees, apply the plan:

   ```bash
   python3 ~/.claude/skills/issues-version/scripts/issues_version.py <team flags> --apply [--manual ...] [--move ...]
   ```

   The script reads the board again after the changes and prints the failures and the
   mismatches. Both lists must be empty. If a list is not empty, tell the user which issues
   failed. Do not run `--apply` again without a new dry run.

## Report

Write the report in short sentences. Use this structure:

1. One line: how many issues moved to Done and how many got a version.
2. A table: the status before, the count, and the status now.
3. The issues for each version, newest version first, as issue-number ranges.
4. A short "Things to check" list: the versions that are guesses, the corrected versions,
   the open issues with no released fix, and the issues that the floor made unsure.

## Problems

- `gh` says the token has no `project` scope: tell the user to run `! gh auth refresh -s project`.
- A tag has no release PR (`warning: no release PR`): someone pushed the release to `main`
  without a PR. The PRs of that release then count for the next release. Tell the user.
- An issue that you expect is missing from the plan: it is in the floor, or its status is not
  in `--move` or `--keep`. Increase `--releases` to move the floor back.
