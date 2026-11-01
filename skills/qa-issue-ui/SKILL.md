---
name: qa-issue-ui
description: Use when the user wants a closed or fixed GitHub issue checked on a live staging site, in a real browser, through the Chrome DevTools MCP. Read the issue and its fix PR, plan the checks, stop each write request inside the page so the shared environment does not change, take a screenshot while each action runs and after it ends, check the state again after a reload, and report a results table with the screenshots in chat. Use it when the user says "/qa-issue-ui", "test this issue on staging", "can you test it yourself", "do it by yourself via chrome dev tools", "QA this fix", "check if issue 123 works on staging", or pastes an issue URL and asks how to test it, even if they do not name the browser or the MCP. For a backend fix that has no page to click, use `qa-issue-api` instead.
---

# QA a UI issue on staging

Check that a fix works on a live staging site, and prove it with screenshots, without a change to the data that other people use.

## Rules

- **Do not change shared data.** Before you click a control that writes (save, send, delete, close, activate, sign out), install the write guard from `scripts/guard.js`. The guard keeps the request in the browser. A test that needs a real write needs a "yes" from the user first, and a test record that the user owns.
- **Do not send a message to a real person.** An email, a chat message or an invite to a real address is a real write, even on staging.
- **Look before you report.** Read each screenshot with the Read tool before you put it in the report.
- **Keep the repository clean.** The MCP saves files only inside the workspace root. Move each screenshot to the scratchpad at once, and run `git status --short` at the end.
- **Do not leave a browser popup open.** A `confirm` or `alert` popup stops each later MCP call. Dismiss a stray popup with `handle_dialog` and the `dismiss` action.
- If this skill has a file for the site in `references/`, such as `references/<project>.local.md`, read it first. It names the URLs, the write paths and the safe test data. Keep a `*.local.md` file out of a public repository.

## Steps

1. **Read the issue and the fix.**
   - Run `gh issue view <n> --repo <owner/repo> --json title,body,state,comments`.
   - Find the fix PR in the comments ("Fixed in #N") or with `gh pr list --search "<n>" --state merged`.
   - Read the PR body and the diff of the files that the issue names. Use `rtk proxy git show <sha> -- <file>` if a filter hides the diff.
   - Write one short line for each item of the issue scope. Each line becomes one row of the results table.
2. **Plan each check.** For each row, find:
   - The page and its URL. Search the route file of the app, not the menu.
   - The control to use, and the text or state that shows a pass.
   - The kind of action: read-only, a write that the guard can stop, or a write that the guard cannot stop. Ask the user before a check of the last kind.
   - A check that needs data that does not exist, such as a button on a record that is not there. Say so and skip it, or ask the user for test data.
3. **Open the page.** Run `list_pages`. Use the page that is already signed in to the site, and go to the URL with `navigate_page`. Do not open a new browser.
4. **Install the guard.** Copy the function from `scripts/guard.js`. Set `GUARD_PATH` to a part of the URL that each write of the page contains, and set `DELAY_MS` to `10000`. Run it with `evaluate_script`. A reload removes the guard, so install it again after each reload.
   - Check first that the page sends its writes through `fetch`. Search the API helper of the app. The guard does not cover XMLHttpRequest, a form post or a navigation.
5. **Run each check and take two screenshots.** Each screenshot has a red box on the tested part. Draw the box with the function from `scripts/highlight.js`. Give the element as `args` with its uid from `take_snapshot`.
   - Scroll the control into view, and draw the box on it. The box lets a click go through.
   - Click the control with `evaluate_script` (`button.click()`). Return at once, so that the call does not wait for the request.
   - At once, take the "while it runs" screenshot with `take_screenshot` and a `filePath` inside the workspace root. Do not use `fullPage`, because the box is fixed to the viewport.
   - Run `wait_for` with the text that shows the end state, such as the error text.
   - Scroll the result into view, then draw the box on the result. A banner or a toast can be far from the control, so look for it with `take_snapshot` (role `alert` or `status`) before you scroll.
   - Take the "after" screenshot. Then remove the box with the one-line function in the header of `scripts/highlight.js`.
   - Read `window.__qaBlocked` to see each request that the guard stopped.
6. **Check a visual-only change** (a color, a theme, a phone layout) with `emulate`: `colorScheme` for dark or light, and `viewport` with `mobile,touch` for a phone. A narrow desktop window is not a touch device, because a mouse can still hover.
   - Take one screenshot with the red box on the changed part. Then remove the box and take one clean screenshot, because the red color can hide a color change.
7. **Check the state after the run.** Reload the page, which removes the guard. Read the record again with a GET request, or from the page. Compare it with the state before the run. Report any change.
8. **Prepare the screenshots.**
   - Move them to `<scratchpad>/qa-<issue>/`.
   - Shrink each one: `sips -s format jpeg -s formatOptions 82 --resampleWidth 1800 <in>.png --out <out>.jpg`.
   - Run `git status --short` and check that the repository is clean.
   - Read each screenshot.
9. **Report in chat.** Use the format below.

## Report format

Write the report in the chat, not in a code block, so that the table renders. Keep each table cell short, because a long cell wraps and breaks the table when the user copies it.

```
| Check | While it runs | After it ends | Result |
| --- | --- | --- | --- |
| **<control or item>** | <busy state> | <end state> | **Pass** |

**1. <check>, <state>.** <one sentence on what the screenshot shows>

![<check> <state>](<absolute path to the .jpg>)

**Not tested:** <each skipped check and the reason>

**Follow-ups:** <each gap that is not a fail of the issue>
```

- Put one row in the table for each item of the issue scope. Use **Pass**, **Fail** or **Not tested**.
- After the table, show each screenshot in test order, with one sentence of caption.
- Say that staging did not change, and name the proof: the list of stopped requests, and the state after the reload.
- Keep a gap that is not part of the issue apart from the results. Offer to open an issue for it. Do not open one without a "yes".
- If the chat cannot show local images, say so. Then offer `open <files>` to show them in Preview, or a private page through the Artifact tool.

## Common problems

| Problem | Cause | Fix |
| --- | --- | --- |
| `take_screenshot` returns "Access denied: path … is not within any of the configured workspace roots" | The MCP saves files only inside the workspace root | Save inside the repository, then move the file to the scratchpad at once |
| A later MCP call shows "Open dialog … Call handle_dialog" | The page opened `confirm` or `alert` | Run `handle_dialog` with `dismiss`. Override `window.confirm` in the guard before the click |
| The "while it runs" screenshot shows the end state | The request ended before the screenshot | Set `DELAY_MS` to 10000 or more, and take the screenshot right after the click |
| The error does not show in the screenshot | The page shows it at the top, out of view | Find the `alert` element with `take_snapshot`, scroll it into view, then take the screenshot |
| The red box is not on the element in the screenshot | The page scrolled or the layout moved after the box was drawn, or the screenshot used `fullPage` | Draw the box again right before the screenshot. Use a viewport screenshot |
| `highlight.js` returns `inView: false` or `skipped` | The element is out of the viewport, or it is hidden | Scroll the element into view, or find the visible element with `take_snapshot`, then draw the box again |
| A record changed during the run | A click ran before the guard, or the page wrote through a path that the guard does not cover | Stop. Tell the user what changed and when. Do not try to undo a final action, such as a close or a delete, without the user |
