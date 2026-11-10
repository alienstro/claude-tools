# Report template

Copy this into `$W/report.md`. Use the full path of each screenshot. Keep each sentence short.

```markdown
# QA with user stories: #<n> <issue title>

Branch `<branch>` at `<short sha>`, on <date>. Stack: <each part, its port, its source folder>.

| # | Story | Screens | Tool | Result |
|---|---|---|---|---|
| S1 | As a <who>, I <action>, so that <value>. | Desktop app, macOS, light | CDP helper | PASS |
| S2 | ... | Web browser, 390 px | Playwright | PASS |

## Screen list

| Screen | Story | Shot | Tool |
|---|---|---|---|
| <surface, platform, way in, state, role, theme or width> | S1 | `S1-<name>.png` | <tool> |
| ... | ... | ... | ... |

Not affected: <each axis that you skipped, and why>.

## S1. <short name>

**Story:** As a <who> in <surface>, I <action>, so that <value>.

**Steps**
1. <action>
2. <action>

**Expected:** <exact text or state>.

**Result:** PASS. <one sentence of what showed>.

![S1 <what the shot shows>](<full path>/ev/S1-<name>.png)

Tool: <tool>. <If a tool failed first: which tool, and why.>

<one shot for each screen of this story, each with its tool line>

**Text proof**
<the file, the request and the response, or the DOM state, in a code block>

## Restored

- <each change the stories made, and its value now>

## Notes

- <problems that no story covers, test-tool problems and their cause>
```

## A good story

- One member action and one result. "and" in the action means two stories.
- The expected result names the exact words on the screen, such as "Version 0.1.0", not "the version shows".
- The proof says where the red box goes: the row, the message, the switch.
- A hidden feature gets a control story on the surface that must not show it.
