---
name: qa-explore
description: Use when the user wants an exploratory QA pass of a whole page, a flow or the whole app, to find bugs and things to improve, not to prove one change. Walks each page live as a new member and as a power user, with the best tool that the session has (the Electron debug port, Playwright, Chrome DevTools MCP, Claude in Chrome, computer use), and looks for bugs, misleading or unclear words, bad UX, bad UI, bad flow, slow loads, errors and accessibility gaps. Measures load times, keeps a marked screenshot of each finding, and ends with a list of issue drafts, each with a brief explanation, a severity and a suggested fix. Files nothing unless the user picks drafts. Use it when the user says "/qa-explore", "explore the app", "find bugs on this page", "QA the whole page", "what is wrong with this flow", "audit the UX", "test it like a new user", "find things to improve", or "draft issues for this page", even if they do not say "exploratory". To prove that one branch does what its issue asks, use `qa-stories`. To test merged issues on a test environment, use `qa-e2e`.
user-invocable: true
argument-hint: "[page | route | URL | flow name] (empty = the whole app)"
---

# Exploratory QA

Use the app as a real person does, find what is wrong or weak, and give the user a short list of issue drafts. Each draft has proof.

This skill does not prove one change. `qa-stories` does that. This skill looks at all of a page, which includes the parts that no issue names.

## Set up

1. Read `team.local.md` in this skill folder. It holds each project's targets: how to start each one, its sign-in, its QA space, its credit cap, and the repo of each kind of fix.
2. Read `~/.claude/skills/qa-e2e/references/screens-and-tools.md` one time. It says how to find the tools of this session and which tool to use first for each surface.
3. For a desktop app (Electron), also read `~/.claude/skills/qa-stories/references/desktop-electron.md`.
4. Read `references/checklist.md` in this skill folder. It is the list of problems to look for on each page.

Below, `$S` is `~/.claude/skills/qa-stories/scripts/` (`cdp.mjs`, `raise.sh`), `$E` is `~/.claude/skills/qa-e2e/scripts/` (`mark_box.py`, `contact_sheet.py`), `$C` is `~/.claude/skills/qa-explore/scripts/cu.sh`, and `$W` is a new folder in your scratchpad. `$W/ev` holds the marked shots, `$W/raw` holds the raw shots, and `$W/report.md` holds the report.

## Input

| Argument | Do |
|---|---|
| A page, a route or a URL | Explore that page and each dialog, menu and state that it opens |
| A flow name, such as "onboarding" or "add an agent" | Explore each page of that flow, from the first step to the last step |
| Nothing | Explore the whole app. Make the page map first (step 2), then show it to the user |

## Rules

- **Ask the set-up questions at each run.** Use one AskUserQuestion with these questions. Do not choose for the user.
  - The target, from `team.local.md`. Each target tests different code, and the report names it.
  - The tool, when the app already runs without a debug port: restart it with the port, or use computer use on the open window.
  - The scope.
  - The sends: no sends, or sends inside the credit cap of `team.local.md`. Say which test data the app cannot delete, such as chat messages.
- **Test in the QA space.** Use the QA space of `team.local.md` for each write, such as a message, a group or a reminder. If the project has no QA space, tell the user what stays after the run before the first write.
- **Explore live.** Each finding comes from a live run on the target. The code can help you find a cause, but a finding that you only read in the code is a Note, not a finding.
- **Confirm each finding one time more.** Do the steps again before you keep a finding. A click that does not arrive or an old shot is a test-tool problem, not a finding.
- **Repeat an agent finding.** An AI agent's answer changes between runs. Send the same words 2 or 3 times before you keep a finding about an agent's answer, and give the count, such as "3 runs of 4".
- **Tag each test message.** Start each message that you send with a run tag, such as `qx1:`, `qx2:`. The tag finds the message in the tree, in the report and in the clean-up.
- **Check pixels at 1:1.** A scaled shot can hide a colour, a dim layer or an overlap. Before you keep a finding about a colour, contrast, a dim layer or an overlap, read a 1:1 crop or sample the pixels.
- **Keep shared data safe.** A staging target is shared with the team.
  - Do not delete, rename or change data that you did not make.
  - Ask the user before an action that costs money or credits above the cap, sends an e-mail or a message outside the app, connects an app, or pays.
  - Record each thing that you make, and remove it at the end. Record the credits before and after the run.
- **Never type a password, a token or another secret.** If a page needs a sign-in that you do not have, ask the user to sign in, then go on.
- **Do not fix code.** This skill only finds and drafts. Offer a fix after the report.
- **Look for duplicates.** Before you keep a draft, search the open issues of each repo in `team.local.md`: `gh issue list --repo <owner/repo> --state open --search "<words>"`. Search with the words on the screen and with the component name.
  - An open issue covers the whole finding: name it, and do not draft it.
  - An open issue covers only a part, or has the same cause: make the draft a comment on that issue (type "Comment on #N").
- **Look at each shot before you keep it.** Read each marked shot with the Read tool, and compare it with the live state.
- **Respect the machine.** One GUI test at a time, one dev server per part.
- Write in the style that the user's rules ask for.

## Steps

### 1. Choose the target and start it

Ask the set-up questions (see **Rules**). Start the target as `team.local.md` says. Then confirm that the page loads and the session is signed in.

With computer use, set `CU_APP` and `W`, then use `$C` for each action and each wait:

```bash
export CU_APP=<bundle id> W=<run folder>
Q='Send|entry area' $C act <name> click --element-index <n>   # saves $W/ev/<name>.raw.png, prints the filtered tree
$C wait-for 'qx3:' --timeout 180                               # prints the seconds until the text shows
```

Each `$C` read is a full read with a shot, because a read with `--no-screenshot` can give an old tree. Move each raw shot to `$W/raw` before you make the contact sheet.

### 2. Make the page map

List each page, dialog, menu and state in the scope:

- the routes of the app (for a Next.js app, the `page.tsx` files under `app/`);
- each item of the side bar, the top bar and each menu;
- each state of a page: empty, loading, one item, many items, error, no network, a long name, a narrow window;
- each place that shows the same value, such as a name in the side bar, the header and a placeholder.

This step is a short stop: show the map to the user in one table before the first action of step 3, then go on. Do not wait for an answer unless the scope is not clear. The same table goes into the report.

### 3. Walk each page as two people

Walk each row of the map two times. Use the problems in `references/checklist.md`.

- **New member.** First visit, no help, reads each word, uses only the mouse. Ask: "Do I know where I am, what this does, and what to do next?" Do the main task of the page from start to end.
- **Power user.** Knows the way and works fast. Uses the keyboard, the back button, a reload in the middle of a task, two windows, a double click, a long input, many items. Ask: "What breaks, what is slow, and what makes me wait or do a step two times?"

Measure the speed of each page and each main action (see "Speed" in `references/checklist.md`). Read the console errors and the failed requests of each page. If the session has no debug port, say in the report that it has no console, network or LCP data.

Read the accessibility tree of each page one time (see "Accessibility tree" in `references/checklist.md`).

For each problem, save a raw shot as `$W/raw/F<n>-<name>.raw.png`. Then crop it and draw a red box around the problem (no more than three boxes). Give the crop and the boxes in the pixels of the raw shot:

```bash
python3 $E/mark_box.py --crop <x,y,w,h> $W/raw/F<n>-<name>.raw.png $W/ev/F<n>-<name>.png <x,y,w,h> [...]
```

Read the marked shot. If the box misses the problem, draw it again.

### 4. Sort the findings

Give each finding one type, one severity and one repo from `references/checklist.md` and `team.local.md`. Join findings with one cause into one draft. Put the drafts in order: severity first, then the number of pages that show the problem.

### 5. Clean up and report

1. Remove each thing that you made (see **Rules**), and prove it. List what the app cannot remove, and the credits used.
2. Write `$W/report.md` from `references/report-template.md`.
3. Make the contact sheet of all marked shots:

   ```bash
   python3 $E/contact_sheet.py $W/ev $W/contact-sheet.png
   ```

4. Show the contact sheet in the chat with the Read tool.
5. Give the user the list of drafts, in this format, one block for each draft:

   ```
   F1 · S2 · UX · <repo> · <title>          (or: F1 · S2 · Bug · Comment on #380 · <title>)
   What: <one sentence: what happens, on which page>
   Why: <one sentence: how it hurts the member>
   Fix: <one sentence: the suggested change>
   ```

   After the list, give the notes, the pages that you could not reach, and the processes that you started.
6. Ask which drafts to file. For each draft that the user picks, use the `create-issue` skill with the draft text, its repo and its screenshot. For a "Comment on #N" draft, post a comment on that issue with `gh issue comment`, with the steps and the shot.
7. End the reply with these two lines, with the full absolute paths:

   ```
   - Report: <$W>/report.md
   - Contact sheet: <$W>/contact-sheet.png
   ```
