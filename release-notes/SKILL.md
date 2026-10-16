---
name: release-notes
description: Use when the user wants a draft of release notes for the next release, or for a release that is already tagged. Reads the previous release tags and notes, collects the PRs since the last tag, and writes notes in the same format as the earlier releases (Features, Bug Fixes, Reliability and Maintenance, with PR numbers), plus the release title and the next version number. Then offers a GitHub draft release. Use it when the user says "/release-notes", "draft the release notes", "write the changelog for 1.7.0", "what goes in the next release", "prepare the release", "notes for the release PR", or "what changed since the last release", even if they do not say "release notes".
user-invocable: true
allowed-tools: Bash, Read, Write
---

# Release notes

Write a draft of the release notes for one release. The notes go in two places: the body of
the release PR from `dev` to `main`, and the GitHub release. Both use the same text, so the
draft must be ready to paste.

The readers are owners, admins, partners and the team. They want to know what they can do
now and what works better. They do not want to know how the code changed.

## Steps

### 1. Find the range

- The start is the newest release tag. Run `gh release list --limit 5` to see it.
- The end is `origin/dev` for the next release. For a release that already has a tag, use
  the previous tag as the start and that tag as the end.
- If the user names a version or a range, use it.

### 2. Read the two newest release notes

Run `gh release view <tag> --json name,body -q '.name, .body'` for the two newest releases
before the release that you write. Copy their section names, their bullet form and their
title form. The newer of the two is the style reference. An older release can use an older
style, so do not copy it.

### 3. Collect the changes

Run the script from the repository root:

```
python3 <skill-dir>/scripts/collect_changes.py [--from <tag>] [--to <ref>]
```

The script calls `git` and `gh` directly. Do not collect the commits with a plain `git log`
in the shell, because a shell hook (such as `rtk`) can cut the long commit subjects.

The script prints each PR in the range with its type, base branch, closed issues and body.
It also prints the direct pushes that have no PR, the new migration folders, and a suggested
version. It skips a `dev` → `main` release PR.

Read each `FLAG:` line:

- `merged into <branch>, part of a larger PR`: the PR went into a feature branch. Put its
  change into the bullet of the larger PR. Add its number to that bullet only when it adds
  something that a reader can see.
- `merged into main directly`: a hotfix. Check the previous notes. Leave it out when it is
  already there.
- `named in the <tag> notes`: the previous release already has it. Leave it out.

The output can be long. Save it to a file and read it in parts if it is more than about
800 lines.

### 4. Sort the changes into sections

Use the section names of the newest notes. For this repository, they are:

- `### Features`: a new thing that an owner, an admin, a partner or an agent can do.
  Most `feat:` PRs go here.
- `### Bug Fixes`: a thing that did not work before and works now. Most `fix:` PRs go here.
- `### Reliability and Maintenance`: CI, tests, performance, cost, dependency updates,
  logs, and the deploy notes. Most `chore:`, `ci:`, `perf:` and `refactor:` PRs go here.

The commit type is a hint, not a rule. A `fix:` PR that adds a new owner option is a feature.
A `feat:` PR that only changes a CI job is maintenance. Put each change where the reader
expects it.

Put a `### Removed` section only when the release removes something a user could see or use.

### 5. Write the bullets

Use this form for each bullet:

```
- **Short name**: One to three plain sentences about the effect. (#123)
```

Follow these rules, because the earlier notes follow them:

- Start the short name with a capital letter and write the rest in lower case, except
  for names such as PayMongo or Sentry. Use two to five words.
- Write what the reader can do now, or what works now. Do not describe the code, the
  classes, or the tests.
- Use short sentences, the active voice and the present tense.
- Join the PRs that change one thing into one bullet, and list all their numbers:
  `(#826, #828)`. A follow-up fix to a feature of the same release goes into the feature
  bullet, not into Bug Fixes, because the reader never saw the broken version.
- Leave out the changes that a reader never sees: a test-only PR, an internal refactor, a
  revert of a change in the same range, or a fix to a feature that is new in this release.
- Put the most important change first in each section.
- Keep the PR numbers as plain `(#123)`. GitHub makes them links.
- Do not write secret values, internal hostnames or private customer names. A name of an
  environment variable is OK.

Add these bullets to the end of `### Reliability and Maintenance` when they apply:

- **Database changes**: the number of new migrations and what each one adds, in plain words.
  Use the migration folder names from the script. (#PRs)
- **Deploy settings**: each new environment variable or setting that an operator must set
  before the deploy. Read the PR bodies to find them. Leave this bullet out when there is
  none.

### 6. Write the title and the version

- Use the suggested version of the script unless the user names one. The script adds one
  to the minor number when the range has a `feat:` PR, and to the patch number when it
  has only fixes.
- Write the title as `<version> - <Theme>, <Theme>, <Theme>`. Pick the two to four biggest
  user-visible changes. Write each theme in title case, as the newest titles do.

### 7. Save and show the draft

Save the draft as `release-notes-<version>.md` in the scratchpad folder of the session. When
there is no scratchpad folder, use `${TMPDIR:-/tmp}`. Do not save the draft in the
repository, because the notes live in the PR and in the release, not in git.

Put only the release body in the file. It starts with `## Release Notes`.

In the chat, show the title, the full body, and the file path. Under them, list:

- the PRs that you left out, each with a short reason, so the user can check the choice;
- the changes whose effect is not clear from the PR, as questions for the user.

### 8. Offer a GitHub draft release

Ask the user before you make the draft release. A draft release is visible to each person
with write access to the repository.

Before you ask, run `gh release view <version>`. If a release with that version exists, tell
the user and do not offer a new one.

When the user says yes, run:

```
gh release create <version> --draft --target main --title "<title>" --notes-file <file>
```

Caution: GitHub makes the tag only when someone publishes the draft. The tag then goes on
the newest commit of `main`. Tell the user to publish the draft only after the release PR
merges into `main`. If they publish it before, the tag goes on the wrong commit.

Give the user the URL from the command output.

## Example

Three bullets from the 1.6.0 notes:

```
### Features

- **Safe email replacement**: An agent can replace its email address after one short question to the owner. The old mailbox goes only when the new one works, and a failed change refunds the credits. (#781)

### Bug Fixes

- **Marketplace tool lists**: A click on each marketplace card that has tools opens its tool list again. Are.na and Cohere now have tools. (#792)

### Reliability and Maintenance

- **Database changes**: This release adds three migrations: the email replacement offer, the owner payment accounts, and the Herminie owner handle. (#781, #785, #788)
```
