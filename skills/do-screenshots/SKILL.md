---
name: do-screenshots
description: Use when the user wants to see a UI change as a picture. Take a headless Playwright screenshot of the real page that runs the current branch, read it, and report the path with a before/now table. Triggers on "/do-screenshots", "screenshot the change", "show me the UI change", "I want to see it".
---

# To Screenshot

Show the user a UI change as a real screenshot of the page, not as a description of the code.

## Rules

- Use only local data and a throwaway local secret. Never use production data, a real password or a real token.
- Do not print a secret. Write a token to a file in the scratchpad and read it from there.
- Run one dev server only. Reuse a server that already runs on the port.
- Put every screenshot in the scratchpad `shots/` directory. Do not write screenshots into the repository.
- Read each screenshot with the Read tool before you report it. Do not report a picture that you did not look at.
- Write the report in ASD-STE100 Simplified Technical English.

## Steps

1. **Find what changed.** Run `git diff <base>...HEAD --stat` and find the UI text, the values or the components that changed. Write down the "before" value of each one from the base commit. That gives the "Before" column.
2. **Find the page.** Search for the component or the text with `git grep`. Find the route, the tab and the data source of the page. If this skill has a file for the repository in `references/`, such as `references/<repo>.local.md`, read it first. Keep a `*.local.md` file out of a public repository.
3. **Check the data path before the browser.** Call the API of the page with `curl` and the local session. A `503` or `401` answer tells you what is missing faster than a browser does.
4. **Start the smallest topology.** Start only the app that serves the page. Give it a scratch database when it needs one (`createdb <name>`, then apply the migrations). Set a larger heap on an 8 GB machine: `NODE_OPTIONS=--max-old-space-size=4096`.
5. **Set up Playwright one time per session.** Install `playwright-core` in the scratchpad, not in the repository:

   ```sh
   cd <scratchpad> && npm init -y >/dev/null && npm i playwright-core@1 --silent
   ```

   The script finds the cached headless Chromium in `~/Library/Caches/ms-playwright/` by itself.
6. **Take the screenshot.** Run the bundled script from the scratchpad:

   ```sh
   node ~/.claude/skills/do-screenshots/scripts/shot.js \
     --url http://localhost:<port>/<page> \
     --out <scratchpad>/shots/<page>-<change>.png \
     [--cookie <name>=@<scratchpad>/token.txt] [--click-tab "<Tab name>"] \
     [--text "<exact text near the change>"] [--crop]
   ```

   `--text` scrolls the change into view. `--crop` also saves `<out>-crop.png` of the card that holds the text.
7. **Read the screenshot.** Open each PNG with the Read tool. Compare it with the "Before" values from step 1. Note any text on the page that looks wrong, also when your change did not cause it.
8. **Clean up.** Stop the server that you started. Drop the scratch database. Revert files that the dev server generated, such as `next-env.d.ts`. Run `git status --short` and confirm that the tree is clean.
9. **Report** in the format below.

## Report format

Use this shape. Keep the headings in bold, and keep the table.

```markdown
I took the screenshot headless with Playwright. It shows the real <page name> page, running on this branch's code:

**Path:** `<absolute path to the PNG>`

**What it shows on the `<CARD OR AREA NAME>` card**

| | Before this change | Now (screenshot) |
| --- | --- | --- |
| <Field> | <old value> | **<new value>** |
| <Field> | <old text> | "<new text, with the changed words in bold>" |

**How I ran it**
- <topology: which app ran, which database, which data>
- <sign-in: a throwaway local secret, no real password or production data>
- <API proof: the values that the API returned for the changed field>
- <cleanup: server stopped, scratch database dropped, generated files reverted, tree clean>

**What I could not show:** <a part of the change that the screenshot does not cover, why, and where the code for it is, as `path:line`>. Leave out this section when nothing is missing.

**Something confusing that I found (not fixed):** <text on the page that can mislead a person, its `path:line`, and a one-line fix offer>. Leave out this section when nothing is wrong.
```

## Common failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `curl` returns `000` and the log shows `heap out of memory` | A child server, such as an embedded agent, ran out of heap | Skip the child if the page does not need it, or set `NODE_OPTIONS=--max-old-space-size=4096` |
| API returns `503` with `database_required` | The page refuses the in-process store | Create a scratch database and apply the migrations |
| The tab click times out | The tab name is wrong | Read the tab list in the component, and pass the exact label to `--click-tab` |
| The screenshot shows the sign-in page | The cookie name or the secret does not match | Read the cookie name in the auth code, and mint the token with the same secret that the server has |
