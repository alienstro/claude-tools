---
name: qa-verification
description: Use after code changes when the user requests manual-style QA, exploratory checks, regression checks, or evidence from real user workflows. Triggers include "QA your changes", "test it like I would", "prove the fix", and "$qa-verification". Not for code review alone.
---

# QA Verification

## Purpose

Check changes through the actions a person performs, not only through code inspection or automated test results.
Combine checks of expected behavior with exploration of nearby failure paths.
Use the real interface and dependencies when the claim requires them.

## Scope And Safety

- Use this skill for UI changes and user workflows through a CLI, API, or native application.
- Do not force browser checks onto changes without a UI.
- Keep QA read-only with respect to source files unless the user also requests fixes.
- Do not create or modify test files unless the user explicitly requests tests.
- Use existing tests as additional evidence, not as a substitute for real workflow checks.
- Follow the project instructions and the installed interface documentation.
- Reuse existing services and browser sessions.
- Run checks sequentially with one agent and one test worker.
- Do not install tools or create another environment without an established need and permission.

**Caution:** A QA request does not authorize purchases, messages, account changes, production writes, or destructive actions.

Confirm authorization before any action with those effects.
Prefer a local environment with disposable data.
Use another environment only within the scope the user authorizes.
Preserve user changes, credentials, cookies, browser profiles, and existing processes.
Do not bypass authentication or security controls to obtain a pass.

## Procedure

Show the six procedure steps as a checklist before execution.
Update the checklist after each step with its result or blocker.
Keep the claim table visible as the contract for the checks.

### 1. Define The Claims

1. Read the applicable instructions and the requested behavior.
2. Inspect the relevant diff, including staged, unstaged, and relevant untracked files.
3. Identify the comparison base without assuming its branch name.
4. Map each changed behavior to a user action and an observable result.
5. Add checks for nearby behavior that must remain unchanged.
6. Record each check before execution.

Use this table:

| Claim | Action | Expected Result | Actual Result | Status | Evidence |
| --- | --- | --- | --- | --- | --- |

Use `NOT RUN` until a check starts.
Select checks by risk and relevance rather than applying every possible check.
State the planned scope and important exclusions.

### 2. Confirm The Real Environment

1. Identify the application version, environment, interface, data scope, and required dependencies.
2. Confirm that the application actually runs the changed code.
3. Attach to the existing session through the installed interface.
4. Inspect the current page or interface state before actions.
5. Confirm authentication through observable state.
6. Record unavailable dependencies as blockers for the affected checks.

For managed browsers, follow the installed adapter and the project's route-selection rules.
Do not offer a live handoff URL before inspection proves an owner-only step is necessary.
Continue automation when the authenticated session permits it.
Report an adapter failure instead of guessing the session state.

Do not silently replace real services with mocks.
Label any authorized mock check as isolated UI evidence.
Keep the real integration claim `BLOCKED` until real evidence supports it.

### 3. Perform The User Workflow

1. Start from the normal entry point.
2. Perform the complete affected workflow through the user interface.
3. Check each intermediate result and the final result.
4. Reload or reopen the interface when the feature stores state.
5. Verify the stored result through an authoritative read when the claim requires it.
6. Repeat a safe action when repeat behavior matters.
7. Check the selected existing behavior for regressions.

Prefer DOM state and semantic actions when the interface exposes them.
Prefer Playwright for browser checks when the installed interface and project rules permit it.
Use the permitted browser adapter when Playwright cannot control the required session.
Use DOM state for actions and assertions; capture screenshots separately as visible evidence.
Do not create test files merely to use Playwright.
Use direct browser actions or existing tests unless the user requests new tests.
Do not replace a UI workflow with direct API calls.
Use API or state reads to support the UI result, not to bypass it.
For CLI-only changes, use the real command interface and record its output and exit status.

### 4. Explore Relevant Failure Paths

Choose checks that fit the affected feature:

| Risk | Example Check |
| --- | --- |
| Input validation | Empty values, invalid values, limits, and visible error messages |
| Navigation | Back, forward, direct entry, reload, and cancellation |
| State | Empty data, pending operations, repeated actions, and stale views |
| Recovery | Safe retry after an observed failure |
| Permissions | Authorized roles and visible access restrictions |
| Layout | Relevant narrow and wide views, overflow, and obscured controls |
| Keyboard access | Focus order, labels, activation, and modal escape |
| Integration | Request failures, stored results, and downstream effects |

Inspect available console and network errors during browser checks.
Separate existing errors from errors that the change demonstrably causes.
Label uncertain attribution explicitly.
Do not claim a complete accessibility, security, or compatibility audit from these focused checks.

**Caution:** Fault simulation can interrupt shared services or affect other users.

Simulate failures only in an authorized, isolated scope.
Mark unsafe or unavailable checks `NOT RUN` with a reason.

### 5. Record Issues And Evidence

1. Reproduce each issue with the smallest safe sequence.
2. Record the environment, prerequisites, inputs, steps, expected result, and actual result.
3. Assign severity from observed user impact.
4. Capture the required evidence described below.
5. Inspect each screenshot before using it as evidence.
6. Redact secrets and personal data from all evidence.
7. Store evidence outside tracked source files unless the user requests otherwise.

#### Visible Evidence Requirements

For each UI claim, capture a screenshot that clearly shows the observed result.
Capture the relevant intermediate states for workflows with multiple steps.
Capture a Playwright trace for each multi-step browser workflow when the interface supports traces.
Use a video or ordered screenshots when the interface cannot record a trace.
Record which actions correspond to each image, trace, or video.
Include error states and reproduction evidence for failed checks.

Inspect each image for the expected content, readable text, and unintended private data.
Do not present a blank page, spinner, or unrelated screen as proof of success.
Do not fabricate screenshots, annotations, or results to fill evidence gaps.
For motion or timing claims, require a trace or video that actually shows the behavior.
Static screenshots alone do not prove motion, timing, saved state, or downstream effects.

Save artifacts in a persistent local QA folder outside tracked source files.
Use an existing project artifact folder when it is suitable.
Otherwise, use `~/qa-evidence/<project>/<date-and-run-id>/`.
Save the report beside its artifacts.
Do not leave the only evidence in temporary storage that cleanup can erase.
Keep artifacts after cleanup unless the user requests their removal.

Show representative screenshots inline when the conversation interface supports images.
Provide clickable paths to every screenshot, trace, video, and report.
Do not provide only a directory path or a claim that evidence exists.
For a trace, explain how the user can open it with the installed trace viewer.

For CLI or API checks, save redacted command output, exit status, and relevant response data as viewable files.
Do not force a browser screenshot onto a check without a UI.
Link these files rather than relying only on the conversation transcript.

If screenshot capture fails, mark the UI evidence requirement `BLOCKED`.
Report the observed behavior separately, but do not mark the complete UI claim `PASS`.
If required evidence is missing, the overall result cannot be `PASS`.

Use these severity levels:

- `Critical`: Data loss, unauthorized access, or an essential workflow unavailable without a workaround.
- `Major`: A required result fails or a core action gives an incorrect result.
- `Minor`: A limited defect has a practical workaround.
- `Cosmetic`: A visual defect does not prevent task completion.

Do not infer successful persistence from a notification or screenshot alone.
Do not label a failure a regression without comparison evidence.
Compare the previous behavior only when the comparison preserves the current workspace and respects resource limits.
Never stash user changes or create another worktree merely to obtain comparison evidence.

If the user requests fixes, rerun the failed sequence after each fix.
Then rerun the dependent checks and the selected regression checks.
Report unrelated issues without expanding the repair scope.

### 6. Clean Up And Report

1. Remove only temporary data and resources that this QA run creates and can safely identify.
2. Stop only processes that this QA run starts.
3. Preserve evidence and report any incomplete cleanup.
4. Report failures before successful checks.

Use this report order:

- Overall result: `PASS`, `FAIL`, `PARTIAL`, or `BLOCKED`.
- Scope: application version, environment, interfaces, and changed behavior.
- Issues: severity, reproduction steps, expected result, actual result, and evidence.
- Check table: `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN` for each claim.
- Evidence locations and relevant command results.
- Exclusions, comparison limits, cleanup, and remaining risks.

Overall `FAIL` means at least one check demonstrates incorrect behavior.
Overall `BLOCKED` means prerequisites prevent every required check.
Overall `PARTIAL` means no check fails, but some required checks lack evidence.
Overall `PASS` requires evidence for every required check within the declared scope.
Never equate an unavailable check with a pass.
State that QA supports only the checked scope, not an absence of all defects.
