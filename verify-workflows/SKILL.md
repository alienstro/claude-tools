---
name: verify-workflows
description: Use when a user needs proof that a feature works across real systems, services, interfaces, environments, state, or side effects that mocks cannot prove.
---

# Verify External Workflows

## Overview

This skill proves real behavior across all boundaries in a workflow.
It applies to any project with integrations, dependencies, state, or external effects.

## Scope

Use this skill when a user needs proof that:

- The complete feature works in its real environment.
- The real interfaces and dependencies work together.
- Configuration, routing, authentication, and state have the intended values.
- A state change reaches every required system and persists correctly.
- The user sees the correct result after the operation completes.
- Retries, repeat calls, failures, and cleanup behave as required.

Do not use a mock as final proof when the user requests a real integration result.

## Workflow

1. Define an acceptance matrix before running the workflow.

   - List every component, service, interface, dependency, and state boundary.
   - Give each boundary one observable pass condition.
   - Record the input, expected output, and evidence for each condition.
   - Mark each action as read-only, reversible, or irreversible.
   - Record the exact data, identity, environment, and resource scope.

2. Prepare the real environment.

   - Read the repository instructions and the relevant tool instructions.
   - Use the supported interface for each boundary, such as a CLI, API, UI, SDK, or connector.
   - Confirm versions, configuration, network access, credentials, services, data, and resources.
   - Preserve existing state unless the test requires a scoped change.
   - Prepare cleanup before creating temporary resources.

   **Caution:** Never expose or inspect secrets when a safe supported check exists.
   Verify identity and access through visible results or authorized read-only operations.

3. Run the smallest real path.

   - Start with a harmless read-only operation at each boundary.
   - Run the smallest end-to-end case with real inputs and real dependencies.
   - Verify each state transition through authoritative output, logs, traces, or safe reads.
   - Verify persistence, user-visible output, repeat behavior, and cleanup.
   - Run relevant failure and recovery paths when they affect the requested result.

   **Caution:** Perform an irreversible action only after clear user authorization.
   Use the smallest permitted scope and make one real attempt.

4. Debug each failed acceptance row.

   - Capture the exact command, phase, timestamp, exit code, and error.
   - Classify the cause as code, configuration, dependency, environment, authentication, or external service.
   - Fix the smallest local cause when the agent controls it.
   - Use a reversible workaround when it preserves the behavior under test.
   - Rerun the same failed phase and then rerun dependent phases.
   - Remove temporary changes or record them as part of the result.

   Do not hide a failure with a stub, broad retry loop, disabled security control, or alternate product.

5. Stop only at a valid terminal state.

   - Continue until every acceptance row passes.
   - If an external condition blocks progress, report the exact blocker and required action.
   - Do not label a blocked row as passed because a local substitute succeeded.

## Result Report

Report the result in this order:

- Overall status: `PASS`, `PARTIAL`, or `BLOCKED`.
- Acceptance matrix with one status per row.
- Real evidence for each passed row.
- Blockers with exact errors and their classification.
- Fixes and workarounds with scope and reversibility.
- Created resources and identifiers without secrets.
- Residual risks, skipped actions, and the next required action.

Never report credentials, secrets, session contents, passwords, or unredacted private data.
