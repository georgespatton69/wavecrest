---
name: wavecrest-dashboard
description: "Wavecrest Streamlit dashboard — architecture, 5 tabs, DB, deployment, seed system, known patterns"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4d2a8846-9266-484d-a3c4-fd5e4eb1e961
---

Social media dashboard for www.wavecrestbh.com, Streamlit, 5-tab layout. LIVE on Railway.

## Launch
`python3 -m streamlit run /Users/georges.patton/Wavecrest/dashboard/app.py --server.port 8502`
Port 8501 = AM Biomedical dashboard. Kill: `lsof -ti:8502 | xargs kill -9`

## Key Files
- `dashboard/app.py` — main dashboard (~1800+ lines, all 5 tabs) + competitor-sync API endpoint
- `dashboard/styles/theme.py` — COLORS, SCRIPT_CATEGORIES, LEAD_STAGES, AD_STATUS_COLORS, badges, mobile CSS
- `tools/db_helpers.py` — execute_query, insert_row, update_row, delete_row
- `tools/db_init.py` — schema (18 tables) + seed_scripts_from_json() + seed_competitors_from_json() + migrate_scripts_check()
- `tools/meta_api.py` — Meta Marketing + Leads API
- `tools/sync_competitors.py` — two-way competitor sync (pull live → scrape → export → push)
- `tools/ig_scraper.py` — Instaloader scraper (10 posts/competitor)
- `tools/competitive_intel.py` — competitor CRUD + demo data
- `tools/seed_scripts.json` (51 scripts, one-time seed) / `tools/seed_competitors.json` (merge logic)
- `data/wavecrest.db` — local SQLite; `.env` — META keys (unconfigured), RAILWAY_URL, SYNC_API_KEY

## The 5 Tabs (all COMPLETE)
1. **Content Suggestions** — submit ideas (name/title/desc/link/images/priority/channel), organic|paid two-column, image upload, "Move to Todos" → creates script (type='suggestions', status='todo') then deletes suggestion.
2. **Competitive Intel** — 4 sub-tabs (Overview, Competitors, Activity Feed, Add Competitor); notable-posts toggle (is_notable), IG iframe embeds (400x760), Log Competitor Post form, scraper, CSV export, demo data.
3. **Scripts Management** — Manage subtab (top: two-column Kanban Todos|Completed with 6 category expanders; bottom: Scripts Library backlog expanders w/ Edit/Move/Delete) + Input subtab (5 category-specific forms save status='backlog'). 6 categories: influencer_reels, ad_reels, voiceover_reels, therapist_scripts, carousel_posts, suggestions. Status flow backlog→todo→completed (CHECK constraint; suggestions skip to todo).
4. **Lead Management CRM** — 4-col pipeline (New→Contacted→Qualified→Enrolled), lead cards w/ activity log, arrow moves, Add Lead form, Meta lead-form sync, lead_activity table.
5. **Ad Performance** — Overview (6 metric cards + Plotly spend/comparison charts), Campaigns (Campaign→AdSet→Ad drilldown), Log Metrics (auto-calc CTR/CPC/CPM), Meta sync.

## Database (18 tables)
content_pillars, scripts, content_calendar, idea_bank, posts_performance, account_snapshots, competitors, competitor_snapshots, competitor_posts, analysis_log, content_suggestions, suggestion_images, leads, lead_activity, ad_campaigns, ad_sets, ads, ad_metrics.

## Meta API (tools/meta_api.py)
MetaAPI class: sync_campaigns(), sync_metrics(), sync_leads() with dedup. Creds in .env (META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, META_PAGE_ID). NOT configured — needs Meta developer account. (Distinct from [[meta-ads-client-work]], which is manual campaigns in Ads Manager.)

## Deployment (Railway) — LIVE at web-production-b8ad5.up.railway.app
- Repo github.com/georgespatton69/wavecrest (PUBLIC). GitHub CLI `~/bin/gh` as georgespatton69. SSH `~/.ssh/id_ed25519`.
- Files: Procfile (`web: python tools/db_init.py && streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`), requirements.txt, .streamlit/config.toml.
- DB_PATH via `DATABASE_PATH` env. Railway env: DASHBOARD_PASSWORD, DATABASE_PATH=/app/data/wavecrest.db, PORT=8080, SYNC_API_KEY. Volume at /app/data. Auto-deploys on push to main (1-3 min; check with curl `%{http_code}`).

## Seed System
seed_scripts.json = 51 scripts, one-time (only if table empty). seed_competitors.json = merge (match by handle/post_url, skip existing, preserve live-site data), runs every deploy via db_init.py. **CRITICAL Seed ID Mapping**: seed JSON uses 1-based array positions for competitor_id, NOT raw DB IDs (local IDs start at 5,6,7…). `export_to_json()` remaps DB→seed indices; `seed_competitors_from_json()` builds its own id_map. Out of sync → Railway deploy crashes `FOREIGN KEY constraint failed`. Fixed permanently in sync_competitors.py export.

## Competitor Sync Pipeline
Two-way local↔Railway: pull new competitors from live → scrape locally (Instaloader) → export seed JSON → git push → auto-deploy. API endpoint in app.py before auth gate: `?api=competitors&key=SYNC_API_KEY` (works via Streamlit WebSocket only, NOT raw curl). IG scraping must run local/residential (cloud IPs get 429). Daily 7am cron: `0 7 * * * cd /Users/georges.patton/Wavecrest && /usr/bin/python3 tools/sync_competitors.py`. Mac must stay awake. No cost.

## Design / Theme / Security
- Mobile: all responsive CSS in `get_custom_css()` in theme.py, single `@media (max-width:768px)` block (columns stack, tabs scroll, 44px targets, responsive iframes, 16px inputs anti-zoom). Selectors: `[data-testid="stHorizontalBlock"|"column"|"stMetric"]`.
- Colors match wavecrestbh.com: primary #204CE5, dark #044AD3, text #112337, bg #F2F3F5. config.toml [theme] + COLORS dict. migrate_scripts_check() does CHECK-constraint migrations (table-recreate pattern).
- Security (done): password auth check_password() + DASHBOARD_PASSWORD; esc()=html.escape() on user input; safe_url() http/https only; rel="noopener noreferrer"; .env/db/creds gitignored.
- Demo data (LOCAL only, not git): 15 leads, 3 campaigns/6 ad sets/12 ads/60 metric rows (Jan18–Feb16 2026). Railway starts empty.

## Future / Next Steps
Daily DB backup (user wants next); Meta API setup (connect developer account); in-app lead messaging (Meta Conversations API — needs 24hr window, templates, App Review, Business Verification).

## Known Issues / Patterns
- `update_row` auto-adds updated_at — fails on tables without it (use execute_query directly).
- f-strings: no backslash escapes inside {expressions} — extract to vars first.
- Stale .pyc → ImportErrors: `find dashboard -name "__pycache__" -type d -exec rm -rf {} +`.
- User prefers simple, not highly technical, implementations.
- IG embeds: raw HTML iframe (400x760), not st.components.v1.iframe (width issues).
- Centering: `_, center, _ = st.columns([1,2,1])`.
- Hide selectbox search: `div[data-baseweb='select'] input { opacity:0; width:0; padding:0; }`.
- `st.stop()` kills the ENTIRE app, not one tab — never use inside tab blocks.
- Railway stdout buffering: always `flush=True` on deploy-time print().
- Failed db_init.py deploys can reset DB if volume recreated — live-site data may be lost.
