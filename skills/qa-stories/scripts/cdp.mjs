#!/usr/bin/env node
// Talks to the app page through its Chrome debug port.
// Usage:
//   cdp.mjs eval '<expression>'        run in the page, print the JSON result
//   cdp.mjs nav '<url>'                load a URL in the page (chrome:// pages too), wait for the load
//   cdp.mjs cookie <name> <out-file>   write the cookie value to a file (mode 600), print only "written"
//   cdp.mjs shot <out.png>             save a screenshot of the page; works when the window has no focus
// CDP_PORT selects the port (default 9333).
import { writeFileSync } from "node:fs";

const [cmd, a, b] = process.argv.slice(2);
const port = process.env.CDP_PORT ?? "9333";
if (!["eval", "nav", "cookie", "shot"].includes(cmd) || !a) {
  console.error("Usage: cdp.mjs eval '<expr>' | nav '<url>' | cookie <name> <out-file> | shot <out.png>");
  process.exit(2);
}
const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
const page = list.find((t) => t.type === "page");
if (!page) throw new Error(`No page on debug port ${port}.`);
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((ok) => ws.addEventListener("open", ok));
let id = 0;
const call = (method, params) =>
  new Promise((ok) => {
    const n = ++id;
    ws.addEventListener("message", function on(e) {
      const m = JSON.parse(e.data);
      if (m.id === n) {
        ws.removeEventListener("message", on);
        ok(m);
      }
    });
    ws.send(JSON.stringify({ id: n, method, params }));
  });

if (cmd === "eval") {
  const r = await call("Runtime.evaluate", { expression: a, awaitPromise: true, returnByValue: true });
  const ex = r.result?.exceptionDetails;
  console.log(ex ? `ERROR: ${ex.exception?.description ?? ex.text}` : JSON.stringify(r.result?.result?.value, null, 1));
} else if (cmd === "nav") {
  await call("Page.enable");
  const loaded = new Promise((ok) => {
    ws.addEventListener("message", (e) => {
      if (JSON.parse(e.data).method === "Page.loadEventFired") ok();
    });
    setTimeout(ok, 15000);
  });
  const r = await call("Page.navigate", { url: a });
  if (r.result?.errorText) console.log(`ERROR: ${r.result.errorText}`);
  await loaded;
  const href = await call("Runtime.evaluate", { expression: "location.href", returnByValue: true });
  console.log(href.result?.result?.value);
} else if (cmd === "shot") {
  const r = await call("Page.captureScreenshot", { format: "png" });
  if (!r.result?.data) throw new Error(`No screenshot: ${JSON.stringify(r.error)}`);
  writeFileSync(a, Buffer.from(r.result.data, "base64"));
  console.log(a);
} else {
  if (!b) throw new Error("cookie needs <name> <out-file>.");
  const r = await call("Network.getCookies", {});
  const c = r.result.cookies.find((x) => x.name === a);
  if (!c) throw new Error(`No cookie named ${a}.`);
  writeFileSync(b, `${c.value}`, { mode: 0o600 });
  console.log("written");
}
ws.close();
