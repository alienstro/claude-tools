# Claude skills

These are my custom skills for [Claude Code](https://claude.com/claude-code). Each folder is one skill with a `SKILL.md` file.

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
| `do-screenshots` | Takes a headless Playwright screenshot of a UI change and reports it in a table. |
| `qa-verification` | Checks a change through the real user workflow and records the evidence. |
| `qa-issue` | Checks a fixed issue on a staging site in a real browser and blocks each write request. |
| `verify-workflows` | Proves that a feature works across real systems, not only mocks. |
| `handoff-summary` | Writes a handoff document so that a new session can continue the work. |
| `hermes-reset` | Resets a Hermes host to the state before CitizenAI setup, over SSH. |
| `writing-maintainable-code` | Applies DRY, SOLID, and reusability, maintainability, testability and scalability. |

## Install

Copy a skill folder into `~/.claude/skills/`:

```sh
git clone https://github.com/alienstro/claude-skills.git
cp -R claude-skills/create-commit ~/.claude/skills/
```

## Team values

`create-issue` and `issues-version` need the values of your team: the owner, the repository, the project board and its ids. Put these values in a `team.local.md` file in the skill folder. The skill reads this file first. When the file does not exist, the skill asks you for the values.

`do-screenshots` reads `references/<repo>.local.md` for the steps that start your app. `qa-issue` reads `references/<project>.local.md` for the site URLs, the write paths and the safe test data.

Git ignores each `*.local.md` file, so your private values stay on your machine.
