---
name: qa-issue-api
description: Use when the user wants a closed or fixed GitHub issue checked on staging, and the fix changes backend behavior that has no page to click, such as an API endpoint, an MCP tool, a webhook, a background job, a timer, a billing rule or a migration. Read the issue and its fix PR, confirm that staging runs the fix, plan the checks, send real read-only requests, read the state again after the run, and report a results table with the request and the response of each check as text proof. Use it when the user says "/qa-issue-api", "QA this backend fix", "test the API fix on staging", "check if issue 123 works on the staging API", "test this MCP tool on staging", or asks to QA an issue that has no UI, even if they do not say "API". For a fix that shows on a page, use `qa-issue-ui` instead.
---

# QA a backend issue on staging

Check that a backend fix works on a live staging server, and prove it with the real requests and responses, without a change to the data that other people use.

## Rules

- **Do not change shared data.** An HTTP write goes to the server at once, and no guard can stop it. Send only read requests, unless the user says "yes" to a write on a test record that the user owns.
- **Read the database only in a read-only transaction.** Start each SQL session with `BEGIN READ ONLY;`. Then the database refuses each write.
- **Do not send a message to a real person.** An email, an SMS, a chat message or an invite to a real address is a real write, even on staging.
- **Do not show a secret.** Keep each token in a shell variable, never in the command text. Replace each token, cookie, API key and one-time code with `<redacted>` in each saved file and in the report.
- **Test the real staging build.** Confirm that staging runs a commit that contains the fix before you test. A test of an old build gives a false fail.
- **Use raw output.** Run `curl` and `psql` through `rtk proxy`, because the rtk filter can change the output.
- **Keep the repository clean.** Save each request and response in the scratchpad, and run `git status --short` at the end.
- If this skill has a file for the project in `references/`, such as `references/<project>.local.md`, read it first. It names the URLs, the auth, the deploy check and the safe test data. Keep a `*.local.md` file out of a public repository.

## Steps

1. **Read the issue and the fix.**
   - Run `gh issue view <n> --repo <owner/repo> --json title,body,state,comments`.
   - Find the fix PR in the comments ("Fixed in #N") or with `gh pr list --search "<n>" --state merged`.
   - Read the PR body, the diff and the tests of the fix. The tests show the inputs and the expected outputs.
   - Write one short line for each item of the issue scope. Each line becomes one row of the results table.
2. **Confirm that staging runs the fix.**
   - Find the commit that staging runs, with the deploy check in the reference file.
   - Run `git merge-base --is-ancestor <fix sha> <staging sha>`. Exit code 0 means that staging has the fix.
   - If staging does not have the fix, stop and tell the user.
3. **Plan each check.** For each row, find:
   - The surface: an HTTP endpoint, an MCP tool, a webhook, a background job, or a database state.
   - The request to send, and the response that shows a pass. Include the input that caused the bug, because the fix must now give the new result.
   - The kind of action: read-only, a write on a test record that the user owns, or a write on shared data. Ask the user before each write.
   - A check that you cannot start, such as a timer that runs once a day, or a webhook that only a vendor sends. Find an indirect proof, such as a log line or a database row. If you find none, mark the check **Not tested** and say why.
4. **Get the auth.** Use the token source in the reference file, or ask the user. Put the token in a variable, for example `export QA_TOKEN=...`, and send `-H "Authorization: Bearer $QA_TOKEN"`.
5. **Read the state before the run.** Read each record that a check can touch, with a GET request or a read-only SQL query. Save the result as `00-before.txt`.
6. **Run each check.**
   - Send the request with `rtk proxy curl -sS -w '\nHTTP %{http_code} %{time_total}s\n'`.
   - For an MCP tool, send a JSON-RPC `tools/call` request to the MCP endpoint. Do not use an MCP tool that this session has, because it can point to a different environment.
   - Save each request and response as `<nn>-<check>.txt` in `<scratchpad>/qa-<issue>/`. Remove each secret from the file.
   - Compare the response with the expected result: the status code, the error code, the fields and the values. Do not compare only the status code.
7. **Check a background change** (a timer, a job, a retry) with a time limit. Read the state at fixed times, for example each 60 seconds for 10 minutes. Stop at the limit, and report the last state that you saw.
8. **Check the state after the run.** Read each record again. Compare it with `00-before.txt`. Report each change.
9. **Clean up.** Delete each test record that you made, and only with the user's "yes". Run `unset QA_TOKEN` and `git status --short`.
10. **Report in chat.** Use the format below.

## Report format

Write the report in the chat, not in a code block, so that the table renders. Keep each table cell short, because a long cell wraps and breaks the table when the user copies it.

```
| Check | Request | Expected | Actual | Result |
| --- | --- | --- | --- | --- |
| **<item>** | `POST /mcp` `tools/call x` | `INTEGRATION_NO_MATCH` | `INTEGRATION_NO_MATCH` | **Pass** |

**1. <check>.** <one sentence on what the response shows>

    <the request, with secrets redacted>
    <the important part of the response, not more than 15 lines>

**Not tested:** <each skipped check and the reason>

**Follow-ups:** <each gap that is not a fail of the issue>
```

- Put one row in the table for each item of the issue scope. Use **Pass**, **Fail** or **Not tested**.
- After the table, show the proof of each check in test order. Give the path of the full file in the scratchpad.
- Name the staging commit that you tested.
- Say that staging did not change, and name the proof: the before and after state.
- Keep a gap that is not part of the issue apart from the results. Offer to open an issue for it. Do not open one without a "yes".

## Common problems

| Problem | Cause | Fix |
| --- | --- | --- |
| `401` on each request | The token is missing, expired, or for a different environment | Get a new staging token. Check that the URL is the staging URL |
| The response is the old behavior | Staging does not run the fix yet | Do step 2 again. Wait for the deploy, then test again |
| The output is short or changed | The rtk filter changed the output | Run the command through `rtk proxy` |
| A count or a sum differs from the local test | Staging has its own database with different data | Compare with the staging state before the run, not with local data |
| A timestamp is 8 hours off | The database session uses a local time zone | Run `SET TIME ZONE 'UTC';` in the SQL session |
| A record changed during the run | A request wrote data, or a different user or job changed it | Stop. Tell the user what changed and when. Do not undo a final action, such as a delete, without the user |
