# Claude tools

These are my custom tools for [Claude Code](https://claude.com/claude-code): skills and hooks.

```text
claude-tools/
├── skills/   One folder for each skill, with a SKILL.md file. Install into ~/.claude/skills/.
└── hooks/    Scripts that Claude Code runs on events. Install into ~/.claude/hooks/.
```

## Install

Clone the repository one time:

```sh
git clone https://github.com/alienstro/claude-tools.git
```

Copy one skill:

```sh
cp -R claude-tools/skills/create-commit ~/.claude/skills/
```

Copy all skills:

```sh
cp -R claude-tools/skills/. ~/.claude/skills/
```

Each hook also needs an entry in `~/.claude/settings.json`. See the hook section below.

## Skills

| Skill | What it does |
| --- | --- |
| `branch-out` | Starts a `feat/<name>` branch from the base branch and keeps the uncommitted changes. |
| `create-commit` | Stages the changes and writes a plain-language conventional commit. |
| `create-pr` | Opens a pull request with a short summary, a behaviour table and a size table. |
| `edit-pr` | Rewrites the title and the description of a pull request in the same format. |
| `create-issue` | Opens a GitHub issue in a team format and sets the type, the labels and the project fields. |
| `close-issue` | Links a PR to its issue, closes the issue after the merge, and sets the board status to "For Testing". |
| `issues-version` | Sets the release version on shipped issues and moves them out of the testing columns. |
| `create-release-notes` | Drafts the release notes for the next release from the PRs since the last tag. |
| `do-tests` | Runs only the checks for the changed code, or the full gate, with memory limits. |
| `do-ci` | Runs the CI workflow steps on a clean copy of the last commit, as the CI runner does. |
| `do-screenshots` | Takes a headless Playwright screenshot of a UI change and reports it in a table. |
| `qa-verification` | Checks a change through the real user workflow and records the evidence. |
| `qa-e2e` | Tests one issue or a board column end to end on a live environment and posts the results. |
| `qa-issue-ui` | Checks a fixed issue on a staging site in a real browser and blocks each write request. |
| `qa-issue-api` | Checks a backend fix on staging with real read-only requests and reports the proof. |
| `verify-workflows` | Proves that a feature works across real systems, not only mocks. |
| `handoff-summary` | Writes a handoff document so that a new session can continue the work. |
| `hermes-reset` | Resets a Hermes host to the state before CitizenAI setup, over SSH. |
| `writing-maintainable-code` | Applies DRY, SOLID, and reusability, maintainability, testability and scalability. |

### Team values

`create-issue`, `issues-version` and `qa-e2e` need the values of your team: the owner, the repository, the project board and its ids. Put these values in a `team.local.md` file in the skill folder. The skill reads this file first. When the file does not exist, the skill asks you for the values.

`do-screenshots` reads `references/<repo>.local.md` for the steps that start your app. `qa-issue-ui` and `qa-issue-api` read `references/<project>.local.md` for the site URLs, the write paths and the safe test data.

Git ignores each `*.local.md` file, so your private values stay on your machine.

## Hooks

| Hook | Event | What it does |
| --- | --- | --- |
| `context-guard.mjs` | `UserPromptSubmit` | Hands off to a fresh Claude tab in Orca when the context is more than 300k tokens. |

### `context-guard.mjs`: auto handoff at a context limit

A long session costs more on each turn, and each `/compact` loses detail. This hook starts a fresh session instead. When the context is more than 300k tokens, the hook blocks your prompt and starts a new Claude in the same Orca worktree. The new agent gets the Orca "Focused handoff" brief, with your blocked prompt as its task.

1. The hook reads the context size of the last turn from the transcript. A `/compact` resets it to 0.
2. Below the limit, or for a prompt that starts with `/`, the prompt passes.
3. Above the limit, the hook runs `orca agent launch --agent claude --focus` with the brief: the transcript path, the last prompt and answer, and your blocked prompt.
4. The hook switches Orca to the new tab with `orca terminal switch`.
5. The old tab shows "Handed off to a new Claude (`<handle>`)". A marker file in `~/.claude/hooks/state/` stops a second launch.
6. Outside an Orca terminal, or when the launch fails, the hook blocks and asks you to hand off by hand.
7. An error in the hook itself lets the prompt pass, so the hook never locks a session.

Install:

```sh
mkdir -p ~/.claude/hooks
cp claude-tools/hooks/context-guard.mjs ~/.claude/hooks/
```

Then add this entry to `hooks.UserPromptSubmit` in `~/.claude/settings.json`:

```json
{ "hooks": [{ "type": "command", "command": "node \"$HOME/.claude/hooks/context-guard.mjs\"", "timeout": 30 }] }
```

Restart Claude Code, or open `/hooks`, to load the hook.

Set `CONTEXT_GUARD_LIMIT` to change the limit, for example `CONTEXT_GUARD_LIMIT=200000`. A new session starts at about 70k tokens (system prompt, tools and skills), so a 300k limit leaves about 230k for work.

Close the old tab after each handoff.
