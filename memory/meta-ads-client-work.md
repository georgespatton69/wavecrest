---
name: meta-ads-client-work
description: User runs Meta (Facebook/Instagram) ad campaigns for multiple clients; workflow and Business Manager setup
metadata: 
  node_type: memory
  type: project
  originSessionId: 4d2a8846-9266-484d-a3c4-fd5e4eb1e961
---

The user does Meta ads / marketing for multiple businesses out of their own Meta Business Manager (agency-style). The verified advertiser entity is **"Creative Package Mckahan"**; the Meta login shows as **Robby Hoffman** (robbyhoffman@me.com). Manages ~12 Pages including Beach Cities Toyota, Elmore Toyota, Lustig Automotive, Dom360, EZ Charge Case, Nexari Labs, plus the clients below.

Active ad clients (own portfolios, each its own Business Manager):
- [[client-alpine-pressure]] — pressure washing, Roaring Fork Valley
- [[client-aspen-party-tours]] — luxury party bus, Aspen
- [[client-samedaypsych]] — remote clinician hiring (Wavecrest subsidiary)
- [[wavecrest-detox-ads]] — the parent business's own addiction-treatment ads (LegitScript/Meta-authorized, no pixel)

**How the user works with me:** screenshot-driven. They paste screenshots to `~/Desktop/` and say "see screenshot"; I read the newest PNG there and advise step-by-step through Meta Ads Manager. They want pragmatic "just launch it" guidance, not over-engineering. I pull brand assets (logos/hero images) from client sites and generate branded overlay badges with Python/PIL, saving PNGs to `~/Desktop/`.

**NEXT TASK (started 2026-07-27, moved to a fresh session): build/choose a CRM to hold the scraped commercial leads.** Foundations already exist: the Alpine `Alpine-Commercial-Leads.xlsx` Outreach Pipeline tab, the two-sheet plan (Meta-connected Google Sheet via Zapier = Lookalike export source + Excel pipeline), and the Wavecrest Streamlit dashboard already has a **Lead Management CRM (Tab 4, `leads`/`lead_activity` tables)**. Open scoping question to resolve via brainstorming: (A) dedicated CRM tool e.g. HubSpot free, (B) extend the existing Wavecrest dashboard CRM, (C) level up the Google Sheet + Zapier, (D) new standalone WAT tool — AND whether it's Alpine-only or a reusable system across all clients (Aspen, SameDayPsych, etc.). Was about to brainstorm this when context filled up. The scrape pipeline scripts (OSM Overpass scraper + email extractor) live in the session scratchpad; user was also offered saving them to `tools/`.

**Meta setup patterns learned this session:**
- Build each client's assets in **their own** Business portfolio (not the user's) when the client will own it long-term — avoids painful Page/ad-account transfers. Add self as admin temporarily.
- **Employment/Housing/Credit** special ad category (e.g. clinician hiring) strips profession + detailed-interest targeting and forces 15-mi min radius — lean on geo + copy hook + retargeting, or use LinkedIn for job-title targeting.
- Messaging (click-to-Messenger) ads need **Engagement** objective → Message destinations → performance goal "Maximize number of messaging conversations."
- Ad-transparency beneficiary/payer disclosure shows in Ad Library; leave "advertiser" blank if the client isn't a verified advertiser (Page identity is used).
- Meta repeatedly nudges toward Advantage+ audience / audience expansion / AI creative — for tight local services, decline these (choose "Further limit the reach of your ads" to enforce a hard age range).

**Ads Manager traps that silently corrupt creative tests** (learned building [[wavecrest-detox-ads]], applies to any campaign):
- There are **TWO separate enhancement blocks at the ad level**, both default ON, and killing one does nothing to the other: **Advantage+ creative enhancements (6)** — Add overlays, Visual touch-ups (AI-*expands* the image), Text improvements, Add music, Add animation, Flex media; and **Essential enhancements (5)** — Relevant comments, Enhance CTA (stamps text onto the artwork), Adjust brightness and contrast (alters colors), Reveal details over time (shows a screenshot of the landing page in the ad), Show spotlights. Target state for a controlled test: **0/6 and 0/5 on every ad**. Each toggle throws a "Keep using" nag; the gray "Turn off" is the correct button.
- **Duplicating an ad from a recommendation card's "Duplicate ad" button applies recommendations** (re-enables Advantage+ creative + Add music). Always duplicate from the **ad's "..." menu** — the flow with the "Original campaign / Existing campaign / New campaign" radios.
- **Duplicates inherit stale placement specs from the source ad.** Symptom: a phantom `#2446880` "WhatsApp number required" error on the copy while the original is clean — the source ad was built while WhatsApp Status was an active placement. Fix: edit + re-save the source ad first (forces its creative to re-save), then re-duplicate.
- **"Allow limited spending to excluded placements"** (under Manual placements) quietly spends ~5% of budget on each placement you excluded. Uncheck it or the exclusions are theater.
- **Advantage+ detailed targeting cannot be turned off** on some objectives (e.g. Traffic/link clicks) — it says so in an inline notice. Any detailed targeting there is a *suggestion* Meta will expand past, not a filter. Household income by ZIP percentile **does still exist** (top 5% / 10% / 10–25%); selections are a union (OR), and "top 10%" already contains "top 5%".
- **Feed-shaped assets (1:1, 4:5) break in other slots**: forced to 9:16 they garble baked-in text; set to "Original" they letterback with gray bars. Right column (1.91:1) makes a square a postage stamp. Feeds-only is usually the honest fix. Also hiding in the Feeds group: Marketplace, right column, Notifications — all worth unchecking.
- Meta's recommendations recite defaults without reading the setup (e.g. pitching "add music to Reels" when Reels is excluded; pitching a conversion-rate stat to a campaign with no pixel). Treat the campaign score as *Meta's* preferences, not the account's health.
