---
name: hermes-reset
description: Reset Hermes to a pre-CitizenAI state. Clear the transient conversation state and remove every CitizenAI artifact, but keep the Hermes install, Hermes authentication, other skills, and the CitizenAI browser profile.
user-invocable: true
---

# Hermes Reset

Use this skill when the owner asks to reset Hermes memory, sessions, or history, or to start fresh.
The reset puts Hermes back to the state before CitizenAI setup, so the next setup is a first-time setup.

The argument is the SSH target of the Hermes host, for example `ssh user@hermes-host`.
Run each script on that host with `ssh <target> 'bash -s' <<'EOF' ... EOF`.

## Safety rules

- Keep the Hermes install, `~/.hermes/auth.json`, and the provider configuration.
- Keep every line of `~/.hermes/.env`, `~/.hermes/config.yaml`, and `~/.hermes/SOUL.md` that is not CitizenAI text.
- Keep `~/.citizen-ai/browser/`, which holds the cookies and the persistent browser profiles.
  CAUTION: `~/.citizen-ai` (with a dash) is not `~/.citizenai` (no dash). Step 3 removes only `~/.citizenai`.
- Keep the skills that CitizenAI does not ship.
  Some of these skills, such as `social-media/*` and `productivity/browser-checkout-handoff`, mention CitizenAI.
  Do not remove them.
- Do not touch the files of another user, such as `/root/.hermes`.
- Do not run pairing, reinstall Hermes, or install CitizenAI.
- Do not write backup copies. Git and the owner's own backups are the safety net.
- Do not show credentials, tokens, cookies, session contents, or private browser data.

## Step 1: Inventory

Before you remove anything, list the CitizenAI artifacts:

```bash
ls -a ~/.hermes ~/.local/bin | grep -i citizen
find ~/.hermes/skills ~/.hermes/plugins -maxdepth 2 -iname '*citizen*'
find ~/.agents/skills ~/.claude/skills -maxdepth 1 -iname '*citizen*' 2>/dev/null
ls -d ~/.citizenai 2>/dev/null
grep -n -i citizen ~/.hermes/SOUL.md ~/.hermes/config.yaml
grep -i citizen ~/.hermes/.env | cut -d= -f1
systemctl --user list-units --all --no-legend '*citizen*'
```

If the inventory shows a CitizenAI artifact that Step 3 does not remove, add it to Step 3 before you continue.

## Step 2: Clear the transient state

```bash
set -e
systemctl --user stop citizen-ai-browser-session-worker-hermes.service 2>/dev/null || true

rm -rf \
  ~/.hermes/memories/* \
  ~/.hermes/sessions/* \
  ~/.hermes/terminal-sessions/* \
  ~/.hermes/pending_messages/* \
  ~/.hermes/cache/* \
  ~/.hermes/audio_cache/* \
  ~/.hermes/image_cache/* \
  ~/.hermes/images/* \
  ~/.hermes/pastes/* \
  ~/.hermes/logs/* \
  ~/.hermes/cron/output/*

rm -f \
  ~/.hermes/.hermes_history \
  ~/.hermes/state.db \
  ~/.hermes/state.db-shm \
  ~/.hermes/state.db-wal \
  ~/.hermes/gateway_state.json \
  ~/.hermes/processes.json
```

## Step 3: Remove the CitizenAI artifacts

CAUTION: This step removes the CitizenAI pairing, `connection.json`, and `install.json`.
The owner must approve a new pairing link.

```bash
set -e
H=~/.hermes

# The browser-session worker service.
systemctl --user disable --now citizen-ai-browser-session-worker-hermes.service 2>/dev/null || true
rm -f ~/.config/systemd/user/citizen-ai-browser-session-worker-hermes.service
systemctl --user daemon-reload
systemctl --user reset-failed 2>/dev/null || true

# The skills, the plugin, the pairing state, the launcher, the worker files, and the logs.
# `npx skills add --global` keeps the skill in ~/.agents/skills and links it into each runtime.
# Remove the copy, not only the links: an old copy asks the next setup for a retired setup code.
rm -rf \
  ~/.agents/skills/citizen-ai-accounts \
  ~/.claude/skills/citizen-ai-accounts \
  ~/.citizenai \
  $H/skills/citizen-ai-accounts \
  $H/skills/productivity/citizen-ai-virtual-helper \
  $H/plugins/citizen-ai \
  $H/citizen-ai \
  $H/citizenai \
  $H/citizen-agent* \
  $H/citizen-ai-* \
  $H/citizen-direct-vps-smoke.log \
  $H/config.yaml.before-citizenai-toolset-fix.* \
  ~/.local/bin/citizen-agent \
  ~/.local/bin/citizen-agent.bak.*

# The managed block in SOUL.md.
sed -i '/<!-- BEGIN CITIZENAI MANAGED -->/,/<!-- END CITIZENAI MANAGED -->/d' $H/SOUL.md

# The CitizenAI keys in .env.
sed -i -e '/^CITIZEN_/d' -e '/^MCP_CITIZEN_AI/d' -e '/MCP_CITIZEN_AI_API_KEY/d' $H/.env

# The skill entry in the lock file of the `skills` command.
python3 - <<'PY'
import json, os
p = os.path.expanduser("~/.agents/.skill-lock.json")
if os.path.exists(p):
    lock = json.load(open(p))
    if lock.get("skills", {}).pop("citizen-ai-accounts", None) is not None:
        json.dump(lock, open(p, "w"), indent=2)
PY

# The plugin entries in config.yaml.
python3 - <<'PY'
import os
p = os.path.expanduser("~/.hermes/config.yaml")
s = open(p).read()
s = s.replace("  enabled:\n    - citizen-ai\n  disabled:", "  enabled: []\n  disabled:")
s = s.replace("  entries:\n    citizen-ai:\n      allow_tool_override: false\n", "  entries: {}\n")
open(p, "w").write(s)
PY
```

If `config.yaml` has other plugins or a `citizen-ai` MCP server entry, the string replacements do not match.
In that case, edit the YAML with `yaml.safe_load` and `yaml.safe_dump`, and remove only the `citizen-ai` keys.

## Verification

Confirm that the transient state is gone:

```bash
test ! -e ~/.hermes/.hermes_history
test ! -e ~/.hermes/state.db
test -z "$(find ~/.hermes/sessions ~/.hermes/memories ~/.hermes/terminal-sessions ~/.hermes/pending_messages -type f -print -quit 2>/dev/null)"
```

Confirm that no CitizenAI artifact remains and that `config.yaml` is valid YAML:

```bash
! grep -qi citizen ~/.hermes/SOUL.md ~/.hermes/config.yaml ~/.hermes/.env
! ls -a ~/.hermes ~/.local/bin | grep -qi citizen
test -z "$(find ~/.hermes/skills ~/.hermes/plugins -maxdepth 2 -iname '*citizen*')"
test -z "$(find ~/.agents/skills ~/.claude/skills -maxdepth 1 -iname '*citizen*' 2>/dev/null)"
test ! -e ~/.citizenai
! grep -q citizen-ai-accounts ~/.agents/.skill-lock.json 2>/dev/null
test -z "$(systemctl --user list-units --all --no-legend '*citizen*')"
! pgrep -u "$USER" -f citizen
python3 -c 'import yaml,os; yaml.safe_load(open(os.path.expanduser("~/.hermes/config.yaml")))'
```

Confirm that the protected state remains:

```bash
test -s ~/.hermes/auth.json
test -d ~/.citizen-ai/browser
test -d ~/.hermes/skills
```

After the reset, exit any Hermes process that runs and start a new one:

```bash
exit
hermes
```

Tell the owner that Hermes was reset and that CitizenAI was removed.
Tell the owner that the next CitizenAI setup needs a new approval link.
