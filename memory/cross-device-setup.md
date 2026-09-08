---
name: cross-device-setup
description: How the user works with Claude across phone + computer for this repo — Remote Control, Dispatch (phone→computer, working), and the phone-inbox memory loop.
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
- **Dispatch SET UP + PAIRED (2026-09-08)** — Claude Desktop app installed (macOS, plan = Max, name "Robby"), phone paired. Dispatch = its own left-sidebar item (Beta), NOT a "Cowork" tab in this build (v1.46388.3). Registered projects so far: **Wavecrest** (`/Users/georges.patton/Wavecrest`) and **Alpine Pressure** (`/Users/georges.patton/Alpine Pressure`, a WAT project). Both confirmed working from the phone.
  - **To add a new project:** Desktop app → Projects section → **+** → name it → **"Use a folder"** → type/pick the folder path → Create. Then from phone: *"In my <name> project, ..."*. macOS permission grants are one-time (per app, not per folder).

## Key facts learned (verified vs code.claude.com docs)
- **Remote Control** = drive an EXISTING VS Code/CLI session from phone. Session must stay running (don't quit VS Code). Works now.
- **Dispatch** = spawn a NEW session from phone — **Desktop app ONLY**, not VS Code. New session shows in Desktop app's Code tab (Dispatch badge), NOT as a VS Code tab. Needs Pro/Max plan. **For a phone Dispatch to run, the Desktop app must be OPEN and the Mac AWAKE** (screen may sleep; system must not — `pmset sleep 0` on AC handles this).
- **Background sessions / agent view** (`claude --bg`, `claude agents`) = local parallelism via CLI. NOT phone-related; not what the user wants.
- Phone-inbox capture only works in a **Code chat** (connected to repo), NOT a normal Claude chat. In a Remote-Control session it saves straight to memory; in a cloud Code session it writes phone-inbox.md + pushes.

## Pending (resume here)
1. **Build `tools/setup_cross_device.sh`** — one-command setup (symlink memory + phone-inbox + hook) so future projects are trivial. User approved building it "for later." (Note: this is the memory/inbox loop, separate from Dispatch project registration which is done per-project in the Desktop app.)
2. Delete `memory.bak` backup once phone loop confirmed.
3. Fix git commit identity — currently `George S. Patton <georges.patton@Mac.lan>` (auto-guessed).
