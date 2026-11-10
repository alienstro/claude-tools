# Desktop app (Electron) and browser with no app

Notes from real runs. Read them before the first desktop story.

## Find the app

```bash
orca computer list-apps --json | jq -r '.result.apps[] | select(.isRunning) | "\(.name) \(.bundleId) \(.pid)"'
```

A dev Electron app shows as `Electron com.github.Electron <pid>`. Use `--app pid:<pid>`, because the bundle id is the same for every dev Electron app. The main process of a dev app is the `.../Electron.app/Contents/MacOS/Electron` process; its children are the helpers.

## Clicks and shots

- **Electron ignores background clicks.** A background click reports `unverified (synthetic input)` and the page does not change. Use foreground input.
- **A covered or inactive window does not repaint.** Chromium stops the paint of a covered window, so the shot and the accessibility tree show an old page. The traffic-light buttons are grey in such a shot.
- **Raise the window first, every time.** Another app can take the focus between two steps:

  ```bash
  $S/raise.sh <pid>
  orca computer click --app pid:<pid> --x <x> --y <y> --restore-window --json
  ```

  If a click fails with "no longer the focused topmost recipient", raise the window and click again.
- **If the user works in another app and it takes the focus back,** do not fight it. Do the step with a DOM click (`node $S/cdp.mjs eval '...click()'`) and take the shot with `node $S/cdp.mjs shot <out.png>`. That shot has no title bar, and its scale is the page's `devicePixelRatio`. Say in the report which shots came this way.
- **Tell the user before the first foreground click.** It brings the window to the front and moves the pointer.
- **Coordinates:** the shot has `scale` 2 on a Retina screen. Click at `pixel / 2`.
- **Confirm each step through the debug port, not only the shot:** `node $S/cdp.mjs eval 'location.pathname'`.

## The debug port

The app starts with `--remote-debugging-port=<port>` (see `team.local.md`). `$S/cdp.mjs` uses it:

```bash
node $S/cdp.mjs eval '<expression>'           # runs in the page, prints the JSON result
node $S/cdp.mjs nav '<url>'                     # loads a URL in the page (also chrome:// pages)
node $S/cdp.mjs cookie <name> <out-file>        # writes the cookie value to a file (mode 600), prints nothing secret
```

- `nav` is a browser navigation, so the app's `will-navigate` guard does not stop it. Use it to open `chrome://gpu` and similar pages for a shot, then `nav` back to the app page.
- Electron does not support `Target.createTarget` (a new tab). Use the app's own page.
- A page that `nav` opens still gets the preload. Use it to prove that the bridge refuses a page that is not the app's.

## A restart

1. Raise the window, then `orca computer hotkey --app pid:<pid> --key CmdOrCtrl+Q --restore-window --json`.
2. Wait until no process of the app is left: `pgrep -f '<worktree>/node_modules/.pnpm/electron'`.
3. Start the app with the same command (`team.local.md`). The new process has a new pid.

## GPU proof

- In the page: a WebGL context and its renderer.

  ```js
  (() => { const gl = document.createElement("canvas").getContext("webgl");
    const i = gl && gl.getExtension("WEBGL_debug_renderer_info");
    return { webgl: !!gl, renderer: i ? gl.getParameter(i.UNMASKED_RENDERER_WEBGL) : null }; })()
  ```

- On screen: `node $S/cdp.mjs nav chrome://gpu`, raise the window, take the shot of "Graphics Feature Status", then `nav` back.

## Browser with no app

A browser tab often has no session for the local stack, and you must not type a password. Use the app's session in a headless browser:

```bash
node $S/cdp.mjs cookie <session-cookie-name> $W/cookie.txt
cd $W && npm init -y >/dev/null && npm i playwright-core@1 --silent   # one time
node ~/.claude/skills/do-screenshots/scripts/shot.js --url <page> --cookie <name>=@$W/cookie.txt --out $W/ev/<story>-browser.raw.png
```

The headless browser sends its own user agent, with no app tag, so the page renders as a web browser sees it. Delete `$W/cookie.txt` at the end.

## Shell trap

In zsh, `path` is the same array as `PATH`. A loop such as `for path in ...` breaks every command after it. Use another name, such as `page`.
