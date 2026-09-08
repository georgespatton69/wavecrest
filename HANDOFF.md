# Session Handoff — Strategize From Anywhere

**Purpose:** This file lets a fresh Claude session (on your phone/web at claude.ai/code, or a new VS Code window) pick up strategy work on Wavecrest without the context that normally lives in Claude's local memory.

**Full memory is now in the repo.** The laptop's Claude memory folder is live-synced into this repo at [`memory/`](memory/) via a symlink, so phone/web sessions can read the *complete* project context — not just this summary. Start a phone session with: *"Read memory/MEMORY.md and let's strategize."*

**Capturing ideas on the go:** jot them into [`memory/phone-inbox.md`](memory/phone-inbox.md) and push. When back at the computer, `git pull` and triage them into the right files. (Phone writes only to the inbox to avoid merge conflicts with the laptop's auto-writes.)

> Keep this file updated when major state changes. Ask Claude: *"update HANDOFF.md with where we are."*

---

## How to strategize from your phone

1. Open **claude.ai/code**, select the **Wavecrest** project (connected to `github.com/georgespatton69/wavecrest`).
2. Start a new chat — it starts fresh, but has all repo files including this one.
3. Say: *"Read HANDOFF.md and let's strategize on [topic]."*

The **conversation** doesn't carry over between surfaces, but the **project context** does via this repo.

---

## What works remotely vs. only on the laptop

| Available on phone/web | Laptop (VS Code) only |
|---|---|
| All committed repo files (workflows, tools, docs, this file) | `.env` secrets & API keys (gitignored) |
| Reading/strategizing/planning | Running the Streamlit dashboard locally |
| Editing files, drafting workflows | The local SQLite DB (`data/wavecrest.db`, gitignored) |
| | Claude's local memory (`~/.claude/…/memory/`) |

---

## The framework (read CLAUDE.md for full detail)

**WAT = Workflows, Agents, Tools.**
- `workflows/` — markdown SOPs (what to do & how)
- `tools/` — Python scripts (deterministic execution; creds in `.env`)
- Claude orchestrates: reads the workflow, runs the right tool, recovers from errors.

---

## Current state of active work (snapshot — verify before acting)

### Software
- **Wavecrest Dashboard** — Streamlit 5-tab social dashboard, LIVE on Railway (`web-production-b8ad5.up.railway.app`). 18 DB tables, seed system, competitor sync.
- **ICA-ERM** — marketing lead gen + future software tools for an ERM consulting firm.

### Meta Ads client work (manual campaigns, run from own Business Manager)
Behavioral-health cluster:
- **Wavecrest Detox (own business)** — addiction-treatment ads; LegitScript + Meta auth APPROVED; no pixel (HIPAA); PPO-only; 15-creative library.
- **Colorado Behavioral** — LIVE; rebuilding lead form PERSON-first + testing EMOTIONAL creative (zero leads on $311 with insurance-first form).
- **Indiana Behavioral** — LegitScript certified; person-first relaunch built, ads started ~9/08; callback 855-803-0651.
- **Addiction Behavioral (ABH)** — umbrella ad account for Virtual IOP lead ads; 3 campaigns (CO/CA/IN) built, ready to publish; shared form + dev handoff sent.
- **SameDayPsych** — Wavecrest subsidiary; remote PMHNP/psychiatrist hiring ads (Employment category).

Other verticals:
- **Alpine Pressure** — pressure washing; Messenger A/B campaign published, in Meta review.
- **Aspen Party Tours** — luxury party bus; Messenger A/B campaign built, ready to publish.
- **TDV Tax Relief** — IRS tax-resolution firm (NOT rehab); Meta account not built yet; competitive research in progress.

### User preferences
- Prefers simple, pragmatic "just launch it" guidance over heavy technicality.
- Marketing work is screenshot-driven (pastes PNGs to `~/Desktop/`, says "see screenshot").

---

*Last updated: 2026-09-07*
