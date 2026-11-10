---
name: qa-e2e
description: Use when the user wants one issue or many issues tested end to end on a live test environment, with each result proved and recorded. Takes an issue number, a list of issues, or a testing status of a GitHub Project board (such as "For Testing" or "Ready for QA"). Confirms that the test environment runs each fix, tests each fix on each screen that it touches (web page in a browser, desktop or chat app, mobile simulator, API, CLI, background job, or logs and queries for code with no page), with the best tool that the session has (Playwright, the debug port, Chrome DevTools MCP, Claude in Chrome, computer use, a simulator). A live test is required for each issue: regression tests support a verdict but never replace the live check. It posts a comment with a results table, at least one live screenshot of each result, and text evidence on each issue, and moves each issue to the pass status (such as "For Release") or the fail status (such as "Failed Testing"). Can also give only the manual test steps of an issue when the user wants to run them by hand. Use it when the user says "/qa-e2e", "QA the For Testing column", "test all the issues waiting for QA", "QA the board", "test issue 123 end to end", "how can we test this", "give me the e2e steps", or pastes an issue or board URL and asks to test it, even if they do not name a surface or a status.
user-invocable: true
argument-hint: "[Issue #42 | issue URL | PR URL | board URL] (empty = find testable issues)"
---

# QA end to end

Test each issue on its real surface. Prove each result in a comment on the issue. Then move the issue: a pass goes to the pass status, and a fail goes to the fail status.

## Set up

1. Read `team.local.md` in this skill folder, if it exists. It holds the values of each project: the board, the statuses, the test environment, the surface profiles, the evidence branch, the test commands and the team rules. Keep it out of a public repository.
2. If it does not exist, or the current repository is not in it, ask the user for: the board (owner and project number) or the issue list, the test status, the pass and fail statuses, the test environment and how to read its build, and the surfaces to use. Offer to save the answers as a new section of `team.local.md`.
3. Read `references/surfaces.md` once. It says how to test and prove each kind of surface.
4. Read `references/screens-and-tools.md` once. It says how to list every screen of a change, how to find the tools of this session, and which tool to use first for each surface.

Below, `$S` is this skill's `scripts/` folder, and `$W` is a new folder in your scratchpad (`$W/ev` for screenshots, `$W/final` for comments).

## Input

Read the argument of `/qa-e2e` (or the request) and pick the issues:

| Argument | Example | Issues to test |
|---|---|---|
| One issue | `Issue #42`, `#42`, `42`, `https://github.com/<owner>/<repo>/issues/42` | That issue. A bare number belongs to the current repository; a link names its own repository |
| Several issues | `#42 #57 https://github.com/<o>/<r>/issues/60` | Each one |
| A PR | `https://github.com/<o>/<r>/pull/88`, `PR #88` | The issues that the PR closes or links (`gh pr view 88 --json closingIssuesReferences,body`). With none, test the PR's own change |
| A board | `https://github.com/orgs/<o>/projects/<number>` (any view) | Every issue in the board's test status |
| A board and a status | `<board link> "Ready for QA"` | Every issue in that status |
| Nothing | `/qa-e2e` | Find the issues that can be tested (below), show the list, and test them |

**Find the issues that can be tested** (no argument):
1. If `team.local.md` names a board, take its test status.
2. Otherwise take the issues of the current repository that are closed as completed in the last 14 days, or that have a merged fix PR, and that have no QA result comment yet (`gh issue list --state closed --search "closed:>=<date> reason:completed"`, then skip each issue whose comments contain "QA result").
3. Keep only the issues whose fix is on the test environment (step 2). List the rest as "not deployed".

For a single issue with no board, skip the status move and post only the comment, unless the issue is on a board in `team.local.md`.

## Modes

| The user asks for | Do |
|---|---|
| Test and record (the default) | All steps |
| Only the steps ("how can we test this", "give me the e2e steps") | Steps 1 to 3, then write the plan as numbered manual steps: a setup check, each action, the exact expected result, and one control check. Post nothing. When the user sends back a screenshot or output, read it and give a verdict table |
| A dry run ("test but do not post") | All steps except the posts and the moves. Leave the comment files in `$W/final` and give their paths |

## Rules

- **Test each issue live. This is required.** Each issue gets at least one live check on the test environment that shows the expected result of the issue. Regression tests and the code at HEAD support a verdict, but they never replace the live check. An issue with no live check cannot pass.
- **Show each result on each screen. This is required.** Make the screen list of each issue (`references/screens-and-tools.md`). Each row of the list gets a screenshot of its live result, on every surface, with no exception. There is no limit on the number of rows.
- **Use the tools that this session has.** Find them first, then use the tool order in `references/screens-and-tools.md`. If a tool fails two times, use the next one. Each result names its tool. Text proof supports the screenshot, but it never replaces it. See **Screen proof for every surface** in `references/surfaces.md`.
- **Open any application that you need for the screen proof.** The user allows you to drive their desktop through computer use (`$S/app.sh`). Open, start or focus any application that can show the live result. Run one GUI test at a time.
- **Never type a password, a card number, a token or another secret.** If a sign-in page shows, stop and ask the user. The user's own rules can add a test-account exception; follow them.
- **Do not spend money.** Never approve a purchase, a payment, a wallet send or a paid call. Cancel each such prompt. Get test credit only through the free path that `team.local.md` names.
- **Do not change shared data that you do not own.** Use read-only checks, or test data that you make and name `qa<issue>`. List all test data for the user at the end.
- **Never act on a production target.** `team.local.md` names the test targets and the production targets that look the same.
- **Never capture or upload a secret.** Look at the whole window before the first shot. Crop each shot to the region under test.
- **Respect the machine.** One test file at a time, one worker, a memory cap. One GUI test at a time on one desktop.
- **Subagents only when the user allows them.** If the user's rules forbid them, ask first. With a yes, run no more than 3 at a time, and never give them GUI work on your desktop.
- Quote each reply and each value exactly. Write in the style that the user's rules ask for.

## Steps

### 1. List the issues

Resolve the input (see **Input**). For one issue or a list:

```bash
gh issue view <n> --repo <owner/repo> --json number,title,state,body,labels,comments,projectItems
```

From a board:

```bash
$S/list_status.sh <owner> <project-number> <owner/repo> $W "<test status>"
```

The output gives each issue's labels and the PRs that link to it. For an issue with no linked PR, read its last comments (`gh issue view <n> --comments`); a triage comment often names the fix. Also search the log: `git log origin/<branch> --oneline -E --grep='#<n>([^0-9]|$)'`.

From a list: use the issue numbers that the user gives, and find the PRs the same way.

### 2. Confirm that the test environment runs each fix

Read the build that the environment runs (`team.local.md` says how: an image tag, a version endpoint, a commit in a footer). Then:

```bash
git fetch -q origin
$S/check_deployed.sh <owner/repo> <deployed-sha> <pr> <pr> ...
```

A fix that is `NOT-on-staging` cannot pass. Comment that it is not deployed, leave its status, and tell the user. Do the same for a PR that is not merged.

### 3. Plan each issue

For each issue, read the issue, its expected result, and the fix PR summary. A PR's "old and new behaviour" table often gives the exact new text to expect. Then write one line:

`#<n> | surface(s) | live steps | regression test files | data needed | page that shows the result`

The "live steps" field is never empty. Each live step is an action on the test environment and the exact result that you expect to see.

Choose the surfaces from `references/surfaces.md`. Then make the screen list from `references/screens-and-tools.md`, with the tool of each row, and put it in the plan. For a backend fix, also find a page that shows its result: an admin or ops console page, a settings row, a list of records, a public page. When no page shows it, write the application that you open for the screen proof instead. A fix with no page still needs a live step (see **Make the live state** below). Group issues that share one setup, so that one setup serves several checks (one open approval, one test record, one signed-in page).

### 4. Split the work

| Work | Who does it |
|---|---|
| Code at HEAD, regression tests, read-only API and log checks | Subagents (if allowed), 7 to 9 issues each, with `references/subagent-brief.md` |
| A web page | A subagent with its own browser tab, or you |
| Desktop app, chat app, simulator (computer use) | **You.** One desktop runs one GUI |
| Screen proof of a fix with no page (any application, through computer use) | **You.** One desktop runs one GUI |
| The code half of your GUI issues | One more subagent, so that your comments also carry test evidence |

Each subagent writes one comment file per issue and posts nothing. You review, post and move. For one or two issues, do it all yourself.

### 5. Test

Follow `references/surfaces.md` for each surface. Short form:

- **Web:** a new tab of your own; page text, a zoomed screenshot saved to disk, the request status.
- **App through computer use:** `$S/app.sh <app> send|wait|shot|tap|key ...`. Read each shot with the Read tool before you use it.
- **API, CLI, job:** read-only requests and queries; show the request and the response as text. Then take the screen proof in any application that shows the result.
- **Backend fix with a page that shows its result:** do the text checks, then open that page read-only and take a screenshot of the region that shows the result (the new setting, the new record, the new column). Text proves the behaviour, and the screenshot lets a reviewer see it. Do not click a write control to get the shot.
- **No visible surface** (a refactor, removed code, a timer, an internal rule): make the behaviour happen on the test environment, then prove it with the closest live signal. Use log lines since the deploy, read-only queries, the API, or a console page. For removed or replaced code, prove live that the old symptom (the error, the log line, the failed call) no longer occurs after the deploy, and that the path that replaces it works. Then take a screenshot of that signal in any application that shows it.

**Make the live state.** When the live state is hard to reach (a long wait, a rare condition, a large input), make it. Do not fall back to tests only.

- Make your own test data (`qa<issue>`), or trigger the job or the timer.
- Change a test-environment setting for a short time, for example a timeout or a threshold. Ask the user first, because the change affects all users of the environment. Record the old value, and restore it when the test ends.
- Ask the user to do a step that you cannot do (a sign-in, a real device, a payment, a message to real people).

**Add every proof that you can get.** Each comment carries at least one screenshot of the live result, and all the other evidence that exists for its issue: screenshots of each screen or page that shows the result, and the text proof (requests and responses, query counts, log lines, test summaries). When both exist, add both. A screenshot that shows nothing new (an empty list, a total with no matching record) proves nothing. Leave it out and say why. Before you upload a shot, read it, crop it to the region under test, and mask phone numbers, emails and other people's data.

**Put a red box on the proof.** Each screenshot shows a red box around the element that proves the result: the new row, the message, the button, the error text. A reviewer then sees the proof without a search. Draw one box for each point of proof, and no more than three boxes in one shot.

- **Web page:** put a red outline on the element before the shot, then remove it. See `references/surfaces.md`. The outline follows the real bounds of the element and does not move the layout.
- **Any other shot** (desktop app, chat app, mobile screen): crop first, then draw the box in the pixels of the cropped image. Write the result to a new file:

  ```bash
  python3 $S/mark_box.py $W/ev/<n>-<name>.raw.png $W/ev/<n>-<name>.png <x,y,w,h> [<x,y,w,h> ...]
  ```

- Leave a small space between the box and the element, so the line does not cover the text.
- Read the marked shot with the Read tool. If the box misses the element or cuts its text, move it and draw it again.
- Keep the raw shot on disk, and upload only the marked shot.

Poll for a slow reply with `app.sh ... wait`. Do not chain `sleep` commands.

### 6. Decide each verdict

- **PASS:** the fix is on the environment, its regression tests pass, the live check gives the expected result, and a screenshot shows that result. All four are required.
- **FAIL:** an expected result from the issue does not happen. Also fail when the reported symptom shows on another path in the same build, and give that path's exact steps.
- **BLOCKED:** the live check cannot run, or no screenshot can show its result, even after you try each way in **Make the live state** and each screen proof. Comment what passed and the open live step, leave the status, and tell the user what the live step needs. Never pass an issue on tests alone.
- **Note:** a new problem that the issue does not cover. Put it under "Notes" in the comment. It does not fail the issue.

### 7. Post the proof

Write each comment from `references/comment-template.md`, with one `{{IMG:<file>}}` line per screenshot. Then:

```bash
$S/upload_evidence.sh <owner/repo> <evidence-branch> <YYYY-MM-DD>/qa $W/ev/<file> ...
$S/img_links.sh <owner/repo> <evidence-branch> <YYYY-MM-DD>/qa $W/final/*.md
$S/post_result.sh <owner> <project-number> <owner/repo> <n> "<pass status>" $W/final/<n>.md
$S/post_result.sh <owner> <project-number> <owner/repo> <n> "<fail status>" $W/final/<n>.md
$S/post_result.sh <owner> <project-number> <owner/repo> <n> - $W/final/<n>.md      # comment only
```

If the repository has no evidence branch, ask the user before you make one (an orphan branch such as `issue-evidence`). Open one posted comment in a browser and check that its images load.

### 8. Report and clean up

1. Write `$W/report.md`: the results table of all issues, then one section for each issue with its comment text (from `$W/final`), the link to the posted comment, and the full path of each screenshot.
2. Make the contact sheet of all marked shots, and read it with the Read tool:

   ```bash
   python3 $S/contact_sheet.py $W/ev $W/contact-sheet.png
   ```

3. End the reply with these two lines, with the full absolute paths. Do not shorten them:

   ```
   - Report: <$W>/report.md
   - Contact sheet: <$W>/contact-sheet.png
   ```

Also tell the user:
- the issues that passed, in a table grouped by area;
- each failed issue, with its failed step in one sentence;
- each blocked issue, with its open step;
- the notes, with an offer to file them (`create-issue`);
- the test data and the untracked files that you or a subagent left. Ask before you remove shared test data.

Close your browser tabs. Remove each container that you started.

## Context limits

A run of 40 or more issues fills the context. Keep raw output in files, and print only summaries. If the user asks for a handoff, first write the state (done, failed, blocked, notes, leftovers, helper paths) to a handoff file.
