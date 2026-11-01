---
name: do-ci
description: Use when the user wants to run the checks of the repository as the CI runner does, before a merge or a release. Reads the CI workflow, then runs its steps on a clean copy of the last commit, with a fresh install, no build cache and no local env file. Ends with the result of each step, the CI result, and a "Before / Now" table of what the change does. Triggers on "/do-ci", "test it like CI", "run what CI runs", "run CI locally", "will CI pass".
---

# Do CI

Run the steps of the CI workflow on the laptop, as the CI runner does, and report the real result. A local run can pass and CI can then fail, because of four differences:

- Files that are not committed.
- A `node_modules` that does not match the lockfile.
- A build cache that replays an old result.
- A local `.env` file.

This skill removes each of them. It is slower than `/do-tests`, because it installs again and uses no cache. For fast feedback while you work, use `/do-tests`.

## Setup

1. Set the Node memory ceiling for each step. The default `NODE_OPTIONS` of this machine is 512 MB, and a build dies at that size.
   - Tests: `NODE_OPTIONS=--max-old-space-size=1024`.
   - Install, typecheck and build: `NODE_OPTIONS=--max-old-space-size=2048`.
   - Set the value on each command, so a test run does not get the larger ceiling.
2. Run one command at a time. The machine has 8 GB of memory.
3. Run 1 test file at a time, so that only 1 CPU core is busy.
   - `node --test` or `tsx --test`: put `--test-concurrency=1` directly after `--test`. Node ignores the flag when it comes after the file names.
   - Jest or Vitest: add `--maxWorkers=1`.

## Steps

1. Find the CI workflow. Read `.github/workflows/*.yml`, or the CI file of the host, such as `.gitlab-ci.yml`. Pick the job that runs on a pull request. Write down its Node version, its `env`, and each `run:` step in order.
   - If the repository has no CI file, STOP. Tell the user, and suggest `/do-tests full`.
2. WARNING: this skill tests only the last commit. Run `git status --short`. Before you start, tell the user about each uncommitted or untracked file, because the run does not include it.
3. Make a clean worktree of `HEAD` in the scratchpad: `git worktree add --detach <scratchpad>/ci HEAD`. Run every step inside it.
   - Do not copy `.env`, `node_modules`, `.turbo`, `dist/` or other build output into it.
4. Compare `node --version` with the Node version of the workflow. Report a different major version as a risk, because a test can depend on the version.
5. Run the install step of the workflow without changes, such as `pnpm install --frozen-lockfile`.
   - A lockfile error is a CI failure. Report it. Do not fix it with a plain install.
6. Run the other steps in the order of the workflow, one at a time. Set `CI=true` and the `env` of the job on each step. Keep the limits from Setup:
   - Turbo: add `--concurrency=1 --force`. `--force` runs each task again and does not replay the cache.
   - Tests: if the test script reads a concurrency variable, such as `TEST_CONCURRENCY`, set it to `1` and keep the step as it is. Otherwise run the test script of each package, one package at a time, with the 1-file limit from Setup step 3.
   - Skip a step that deploys, publishes, pushes, uploads or needs a secret. Name each skipped step in the report.
7. CI stops at the first failed step. Run the later steps too, but mark them "after a failure", so the report gives the CI result and the full picture.
8. Remove the worktree at the end, also when a step fails: `git worktree remove --force <scratchpad>/ci`.

## Report

Always show the report in the chat: when the run passes, when a step fails, and when the run stops early. When another skill follows in the same request, such as `/create-commit` or `/create-pr`, show the report first.

1. Search the output of each step for `✖`, `✕`, `FAIL`, `ERROR` and `error TS`.
2. Name the workflow file, the job and the commit (short hash).
3. Give a table with one row for each step, in the order of the workflow: the step, its result, and its summary line, such as `ℹ pass N` / `ℹ fail 0` or `Tasks: N successful, N total`. Mark skipped steps and steps "after a failure".
4. Name each failed step and its first error.
5. Write one line: `CI result: pass` or `CI result: fail at <step>`.
6. Name a Node version difference, if one exists.
7. Never say "pass" without the summary line of the runner.

### Before / Now

After the step table, write a table of what the branch changes, under the heading `### Before / Now`, with the header row `| | Before this change | Now (tested) |`.

- Base: `dev` if it exists, else `main`. Get the merge base with `git merge-base HEAD origin/<base>`, and read the changes with `git diff <merge-base> HEAD`.
- Use one row for each changed behaviour, up to 8 rows, the most important first.
- First column: name the screen, the setting, the message or the action in plain words, not a file name or a code name.
- Before: read the old behaviour from the merge base, with `git show <merge-base>:<file>`. Write `—` when the thing did not exist.
- Now (tested): write the new behaviour, with the changed words in bold. Write `(not tested)` after a row that no test in this run covers, and `(test failed)` after a row whose test failed.
- If the branch has no change against the base, write one row: `| Branch | Same as <base> | No change |`.

## Rules

- Do not edit the CI workflow, a test or the lockfile to make a step pass. Report the failure.
- Do not start a dev server or more than one process at the same time.
- Do not commit or push. Use `/create-commit` and `/create-pr` for that.
- Always remove the worktree at the end.
