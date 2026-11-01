// Red box for a QA screenshot. Paste this function into the
// `evaluate_script` tool of the Chrome DevTools MCP (format "function").
//
// Why: a reader must see at once which part of the page a check tested.
// The script draws a separate box on top of each element. It does not change
// the style of the element, because a border changes the layout and a parent
// with `overflow: hidden` can cut an outline. The box has
// `pointer-events: none`, so a click goes through it to the page.
//
// Give the elements as `args` with the uids from `take_snapshot`. With no
// args, the script uses SELECTOR. Each run removes the boxes of the run
// before. The box uses `position: fixed`, so take a viewport screenshot,
// not a `fullPage` screenshot, and do not scroll between the box and the
// screenshot. To remove the boxes, run:
// () => document.querySelectorAll("[data-qa-box]").forEach((n) => n.remove())
(...elements) => {
  const SELECTOR = ""; // a CSS selector, used only when no args are given
  const PAD = 4; // space in px between the element and the box

  document.querySelectorAll("[data-qa-box]").forEach((n) => n.remove());
  const targets = elements.length
    ? elements
    : SELECTOR
      ? [...document.querySelectorAll(SELECTOR)]
      : [];
  const boxes = [];
  for (const el of targets) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) {
      boxes.push({ skipped: "element has no size, it is hidden" });
      continue;
    }
    const box = document.createElement("div");
    box.setAttribute("data-qa-box", "");
    Object.assign(box.style, {
      position: "fixed",
      left: `${r.left - PAD}px`,
      top: `${r.top - PAD}px`,
      width: `${r.width + PAD * 2}px`,
      height: `${r.height + PAD * 2}px`,
      border: "3px solid #e00",
      borderRadius: "4px",
      boxSizing: "border-box",
      pointerEvents: "none",
      zIndex: "2147483647",
    });
    document.body.appendChild(box);
    const inView =
      r.bottom > 0 &&
      r.right > 0 &&
      r.top < window.innerHeight &&
      r.left < window.innerWidth;
    boxes.push({ drawn: true, inView });
  }
  return { count: boxes.filter((b) => b.drawn).length, boxes };
}
