# Surfaces: how to test and prove each kind of fix

Pick the surface from the issue and the files that the fix PR changes. One issue can need two surfaces or more (for example, a console page, the desktop app, and the API behind them).

Before you test, read `screens-and-tools.md` in this folder. It makes the full screen list (each surface, platform, way in, state, role, theme, width and control screen), finds the tools of this session, and gives the tool order for each surface. Each row of the screen list gets its own screenshot. The "Main tool" column below is only the first choice.

| Surface | Main tool | Proof |
|---|---|---|
| Web page or web app | Playwright (headless, clean session), Chrome DevTools MCP, or Claude in Chrome (signed-in session) | Cropped screenshots, page text, network status of the request |
| Desktop app (native, Electron) | The debug port (CDP or Playwright) for the page; `scripts/app.sh` (Orca computer use) for the window, menus and OS dialogs | Cropped screenshots, page state or accessibility tree text |
| Chat app (Telegram, WhatsApp, Slack, Discord desktop) | `scripts/app.sh` on the desktop client | Screenshots cropped to the chat pane, exact reply text |
| Mobile app | iOS Simulator or Android emulator window through `app.sh`; `adb` / `xcrun simctl io booted screenshot` | Screenshots, logcat lines |
| HTTP API, webhook, MCP tool | `curl -s -w ' HTTP %{http_code}'`, the MCP client | Request and response (status and trimmed body) as text, plus a screenshot of the result |
| CLI or script | The shell, then any application that shows the result | Command and output as text, plus a screenshot of the result |
| Background job, timer, migration | Trigger or wait for the job on the test environment, then logs and read-only database queries | Log lines and counts from the live run, plus the test summary, plus a screenshot of the result |
| Refactor or removed code | The live path that the change touches, and the logs since the deploy | The old symptom absent after the deploy, the new path working, plus the test summary and `file:line`, plus a screenshot of the result |
| Email or SMS | The provider's inbox or log; a real device when the user can help | Screenshot of the received message, provider status |

## Web page

- Open a new tab of your own. Never reuse the user's tabs.
- Read the page text first, then zoom on the region under test. Save the screenshot to disk.
- Before the shot, put a red outline on the element that proves the result. Run this in the page, with the selector of that element:

  ```js
  document.querySelectorAll('<selector>').forEach(el => {
    el.dataset.qaMark = '1';
    el.style.setProperty('outline', '3px solid #e5322d', 'important');
    el.style.setProperty('outline-offset', '2px', 'important');
  });
  ```

  An outline does not change the layout, so the page looks the same as for a user. After the shot, remove it: `document.querySelectorAll('[data-qa-mark]').forEach(el => { el.style.removeProperty('outline'); el.style.removeProperty('outline-offset'); delete el.dataset.qaMark; })`.
- If a parent with `overflow: hidden` cuts the outline, put the outline on that parent, or draw the box with `scripts/mark_box.py`.
- A write control (save, send, delete, publish) changes shared data. Click it only with test data that you made, or when the user allows it. If the `qa-issue-ui` skill is installed, its write guard can hold the request in the page.
- For a role or permission fix, the signed-in role decides what you can see. Say which role you used, and which role you could not test.
- If the browser shows a sign-in page, stop and ask. Never type a password.

## Desktop and chat apps (computer use)

```bash
$S/app.sh <app> tree 40                     # read the tree, find the field and buttons
$S/app.sh <app> send "<field regex>" "text" # type in a field and press Return
$S/app.sh <app> wait "<reply regex>" 120 "<your-own-message regex>"
$S/app.sh <app> shot $W/ev/<n>-<name>.png "0.29,0,0.62,1"   # crop to the pane under test
$S/app.sh <app> tap 810 1770                # click a point read from the last shot
```

- Read each shot with the Read tool before you use it as proof.
- Save the shot as `<n>-<name>.raw.png`. Then draw a red box around the proof in the pixels of the cropped shot: `python3 $S/mark_box.py $W/ev/<n>-<name>.raw.png $W/ev/<n>-<name>.png <x,y,w,h>`. Read the marked shot, and move the box if it misses.
- Some controls (chat inline buttons, canvas UI) are not in the tree. Read their place from the last shot and use `tap`.
- If the tree shows only a dialog, the window lost its tree. Click the field by coordinates (`orca computer click --x --y`), then `app.sh <app> type`.
- To edit your last message in many chat apps: `key Up`, `hotkey CmdOrCtrl+A`, `type "<new text>"`.
- One desktop runs one GUI test at a time. Do not give GUI work to parallel agents.
- Before the first shot, look at the whole window once. If it shows secrets (keys, passwords, tokens), close that view or crop it out, and never upload that shot.

## Screen proof for every surface

Each issue needs a screenshot of its live result on each row of its screen list (see `screens-and-tools.md`), on every surface, with no exception. Text proof alone cannot pass an issue. A row with no shot is BLOCKED, never PASS.

The user allows you to drive their desktop through computer use (`scripts/app.sh`). Open, start or focus any application that can show the live result. The surface table above is a start, not a limit.

1. Prefer the place where a user sees the result: the product page, the app screen, the chat reply.
2. If no such place exists, open the application that shows the result best. Examples: browser DevTools, a terminal, a database client, a log viewer, a simulator.
3. Take the shot during or after the live run, never from old output. Crop it to the result.

**Caution:** a debug tool or a terminal can show secrets, such as headers, cookies, env values, or keys. Do not open those views. Look at each shot before you upload it.

## API, CLI and jobs

- Send only read-only requests, or requests that the server refuses before any write (a 400 for bad input, a 401 without a key).
- Read a key from the server's own environment on the server. Never print it.
- Show the request and the response as text in the comment.

## Data that the test needs

- Make your own test data (a test record, a reminder, a one-use code). Name it so it is easy to find (`qa<issue>`). List it for the user at the end.
- Never spend real money. Cancel each approval that would spend.
