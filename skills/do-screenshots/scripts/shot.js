#!/usr/bin/env node
// Takes a headless screenshot of one page, with an optional session cookie,
// tab click and scroll to a text. playwright-core loads from the current
// directory, so the package stays in the scratchpad, not in the repository.
const fs = require("fs");
const path = require("path");
const os = require("os");

function args(argv) {
  const out = { crop: false, width: 1400, height: 1000, timeout: 180000 };
  for (let i = 2; i < argv.length; i++) {
    const key = argv[i].replace(/^--/, "");
    if (key === "crop") out.crop = true;
    else out[key.replace(/-(\w)/g, (_, c) => c.toUpperCase())] = argv[++i];
  }
  if (!out.url || !out.out) {
    console.error(
      'usage: shot.js --url <url> --out <file.png> [--cookie name=value|name=@file] [--click-tab "Name"] [--text "exact text"] [--crop] [--width 1400] [--height 1000]',
    );
    process.exit(2);
  }
  return out;
}

// The newest cached headless shell. Null lets Playwright use its own default.
function headlessShell() {
  const root = path.join(os.homedir(), "Library/Caches/ms-playwright");
  if (!fs.existsSync(root)) return null;
  const dirs = fs
    .readdirSync(root)
    .filter((d) => d.startsWith("chromium_headless_shell-"))
    .sort((a, b) => Number(b.split("-")[1]) - Number(a.split("-")[1]));
  for (const dir of dirs) {
    for (const sub of fs.readdirSync(path.join(root, dir))) {
      const bin = path.join(root, dir, sub, "chrome-headless-shell");
      if (fs.existsSync(bin)) return bin;
    }
  }
  return null;
}

(async () => {
  const opt = args(process.argv);
  const { chromium } = require(
    require.resolve("playwright-core", { paths: [process.cwd()] }),
  );
  const executablePath = headlessShell() ?? undefined;
  const browser = await chromium.launch({ headless: true, executablePath });
  try {
    const context = await browser.newContext({
      viewport: { width: Number(opt.width), height: Number(opt.height) },
    });
    if (opt.cookie) {
      const at = opt.cookie.indexOf("=");
      const name = opt.cookie.slice(0, at);
      let value = opt.cookie.slice(at + 1);
      if (value.startsWith("@")) value = fs.readFileSync(value.slice(1), "utf8").trim();
      await context.addCookies([{ name, value, url: new URL(opt.url).origin }]);
    }
    const page = await context.newPage();
    await page.goto(opt.url, { waitUntil: "networkidle", timeout: opt.timeout });
    if (opt.clickTab) await page.getByRole("tab", { name: opt.clickTab }).click();
    let target = null;
    if (opt.text) {
      target = page.getByText(opt.text).first();
      await target.waitFor({ timeout: opt.timeout });
      await target.scrollIntoViewIfNeeded();
    }
    await page.waitForTimeout(500);
    fs.mkdirSync(path.dirname(opt.out), { recursive: true });
    await page.screenshot({ path: opt.out });
    console.log(`saved ${opt.out}`);
    if (opt.crop && target) {
      // The nearest card-like ancestor of the text.
      const card = target.locator(
        "xpath=ancestor::*[self::article or self::li or self::tr or contains(@class,'card') or contains(@class,'Card') or @data-slot='card'][1]",
      );
      if (await card.count()) {
        const crop = opt.out.replace(/\.png$/, "-crop.png");
        await card.first().screenshot({ path: crop });
        console.log(`saved ${crop}`);
      } else {
        console.log("no card found around the text; no crop");
      }
    }
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
