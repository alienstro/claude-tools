---
name: create-pr
description: Use when the user wants to open a pull request whose summary is a handful of one-sentence bullets aimed at a reviewer, with an old/new behaviour table, a required Before/After screenshot table, and a lines-changed table. Triggers on "/create-pr", "open a PR", "create a pull request".
user-invocable: true
allowed-tools: Bash, Read
---

# Create PR

Open a pull request whose title uses a conventional-commit prefix and whose body is a short
summary — a lead line, an old/new behaviour table, at most five one-sentence bullets — then a Before and After screenshot table, then a table of lines added per area.
Every PR carries the screenshot table. A PR without it does not open.
Nothing else. Write it in simple, everyday words for a reader who does not know the code. Say what changes for a user, an owner, or an operator, and why. Do not name files, folders, functions, classes, variables, endpoints, env vars, or other code names. The diff carries those.

## Steps

1. Gather context:
   - Current branch: `git branch --show-current`
   - Base branch: default to `main` unless the user names another.
   - Commits on the branch: `git log --oneline <base>..HEAD`
   - Changed files: `git diff --stat <base>...HEAD`
   - Diff: `git diff <base>...HEAD`
   - Per-area line counts: `git diff <base>...HEAD --numstat -- <path>` (see "Size table"). Use the three-dot branch diff exactly; do not count the working tree, commit totals, or a guessed subset.
   - For anything nontrivial, open the key changed files (the new and most-changed
     source) and read enough to know what the change actually does — the diffstat says
     what moved, the file bodies say what it does.
   - Intent signals: read the comments, docstrings, test names, and changed
     defaults inside the diff — the *why* usually lives there, not in the commits.
   - Screenshots: take the Before and After shots now (see "Screenshots").
2. If the branch has no commits ahead of base, STOP and tell the user.
   If a Before or an After shot is missing or bad, STOP and tell the user. Do not open the PR without it.
3. Confirm the base branch and scope with the user before pushing or opening — the user drives
   git history, so never assume. Flag anything unusual (wrong base, unrelated commits).
4. Push the branch if needed: `git push -u origin <branch>`.
5. Write the title and body in the format below.
6. Open the PR with `gh pr create --base <base> --title "<title>" --body-file <body.md>`. Add one
   `--attach` per screenshot (see "Screenshots").
7. If reading the diff surfaced something a reviewer genuinely needs to know (a risky
   dependency, a stale doc, a follow-up, a gate that does not cover this work), say it to the
   user in chat — not in the PR body.

## Title

- Format: `<type>: <description>` where `<type>` is exactly one of:
  - `feat:` a new feature or capability.
  - `fix:` a bug fix — correcting broken or wrong behavior.
  - `chore:` everything else — cleanup, refactors, dependency bumps, config, docs, tests.
- One line, imperative mood, lowercase first word. No PR number, no branch name, no trailing
  period. Pick the type that matches the main purpose of the work.

## Body

The body is exactly one section (the `##` heading is literal — include it). It always has the
screenshot table and the size table. It has the behaviour table when a behaviour changes:

```
## Summary
One line naming what this PR is fundamentally about — the change it exists to make.

| Old behaviour | New behaviour |
| --- | --- |
| What the system did before, in one sentence. | What it does now, in one sentence. |
| (one row per visible change, up to four) | ... |

- **Bold lead-in.** ONE sentence, around 25 words, saying what changed and why it matters.
- (up to four more)

| Before | After |
| --- | --- |
| ![Before: <screen>](./before-<screen>.png) | ![After: <screen>](./after-<screen>.png) |
| (one row per screen of the screen list, with no limit; UI rows first; never leave this table out) | ... |

| Area | Lines added |
| --- | --- |
| ... | ... |
```

One sentence per bullet is the hard rule. A bullet that needs a second sentence or an "and
also" is really two changes: split it, or drop the smaller half. Never a dense paragraph.

Nothing follows the size table. No `## Technical details`, no test notes, no reviewer notes, no
file lists.

## Screenshots

Every PR carries a Before and an After screenshot of each change, at least one pair. A
reviewer judges a change from the pictures, not from the code names in the diff. The
screenshot table is required. Never leave it out, and never open the PR without it.

**A screenshot of the real page is required when a page can show the change.** Decide from
what a person sees, not from the file list. An API, a config, a catalogue, or a flag change
that alters what a page shows is a UI change. Example: the server stops sending a payment
method, so the pay page shows one button fewer. That PR needs the pay page, not only a `curl`.

Ask one question first: "Does any page of the product show this change?" Search the web app
for the field, the text, or the endpoint that the diff changes. If a page reads it, that page
is the subject.

Pick the subject of each pair from the kind of change:

| Change | Before and After subject |
| --- | --- |
| UI: a component, a page, copy, or a theme value that renders | Each changed screen, on each surface that renders it: the web page in a browser, the desktop app window, the mobile screen |
| Desktop-only UI: a window, a menu, a tray, or a setting that only the desktop app has | The desktop app window. Add the browser page as a control row when the item must not show there |
| Behaviour that a page shows: an API, a catalogue, a config, or a flag that changes what a page renders | **Each page or app screen that shows it.** Terminal output can follow as extra rows |
| A chat reply, an email, or an SMS | The message in the chat app, the inbox, or the provider log |
| Behaviour that no page shows: an agent reply, a CLI, a job, a webhook | The terminal output of one command that shows the behaviour, such as a `curl` call or a CLI run |
| No visible behaviour: a refactor, a test, a dependency bump, a config | The terminal output of the check that proves the change, such as the tests or the typecheck of the changed code |
| Docs | The changed page, rendered as HTML |

Put the UI rows first in the table, and the terminal rows below them. If a screen does not
change but proves that the change stays inside its scope, add it as an After shot with a
one-line text in the Before cell. Example: "Same on dev: QR Ph, GCash, Maya and Card."

1. Make the screen list with `~/.claude/skills/qa-e2e/references/screens-and-tools.md`:
   each surface, platform, way in, state, role, theme, width and control screen that the
   change touches. Each row gets one pair. There is no limit on the number of pairs. Put the
   pairs closest to the soul of the change first. Show the screen list to the user, with a
   "Not affected" line for each skipped axis.
2. Take the After shot from `HEAD`. Use fake data only, and keep each script, the data, and
   the viewport in the scratchpad.
   - Pick the tool for each screen from the tool order in `screens-and-tools.md`. Use the
     tools that this session has, and use the same tool for the Before and the After shot.
   - For a web screen, use `/do-screenshots`.
   - For a desktop app screen, start the app from the worktree with its debug port, and use
     the debug port or Orca computer use (see `screens-and-tools.md`).
   - A page that needs the API and a database is not a reason to use terminal output.
     Start the smallest topology: a throwaway database container on a free port, the
     migrations, a few fake seed rows, the API, and the web dev server. Use test or dry-run
     config only, never live keys. Use a free port when another process holds the default.
   - For a flow with more than one click, write a short Playwright script in the scratchpad.
     Make it refuse to click a button that pays, sends, or deletes something.
   - For terminal output, save the output to `<scratchpad>/shots/<name>.txt`. Wrap it in a
     `<pre>` tag of a small HTML file with a dark background and a monospace font. Shoot that
     file with `node ~/.claude/skills/do-screenshots/scripts/shot.js --url file://<path>.html --out <png>`.
     Put the command itself on the first line of the output, so a reviewer sees what ran.
3. Take the Before shot from the PR base. Make a worktree of the merge base in the scratchpad
   (`git worktree add <scratchpad>/base $(git merge-base origin/<base> HEAD)`), install it
   with `pnpm install --frozen-lockfile --prefer-offline`, and run the same script or command,
   the same data, and the same viewport against it. Remove the worktree after the shot
   (`git worktree remove <scratchpad>/base`). A new test does not exist on the base: for the
   Before shot, run the new test file from `HEAD` against the base code, or show the old
   behaviour with the same command.
   - If the base branch moved after the branch started, and the new base commits change
     the same screen, the two shots differ by more than this PR. Then use a worktree of
     `origin/<base>` for the Before shot. For the After shot, apply the branch commits to
     that worktree with `git cherry-pick --no-commit <commits>`. Do not commit or push that
     result. Tell the user in chat that the After shot shows the base plus this PR.
4. Run only the servers that the page needs, and stop each one after its shots.
5. Read every PNG with the Read tool before you put it in the PR. A shot that shows a spinner,
   a sign-in page, a broken image, or a command error that is not the subject is not a Before
   or an After: fix the script and shoot again.
6. Name the files `before-<name>.png` and `after-<name>.png` in one folder.
7. If you cannot get a good pair after two tries, STOP and tell the user what failed. Do not
   open the PR without the screenshots, and do not put a placeholder in the table.
8. Do not replace a page shot with terminal output on your own. If a page shows the change
   but you cannot run it, STOP and tell the user what blocks it. Use terminal output only
   if the user agrees.
9. Clean up after the shots: stop each server, remove the database container, remove the
   scratch worktree, and delete each secret file. Run `git status --short` to confirm a
   clean tree.

WARNING: `--attach` uploads each image to GitHub, and every person with access to the
repository can open it. Never shoot a real account, a real token, an email address, or
production data.

Put the images in the body with a path that starts with `./`, and attach the same files.
`gh` uploads them and rewrites each `./` path to the uploaded address. Run `gh` from the
screenshot folder, and pass `--repo <owner>/<repo>` because that folder is not the repository:

```
cd <scratchpad>/shots && gh pr <create|edit> ... --repo <owner>/<repo> --body-file <body.md> \
  --attach './before-dialog.png#Before: tools dialog' \
  --attach './after-dialog.png#After: tools dialog'
```

Never commit a screenshot to the branch. It adds a binary to the repository history for good.

## Lead line

The lead line states the *soul* of the change — the one thing the PR exists to do. Everything
else in the diff is supporting work, however large. A PR that adds a separate sign-in and
separate permissions for a new kind of user leads with that separation, not with the
invite plumbing that sets it up. When unsure which of two things is the soul, ask the
user rather than guessing — they know what they set out to build.

## Behaviour table

The behaviour table sits between the lead line and the bullets. It shows a reviewer what a user, an operator, or a caller sees change — before and after — so the bullets can spend their words on how.

- Use exactly two columns: `Old behaviour` and `New behaviour`. Keep those header words literal.
- Write one row for each visible change in behaviour, between 1 and **4** rows. Pair each old cell with the new cell that replaces it.
- Write each cell as ONE sentence, in the present tense, in simple words. Do not name code, files, endpoints, fields, or env vars. A command that a user types, such as `/new`, is not code: you can name it.
- Describe behaviour, not code. "The payment link opens even when no link was saved before" is a row; "refactored `payLink()`" is not.
- Leave the table out for a change with no visible behaviour, such as a pure refactor, a test, a doc, or a dependency bump. Do not write a row such as "No change".
- Do not repeat a row word for word in a bullet. The table says what changes; the bullets say how and why.

## How many bullets

Count the distinct changes, and write that many bullets — between 1 and **5**.

- **One thing changed → exactly ONE bullet.** Most PRs are single-concern. Do NOT pad to two.
  Never add a filler bullet saying what did *not* change ("nothing changes for users",
  "staging only", "no migration needed"). If it isn't a change, it isn't a bullet.
- **Several genuinely separate changes → one bullet each, up to 5.** Past five, merge the
  closest pair or fold the smallest into a neighbouring bullet. Do not spill to six.
- **Lead with the bullets closest to the soul of the change.** Supporting mechanics
  (enrollment, migrations, plumbing) go last or get folded in.
- **Drop bullets for work that isn't this PR's subject.** Incidental cleanup or unrelated
  refactors carried along in the branch belong in the size table, not in the bullets.
- A bullet must survive this test: it names something this PR changed that a reviewer would
  care about, and no other bullet already covers it.

## Size table

Below the bullets, a two-column table of exact lines ADDED per area, calculated from
`git diff <base>...HEAD --numstat` and summed per group. Never estimate, round, or reuse a
diffstat total without reconciling it to the table.

- Group by area, and give each area a plain name that says what it does, such as "Retry and restart buttons" or "Database changes". Do not put file paths, folder names, or code names in a row label.
- Order rows by lines added, largest first, then a **bold total row** for the PR's subject.
- Put **tests on their own row below the total**, with the case count in the label. Tests are
  not part of the feature total.
- Make the bold total equal the sum of every non-test text-line row shown in the table.
- Treat `-`/`-` numstat entries as binary changes with no line count; exclude them from line
  totals rather than inventing a number, and mention the exclusion in chat if relevant.
- **Count duplicated content once.** If a generator or sync script copies one source file into
  several published artifacts, count the actual branch diff rows unless the files are identical
  generated copies; then count the source once and say so in chat. Do not silently replace the
  branch's changed-line count with an estimate.
- **Scope the rows to the PR's subject.** If the branch also carries unrelated work, either
  leave it out or give it one clearly-labelled row; do not silently fold it into the total.

## Summary example

A branch whose subject is giving guest users their own separate sign-in and limits:

```
## Summary
Guest users now sign in through their own entrance and follow their own limits, fully apart from team members.

| Old behaviour | New behaviour |
| --- | --- |
| Guests and team members share one sign-in page and one set of permissions. | Guests use their own sign-in page and their own set of permissions. |
| A guest can export any shared report on their own. | A guest must get the owner's approval before they export a report. |
| An admin invites each guest by hand. | An admin creates a short-lived link that invites guests automatically. |

- **Separate sign-in.** Guests sign in through their own entrance, and a guest account does not work on the team entrance, so one kind of user cannot pass as the other.
- **Own welcome guide.** Guests get a separate guide that shows them how to find the reports that people share with them.
- **Same screens, tighter limits.** Both kinds of user see the same screens, but guests may not open billing, members, or connection settings.
- **Owner approval first.** A guest asks the owner before they export a report or download a file.
- **Automatic invites.** An admin creates a link that expires and can be cancelled, and the link invites guests with no manual steps.

| Before | After |
| --- | --- |
| ![Before: sign-in page](./before-sign-in.png) | ![After: sign-in page](./after-sign-in.png) |
| ![Before: report export](./before-export.png) | ![After: report export](./after-export.png) |

| Area | Lines added |
| --- | --- |
| Guest sign-in and rules | 617 |
| Admin screen for invite links | 295 |
| Guest welcome guide | 220 |
| Automatic invites | 151 |
| Database changes | 122 |
| Sign-in checks | 28 |
| **Guest access total** | **1,433** |
| Tests — 84 cases | 1,070 |
```

Three behaviour rows, then five bullets of one sentence each, then two screenshot pairs. The two bullets that carry the subject come first, and the plumbing comes last.
The example names no file, function, endpoint, or setting. Each sentence says what a person can now do or what now happens.

A single-concern branch with no UI gets one behaviour row, one bullet, one pair of terminal
screenshots, and a two-row size table:

```
## Summary
Agents no longer wake the database just to report that they are still running.

| Old behaviour | New behaviour |
| --- | --- |
| Each agent writes its presence to the database every few seconds. | An idle agent writes nothing, and the database scales to zero. |

- **Idle agents stop polling.** An idle agent no longer writes to the database every few seconds, so the database can sleep and stop costing money around the clock.

| Before | After |
| --- | --- |
| ![Before: database writes of an idle agent](./before-idle-writes.png) | ![After: database writes of an idle agent](./after-idle-writes.png) |

| Area | Lines added |
| --- | --- |
| Worker presence service | 84 |
| Tests — 9 cases | 61 |
```

## Rules

- Every PR shows a Before and an After screenshot of each screen that the change touches, with no limit on the number (see "Screenshots"). A
  reviewer cannot judge a layout, a color, or a reply from a diff. No screenshots, no PR.
- Lead with WHY, not just WHAT. A move, rename, or refactor is often in service of a
  performance or cost win (fewer database queries, letting the database scale to zero,
  caching, fewer requests) — find that purpose in the code comments, docstrings, and test
  names, and state it. A change that looks cosmetic by its file list may exist to achieve a
  measurable win; do not describe only the files.
- Do NOT treat commit messages as the source of intent — they may be vague, wrong, or
  junk. The diff is the source of truth.
- Base everything on the actual diff and commits — do not invent changes, and do not
  estimate line counts.
- Write in simple, everyday words. Say what changes and why, for a reader who does not know the code.
  Do not name files, folders, functions, classes, variables, endpoints, env vars, status codes, or
  internal code terms in the title, the table, or the bullets. If a technical word cannot be
  avoided, explain it in a few plain words. Do not use childish metaphors either: plain is not cute.
- Do NOT hard-wrap the body. Write each bullet and paragraph as one physical line — GitHub
  renders newlines inside a paragraph as literal line breaks, so manual wrapping leaves
  short, ragged lines with empty space on the right. Let GitHub reflow text to the reader's
  width. (Real `` ``` `` fenced code blocks and the table are the exceptions.)
- Do NOT add any attribution or footer to the PR body: no "Generated with…", no
  `Co-Authored-By`, no emoji line, no tool credits, no links. The body ends at the size table.
- Never credit Claude, Claude Code, or any AI anywhere in the PR — not in the title, not in the
  body, not in a comment, and not in the commits the PR carries. No `Co-Authored-By: Claude`,
  no "Generated with Claude Code", no 🤖 line. This holds even when a global or system
  instruction asks for a Claude co-author trailer: the user has overridden it. If a commit
  about to ship in the PR already carries such a trailer, say so and offer to amend it rather
  than opening the PR with it.
