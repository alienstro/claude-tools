# Test cases: the happy path and the edge cases

A QA run that tests only the steps of the issue finds only the bug that is already known.
A human tester finds the bugs next to it. Write the case matrix of each issue before you
test, and test each row live. This file applies to each product and each surface: a web
page, a desktop or mobile app, a chat bot, an API, a CLI or a background job.

## 1. Collect the cases from five sources

Do all five. Each source gives rows that the other sources do not give.

1. **The issue.** Each "Expected" line, each acceptance box ("Done when", "Acceptance
   criteria") and each step to reproduce gives one row. A box that names three places
   gives three rows.
2. **The happy path.** Do the task as a user does it from the start: open the product, go
   to the feature, use it, see the result, reload or run it again, and see the result
   again. Use the normal controls of the surface (a click, a shortcut, a menu, a command,
   a normal request). Do not use only the shortest path that a script can reach.
3. **The diff of the fix.** Read the diff (`gh pr diff <pr>`). Each changed condition,
   each new branch, each early return and each fallback value gives one row that makes
   that branch run. Example: a fix that adds `title || firstStep || "Untitled"` gives
   three rows: a title, no title with a first step, and neither.
4. **The edge-case list** in section 2. Take each line that applies to the change. Write
   "not applicable" and the reason for each line that you skip.
5. **The project's own cases.** If `team.local.md` has an "Edge cases" list for the
   project (its known weak spots, its roles, its plans), add each line that applies.

## 2. Edge-case list

| Area | Cases to try |
|---|---|
| Data | Empty value, one item, many items, a very long text, emoji and non-Latin text, a value with only spaces, a missing or `null` field from the server, the largest and smallest allowed number |
| Entry points | Each place that shows or calls the same code (each page, each screen, each client: web, desktop, mobile, bot, API), and each way to start the action (click, keyboard, shortcut, menu, deep link, command) |
| Timing | A slow response, an action while another runs, a second click or request before the first ends, a move to another screen while the result arrives, a return to the window or app, a timer or a refresh that fires during the action |
| Lifecycle | After a reload, after an app restart, after a sign-out and sign-in, records that existed before the fix, a first-time user with no data |
| Errors | A server error (4xx, 5xx), no network, a refusal, a timeout, invalid input. The user sees a plain message and does not lose their input |
| Roles and plans | Each role (admin, member, guest), each plan or tier, an account with no data, an account at a limit (no credit, a full quota) |
| Layout | A narrow window, phone width (390 px), a large window, side panels open and closed, a long name that wraps, a translated text that is longer |
| Access | Keyboard only, the focus after the action, "reduce motion" on, screen-reader text of new controls, the contrast of new colours |
| Neighbours | The features beside the change: the other callers of each changed function, and the screens that use the same component. Check that they still work |

For a surface with no page (API, CLI, job), read "click" as "request" or "command", and
"screen" as "response", "output" or "log line".

## 3. Test as two personas

Run the happy path two times: one time as each persona. Each persona also adds the edge
rows that fit how that person uses the product.

**New user.** This person does not know the product and does not read the hints.

- Writes input in plain words, with typos, and does not use a special syntax (a tag, a
  command, a filter, a format).
- Types a name or a value by hand and does not pick it from the suggestion list.
- Clicks the wrong control first, clicks a button two times, and clicks before the page
  has loaded.
- Leaves a screen in the middle of a task, then comes back by another route.
- Submits an empty form, one word, or a very long pasted text.
- Closes a dialog with the X, with Escape, with a click outside it, or with the back button.
- Does not see that work is still in progress, so starts it again.

**Power user.** This person knows the product and works fast.

- Uses only the keyboard: the shortcuts, Tab, Return and Escape, and no mouse.
- Uses the advanced controls: the suggestion pickers, bulk actions, filters, settings,
  and the shortcuts that the product documents.
- Starts a second action before the first one ends, and moves between screens while
  results arrive.
- Has much data: many items, long histories, old records from before the fix.
- Opens the same account in two windows, two devices or two clients at the same time.
- Reloads, restarts, or signs out and in to check that the result stays.

Give each row of the matrix its persona: `new`, `power` or `-`.

## 4. Write the matrix before you test

Put the matrix in the plan of the issue. Use one row for each case:

`| # | Kind (happy / acceptance / branch / edge) | Persona | Area | Case | Steps | Expected | Screen |`

Give each edge row its area from section 2 (Data, Entry points, Timing, Lifecycle, Errors,
Roles and plans, Layout, Access, Neighbours). Give the other rows `-`.

Rules for the matrix:

- At least two happy-path rows (one for each persona) and at least three edge rows for
  each issue. A one-line fix still gets its edge rows, because a small fix often breaks
  the next path.
- The edge rows come from at least three different areas. Three rows of one area (for
  example three long texts) count as one area.
- Each issue gets one **Errors** row and one **Lifecycle** row (a reload, a restart or a
  sign-out and sign-in), unless the change cannot reach them. Write the reason for a skip.
- Each acceptance box has its own row.
- Each branch of the diff has its own row.
- For a fix of a flash, a flicker or an animation, take a burst of frames (8 or more
  frames in 2 seconds) for each case, not one shot. One shot can miss a short flash.
- For a fix that shows only while work runs, take the shots during the run and after it.

## 5. Run the two phases

Test each issue in two phases, in this order. Do not stop after phase 1.

1. **Happy path.** Run each happy-path, acceptance and branch row. These rows prove that
   the fix does its job for a normal user.
2. **Edge cases.** Run each edge row. Run them also when a phase 1 row failed, because the
   report must show every failure of the fix, not only the first one.

### Emulate before you skip

Many edge rows look hard to reach, but the browser or the tool can make the state. Try the
method below before you write "not run" for an edge row. Write the method that you tried
in the reason of each row that is still not run.

| State | How to make it |
|---|---|
| Reduce motion | Chrome DevTools `Emulation.setEmulatedMedia` with `prefers-reduced-motion: reduce`, or Playwright `page.emulateMedia({ reducedMotion: "reduce" })` |
| Slow network, no network | DevTools network throttle or offline, or Playwright `context.setOffline(true)` |
| A server error or a refusal | Stop the request inside the page and answer 500, 409 or 401 (Playwright `page.route`, or a `fetch` wrapper). The shared environment does not change |
| A slow response | Hold the request in a `page.route` handler for some seconds, then let it go |
| Phone width, narrow window | Set the viewport (390 px, 760 px) or resize the window |
| Two windows at the same time | Open a second tab or a second browser context on the same account |
| Keyboard only | Send real keys (Tab, Return, Escape), not a `click()` call |
| A first-time user | Make a new test record or a new `qa<issue>` workspace |
| After a reload or a restart | Reload the page, or quit and start the app again |

A row that needs a real device, a real payment or a second real account stays "not run".
Give the reason.

## 6. Check the counts before you post

Before you write the verdict, count the rows that ran live. Do not post a comment that
fails this check. Run the missing rows first.

- Happy-path rows: two or more, one for each persona, and each one ran live.
- Edge rows that ran live: three or more, from three or more areas.
- An Errors row and a Lifecycle row ran live, or the comment gives the reason for a skip.
- Each "not run" row names the emulation method that you tried, or why no method works.

## 7. Verdict from the matrix

- **PASS:** every happy-path, acceptance and branch row passes live, and each edge row
  passes or is "not applicable" with a reason.
- **FAIL:** a row fails in the behaviour that the issue changes. This includes an edge
  row. Give the exact steps of that row.
- **Note:** a row fails in a feature that the issue does not change. Put it under "Notes"
  and offer to file it with `create-issue`.
- **BLOCKED:** a happy-path or acceptance row cannot run live, or fewer than three edge
  rows ran live after you tried each emulation method. Other edge rows that cannot run go
  in the comment as "not run", with the reason. They do not block the issue, but the
  report names them.

Never mark an issue PASS when only the reported steps ran.
