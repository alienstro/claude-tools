# Comment template

One comment per issue. Put the verdict first. Quote bot replies exactly. Give each failed row the exact step and the exact actual text.

```markdown
## QA result: PASS | FAIL | BLOCKED — staging `<build tag>`

**Fix:** #<PR> (<short sha>). **Tested:** <YYYY-MM-DD> on <surface: Telegram bot name / WhatsApp staging number / console page / API>.

| # | Step | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | <what you did, with the time> | <expected, from the issue or the PR> | <exact reply or value> | ✅ |
| 2 | ... | ... | ... | ❌ |

<For a FAIL: one line "Repro:" with the shortest steps.>
<For a BLOCKED: one line "Open step:" with who must do what.>

**Notes (not part of this fix, please triage):**
- <new problem, with evidence>

{{IMG:<issue>-<short-name>.png}}

### Code and regression tests
| # | Check | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | Fix at HEAD | present | `path/file.ts:123` | ✅ |
| 2 | `tests/<file>.test.ts` | all pass | tests=N pass=N fail=0 | ✅ |

<details><summary>Evidence</summary>

```
<exact commands and trimmed outputs: test summaries, curl status lines, read-only SQL counts, journal lines>
```
</details>
```

Rules:
- Text evidence (commands and outputs) is the proof for a backend fix. Screenshots are the proof for a screen.
- Add every proof that exists: a screenshot of each screen or page that shows the result, and the text proof. A backend fix whose result shows on a page (a console page, a settings row, a record list) gets a read-only screenshot of that region too. With no such page, write "No page shows this result" and say why.
- Mask personal data: phone numbers, emails, other people's names. Never paste a secret, a token or an env value.
- The first table holds the live steps on the test environment, and it is never empty. A PASS comment with only the "Code and regression tests" table is not allowed.
- Say what you did not run, and why.
