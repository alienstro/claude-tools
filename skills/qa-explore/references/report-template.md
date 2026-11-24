# Report template

Copy this into `$W/report.md`. Use the full path of each screenshot. Keep each sentence short.

```markdown
# Exploratory QA: <scope>

Target <target name and URL>, code <branch and short sha, or "deployed staging">, on <date and time>. Tools: <each tool>. <If no debug port: "No console, network or LCP data.">

## Drafts

| # | Severity | Type | Repo | Title | Page | Action |
|---|---|---|---|---|---|---|
| F1 | S2 | UX | <owner/repo> | <title> | <page> | New issue |
| F2 | S3 | Bug | <owner/repo> | <title> | <page> | Comment on #123 |

## Page map

| Page or state | New member | Power user | Findings |
|---|---|---|---|
| <page, state, width> | Done | Done | F1, F3 |
| <page> | Not reached: <why> | — | — |

## F1. <title>

**Severity and type:** S2, UX. **Repo:** <owner/repo>. **Runs:** <n of m, for an agent's answer>.
**Page:** <page and state>. **Who:** new member | power user.

**Steps**
1. <action>
2. <action>

**Expected:** <what a member expects>.
**Actual:** <exact text or state that showed>.
**Why it matters:** <one sentence>.
**Suggested fix:** <one sentence>.

![F1 <what the shot shows>](<full path>/ev/F1-<name>.png)

Tool: <tool>.

**Text proof**
<the console error, the request and the response, the timing numbers or the DOM state, in a code block>

## Speed

| Page or action | Measure | Value (middle of 3) | Target |
|---|---|---|---|
| <page> | LCP | <ms> | ≤ 2500 ms |

## Cleaned up

- <each thing that you made, and proof that it is gone>
- <each thing that the app cannot remove, such as test messages>
- Credits: <before> → <after>

## Notes

- <problems that you saw only in the code, test-tool problems, pages that you could not reach>
```

## A good draft

- One problem and one fix. "and" in the title means two drafts.
- The title names the problem from the member's side, such as "Save shows 'Saved' before the request ends", not "Fix save button".
- The actual result quotes the exact words on the screen.
- The fix is a suggestion. The team decides.
