// Write guard for a manual QA run. Paste this function into the
// `evaluate_script` tool of the Chrome DevTools MCP (format "function").
//
// Why: a QA run must not change a shared environment. The guard stops each
// write request that the page sends through `fetch` to a path that contains
// GUARD_PATH. The request never leaves the browser. It waits DELAY_MS, so a
// screenshot can show the busy state, and then it fails as a lost network
// connection does, so the page shows its error state.
//
// Edit the two constants before each run. A page reload removes the guard.
// The guard covers `fetch` only. If the page writes through XMLHttpRequest,
// a form post or a navigation, the guard does not stop it.
() => {
  const GUARD_PATH = "/api/"; // a part of the URL of each write to stop
  const DELAY_MS = 10000; // time from the click to the failure

  if (window.__qaGuard) {
    return { alreadyInstalled: true, blocked: window.__qaBlocked };
  }
  window.__qaBlocked = [];
  const realFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    const url = typeof input === "string" ? input : input.url;
    const method = (
      init.method ||
      (typeof input !== "string" && input.method) ||
      "GET"
    ).toUpperCase();
    if (url.includes(GUARD_PATH) && method !== "GET" && method !== "HEAD") {
      window.__qaBlocked.push({ method, url, at: Date.now() });
      return new Promise((_, reject) =>
        setTimeout(() => reject(new TypeError("Failed to fetch")), DELAY_MS),
      );
    }
    return realFetch(input, init);
  };
  // A browser confirm popup stops the MCP until a person answers it. The
  // guard blocks the write that follows, so an automatic "yes" is safe.
  window.confirm = () => true;
  window.__qaGuard = true;
  return { installed: true, guardPath: GUARD_PATH, delayMs: DELAY_MS };
}
