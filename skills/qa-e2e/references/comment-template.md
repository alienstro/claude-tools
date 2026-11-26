# Comment template

One comment per issue. Put the verdict first. Quote bot replies exactly. Give each failed row the exact step and the exact actual text.

```markdown
## QA result: PASS | FAIL | BLOCKED | NOT DEPLOYED — <test environment> `<build tag>`

**Fix:** #<PR> (<short sha>). **Tested:** <YYYY-MM-DD> on <each surface: the page, app, bot, API or job that you used>.

**Coverage:** happy path <passed>/<ran> · edge cases <passed>/<ran> live, <n> not run · edge areas: <areas that ran live>
**Not applicable:** <Area>: <reason>; <Area>: <reason>

### Happy path
| # | Kind | Persona | Screen | Step | Expected | Actual | Proof | Result |
|---|---|---|---|---|---|---|---|---|
| 1 | happy | new | <row of the screen list> | <what you did, with the time> | <expected, from the issue or the PR> | <exact reply or value> | <tool>: <n>-<name>.png | ✅ |
| 2 | happy | power | ... | ... | ... | ... | ... | ✅ |
| 3 | acceptance | - | ... | ... | ... | ... | ... | ✅ |

### Edge cases
| # | Area | Persona | Screen | Step | Expected | Actual | Proof | Result |
|---|---|---|---|---|---|---|---|---|
| 4 | Errors | new | ... | <step, and the emulation that made the state> | ... | ... | ... | ❌ |
| 5 | Lifecycle | power | ... | ... | ... | ... | ... | ✅ |
| 6 | Timing | power | ... | ... | ... | <reply on the first run> / <reply on the second run> | ... | ⚠️ |
| 7 | Access | - | ... | ... | ... | not run: <reason>; tried: <emulation method, or none possible> | - | ⏭️ |

<For a FAIL: one line "Repro:" with the shortest steps.>
<For a BLOCKED: one line "Open step:" with who must do what.>
<If you changed a setting of the test environment: one line "Restored: <setting> to <old value> at <time>".>

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
- Each comment has at least one screenshot of the live result. Text evidence supports it, but it never replaces it.
- The Proof cell of each live row names its screenshot file. When the screen of a row shows nothing new (an empty list, a total with no matching record), write `<tool>: text: <reason>` and put the text proof under "Evidence".
- Result marks: ✅ pass, ❌ fail, ⚠️ flaky (failed one time, then passed), ⏭️ not run.
- Add every proof that exists: a screenshot of each screen or page that shows the result, and the text proof. A fix with no page of its own gets a screenshot from any application that shows the result. See **Screen proof for every surface** in `surfaces.md`.
- Mask personal data: phone numbers, emails, other people's names. Never paste a secret, a token or an env value.
- The "Happy path" and "Edge cases" tables hold the live steps on the test environment. Neither table is empty. Number the rows across both tables.
- Each area of `test-cases.md` section 2 has an edge row or an entry in **Not applicable**. Use the exact area names.
- Run `scripts/check_coverage.py <comment.md>`. Copy the Coverage line that it prints. Fix each gap that it names before you post.
- The live tables are never empty. A PASS comment with only the "Code and regression tests" table is not allowed.
- Say what you did not run, and why.
