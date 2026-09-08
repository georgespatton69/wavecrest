---
name: cross-device-setup
description: How the user works with Claude across phone + computer for this repo — Remote Control, phone-inbox memory loop, and what's still pending (Dispatch).
metadata:
  type: project
---

# Cross-Device Setup (phone ⇄ computer)

Set up 2026-09-07/08 so the user can capture ideas + drive work from their phone. User is on the **VS Code extension** (no `claude` CLI installed), macOS, plugged in + external display + system sleep disabled (`pmset sleep 0`).

## What's built (all in repo, git-synced to github.com/georgespatton69/wavecrest)
- **Memory lives in the repo:** `~/.claude/projects/.../memory` is a **symlink → repo `memory/`**. Laptop reads/writes memory as normal; commits carry it to the phone. See [[phone-inbox]].
- **Auto-load rule:** top of `CLAUDE.md` tells every session (incl. phone/web) to read `memory/MEMORY.md` first.
- **SessionStart hook** (`tools/session_start_phone_inbox.sh`, wired in `.claude/settings.local.json` — personal, gitignored): on each computer session, fast-forward pulls + surfaces unprocessed `memory/phone-inbox.md` notes. Activates next session after it was added.
- **HANDOFF.md** = orientation doc for fresh phone/web sessions.
- **Remote Control ENABLED** in `~/.claude/settings.json`: `remoteControlAtStartup`, `inputNeededNotifEnabled`, `agentPushNotifEnabled` (all true). In VS Code, activated per-session by typing `/remote-control` (setting alone may not auto-start; verify auto-start on a fresh session).

## Key facts learned (verified vs code.claude.com docs)
- **Remote Control** = drive an EXISTING VS Code/CLI session from phone. Session must stay running (don't quit VS Code). Works now.
- **Dispatch** = spawn a NEW session from phone — **Desktop app ONLY**, not VS Code. New session shows in Desktop app's Code tab (Dispatch badge), NOT as a VS Code tab. Needs Pro/Max plan.
- **Background sessions / agent view** (`claude --bg`, `claude agents`) = local parallelism via CLI. NOT phone-related; not what the user wants.
- Phone-inbox capture only works in a **Code chat** (connected to repo), NOT a normal Claude chat. In a Remote-Control session it saves straight to memory; in a cloud Code session it writes phone-inbox.md + pushes.

## Pending (resume here)
1. **Dispatch setup** — install Claude Desktop app (claude.ai/download), sign in as georges.patton69@gmail.com, confirm Pro/Max, find Cowork tab → Dispatch, link Wavecrest via "Use existing folder". Undocumented bit: exact phone folder-picking flow — figure out in UI.
2. **Build `tools/setup_cross_device.sh`** — one-command setup (symlink memory + phone-inbox + hook) so future projects are trivial. User approved building it "for later."
3. Delete `memory.bak` backup once phone loop confirmed.
4. Fix git commit identity — currently `George S. Patton <georges.patton@Mac.lan>` (auto-guessed).
