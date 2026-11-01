---
name: handoff-summary
description: Create a detailed, paste-ready handoff document that gives a new session enough implementation context to continue without rediscovery. Triggers on "/handoff-summary", "write a handoff", "session summary", "continuation prompt", "context transfer", or a request for a descriptive record of completed work, implementation details, decisions, changed files, verification, repository state, external actions, blockers, and remaining tasks.
---

# Handoff Summary

Produce a self-contained, descriptive handoff that lets a fresh session continue without rereading the transcript or re-investigating work that is already understood. Preserve the reasoning-relevant context behind the implementation, not merely a short list of outcomes.

## Gather Evidence

1. Identify the current user goal, intended outcome, acceptance criteria, and latest scope. Treat later user corrections as authoritative.
2. Review the conversation, relevant specs, plans, and issue context for completed work, explicitly deferred work, blockers, and decisions that constrain the next session.
3. Describe how the implementation works. Capture important data flow, state transitions, validation rules, public interfaces, schemas, routes, commands, failure handling, compatibility behavior, and deployment sequencing when they matter.
4. If working in a repository, use read-only inspection such as `git status --short`, branch and commit checks, and focused diffs to confirm the current state. Distinguish committed, staged, unstaged, and untracked changes, including changes in separate worktrees or repositories. Do not modify files, run migrations, or rerun tests solely to create the handoff.
5. Record verification commands and their observed results, including test counts when known. Identify checks that were not run, could not run, or need repeating after later edits. Never imply that a check passed without successful evidence.
6. Record external state changes such as commits, pushes, pull requests, package publications, deployments, applied migrations, browser validation, modified databases, or third-party actions. Include identifiers and links when available.
7. Preserve important rationale: explain why non-obvious choices were made, which alternatives were rejected, and what must remain immutable or backward compatible.
8. Exclude secrets, credentials, private chain-of-thought, raw tool transcripts, redundant chronology, and obsolete failed attempts that do not affect continuation.

## Write the Handoff

Use only the sections that carry useful information:

```markdown
## Goal

<Current objective, intended outcome, and relevant acceptance criteria.>

## Current State

- <Repository, worktree, branch, commit, dirty/staged state, active PR, deployment, or package state.>

## Completed

- <Completed user-visible behavior, internal behavior, and important decisions.>

## Implementation Details

- **<Area or flow>** — <How it works, including important symbols, data flow, validation, state transitions, compatibility behavior, and failure cases.>

## Changed Files

- `<path>` — <what changed and why>

## Decisions

- <Decision and rationale, especially compatibility, security, rollout, or scope choices.>

## Verification

- `<command>` — <exact observed result, including pass/fail counts or limitations.>

## External State

- <Commits, pushes, PRs, publishes, deployments, migrations, browser checks, or other actions outside the working tree.>

## Remaining

1. <Next concrete action, ordered by dependency and priority.>

## Continuation Notes

- <Constraints, assumptions, user-owned changes, known unrelated failures, rollout dependencies, or cautions.>
```

## Quality Rules

- Prefer completeness over brevity. Aim for roughly 700–1,200 words for substantial work; use less for genuinely small tasks and more when multiple worktrees, releases, migrations, or deployment steps are involved.
- Lead with outcomes and current state, not a chronological diary, but include brief chronology when ordering explains dependencies or why the repository is in its present state.
- Explain behavior, not just filenames. A new session should understand what each major component does and how the pieces interact without reopening every changed file.
- Name concrete symbols, routes, tools, schema models, versions, hashes, error cases, and identifiers when they are important for safe continuation.
- Group changed files by concern when many files changed. List every high-value file individually, but summarize repetitive test or metadata files without dumping the entire diff.
- Use repository-relative paths and exact command names when available. Include absolute worktree paths only when distinguishing multiple local worktrees requires them.
- Separate completed, partially completed, and remaining work unambiguously. Do not present an implemented but uncommitted change as shipped or deployed.
- Preserve user-owned or unrelated worktree changes and warn the next session not to revert them.
- Distinguish verified facts from assumptions. Call out failures, skipped checks, stale results, and checks that must be repeated after subsequent edits.
- Record whether changes are committed, staged, pushed, merged, published, migrated, or deployed, including relevant commit hashes, PR numbers, branches, package versions, and links when known.
- Surface sequencing constraints prominently, such as deploying an API artifact before publishing a client that pins it.
- Avoid vague bullets such as “updated service” or “added tests.” State the behavior added, the condition it handles, and why it matters.
- End with a concrete sentence beginning with `Next action:` that tells the fresh session exactly what to do first.
- Output only the handoff summary; do not add instructions about copying it or commentary outside the summary.
