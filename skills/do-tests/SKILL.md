---
name: do-tests
description: Use when the user wants to run the checks of the repository. By default, run only the tests, lint and typecheck that touch the changed code of the branch. With the argument `full`, run the full gate: lint, typecheck, test and build. Always ends with a "Before / Now" table of what the change does. Triggers on "/do-tests", "run the tests", "test the changes", "run the gate", "verify before push".
---

# Do Tests

Run the checks of the repository and report the real result. Every run ends with the report and its "Before / Now" table in the chat (see "Report").

## Modes

- **Changed (default):** `/do-tests` checks only the code that the branch changes. Use this mode for fast feedback.
- **Full:** `/do-tests full` runs the gate through Turbo on the changed packages and on every package that imports them. Run it one time before a merge. A changed-only run does not replace it, because it cannot find a break in code that imports the changed code.

## Setup (both modes)

1. Set the Node memory ceiling for each step. The ceiling applies to each Node process, and it does not reserve memory. The default `NODE_OPTIONS` of this machine is 512 MB, and the build dies at that size.
   - Tests: `NODE_OPTIONS=--max-old-space-size=1024`. One test file uses at most about 170 MB, so 1 runaway file stays near 1 GB.
   - Typecheck and build: `NODE_OPTIONS=--max-old-space-size=2048`. A typecheck can use about 500 MB and a build more than 1 GB, and only one runs at a time.
   - Set the value on each command, for example `NODE_OPTIONS=--max-old-space-size=1024 <test command>`, so a test run does not get the larger ceiling.

## Changed mode

1. Find the base branch: `dev` if it exists, else `main`. Get the changed files:
   `git diff --name-only $(git merge-base HEAD <base>)` plus `git ls-files --others --exclude-standard`.
   Remove deleted files, generated files, `dist/` and lockfiles from the list.
2. Find the tests to run, and group them by package (the nearest `package.json`):
   - Each changed test file (`*.test.ts`, `*.test.tsx`, `*.spec.ts`).
   - For each changed source file, the test that names it. Search with `rg -l "<basename without extension>" -g '*.test.*' -g '*.spec.*'` inside its package.
3. Read the `test` script of each package to find its runner. Run only the selected files with that runner:
   - `node --test` or `tsx --test`: pass the files in place of the glob, keep every flag and `--import` of the script.
   - Jest: use `--runTestsByPath <files>`, and keep `--config` and `--selectProjects`. Without `--runTestsByPath`, Jest can run the whole suite.
   - Vitest: `pnpm exec vitest run <files>`.
4. Run the lint only on the changed files, inside each package: `pnpm exec eslint <files>`. If the repository uses Prettier, also run `pnpm exec prettier --check <files>`.
5. Run the typecheck of each changed package (the `typecheck` script, or `tsc --noEmit`). A typecheck cannot check only one file, so filter the output to the changed files. Also report the other errors, and say if they also occur on the base branch.
6. If a changed package is a dependency of other packages and has a `build` script, build it before you test the packages that import it. Otherwise they test the old `dist/`.

## Full mode

Use Turbo with limits. Turbo runs only the packages that the branch changes and the packages that import them. It also replays the cached result of a package whose inputs did not change. Do not use `pnpm run verify` or a plain `turbo run test`: with no limits, Turbo runs up to 10 tasks at once and lags the machine.

1. Get the merge base from Changed mode step 1: `git merge-base HEAD <base>`.
2. Run the lint on the whole repository: `pnpm run lint`. The lint is not a Turbo task.
3. Run the typecheck and the build of the affected packages, one task at a time. Use the task names from the `verify` script, for example:
   `NODE_OPTIONS=--max-old-space-size=2048 pnpm exec turbo run typecheck build:eve --filter='...[<merge-base>]' --concurrency=1`
4. Run the tests of the affected packages, one package and one file at a time:
   `TEST_CONCURRENCY=1 NODE_OPTIONS=--max-old-space-size=1024 pnpm exec turbo run test --filter='...[<merge-base>]' --concurrency=1`
   This works only when each `test` script reads `TEST_CONCURRENCY`. If a script does not, run that package by hand with its runner's 1-file flag.
5. Do not remove a package from the list that Turbo selects. A change to a root file, such as the lockfile, can select every package, and that is correct.
6. Read the Turbo summary lines `Tasks: N successful, N total` and `Cached: N cached`, and the runner summary of each package, such as `ℹ pass N` / `ℹ fail 0`. Turbo replays the log of a cached task, so a cached package also shows its runner summary.
7. If `TURBO_CACHE_DIR` is not set, a new worktree starts with an empty cache. The filter still skips the packages that the branch does not affect.

After a fix for a failed check, run only the failed test files with the rules of Changed mode. Then run Full mode one time before the merge.

## Report (both modes)

Always show the report in the chat. Show it when the checks pass, when a check fails, and when the run stops early. When another skill or step follows in the same request, such as `/create-commit` or `/create-pr`, show the report first, and then start the next step. A report that only goes into a later summary is a skipped report.

Never skip the report or the table. These cases still need both:

- The branch has no change against the base, for example after a merge. Run the skill, say that no test ran and why, and write the "No changes" row.
- The tests ran earlier in the session. Give their summary lines, say when they ran, and write the table again.
- The skill is already loaded, or the user calls it again in the same session. Each call gets its own report and table.
- You think that the run is not needed. Do not decide this alone. Run the skill, or ask the user first.

Put the table under the heading `### Before / Now`. Before you start the next step or end the turn, check that the reply has that heading and the header row `| | Before this change | Now (tested) |`. If it does not, add the table first.

1. Search the output for `✖`, `✕`, `FAIL`, `ERROR` and `error TS`.
2. Name the mode that you ran. In changed mode, list the test files that you ran.3. Name each failed check and its first error. If a failure is outside the changed code, say so, and do not call it a regression without a run on the base branch.
4. Never say "pass" without the summary line of the runner, such as `ℹ pass N` / `ℹ fail 0` or `Tests: N passed`.
5. Always write a "Before / Now" table of what the change does, in both modes. Use one row for each behaviour that the branch changes. Use the format below.

### Before / Now table

The table shows what the branch changes for a user, an admin, or a caller, and which test proves it. It does not list test counts. Example:

```markdown
| | Before this change | Now (tested) |
| --- | --- | --- |
| Admin menu, Account group | Profile, Billing | Profile, **Notifications**, Billing |
| Email alerts | No setting (always on) | **Off / Daily digest / Each event**, with a time zone list |
| Quiet hours | No setting | **Start time, end time, weekend switch**, each with a help text |
| Billing card | Heading "Plan", in the Profile tab | Heading "**Subscription**", in the Billing tab |
```

Fill the table with these rules:

- **Base:** use the base branch of Changed mode step 1 in both modes: `dev` if it exists, else `main`. Get the merge base with `git merge-base HEAD <base>`.
- **Rows:** find each changed behaviour in the diff from the merge base to the working tree: `git diff <merge-base>`, plus each untracked file from `git ls-files --others --exclude-standard`. Do not use `git diff <merge-base>...HEAD`, because it misses changes that are not committed. Use up to 8 rows. Put the most important behaviour first.
- **No changes:** if the branch has no changes against the base, write one row that says so, such as `| Branch | Same as dev | No change |`.
- **First column:** name the screen, the setting, the message, or the action in plain words. Do not use a file name or a code name.
- **Before this change:** read the old value or the old behaviour from the base commit, with `git show <merge-base>:<file>`. Write `No setting` or `—` when the thing did not exist.
- **Now (tested):** write the new value or behaviour. Put the changed words in bold.
- **Proof:** a row is tested only when a test that ran in this session and passed covers it. For a row that no test covers, write `(not tested)` after the value, and name it below the table.
- For a failed test, mark its row `(test failed)`, and give the first error below the table.
- For a change with no visible behaviour, such as a refactor, write one row that says what stays the same, and name the tests that prove it.

## Rules

- Always end the run with the report and the "Before / Now" table in the chat, before any other step. This applies to each call, with no exception (see "Report").
- Do not skip a failed test, and do not edit a test to make it pass without telling the user.
- Do not start a dev server or more than one process at the same time.
- Do not commit or push. Use `/create-commit` and `/create-pr` for that.
