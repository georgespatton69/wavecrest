# Alpine Commercial CRM — Design Spec

**Date:** 2026-07-27
**Status:** Approved (brainstorming complete)
**Owner:** Robby (agency) + Brandon Williams (Alpine Pressure)

## Purpose

A standalone web app to run Alpine Pressure's **commercial** outreach operation end to end. It replaces the current `Alpine-Commercial-Leads.xlsx` tracker with a real CRM that does four jobs:

1. **Work the outbound list** — track calls/emails to the scraped property managers, HOAs, hotels; know who's been contacted, what's due, and move each lead toward a recurring contract.
2. **Catch inbound Meta leads** — pull form submissions from the Commercial Lead-Form campaign into the same pipeline.
3. **Report/forecast** — pipeline value, stage counts, win rate, follow-ups due.
4. **Feed the Lookalike** — track Won + consented customers and export them as the compliant commercial Lookalike seed.

This is the commercial arm of [[client-alpine-pressure]] / [[meta-ads-client-work]]. Residential campaigns are handled separately in Ads Manager.

## Decisions (locked)

| Decision | Choice |
|---|---|
| Form factor | Standalone **Streamlit** web app, own repo/deploy on Railway (same stack as the Wavecrest dashboard, but a separate app — Alpine B2B ≠ Wavecrest social) |
| Access | Single **shared password** gate (you + Brandon) |
| Inbound path | **Google Sheet relay** — Zapier appends to the *Meta Commercial Leads* sheet; CRM has an "Import inbound" button that pulls new rows |
| Persistence | **Railway persistent volume + SQLite** now; keep all DB access behind one `db.py` module so a later swap to Postgres is contained, not a rewrite |
| Seed source | `Alpine-Commercial-Leads.xlsx` — 287 tiered leads as the working set, 17 enriched Tier-1 rows overlaid, 553 raw kept as backlog |

## Architecture

Small Streamlit app, four screens + a login gate, backed by a SQLite file on a mounted Railway volume. All persistence goes through a single `db.py` data-access module (the migration seam). No webhooks — inbound is pull-based from a Google Sheet.

```
alpine-crm/
  app.py               # login gate + tab router
  db.py                # ALL SQL lives here (SQLite now, Postgres-swappable)
  screens/
    pipeline.py        # working table + lead detail panel
    inbound.py         # import-from-Sheet button
    dashboard.py       # metrics + charts
    lookalike.py       # Won+consent filter + CSV export
  lib/
    sheets.py          # read the Meta Commercial Leads Google Sheet (inbound)
    seed.py            # one-time import from the Excel
  tests/
  requirements.txt
  Procfile
```

### Screens

**Login** — one shared password (env var), Streamlit session flag. Nothing else renders until authenticated.

**Pipeline** (daily driver)
- Filterable/searchable table: filter by tier, category, city, stage; search by name.
- Click a lead → detail panel:
  - Contact info (name, role, phone, email(s), website, property type, units).
  - Change **stage** (writes a `stage_change` activity automatically).
  - Set **next follow-up date**.
  - **Log an activity**: call / email / note (free-text body).
  - Toggle **recurring**, **consent**; set **contract_value**.
  - Activity history for the lead, newest first.

**Inbound**
- Button: "Import from Google Sheet." Reads the Zapier-fed *Meta Commercial Leads* sheet, dedupes against existing leads by (lower(email)) then (lower(name)), inserts new ones as `source=meta_form`, `stage=New`, `tier=Inbound`.
- Shows a summary of what was imported / skipped as duplicates.

**Dashboard**
- Stage counts (New→Contacted→Interested→Quoted→Won/Lost).
- Pipeline $ value (sum of `contract_value` for open stages) and Won $ value.
- Win rate (Won / (Won+Lost)).
- Follow-ups **due today** and **overdue**.
- Contacted this week.
- Breakdown by tier and by category.

**Lookalike**
- Filters to `stage=Won AND consent=1`.
- Shows the list; **Download CSV** formatted for Meta Custom Audience upload (name, email, phone, city, country).

## Data model (SQLite)

### `leads`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT NOT NULL | business name |
| category | TEXT | PropertyMgmt/HOA, Hotel, Restaurant, etc. |
| tier | TEXT | '1'–'5' or 'Inbound' |
| tier_label | TEXT | e.g. "Property Mgmt / HOA" |
| region | TEXT | Roaring Fork Valley / Eagle County (Vail) |
| city | TEXT | |
| address | TEXT | |
| website | TEXT | |
| phone | TEXT | |
| primary_email | TEXT | first/best email |
| all_emails | TEXT | semicolon-joined, as in the source |
| property_type | TEXT | |
| units | TEXT | |
| contact_name | TEXT | |
| contact_role | TEXT | |
| stage | TEXT NOT NULL DEFAULT 'New' | CHECK IN (New, Contacted, Interested, Quoted, Won, Lost) |
| next_followup | DATE | |
| contract_value | REAL | |
| recurring | INTEGER DEFAULT 0 | bool |
| consent | INTEGER DEFAULT 0 | bool |
| source | TEXT DEFAULT 'scrape' | scrape / meta_form / manual |
| notes | TEXT | |
| created_at | TIMESTAMP DEFAULT now | |
| updated_at | TIMESTAMP DEFAULT now | |

### `activities`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| lead_id | INTEGER NOT NULL → leads(id) ON DELETE CASCADE | |
| type | TEXT NOT NULL | call / email / note / stage_change |
| body | TEXT | e.g. "New → Contacted", or free-text call notes |
| created_at | TIMESTAMP DEFAULT now | |

Every stage change and logged touch appends an `activities` row, giving each lead a full paper trail.

## Data flow

- **Seed (one-time):** `lib/seed.py` reads the Excel. Working set = 287 tiered rows (has tier + has_contact). Overlay the 17 enriched Tier-1 pipeline rows (contacts, notes, property type) onto matching businesses. Dedupe by name. 553 raw rows are *not* auto-imported — kept as a documented backlog to pull from later. All seeded leads start at `stage=New`, `source=scrape`.
- **Inbound:** Zapier → *Meta Commercial Leads* Google Sheet → "Import" button → `leads` (source=meta_form). Pull-based; no live webhook.
- **Lookalike out:** Pipeline work sets `stage=Won` + `consent=1` → Lookalike tab filters → CSV → Meta Custom Audience → Lookalike (Phase 2 of the ads plan).

## Error handling

- **Google Sheet import:** if the sheet is unreachable or empty, show a clear message and change nothing (no partial writes). Import runs in a transaction.
- **Seed:** idempotent — re-running does not duplicate leads (dedupe by name); safe to re-run after schema tweaks.
- **DB writes:** wrapped so a failed write surfaces an error in the UI rather than corrupting state; `updated_at` bumped on every lead mutation.
- **Persistence:** DB file path points at the mounted Railway volume; app logs the resolved path on boot so a mis-mounted volume is obvious immediately.

## Testing

- **Seed importer** against the real Excel: assert working-set row count, that the 17 enriched rows overlaid correctly, and that re-running doesn't duplicate.
- **DB layer** (`db.py`) unit tests: create lead; stage change writes an `activities` row; set follow-up; Lookalike filter returns only Won+consent; inbound dedupe skips existing email/name.
- **Sheets import** with a fake/sample sheet payload: new rows inserted, duplicates skipped, unreachable sheet is a no-op.
- UI is thin over the tested `db.py`, so most coverage sits at the data layer.

## Out of scope (YAGNI)

- Multi-user accounts / per-user permissions (shared password only).
- Live webhook inbound (pull-based Sheet import instead).
- Auto-importing all 553 raw leads (backlog, imported on demand later).
- Email/SMS sending from the CRM (outreach happens in the user's own tools; CRM tracks it).
- Postgres (kept behind the `db.py` seam for a later, contained migration).

## Related memory
[[client-alpine-pressure]] · [[meta-ads-client-work]]
