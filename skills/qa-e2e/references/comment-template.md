# Comment template

One comment per issue. Put the verdict first. Quote bot replies exactly. Give each failed row the exact step and the exact actual text.

```markdown
## QA result: PASS | FAIL | BLOCKED — staging `<build tag>`

**Fix:** #<PR> (<short sha>). **Tested:** <YYYY-MM-DD> on <surface: Telegram bot name / WhatsApp staging number / console page / API>.

**Coverage:** happy path <passed>/<ran> · edge cases <passed>/<ran> live, <n> not run · edge areas: <Data, Timing, Errors, ...>

### Happy path
| # | Kind | Persona | Screen | Step | Expected | Actual | Tool | Result |
|---|---|---|---|---|---|---|---|---|
| 1 | happy | new | <row of the screen list> | <what you did, with the time> | <expected, from the issue or the PR> | <exact reply or value> | <tool that took the shot> | ✅ |
| 2 | happy | power | ... | ... | ... | ... | ... | ✅ |
| 3 | acceptance | - | ... | ... | ... | ... | ... | ✅ |

### Edge cases
| # | Area | Persona | Screen | Step | Expected | Actual | Tool | Result |
|---|---|---|---|---|---|---|---|---|
| 4 | Errors | new | ... | <step, and the emulation that made the state> | ... | ... | ... | ❌ |
| 5 | Lifecycle | power | ... | ... | ... | ... | ... | ✅ |
| 6 | Access | - | ... | ... | ... | not run: <reason, and the emulation method that you tried> | - | ⏭️ |

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
- Each comment has at least one screenshot of the live result, on every surface, with no exception. Text evidence supports it, but it never replaces it.
- Add every proof that exists: a screenshot of each screen or page that shows the result, and the text proof. A fix with no page of its own gets a screenshot from any application that shows the result. See **Screen proof for every surface** in `surfaces.md`.
- Mask personal data: phone numbers, emails, other people's names. Never paste a secret, a token or an env value.
- The "Happy path" and "Edge cases" tables hold the live steps on the test environment. Neither table is empty. Number the rows across both tables.
- Fill the **Coverage** line from the two tables. It must meet the counts in section 6 of `test-cases.md`.
- The live tables are never empty. A PASS comment with only the "Code and regression tests" table is not allowed.
- Say what you did not run, and why.
