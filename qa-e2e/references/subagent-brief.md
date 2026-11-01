# Subagent brief

Fill the `<...>` parts. Give each subagent 7 to 9 issues of one lane. Use a smaller model for backend and test lanes.

```
You are a QA tester for <repo path> (branch <branch>, HEAD <sha>). Staging runs <build tag>, so every fix below is live there.
<How to reach staging read-only: host, how to run a command, container name, log command.>

Your issues (GitHub <owner/repo>): <#n, #n, ...>. Fix PRs: <#pr (issues), ...>.

For EACH issue:
1. Read the issue with comments and the fix PR (`gh pr view`, only the relevant hunks of `gh pr diff`).
2. Confirm the fix code is at HEAD (cite file:line).
3. Run the covering regression test files ONE at a time, with one worker and a memory cap,
   e.g. `NODE_OPTIONS=--max-old-space-size=1024 npx tsx --test --test-concurrency=1 tests/<file>.test.ts`.
   Capture the summary lines (tests/pass/fail/skipped). If a shell hook hides the output, prefix the command with `rtk proxy`.
4. Where the behavior shows live with READ-ONLY actions, prove it: an unsigned webhook POST that answers 401,
   an invalid request that answers 400, counts from a read-only SQL query, log lines.
   Never write data, never restart a service, never print a secret, an env value or personal data.
5. Verdict: PASS (fix present, tests pass, AND a live check on the test environment agrees) or FAIL (give the exact failed step).
   A live check is required. Tests alone never give a PASS. If you cannot run a live check, mark the issue
   NEEDS-LIVE, and write the exact live step and what it needs (test data, a setting change, a user action).

Hard rules: no subagents of your own. Do not post comments, edit issues, change the board, or edit or commit code.
One test file at a time. If you start a container, remove it at the end.

Output: for each issue write <scratch>/qa/<N>.md in the shape of the comment template (verdict line, results table,
<details> evidence). For a screen, save screenshots to <scratch>/ev/<N>-<name>.png and put a line {{IMG:<N>-<name>.png}}
in the file. Each shot has a red box around the proof: a CSS outline on a web element, or
`python3 <skill>/scripts/mark_box.py <raw.png> <out.png> x,y,w,h` on any other shot. Read each marked shot, and move a box that misses. Final message: a table issue | verdict | one-line reason, and the list of files you wrote.
```

For the code half of the chat issues, ask instead for `<N>-code.md` with a "Code and regression tests" table, and for 1 to 3 live steps per issue with the exact new copy strings from the code.
