---
name: edit-pr
description: Use when the user wants to rewrite an existing pull request's title and description into a handful of one-sentence bullets aimed at a reviewer, with an old/new behaviour table and a lines-changed table. Triggers on "/edit-pr", "update the PR description", "rewrite this PR".
user-invocable: true
allowed-tools: Bash, Read
---

# Edit PR

Rewrite an existing pull request in place: a title with a conventional-commit prefix, and a
body that is a short summary — a lead line, an old/new behaviour table, at most five
one-sentence bullets — then, when any screen changes, a Before and After screenshot table of each screen, then a table of lines added per area. Nothing else. Write it in simple, everyday words for a reader who does not know the code. Say what changes for a user, an owner, or an operator, and why. Do not name files, folders, functions, classes, variables, endpoints, env vars, or other code names. The diff carries those.

Never opens a new PR. If the branch has none, stop and point at `/create-pr`.

## Steps

1. Identify the target PR:
   - If the user names a PR number, use it.
   - Otherwise find the PR for the current branch:
     `gh pr view --json number,title,body,baseRefName,headRefName`
   - If no PR exists for the branch, STOP and tell the user to use `/create-pr` instead.
2. Read the PR's actual base branch from `baseRefName` — do NOT assume `main` or `dev`.
3. Gather context:
   - Commits on the branch: `git log --oneline <base>..HEAD`
   - Changed files: `git diff --stat <base>...HEAD`
   - Diff: `git diff <base>...HEAD`
   - Per-area line counts: `git diff <base>...HEAD --numstat -- <path>` (see "Size table"). Use the three-dot branch diff exactly; do not count the working tree, commit totals, or a guessed subset.
   - For anything nontrivial, open the key changed files (the new and most-changed
     source) and read enough to know what the change actually does — the diffstat says
     what moved, the file bodies say what it does.
   - Intent signals: read the comments, docstrings, test names, and changed
     defaults inside the diff — the *why* usually lives there, not in the commits.
   - The PR's current title and body are reference only. You are replacing them, and they
     may describe an older, narrower version of the branch.
   - Screenshots: if the diff changes any screen, make the screen list and take the Before and
     After shots of each screen now (see "Screenshots"). Shoot again after each new UI commit:
     an old After shot shows an old version.
4. Write the new title and body in the format below.
5. Show the proposed title and body to the user and confirm before applying — the user drives
   git history. Flag anything unusual (scope that outgrew the old title, wrong base,
   unrelated commits).
6. Apply: `gh pr edit <number> --title "<title>" --body "<body>"`. When a screen changes, use
   `--body-file` and one `--attach` per screenshot (see "Screenshots").
7. If reading the diff surfaced something a reviewer genuinely needs to know (a risky
   dependency, a stale doc, a follow-up, work that is committed but not deployed), say it to
   the user in chat — not in the PR body.

Scope: if the user asks to change only the title or only the description, edit just that field
and leave the other untouched.

## Title

- Format: `<type>: <description>` where `<type>` is exactly one of:
  - `feat:` a new feature or capability.
  - `fix:` a bug fix — correcting broken or wrong behavior.
  - `chore:` everything else — cleanup, refactors, dependency bumps, config, docs, tests.
- One line, imperative mood, lowercase first word. No PR number, no branch name, no trailing
  period. Pick the type that matches the main purpose of the work *as it stands now* — a
  branch that grew past its original title gets a new one.

## Body

The body is exactly one section with two tables, or three when a screen changes (the `##` heading is literal — include it):

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
| (one row per screen of the screen list, with no limit; leave the table out when no screen changed) | ... |

| Area | Lines added |
| --- | --- |
| ... | ... |
```

One sentence per bullet is the hard rule. A bullet that needs a second sentence or an "and
also" is really two changes: split it, or drop the smaller half. Never a dense paragraph.

Nothing follows the size table. No `## Technical details`, no test notes, no reviewer notes, no
file lists.

## Screenshots

A PR that changes what a person sees on any screen carries a Before and an After screenshot of
each screen that the change touches. A reviewer judges a UI change from the pictures, not from
the class names in the diff. Leave the table out only when no screen changes.

A screen is any place where a person sees the change: a web page, the desktop app window, a
mobile screen, a chat reply, an email. An API, a config, or a flag change that alters what a
page shows also changes that page.

1. Make the screen list with `~/.claude/skills/qa-e2e/references/screens-and-tools.md`:
   each surface, platform, way in, state, role, theme, width and control screen that the
   change touches. Each row gets one pair. There is no limit on the number of pairs. Put the
   pairs closest to the soul of the change first. Show the screen list to the user, with a
   "Not affected" line for each skipped axis.
2. Take the After shot from `HEAD`. Use fake data only, and keep the script, the data, and the
   viewport in the scratchpad.
   - Pick the tool for each screen from the tool order in `screens-and-tools.md`. Use the
     tools that this session has, and use the same tool for the Before and the After shot.
   - For a web screen, use `/do-screenshots`.
   - For a desktop app screen, start the app from the worktree with its debug port, and use
     the debug port or Orca computer use (see `screens-and-tools.md`).
3. Take the Before shot from the PR base. Make a worktree of the merge base in the scratchpad
   (`git worktree add <scratchpad>/base $(git merge-base origin/<base> HEAD)`), install it
   with `pnpm install --frozen-lockfile --prefer-offline`, and run the same script, the same
   data, and the same viewport against it. Remove the worktree after the shot
   (`git worktree remove <scratchpad>/base`).
4. Run one dev server for each part at a time, and stop each one after its shots.
5. Read every PNG with the Read tool before you put it in the PR. A shot that shows a spinner,
   a sign-in page, or a broken image is not a Before or an After: fix the script and shoot again.
6. Name the files `before-<screen>.png` and `after-<screen>.png` in one folder.
7. If you cannot get a good pair for a screen after two tries, STOP and tell the user which
   screen failed and why. Do not drop the screen, and do not put a placeholder in the table.

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

A long-running branch usually grew since the PR was opened. Re-derive the bullets from the
current diff; do not preserve a bullet just because the old body had it.

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

Three behaviour rows, then five bullets, one sentence each, the two that carry the subject first and the plumbing last.
The example names no file, function, endpoint, or setting. Each sentence says what a person can now do or what now happens.

A single-concern branch gets one behaviour row, one bullet, and a two-row size table:

```
## Summary
Agents no longer wake the database just to report that they are still running.

| Old behaviour | New behaviour |
| --- | --- |
| Each agent writes its presence to the database every few seconds. | An idle agent writes nothing, and the database scales to zero. |

- **Idle agents stop polling.** An idle agent no longer writes to the database every few seconds, so the database can sleep and stop costing money around the clock.

| Area | Lines added |
| --- | --- |
| Worker presence service | 84 |
| Tests — 9 cases | 61 |
```

## Rules

- A PR that changes any screen shows a Before and an After screenshot of each screen that the
  change touches, with no limit on the number (see "Screenshots"). A reviewer cannot judge a layout, a color, or a cut-off text from a diff.
- Lead with WHY, not just WHAT. A move, rename, or refactor is often in service of a
  performance or cost win (fewer database queries, letting the database scale to zero,
  caching, fewer requests) — find that purpose in the code comments, docstrings, and test
  names, and state it. A change that looks cosmetic by its file list may exist to achieve a
  measurable win; do not describe only the files.
- Do NOT treat commit messages or the existing PR body as the source of intent — they may be
  vague, wrong, or stale. The diff is the source of truth.
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
  already in the PR carries such a trailer, say so and offer to amend it rather than leaving
  it in place.
