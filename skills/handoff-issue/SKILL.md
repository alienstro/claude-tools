---
name: handoff-issue
description: Use when the user wants a GitHub issue built in its own Orca worktree by a new agent session. Reads the issue, creates an Orca worktree and branch from the base branch, links the issue, starts a Claude (or Codex) session there with a complete task brief, and checks that the brief arrived. When the user names a PR target, such as "pr to dev", the agent ends with /do-tests full, /create-commit and /create-pr to that branch. Use it when the user says "/handoff-issue", "create a worktree and implement it there", "open a claude session in that worktree", "hand this issue off", "give issue 123 to another agent", "start a worker on this issue", or "handoff and pr to dev", even if they do not say "Orca".
---

# Hand off an issue

Give one GitHub issue to a new agent session in its own Orca worktree. The new session
knows nothing about this conversation. The brief that you write is all that it gets.

This is a full handoff. Report the worktree and the agent handle, then stop. Do not wait for
the agent to finish, unless the user asks you to watch it.

## Team values

Read `team.local.md` in this skill folder first, if it exists. It holds the repository,
the base branch, the gate command and the test limits of your team. A value in
`team.local.md` wins over an example in this file. Keep `team.local.md` out of a public
repository.

When `team.local.md` does not exist, read the `AGENTS.md` or `CLAUDE.md` of the repository
for the gate command and the test rules. Ask the user for a value that you cannot find.

## Caution: a second session uses memory

Each new agent session uses its own memory and CPU. On a small machine, start a session
only when the user asks for it. Start one session for each issue. Tell the user that a
second session runs.

## Two modes

| The user says | Mode | The agent ends with |
|---|---|---|
| `/handoff-issue <issues>` | Local | A local commit. No push, no PR |
| `/handoff-issue <issues> and pr to <branch>` | PR | `/do-tests full`, `/create-commit`, then `/create-pr` to `<branch>` |

In PR mode, `<branch>` is the PR target. Use the brief ending "PR mode" below. The user's
words are the approval to push and to open the PR, so the agent must not stop to ask for it.
If `<branch>` differs from the worktree base ref, tell the user before the handoff, because
the PR then carries commits that the user did not see.

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
   - Base: the repository base ref from `orca repo list` (`worktreeBaseRef`). Do not pass
     `--base-branch` unless the user asks for stacked work.
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
8. **Report** to the user: the worktree path, the branch, the agent handle, and a short list
   of what the brief tells the agent to do. In PR mode, name the PR target and tell the user
   that the agent pushes and opens the PR by itself. Tell the user that the issue status on
   the board does not change. Offer to move it to "In progress".

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
<the test limits from team.local.md>.
<the ending of the mode, from below>
Do not spawn subagents.
At the end, report the changed files, the test results and anything that you could not do.
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
1. Run /do-tests full. If a check fails, fix it and run /do-tests full again. Do not go to
   step 2 while a check fails.
2. Run /create-commit on branch <branch>. Use no AI attribution trailer.
3. Run /create-pr with the base branch <PR target>. The user approved the push and the PR
   to <PR target> in advance: this brief is that approval, so do not stop to ask for it.
   Use no AI attribution line in the PR body.
If /do-tests full still fails after two fix rounds, do not push. Commit the work, and
report the failed check and its output.
At the end, also report the PR link.
```

Change other rules only when the user asks.

## Common mistakes

| Mistake | Result | Do this |
|---|---|---|
| The brief says "as we discussed" | The agent cannot see the discussion and guesses | Write each decision in the brief |
| The brief holds a complete plan with code | The agent copies a plan that does not match the code | Give the goal, the files and the limits |
| `--base-branch` set to the current branch | The work stacks on an unrelated branch | Use the repository base ref |
| No `--issue` | Orca does not link the worktree to the issue | Pass `--issue <number>` |
| The launch reply is lost and you run the command again | Two agents work on one issue | Use `--retry-launch <operationId>` |
| You wait for the agent to finish | This session uses memory and tokens for no work | Report the handle and stop |
| PR mode with no approval line in the brief | `/create-pr` stops to confirm the base, and the agent waits for nobody | Keep the "approved in advance" line |
| PR mode with `pnpm run verify` as the gate | Turbo runs many tasks at once and lags the machine | Use `/do-tests full`, which runs one task at a time |
