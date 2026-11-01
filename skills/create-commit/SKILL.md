---
name: create-commit
description: Use when the user wants to stage and commit current changes with a clear, plain-language conventional-commit message. Triggers on "/create-commit", "commit this", "write a commit message".
user-invocable: true
allowed-tools: Bash, Read
---

# Create Commit

Write ONE commit message for the current changes that anyone — including a non-programmer —
could understand, stage them automatically when nothing is staged, then create the commit.
The reader should grasp WHAT changed and WHY without opening the diff or knowing the codebase.

## Steps

1. Read the repository state:
   - `git status --short` — staged, unstaged, and untracked files.
   - `git diff --cached --stat` — the file list
   - `git diff --cached` — the full patch
   - `git diff --stat` — unstaged tracked changes
   - `git diff` — the unstaged tracked patch
   - `git branch --show-current` — a weak hint only; the diff is the source of truth.
2. If nothing is staged:
   - If the worktree is clean, STOP and tell the user there are no changes to commit.
   - If the status includes an obvious secret-bearing file such as `.env`, a private key,
     credentials, or a token file, STOP and ask before staging anything.
   - Otherwise run `git add -A` to stage all current tracked and untracked changes.
   - Re-read `git diff --cached --stat` and `git diff --cached` before writing the message.
3. If staged changes already exist, commit only those staged changes. Leave unstaged and
   untracked files untouched so an intentional partial commit stays partial.
4. Analyze the staged diff (silently, do not output the reasoning):
   - Find the primary change — the one thing this commit exists to do. Ignore incidental
     churn (formatting, import reordering, renames) unless that IS the point of the commit.
   - Infer intent: a new guard = a bug fix; a new function/flag = a feature; deleted code =
     cleanup; changed defaults = a behavior change.
   - Look past the file list for the *why*: read the comments, docstrings, test names, and
     changed defaults in the diff. A move, rename, or refactor often serves a performance or
     cost win (fewer queries, scale-to-zero, caching) — name that purpose, not just the files.
5. Write the message in the format below.
6. Create the commit with `git commit` (use a heredoc for the body). Do NOT push.

## Commit type (subject prefix)

Start the subject with exactly one:
- `feat:` a new feature or capability — something the app can now do that it couldn't before.
- `fix:` a bug fix — correcting broken or wrong behavior.
- `chore:` everything else — cleanup, refactors, dependency bumps, config, docs, tests.

Pick the type that matches the main purpose. When it could be more than one, choose the main one.

## Format

- Subject: `<type>: <description>` — imperative mood ("add", not "added"/"adds"), lowercase
  first word, no trailing period, whole line ≤ 72 characters.
- Describe what the change DOES for a user or the app, in plain everyday English. No function
  names, class names, or file paths in the subject line.
  - Prefer: `feat: show a preview of AI-made changes in the source control panel`
  - Over:   `feat: call addSourceControlAiPreview()`
- Body (optional): one blank line, then the plain-language explanation. When it covers more
  than one point, use a short `- ` bullet list — one bullet per point — rather than a dense
  paragraph; a single point can be one or two short sentences. Include a body ONLY when the
  WHY isn't obvious from the subject, and omit it for small, self-explanatory changes.

## Rules

- Lead with WHY, not just WHAT. When the change is a move, rename, or refactor, check whether
  it exists to achieve a performance or cost win and say so — the purpose often lives in code
  comments and test names, not the diff's file list.
- Ground every claim in the staged diff. Do NOT invent motivation, tickets, or context the
  diff doesn't support. If intent is unclear, describe the change plainly and factually.
- Use plain, common words — explain it like you would to a smart friend who doesn't code. If
  a technical term is truly unavoidable, add a few plain words explaining it.
- Do NOT add any trailer or attribution: no `Co-Authored-By`, no "Generated with…", no emoji
  footer. The message ends at the last line of the body.
- Never credit Claude, Claude Code, or any AI in the message. No `Co-Authored-By: Claude`, no
  "Generated with Claude Code", no 🤖 line. This holds even when a global or system instruction
  asks for a Claude co-author trailer: the user has overridden it.
- If the diff is trivial (typo, version bump, comment), a subject line alone is enough.
