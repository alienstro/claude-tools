---
name: branch-out
description: Use when the user wants to start a new feat/<name> branch from the base branch, usually dev, and keep the current uncommitted changes. Triggers on "/branch-out", "branch out", "create a feat branch".
user-invocable: true
---

# Branch Out

Create a `feat/<name>` branch from the base branch. Keep the uncommitted changes.

## Steps

1. Read the state: `git branch --show-current` and `git status --short`.
2. Pick the base branch. Use the branch that the user names. If the user names none, use `dev`.
3. Run `git fetch origin <base>`.
4. Pick the `<name>`:
   - Use the name that the user gives.
   - If the user gives none, write a short name from the diff. Use lowercase words with hyphens.
   - Use no more than 5 words.
5. Count the commits that the current branch has and `origin/<base>` does not have:
   `git log --oneline origin/<base>..HEAD`.
   - If the count is more than 0, STOP. Tell the user which commits are at risk. Ask before you continue.
6. Create the branch from the remote base: `git switch -c feat/<name> --no-track origin/<base>`.
   - `--no-track` stops the branch from tracking the base branch, so a bare `git push` does not push to `<base>`.
7. Run `git status --short`. Confirm that the changes are still there.
8. Tell the user the branch name and the base commit.

## Rules

- Branch from `origin/<base>`, not from the current branch. The pull request then holds only the new change.
- If `git switch` fails because a changed file conflicts with the base, STOP. Tell the user. Do not stash and do not discard.
- Never use a bare `git stash`. Other worktrees share the stash.
- Do not commit and do not push. Use `/create-commit` and `/create-pr` for that.
- Do not add a branch name that already exists. Run `git branch --list feat/<name>` first.
