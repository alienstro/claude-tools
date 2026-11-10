---
name: qa-stories
description: Use when the user wants proof, with screenshots, that a change on the current branch works end to end before a pull request or a merge. Writes user stories from the issue's goal and "Done when" list, starts the local stack on the branch, runs each story live on each screen that the change touches (desktop app, web page, browser with no app, mobile, chat app, API, CLI), with the best tool that the session has (Playwright, the debug port, Chrome DevTools MCP, Claude in Chrome, computer use, a simulator), and saves a marked screenshot of each screen, with text proof beside it. Ends with a report of PASS, FAIL or BLOCKED for each story and the folder of screenshots. Posts nothing unless the user asks. Use it when the user says "/qa-stories", "test the e2e flow with user stories", "I need screenshots that it worked", "prove this branch works", "QA my branch before the PR", "test it like a user would", or "show me it works in the app", even if they do not say "user story". For issues that are already merged and deployed to a test environment, use `qa-e2e` instead.
user-invocable: true
argument-hint: "[issue #N | issue URL | PR URL] (empty = the issue that the branch name or the last commit names)"
---

# QA with user stories

Prove that the branch does what its issue asks. Write each "Done when" item as a user story, run each story live on the branch, and keep a marked screenshot of each result.

`qa-e2e` tests merged fixes on a shared test environment. This skill tests the current branch on this machine, before a pull request.

## Set up

1. Read `team.local.md` in this skill folder. It holds each project's local stack: how to start it on a worktree, the ports, the surfaces, the app profile, and the files that a test changes. If the repository is not in it, ask the user how to start the stack, and offer to save the answer there.
2. Read `~/.claude/skills/qa-e2e/references/surfaces.md` one time. It says how to test and prove each kind of surface.
3. Read `~/.claude/skills/qa-e2e/references/screens-and-tools.md` one time. It says how to list every screen of the change, how to find the tools of this session, and which tool to use first for each surface.
4. For a desktop app (Electron), also read `references/desktop-electron.md`.

Below, `$S` is this skill's `scripts/` folder, `$E` is `~/.claude/skills/qa-e2e/scripts/` (`app.sh`, `mark_box.py`, `contact_sheet.py`), and `$W` is a new folder in your scratchpad: `$W/ev` holds the screenshots and `$W/report.md` holds the report.

## Input

| Argument | Do |
|---|---|
| `#42`, `42`, an issue URL | Use that issue |
| A PR URL or `PR #88` | Use the issues that the PR closes; with none, use the PR's own summary |
| Nothing | Find the issue number in the branch name, then in `git log -5 --format=%s`. If you find none, ask |

## Rules

- **Run each story live, on the branch.** Unit tests support a verdict, but they never replace the live run. A story with no live run cannot pass.
- **Show each result on each screen.** Each row of the screen list (`screens-and-tools.md`) gets a screenshot of its live result. There is no limit on the number of rows. Text proof (a file, a request, a log line) goes beside the screenshot, never in place of it.
- **Use the tools that this session has.** Find them before step 3, then use the tool order in `screens-and-tools.md`. If a tool fails two times, use the next one. Each shot names its tool in the report.
- **Use the code of the branch.** Before the first story, prove that each running part comes from the branch worktree (the working folder of the process, see `team.local.md`). A part that runs from another checkout gives no proof.
- **Ask before you stop a process that you did not start.** Another session or the user can use it. Offer to start it again at the end.
- **Never type a password, a token or another secret.** If a surface needs a sign-in that you do not have, use the session that the app already has (see "Browser with no app" in `references/desktop-electron.md`), or ask the user.
- **Put back what you change.** Record each setting, file or record that a story changes, and restore it in the last story or at the end.
- **Look at each shot before you keep it.** A covered or inactive window can give an old image. Read each shot with the Read tool, and compare it with the live state.
- **Respect the machine.** One GUI test at a time, one dev server per part, one test package at a time.
- Write in the style that the user's rules ask for.

## Steps

### 1. Read the issue and write the stories

```bash
gh issue view <n> --repo <owner/repo> --json number,title,body,comments
```

Take the goal, the "Done when" list, and the decisions in the last comments or in the user's request. A decision of the user overrides the issue text (for example, "show only the version, no Check for updates").

Write one story for each "Done when" item, and one story for each "works as before" item. Use the format in `references/report-template.md`:

- **Story:** As a `<who>` in `<surface>`, I `<action>`, so that `<value>`.
- **Steps:** each action, in order.
- **Expected:** the exact text or state that shows the result.
- **Proof:** the screenshot (what it shows, where the red box goes) and the text proof.

Add a control story when the change hides something: the same page on the surface that must not show it (for example, the web browser for a desktop-only row).

Then make the screen list from `screens-and-tools.md`: each surface, platform, way in, state, role, theme, width and control screen that the change touches. Give each row a story and a tool. A row with no story gets a new story.

Show the stories and the screen list to the user in one short table before you run them, then go on. Do not wait for an answer unless a story needs something from the user.

### 2. Start the stack on the branch

Start each part as `team.local.md` says, with the worktree as its source. Then check:

```bash
lsof -p <pid> | awk '$4=="cwd"{print $NF}'   # each part must run from the worktree
```

If a part runs from another checkout, ask the user before you stop it (see **Rules**).

### 3. Run each story

Follow the surface notes:

- **Desktop app:** `references/desktop-electron.md`. Raise the window first (`$S/raise.sh <pid>`), then use foreground clicks (`--restore-window`). Read the DOM state through the debug port (`$S/cdp.mjs eval`) to confirm each step.
- **Web page:** a new browser tab, or a headless shot with the session cookie (`references/desktop-electron.md`, "Browser with no app").
- **API or file:** show the request and the response, or the file content, as text. Then take a screenshot of a page that shows the same result.
- **A step that needs a restart:** quit the app as a member does (Cmd+Q), start it again with the same command, and wait until the window loads.

Save each raw shot as `$W/ev/<story>-<name>.raw.png`. Then crop it to the region under test and draw a red box around each point of proof (no more than three):

```bash
python3 $E/mark_box.py $W/ev/<story>-<name>.raw.png $W/ev/<story>-<name>.png <x,y,w,h> [...]
```

Read the marked shot. If the box misses the element or cuts its text, draw it again.

### 4. Decide each verdict

- **PASS:** the live run gives the expected result, and a screenshot shows it on each screen of the story.
- **FAIL:** the expected result does not happen. Give the exact step and what showed instead. Then stop and debug (load `systematic-debugging`) before you change code.
- **BLOCKED:** the live run cannot happen on this machine (no sign-in, no device, no feed). Say what the story needs.
- **Note:** a problem that no story covers. It does not fail a story.

A problem with the test tools (a click that does not arrive, an old shot) is not a FAIL. Find its cause and run the step again.

### 5. Restore and report

1. Restore each change that the stories made (see **Rules**), and prove it (a file, a screenshot).
2. Write `$W/report.md` from `references/report-template.md`: the stories table, then one section for each story with its marked screenshots and its text proof.
3. Make the contact sheet of all marked shots:

   ```bash
   python3 $E/contact_sheet.py $W/ev $W/contact-sheet.png
   ```

4. Show the contact sheet in the chat with the Read tool, so the user sees all shots at once.
5. Tell the user:
   - the table of stories with PASS, FAIL or BLOCKED;
   - the notes, and what you could not prove;
   - the processes that you started or stopped, with an offer to put back the old ones.
6. End the reply with these two lines, with the full absolute paths. Do not shorten them:

   ```
   - Report: <$W>/report.md
   - Contact sheet: <$W>/contact-sheet.png
   ```

Post nothing to GitHub unless the user asks. If they ask, use `qa-e2e`'s `upload_evidence.sh` and `img_links.sh`, and ask before you make an evidence branch.
