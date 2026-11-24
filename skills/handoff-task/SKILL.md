---
name: handoff-task
description: Use when the user wants a task with no GitHub issue built in its own Orca worktree by a new agent session. Takes the task from the user's message or this conversation, creates an Orca worktree and branch from the base branch, starts a Claude (or Codex) session there with a complete task brief, checks that the brief arrived, and watches the agent until it ends. By default the agent ends with /do-tests, /create-commit and /create-pr. The PR target is the branch that the user names, such as "pr to dev", or else the target from the conversation or the repository rules. "local" or "no PR" gives a local commit only. Use it when the user says "/handoff-task", "hand this off to another agent", "do this in a new worktree", "start a worker on this", "no issue needed", or "handoff and pr to dev" with no issue number, even if they do not say "Orca". When the user gives a GitHub issue number, use handoff-issue instead. For a written summary of this session, use handoff-summary instead.
---

# Hand off a task

Give one task with no GitHub issue to a new agent session in its own Orca worktree. The new
session knows nothing about this conversation. No issue holds the specification, so the brief
that you write is the only specification that the agent gets.

This is a full handoff. Report the worktree and the agent handle, then watch the agent until
it ends (step 9). The user must not need to ask "is it done?".

When the user gives a GitHub issue number, use the `handoff-issue` skill instead.

## Team values

Read `../handoff-issue/team.local.md` (the `team.local.md` file of the `handoff-issue` skill)
first, if it exists. Use it only when its `Repository` line names the current repository. It
holds the repository, the base branch, the gate command and the test limits of your team. A
value in that file wins over an example in this file.

When the file does not exist, or names a different repository, read the `AGENTS.md` or
`CLAUDE.md` of the repository for the gate command and the test rules. Get the Orca repo id
from `orca repo list --json`. Ask the user for a value that you cannot find.

## Caution: a second session uses memory

Each new agent session uses its own memory and CPU. On a small machine, start a session
only when the user asks for it. Start one session for each task. Tell the user that a
second session runs.

## Caution: the new worktree does not have your local changes

Orca creates the worktree from the base branch on `origin`. The new agent does not see
uncommitted files, local commits or unpushed branches in this checkout. Before the handoff,
check whether the task needs such work. If it does, tell the user and ask how to continue,
for example to push the work first.

## Two modes

| The user says | Mode | The agent ends with |
|---|---|---|
| `/handoff-task <task>` | PR (default) | `/do-tests`, `/create-commit`, then `/create-pr` to the PR target that you find |
| `/handoff-task <task> and pr to <branch>` | PR | The same steps, to `<branch>` |
| `/handoff-task <task> local`, "no PR" or "do not push" | Local | A local commit. No push, no PR |

PR mode is the default. A `/handoff-task` call is the approval to push and to open the PR,
so the agent must not stop to ask for it. Use the brief ending "PR mode" below.

### Find the PR target

You find the PR target before the handoff. The new agent cannot see this conversation, so
the brief must name the target. Take the first match in this order:

1. The branch that the user names, such as "pr to dev".
2. A target that the user stated earlier in this conversation for this work.
3. The rule of the repository in `AGENTS.md` or `team.local.md`. For example, work for one
   app goes to its own integration branch.
4. The repository base ref from `orca repo list` (`worktreeBaseRef`).

Create the worktree from the PR target, so that the PR carries only the agent's commits.
If the PR target differs from the worktree base ref, pass `--base-branch <PR target>`.
In the report, name the PR target and the rule that chose it, so the user can stop a wrong one.

## Steps

1. **Get the task.** Take it from the arguments, or from the work in this conversation. Write
   a short task title, one goal and a "Done when" list. If you cannot write the goal and the
   "Done when" list from what you know, ask the user one question before the handoff.
2. **Collect the context and the decisions.** List the facts that you found in this
   conversation, such as the file paths, the exact error strings and the steps that show the
   problem. List each decision that the user made, such as an approach that they approved or
   a question that they answered. The new session cannot see the conversation, so each fact
   and each decision goes in the brief.
3. **Resolve Orca.** Use the `orca-cli` skill to choose the executable. Load its guide with
   `orca skills get orca-cli`. Find the repository id:
   `orca repo list --json`, then take the `id` of the row whose `path` is the repository.
4. **Choose the names.**
   - Worktree name: a short kebab-case name for the task, such as `hide-console-conversations`.
   - Branch: `<prefix>/<worktree name>`. Take the prefix from the type of the task: `feat` for
     new behavior, `fix` for a bug, `chore`, `docs` or `refactor` for other work.
   - Base: the PR target from "Find the PR target". In Local mode, use the repository base
     ref from `orca repo list` (`worktreeBaseRef`). Pass `--base-branch` only when the base
     differs from `worktreeBaseRef`, or when the user asks for stacked work.
5. **Write the brief** in the format below. Save it to a file in the scratchpad, so that the
   shell does not change the quotes.
6. **Fetch the base and create the worktree:**

   ```bash
   git fetch origin <base branch>
   orca worktree create --repo id:<repoId> --name <worktree name> \
     --branch <branch> --comment "<task title>" --no-parent \
     --agent claude --prompt "$(cat <brief file>)" --json
   ```

   Use `--agent codex` when the user asks for Codex. Add `--model` and `--effort` only when
   the user names them. Do not pass `--issue`, because no issue exists. Keep `"`, `` ` ``
   and `$` out of the task title, because the shell reads them.
7. **Check the launch.** Read `result.launch` from the output:
   - `outcome.handle` is the agent handle.
   - `prompt.outcome` must be `journaled` or `handed-to-terminal`.

   Then read the terminal one time and check that the agent works:
   `orca terminal read --terminal <handle> --json`.
   If the reply is lost, retry with `--retry-launch <operationId>`. Do not start a second
   agent.
8. **Report** to the user: the worktree path, the branch, the agent handle, and a short list
   of what the brief tells the agent to do. In PR mode, name the PR target and the rule that
   chose it. Tell the user that the agent pushes and opens the PR by itself.
9. **Watch the agent until it ends.** Do not stop after the report. Start one background
   Bash command (`run_in_background: true`) for each agent. It checks the terminal every 60
   seconds and uses no tokens until it exits. Do not poll the terminal yourself:

   ```bash
   h=<handle>; n=<worktree name>; last=; quiet=0
   while true; do
     sleep 60
     out=$( { orca terminal read --terminal "$h" --screen --json; orca terminal read --terminal "$h" --limit 200 --json; } 2>/dev/null)
     # The brief holds the report template, so match only filled values: a URL, "none" with no quote, or a SHA.
     if jq -r '.result.terminal.tail[]?' <<<"$out" | grep -Eq 'PR: https://|(^|[^"])PR: none|Commit: [0-9a-f]{7}'; then echo "DONE $n"; exit 0; fi
     jq -r '.result.terminal.status // empty' <<<"$out" | grep -q exited && { echo "EXITED $n"; exit 1; }
     at=$(orca terminal show --terminal "$h" --json 2>/dev/null | jq -r '.result.terminal.lastOutputAt // 0')
     if [ "$at" = "$last" ]; then quiet=$((quiet+1)); else quiet=0; last=$at; fi
     echo "$(date +%H:%M) $n working, quiet ${quiet} min"
     [ "$quiet" -ge 5 ] && { echo "QUIET $n: no output for 5 min"; exit 2; }
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
a full plan. The agent reads the code itself. No issue exists, so the brief must hold the
whole specification: the goal, the context and the "Done when" list.

Do not write `PR: <url>`, `PR: none` or `Commit: <sha>` in the brief. The step 9 watch
reads these as the final report. Write "pull request #808" or "commit 4e383d7" instead.

```text
Do this task in <owner>/<repo>: <task title>.
No GitHub issue exists for this task. Do not create one, and do not add a "Closes" line.

Goal: <one or two sentences: the result that the user gets>.
Context: <the facts from step 2: file paths, exact error strings, steps that show the problem>.
Done when:
- <one check that the user can see or run>
- <one more check>
Decisions the user approved: <each decision from step 2, with the reason in a few words>.
Change these parts: <the files and the functions to change>.
Do not change: <the out-of-scope parts, by name>.
Update these docs: <the docs that state the rule that changes>.

Rules: follow AGENTS.md. Use test-driven development: change or add tests first.
<the test limits of the repository, from team.local.md or AGENTS.md>.
<the ending of the mode, from below>
Do not spawn subagents.
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
When the work is done, do these three steps in this order:
1. Run /do-tests. It checks only the code that you changed. If a check fails, fix it,
   and run /do-tests again. Do not go to step 2 while a check fails.
2. Run /create-commit on branch <branch>. Use no AI attribution trailer.
3. Run /create-pr with the base branch <PR target>. The user approved the push and the PR
   to <PR target> in advance: this brief is that approval, so do not stop to ask for it.
   The PR links no issue. Use no AI attribution line in the PR body.
If /do-tests still fails after two fix rounds, do not push. Commit the work, and
report the failed check and its output.
```

### Final report

Put this text at the end of the brief in both modes. The user clicks the link, so it must
be the full URL as plain text on its own line.

```text
At the end, write the final report in this format. Write nothing after it.

## Done: <task title>

PR: <the full PR URL on its own line>  (Local mode: Commit: <short SHA> on <branch>)
     If no PR exists, write "PR: none" and the reason.

| Item | Result |
|---|---|
| Branch | <branch> -> <PR target> |
| Done when | <each "Done when" check: pass or fail> |
| Tests | <the pass and fail counts from the last test run> |
| Not done | <each item that you could not do, or "None"> |

Changed files:
- <path>: <the change, in one line>
```

Change other rules only when the user asks.

## Common mistakes

| Mistake | Result | Do this |
|---|---|---|
| The brief says "as we discussed" | The agent cannot see the discussion and guesses | Write each fact and each decision in the brief |
| The brief has no "Done when" list | No issue holds the acceptance checks, so the agent decides when it is done | Write the "Done when" list in each brief |
| The task needs local work that is not pushed | The agent starts from `origin` and cannot find the work | Tell the user and ask before the handoff |
| The brief holds a complete plan with code | The agent copies a plan that does not match the code | Give the goal, the files and the limits |
| `--base-branch` set to the current branch | The work stacks on an unrelated branch | Use the PR target, or the repository base ref in Local mode |
| No "No GitHub issue exists" line | The agent can open an issue or add a `Closes` line that you did not want | Keep the line in the brief |
| The brief holds `PR: https://...` or `Commit: <sha>` | The watch reads it as the final report and stops with a false `DONE` | Write "pull request #808" or "commit 4e383d7" |
| The launch reply is lost and you run the command again | Two agents work on one task | Use `--retry-launch <operationId>` |
| You stop after the report | The user must ask "is it done?" | Run the step 9 watch until it exits |
| You poll the terminal yourself every minute | Each check uses tokens and context | Run the watch as one background command |
| PR mode with no approval line in the brief | `/create-pr` stops to confirm the base, and the agent waits for nobody | Keep the "approved in advance" line |
| PR mode with `pnpm run verify` as the gate | Turbo with no limits runs many tasks at once and lags the machine | Use `/do-tests`, which checks only the changed code. CI runs `pnpm run verify` on the PR |
