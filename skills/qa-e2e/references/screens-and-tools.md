# Screens and tools

Four skills read this file: `qa-e2e`, `qa-stories`, `create-pr` and `edit-pr`. It says which screens a change needs, and which tool takes each screenshot.

## 1. List every screen

Before the first test or shot, make a screen list. A screen is on the list when it renders something that the change touches: a component, a text, a field, an endpoint, a flag, a setting or a stored value.

Find the screens:

1. Search the apps for each changed name, text, field and endpoint (`rg -n`).
2. Follow each import up to the route, the window or the dialog that renders it.
3. For a server change, find each page, app screen, chat reply or email that shows the changed data.

Then go through each axis below. Add one row for each value that the change can touch:

| Axis | Values to check |
|---|---|
| Surface | Web page in a browser, desktop app, mobile app, chat app, email or SMS, terminal output |
| Platform | macOS, Windows, Linux; the web build and the desktop build of the same page |
| Way in | Each route, menu item, button, keyboard shortcut and deep link that opens the screen |
| State | Empty, loading, filled, error, disabled, success, long text that can overflow |
| Role | Owner, member, guest, signed out |
| Theme | Light and dark, when the change has a color, an icon or an image |
| Width | Desktop width and a narrow width (390 px), when the change has layout |
| After a restart | The value stays after a reload or an app restart, when the change stores a value |
| Control | A screen that must not show the change, or must stay the same |

Use risk-based coverage, as test teams do: test each value that the change can touch, not each combination of all axes. For each axis that you skip, write one line in the screen list: "Not affected: `<reason>`." Show the screen list to the user before the first shot.

**Each row of the screen list gets its own screenshot.** There is no limit on the number of rows. A screen that you cannot reach is BLOCKED, with the reason. Never drop a screen from the list without a reason.

## 2. Find the tools of this session

Before you plan the shots, find which tools this session has:

- MCP tools: run `ToolSearch` with `select:` for the names below, or with a keyword such as `screenshot` or `chrome`.
- Command-line tools: `command -v orca npx node adb xcrun screencapture`.
- Playwright: `npx --no-install playwright --version`, or install `playwright-core@1` in the scratchpad.

| Tool | What it reaches |
|---|---|
| Playwright (`playwright-core`, `~/.claude/skills/do-screenshots/scripts/shot.js`) | A web page, headless, with a clean session or a session cookie. An Electron app through `chromium.connectOverCDP('http://localhost:<debug port>')` |
| CDP helper (`~/.claude/skills/qa-stories/scripts/cdp.mjs`) | The page of an Electron app on its debug port: `eval`, `nav`, `shot` |
| Chrome DevTools MCP | A web page in a Chrome that the MCP starts: page text, network, console, screenshot |
| Claude in Chrome (`mcp__claude-in-chrome__*`) | A web page in the user's Chrome, with the user's signed-in session |
| Orca computer use (`orca computer`, `~/.claude/skills/qa-e2e/scripts/app.sh`) | Any visible window: native apps, Electron windows, menus, OS dialogs, simulators, chat apps |
| REA (`mcp__rea__capture_*`) | `capture_web_screenshot`, `capture_electron_scenario`, `capture_native_ui_scenario`, `capture_adb_screen` |
| macOS `screencapture` | The full screen or one region (`screencapture -x -R x,y,w,h <out.png>`) |
| `xcrun simctl io booted screenshot` | The iOS Simulator |
| `adb exec-out screencap -p` | An Android device or emulator |
| `curl`, the MCP client, the shell | An API, an MCP tool, a CLI or a job. Shoot the output (see "Terminal output" below) |

## 3. Pick the tool for each screen

Use the first tool in the row that this session has. If a tool fails two times for a reason in the tool (a click that does not arrive, an empty shot), use the next tool. A product bug is not a tool failure: do not change the tool to hide it.

| Surface | Tool order |
|---|---|
| Web page, clean session | Playwright, then Chrome DevTools MCP, then REA `capture_web_screenshot`, then Claude in Chrome |
| Web page, signed-in session | Claude in Chrome, then Playwright with the session cookie, then Chrome DevTools MCP |
| Electron app, the page inside the window | CDP helper or Playwright over CDP, then Orca computer use, then REA `capture_electron_scenario` |
| Electron app, the window frame, a native menu, an OS dialog, a restart, a focus or tray change | Orca computer use, then `screencapture` of the window region |
| Native desktop app | Orca computer use, then REA `capture_native_ui_scenario`, then `screencapture` |
| Chat app (Telegram, WhatsApp, Slack, Discord) | Orca computer use on the desktop client, then the web client through the web page rows |
| iOS app | `xcrun simctl io booted screenshot`, then Orca computer use on the Simulator window |
| Android app | `adb exec-out screencap -p`, then REA `capture_adb_screen`, then Orca computer use on the emulator window |
| Email or SMS | The provider's inbox or log in a browser, through the web page rows |
| API, MCP tool, webhook, CLI, job, log | The command, then a shot of its output. Also shoot each page or app screen that shows the result |

Why this order: Playwright and CDP use selectors and wait for the page state, so a second run gives the same shot. Computer use clicks on pixels. It is slower, and a covered window or a moved button can make it fail. Use computer use for what only the real window shows.

**A CDP or Playwright shot of an Electron app shows only the page.** It has no title bar, no native menu and no OS dialog. When the screen under test is part of the window or the OS, use Orca computer use or `screencapture`.

## 4. Terminal output as a screenshot

Put the command on the first line of the output. Save the output as `<name>.txt`, wrap it in a `<pre>` tag of a small HTML file with a dark background and a monospace font, then shoot that file:

```bash
node ~/.claude/skills/do-screenshots/scripts/shot.js --url file://<path>.html --out <png>
```

## 5. Record the tool

Each result names the tool that took its shot (a "Tool" column, or one line under the shot). When a tool failed and you used the next one, say which tool failed and why.
