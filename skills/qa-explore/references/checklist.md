# What to look for

Look at each page and each action with this list. Each finding gets one type and one severity.

## Types

| Type | Look for |
|---|---|
| **Bug** | A wrong result, a crash, a blank page, a console error, a failed request, data that does not save, a state that a reload loses, a button that does nothing |
| **Misleading** | Words or a state that say something false: "Saved" before the save ends, a count that is wrong, a success message after an error, a disabled look on a control that works |
| **Unclear** | Words that a new member cannot understand: internal names, a term with no help, an icon with no label or tooltip, an error with no next step, two names for one thing |
| **Flow** | Too many steps, a dead end, no way back, no undo, a step that asks for data that the app already has, a lost input after an error, the next action is not clear |
| **UX** | No feedback after a click, no confirmation before a destructive action, a surprise (focus moves, a page scrolls, a dialog closes), a missing empty state, a missing keyboard path |
| **UI** | Wrong spacing or alignment, cut text, an overlap, a wrong font or colour against the design, a jump in the layout, a broken narrow window, two looks for one control |
| **Speed** | A slow page or action (see **Speed**), a spinner with no end, a layout that jumps while it loads, the same request two times |
| **Accessibility** | Low contrast, no visible focus, a control that the keyboard cannot reach, an image or icon button with no name, a click target smaller than 24 px |

## Severity

| Severity | Meaning |
|---|---|
| **S1 Blocker** | The member cannot finish the main task, or loses data, or sees data of another member |
| **S2 Major** | A wrong or misleading result, or a task that needs a hard workaround |
| **S3 Minor** | The task works, but it is confusing, slow or ugly, and the workaround is easy |
| **S4 Polish** | A suggestion that makes a working page better |

## Speed

Measure each page load and each main action. Use these targets (Google Core Web Vitals and the Nielsen response limits):

| Measure | Good | Finding |
|---|---|---|
| Largest Contentful Paint (LCP) | ≤ 2.5 s | > 2.5 s |
| Interaction to Next Paint (INP), click to the next frame | ≤ 200 ms | > 200 ms |
| Cumulative Layout Shift (CLS) | ≤ 0.1 | > 0.1 |
| Click to visible feedback | ≤ 100 ms | No feedback after 1 s |
| Click to result | ≤ 1 s, or a progress sign | > 10 s with no progress sign |

Read the numbers from the page, through the debug port (`$S/cdp.mjs eval`) or the DevTools MCP:

```js
// Page load: the navigation entry and the LCP.
JSON.stringify({
  nav: performance.getEntriesByType('navigation').map(e => ({ ttfb: e.responseStart, dcl: e.domContentLoadedEventEnd, load: e.loadEventEnd })),
  lcp: performance.getEntriesByType('largest-contentful-paint').at(-1)?.startTime,
  slow: performance.getEntriesByType('resource').filter(r => r.duration > 1000).map(r => ({ url: r.name, ms: Math.round(r.duration) })),
})
```

For an action, record `performance.now()` before the click, wait for the result in the DOM, and record it again. Measure each slow action three times and give the middle value. A shared staging server can be slow for a short time, so give the time of day in the report.

With no debug port (computer use only), time an action with `$C wait-for '<text>'`: it prints the seconds from the call until the text shows. Its step is the poll time, about 0.5–4 s, so use it only for waits longer than 2 s, and say so in the report. You get no LCP, INP, CLS, console or network data.

## Words

- Read each label, button, title, placeholder, tooltip, empty state and error.
- Each word must be true at the time it shows, and it must use the terms of the project glossary (for example, `GLOSSARY.md`).
- An error says what happened and what to do next.
- One action has one name on each page.

## States to force

Empty, loading, one item, many items (scroll), a long name, an error from the server, no network (DevTools offline), a reload in the middle of a task, the back button, a narrow window (390 px for a web page), a second window with the same page.

**One value, many places.** Change a value in one place, such as a rename or a new message. Then check each other place that shows it: the side bar, the header, a placeholder, an empty state, a preview, a second window. Each place must show the new value without a reload.

**After a delay.** For a reminder, a job or another timed result, wait until it is due. Then check each place where the result can land: the same chat, another chat, a panel, a list, the OS notice.

## Chat and agent apps

- **Optimistic send.** Each send path shows the member's message in 100 ms or less: a plain message, a tagged message, a reply, a message with a file.
- **Scroll on send.** After the member sends from a scrolled-up spot, the chat goes to the end.
- **Double submit.** A double Enter or a double click sends one message.
- **Waiting sign.** While an agent works, a sign shows who works. It ends when the answer lands.
- **Routing.** In a chat with many agents, a message goes to the agent that the member means, with and without a tag.
- **Order.** The answers show in an order that the member can follow.
- **Repeat.** An agent's answer changes between runs: send the same words 2 or 3 times (see **Rules** in `SKILL.md`).

## Accessibility tree

Read the accessibility tree of each page one time (the debug port, the DevTools MCP, or `$C act <name> get-app-state`):

- Each visible label has the same accessible name. A composer with the placeholder "Message GROUP" is not named "Message Acme".
- Each menu, popover and list that the mouse opens is in the tree, with a role (`menu`, `listbox`, `option`).
- Each icon button has a name.
- Each action of a right-click menu has a second path: a button or a key.

