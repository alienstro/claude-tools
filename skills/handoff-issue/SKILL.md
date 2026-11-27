---
name: handoff-issue
description: Use when the user wants a GitHub issue built in its own Orca worktree by a new agent session. Reads the issue, creates an Orca worktree and branch from the base branch, links the issue, starts a Claude (or Codex) session there with a complete task brief, and checks that the brief arrived. By default the agent ends with /code-review medium --fix, /do-tests, /create-commit and /create-pr. The PR target is the branch that the user names, such as "pr to dev", or else the target from the conversation, the issue or the repository rules. "local" or "no PR" gives a local commit only. Use it when the user says "/handoff-issue", "create a worktree and implement it there", "open a claude session in that worktree", "hand this issue off", "give issue 123 to another agent", "start a worker on this issue", or "handoff and pr to dev", even if they do not say "Orca".
---

# Hand off an issue

Give one GitHub issue to a new agent session in its own Orca worktree. The new session
knows nothing about this conversation. The brief that you write is all that it gets.

This is a full handoff. Report the worktree and the agent handle, then watch the agent until
it ends (step 11). The user must not need to ask "is it done?".

## Team values

Read `team.local.md` in this skill folder first, if it exists. It holds the repository,
the base branch, the gate command and the test limits of your team. A value in
`team.local.md` wins over an example in this file. Keep `team.local.md` out of a public
repository.

When `team.local.md` does not exist, read the `AGENTS.md` or `CLAUDE.md` of the repository
for the gate command and the test rules. Ask the user for a value that you cannot find.

## Does CI run on the PR target?

Do not assume that CI checks the PR. Many repositories run CI only for a PR to the default
branch. Read `on.pull_request` in each file of `.github/workflows/` (or the CI file of the
host), and look for the PR target in `branches`. The workflow file wins over a sentence in
`team.local.md` or `AGENTS.md`.

When no workflow runs for the PR target, `/do-tests` is the only check before the merge. Say
this in the report of the handoff, so that the user knows it.

## Caution: a second session uses memory

Each new agent session uses its own memory and CPU. On a small machine, start a session
only when the user asks for it. Start one session for each issue. Tell the user that a
second session runs.

## Two modes

| The user says | Mode | The agent ends with |
|---|---|---|
| `/handoff-issue <issues>` | PR (default) | `/code-review medium --fix`, `/do-tests`, `/create-commit`, then `/create-pr` to the PR target that you find |
| `/handoff-issue <issues> and pr to <branch>` | PR | The same steps, to `<branch>` |
| `/handoff-issue <issues> local`, "no PR" or "do not push" | Local | A local commit. No push, no PR |

PR mode is the default. A `/handoff-issue` call is the approval to push and to open the PR,
so the agent must not stop to ask for it. Use the brief ending "PR mode" below.

### Find the PR target

You find the PR target before the handoff. The new agent cannot see this conversation, so
the brief must name the target. Take the first match in this order:

1. The branch that the user names, such as "pr to dev".
2. A target that the user stated earlier in this conversation for this work.
3. A target branch that the issue names, in its body, its comments or a linked PR.
4. The rule of the repository in `AGENTS.md` or `team.local.md`. For example, work for one
   app goes to its own integration branch.
5. The repository base ref from `orca repo list` (`worktreeBaseRef`).

Create the worktree from the PR target, so that the PR carries only the agent's commits.
If the PR target differs from the worktree base ref, pass `--base-branch <PR target>`.
In the report, name the PR target and the rule that chose it, so the user can stop a wrong one.

## Steps

1. **Get the issue.** Take the number from the user, or from an issue that you created in
   this conversation. Read it with `gh issue view <number> --repo <owner>/<repo>`.
2. **Collect the decisions.** List each decision that the user made in this conversation
   about the issue, such as an approach that they approved or an open question that they
   answered. The new session cannot see the conversation, so each decision goes in the
   brief. If an open question in the issue has no answer, ask the user before the handoff.
3. **Resolve Orca.** Use the `orca-cli` skill to choose the executable. Load its guide with
   `orca skills get orca-cli`. Find the repository id:
   `orca repo list --json`, then take the `id` of the row whose `path` is the repository.
4. **Choose the names.**
   - Worktree name: a short kebab-case name for the problem, such as
     `hide-console-conversations`.
   - Branch: `<prefix>/<worktree name>`. Take the prefix from the issue title, such as
     `feat`, `fix` or `chore`.
   - Base: the PR target from "Find the PR target". In Local mode, use the repository base
     ref from `orca repo list` (`worktreeBaseRef`). Pass `--base-branch` only when the base
     differs from `worktreeBaseRef`, or when the user asks for stacked work.
5. **Write the brief** in the format below. Save it to a file in the scratchpad, so that the
   shell does not change the quotes.
6. **Fetch the base and create the worktree:**

   ```bash
   git fetch origin <base branch>
   orca worktree create --repo id:<repoId> --name <worktree name> \
     --branch <branch> --issue <number> --no-parent \
     --agent claude --prompt "$(cat <brief file>)" --json
   ```

   Use `--agent codex` when the user asks for Codex. Add `--model` and `--effort` only when
   the user names them.
7. **Check the launch.** Read `result.launch` from the output:
   - `outcome.handle` is the agent handle.
   - `prompt.outcome` must be `journaled` or `handed-to-terminal`.

   Then read the terminal one time and check that the agent works:
   `orca terminal read --terminal <handle> --json`.
   If the reply is lost, retry with `--retry-launch <operationId>`. Do not start a second
   agent.
8. **Assign the issue to the user.** Do this for each issue that you hand off, after the
   launch works. `@me` is the account that `gh` signs in with:

   ```bash
   gh issue edit <number> --repo <owner>/<repo> --add-assignee @me
   ```

   Keep the other assignees. If the call fails, tell the user, and do not stop the handoff.
9. **Move the issue to "In progress".** Do this for each issue after the launch works. Do
   not ask the user first. Read the board items of the issue, their status and the Status
   options:

   ```bash
   gh api graphql -F n=<number> -f o=<owner> -f r=<repo> -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){projectItems(first:10){nodes{id status:fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}} project{id title field(name:"Status"){... on ProjectV2SingleSelectField{id options{id name}}}}}}}}}'
   ```

   For each item, find the option whose name is "In progress" (ignore the case). Move the item
   only when its status is empty, comes before "In progress" in the option list, or is
   "Failed Testing". Do not move an item back from a later status, such as "For review",
   "Done" or "Won't Do":

   ```bash
   gh project item-edit --project-id <project id> --id <item id> \
     --field-id <Status field id> --single-select-option-id <In progress option id>
   ```

   If the issue is on no board, or the board has no "In progress" option, do not add it. Tell
   the user. If a call fails, tell the user, and do not stop the handoff.
10. **Report** to the user: the worktree path, the branch, the agent handle, the assignee, the
   board status of each issue (moved, or not moved and why), and a short list of what the
   brief tells the agent to do. In PR mode, name the PR target and the rule that chose it.
   Tell the user that the agent pushes and opens the PR by itself.
11. **Watch the agent until it ends.** Do not stop after the report. Start one background
   Bash command (`run_in_background: true`) for each agent. It checks the terminal every 60
   seconds and uses no tokens until it exits. Do not poll the terminal yourself:

   ```bash
   h=<handle>; n=<number>; last=; quiet=0
   while true; do
     sleep 60
     out=$( { orca terminal read --terminal "$h" --screen --json; orca terminal read --terminal "$h" --limit 200 --json; } 2>/dev/null)
     # The brief holds the report template, so match only filled values: a URL, "none" with no quote, or a SHA.
     if jq -r '.result.terminal.tail[]?' <<<"$out" | grep -Eq 'PR: https://|(^|[^"])PR: none|Commit: [0-9a-f]{7}'; then echo "DONE #$n"; exit 0; fi
     jq -r '.result.terminal.status // empty' <<<"$out" | grep -q exited && { echo "EXITED #$n"; exit 1; }
     at=$(orca terminal show --terminal "$h" --json 2>/dev/null | jq -r '.result.terminal.lastOutputAt // 0')
     if [ "$at" = "$last" ]; then quiet=$((quiet+1)); else quiet=0; last=$at; fi
     echo "$(date +%H:%M) #$n working, quiet ${quiet} min"
     [ "$quiet" -ge 5 ] && { echo "QUIET #$n: no output for 5 min"; exit 2; }
   done
   ```

   When the command exits, read the terminal at once with `--screen`, then tell the user:
   - `DONE`: relay the final report of the agent, with the PR link. If the report is not
     complete yet, read the terminal again after one minute.
   - `QUIET`: the agent asks a question or is stuck. Show its last lines and the question.
   - `EXITED`: the session ended without a report. Show the last lines.

   Start a new watch after the user answers a question that the agent asked. Stop watching
   when the user says so.

## Brief format

Write the brief in ASD-STE100 Simplified Technical English. Write facts and decisions, not
a full plan. The agent reads the code itself.

```text
Implement GitHub issue #<number> in <owner>/<repo>: <issue url>. Read it first with gh issue view <number>.

Goal: <one or two sentences: the result that the user gets>.
Decisions the user approved: <each decision from step 2, with the reason in a few words>.
Change these parts: <the files and the functions that the issue names>.
Do not change: <the out-of-scope parts of the issue, by name>.
Update these docs: <the docs that state the rule that changes>.

Rules: follow AGENTS.md. Use test-driven development: change or add tests first.
Before you change code, list the existing behaviour that the change can affect: the callers
of each function that you change, the state that they share, and the user texts that they show.
Run the tests of those parts first, so that you know that they pass before your change.
Write one test for each "Done when" item. For a bug, the test must fail before the fix.
Search the repository for the same problem in other places: each platform, channel, role and
flow that has the same logic. Fix the shared code one time. If you do not fix a place, name it
under "Not done".
<the test limits from team.local.md>.
<the ending of the mode, from below>
Do not spawn subagents, except the reviewers that /code-review starts.
<the final report, from below>
```

### Ending: Local mode

```text
Before you finish, run <the gate command> one time.
Commit on branch <branch> with a conventional commit message and no AI attribution trailer.
Do not push and do not open a PR.
```

### Ending: PR mode

```text
When the work is done, do these five steps in this order:
1. Run `git add -N .` so that the review sees new files. Then run /code-review medium --fix.
   Fix each finding that it reports. Skip a false finding, and give the reason in the report.
   Do not ask the user which findings to fix. One review round only. Use `high` in place of
   `medium` when the change touches money, sign-in, permissions, a data migration or the
   states of a flow.
2. Run /do-tests. It checks the code that you changed and the tests that read it. If a
   check fails, fix it, and run /do-tests again. Do not go to step 3 while a check fails.
   When the change touches a build file, a container file, a deploy workflow, an installer
   or a new entry point of the app, run /do-ci in place of /do-tests.
3. Run /create-commit on branch <branch>. Use no AI attribution trailer.
4. Run /create-pr with the base branch <PR target>. The user approved the push and the PR
   to <PR target> in advance: this brief is that approval, so do not stop to ask for it.
   Use no AI attribution line in the PR body.
5. Read the checks of the PR with `gh pr checks <PR>`. If the PR has checks, wait for them
   with `gh pr checks <PR> --watch`, and fix a failed check. If the PR has no checks, write
   "none run on this PR" in the Checks row of the report.
If /do-tests still fails after two fix rounds, do not push. Commit the work, and
report the failed check and its output.
```

### Final report

Put this text at the end of the brief in both modes. The user clicks the link, so it must
be the full URL as plain text on its own line.

```text
At the end, write the final report in this format. Write nothing after it.

## Done: #<number> <issue title>

PR: <the full PR URL on its own line>  (Local mode: Commit: <short SHA> on <branch>)
     If no PR exists, write "PR: none" and the reason.

| Item | Result |
|---|---|
| Branch | <branch> -> <PR target> |
| Tests | <the pass and fail counts from the last test run> |
| Review | <the findings that /code-review fixed and skipped, or "Local mode: none"> |
| Done when | <each item with the test that proves it, or "not tested"> |
| Other places | <each place with the same problem: fixed, or not fixed and why. Or "None found"> |
| Checks | <the PR checks: passed, failed, or "none run on this PR". Local mode: "none"> |
| Not done | <each item that you could not do, or "None"> |

Changed files:
- <path>: <the change, in one line>
```

Change other rules only when the user asks.

## Common mistakes

| Mistake | Result | Do this |
|---|---|---|
| The brief says "as we discussed" | The agent cannot see the discussion and guesses | Write each decision in the brief |
| The brief holds a complete plan with code | The agent copies a plan that does not match the code | Give the goal, the files and the limits |
| `--base-branch` set to the current branch | The work stacks on an unrelated branch | Use the PR target, or the repository base ref in Local mode |
| No `--issue` | Orca does not link the worktree to the issue | Pass `--issue <number>` |
| The launch reply is lost and you run the command again | Two agents work on one issue | Use `--retry-launch <operationId>` |
| You stop after the report | The user must ask "is it done?" | Run the step 11 watch until it exits |
| You poll the terminal yourself every minute | Each check uses tokens and context | Run the watch as one background command |
| PR mode with no approval line in the brief | `/create-pr` stops to confirm the base, and the agent waits for nobody | Keep the "approved in advance" line |
| PR mode with `pnpm run verify` as the gate | Turbo with no limits runs many tasks at once and lags the machine | Use `/do-tests`. Do not assume that CI runs on the PR. See "Does CI run on the PR target?" |
