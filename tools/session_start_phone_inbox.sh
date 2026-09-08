#!/usr/bin/env bash
# SessionStart hook: fast-forward pull, then surface unprocessed phone-inbox notes.
# Wired up in .claude/settings.local.json (personal, not committed) so it runs on
# this computer only -- never in cloud/phone sessions. See HANDOFF.md.
set -u
export GIT_TERMINAL_PROMPT=0

REPO="/Users/georges.patton/Wavecrest"
INBOX="$REPO/memory/phone-inbox.md"

cd "$REPO" 2>/dev/null || exit 0
[ -f "$INBOX" ] || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# Safe pull: autostash local edits, fast-forward only (never creates merge conflicts).
PULL_NOTE=""
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
if ! git pull --ff-only --autostash --quiet origin "$BRANCH" >/dev/null 2>&1; then
  PULL_NOTE="Couldn't fast-forward from git -- run 'git pull' manually to sync the latest phone notes."
fi

# Extract the "## Unprocessed" section, minus the header, the placeholder, and blanks.
UNPROCESSED="$(awk '/^## Unprocessed/{f=1;next} /^## /{f=0} f' "$INBOX" \
  | grep -vE '^_\(' | grep -vE '^[[:space:]]*$')"

# Nothing to surface and no pull problem -> stay silent.
[ -z "$UNPROCESSED" ] && [ -z "$PULL_NOTE" ] && exit 0

MSG=""
if [ -n "$UNPROCESSED" ]; then
  MSG="📱 Unprocessed phone-inbox notes (captured on the go). Surface these to the user and offer to triage each into the right memory file, then remove it from memory/phone-inbox.md:"$'\n'"$UNPROCESSED"
fi
if [ -n "$PULL_NOTE" ]; then
  if [ -n "$MSG" ]; then MSG="$MSG"$'\n\n'"$PULL_NOTE"; else MSG="$PULL_NOTE"; fi
fi

jq -n --arg ctx "$MSG" \
  '{hookSpecificOutput:{hookEventName:"SessionStart", additionalContext:$ctx}}'
