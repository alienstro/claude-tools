---
name: close-issue
description: Use when a pull request fixes a GitHub issue and the user wants the two linked and the issue closed. Adds "Closes #N" to the PR body, comments "Fixed by #PR" on the issue, closes the issue after the PR merges, and sets the issue's project-board Status to "For Testing" so QA picks it up. Use it when the user says "/close-issue", "close the issue", "close #350 with #356", "link the PR to the issue", "put the PR in the issue", "the PR is merged, close the ticket", or "mark the issue as fixed", even if they do not say "link" or name the board. Needed because a PR to a branch other than the default branch (such as dev) never closes or links its issue by itself.
---

# Close Issue

Link a pull request and the issue that it fixes on both sides. Close the issue when the PR is
merged. Move the issue to "For Testing" on the project board.

## Why this skill exists

GitHub reads `Closes #N` only in a PR to the **default branch**. This team merges feature PRs
into `dev`, and the default branch is `main`. So GitHub does not close the issue, and it does
not fill the "closing issues" link of the PR. The `#N` text still makes a cross-reference, and
the `issues-version` skill reads that cross-reference to find the release of each issue. This
skill does by hand what GitHub does not do for `dev`.

## Inputs

- The PR: a number or a URL in the arguments. If there is none, use the PR of the current
  branch: `gh pr view --json number`.
- The issue: a number or a URL in the arguments. If there is none, look for it in this order:
  1. `#N` in the PR body.
  2. A number in the branch name, such as `fix/350-pay-page`.
  3. An open issue whose title matches the words of the branch name:
     `gh issue list --state open --search "<words> in:title"`.

  Ask the user to confirm an issue that you found in step 2 or 3. A wrong match closes the
  wrong issue.
- One PR can fix more than one issue. Do each step for each issue.

## Steps

1. **Read the state.**

   ```sh
   gh pr view <pr> --json number,title,url,state,mergedAt,baseRefName,body
   gh issue view <issue> --json number,title,state,url,comments
   gh repo view --json nameWithOwner,defaultBranchRef
   ```

   Stop and tell the user if the PR state is `CLOSED` and `mergedAt` is empty. A PR that was
   closed without a merge does not fix the issue, so do not link or close anything.

2. **Put the issue in the PR.** Search the PR body for `#<issue>` or the issue URL. If the body
   does not name the issue, add one line at the end of the body:

   ```
   Closes #<issue>
   ```

   Write the body to a file in the scratchpad and run `gh pr edit <pr> --body-file <file>`.
   Do not use `--body` with an inline string, because the shell can change backticks and `$`
   in the body. Keep the rest of the body unchanged. For more than one issue, put each on its
   own line.

3. **Put the PR in the issue.** Search the issue comments for `#<pr>` or the PR URL. If no
   comment names the PR, post one comment:

   ```
   Fixed by #<pr>.
   ```

   If the PR is merged, add the base branch: `Fixed by #<pr>, merged into \`dev\`.` If the PR
   is still open, write `Fix in review: #<pr>.` Keep the comment to one line. The PR holds the
   details.

4. **Close the issue only when the PR is merged.**
   - PR merged and issue open: `gh issue close <issue> --reason completed`.
   - PR merged and issue already closed: do nothing. GitHub closes it by itself for a PR to the
     default branch.
   - PR open: do not close. Tell the user to run `/close-issue` again after the merge. A PR in
     review can still change, close, or get a revert.

5. **Move the card on the board.** Do this step only after step 4 closed the issue, or found it
   closed. A board can have a rule "Item closed → Done", and that rule fires on the close.
   A status that you set after the close replaces the status of that rule.

   ```sh
   python3 ~/.claude/skills/close-issue/scripts/set_board_status.py \
     --repo <owner>/<name> --issue <issue> --status "For Testing"
   ```

   The script prints one line for each board that holds the issue. If a board has no
   "For Testing" status, the script does not change that card. Tell the user the statuses
   that the board has. If the PR is still open, skip this step.

6. **Check the result.** Read the issue state and the PR body again:

   ```sh
   gh issue view <issue> --json state,stateReason
   gh pr view <pr> --json body -q .body | grep -n "#<issue>"
   ```

   Run the board script again with `--dry-run`. It must say `already set` for each board.

## Report

Write the report in ASD-STE100 Simplified Technical English. Use this shape:

```markdown
Issue #<issue> is <closed / still open, because PR #<pr> is not merged>.

| | Before | Now |
| --- | --- | --- |
| PR #<pr> body | <no link to the issue / named the issue> | **Closes #<issue>** / no change |
| Issue #<issue> comment | <no link to the PR> | **"Fixed by #<pr>, merged into `dev`."** |
| Issue #<issue> state | Open | **Closed (completed)** |
| Board <name> Status | <old status> | **For Testing** |

<Next step, if any: "Run /close-issue again after PR #<pr> merges.">
```

Write "no change" in a row when the link or the state was already there.

## Rules

- Do not close an issue for a PR that is not merged.
- Do not post a second comment or add a second `Closes` line. Run the skill two times and the
  result stays the same.
- Do not name Claude, Claude Code, or an AI tool in a comment or in the PR body.
- Comments and PR edits are public to everyone with access to the repository. Write only the
  short link text above, with no secret, token, or customer data.
