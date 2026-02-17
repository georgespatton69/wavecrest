"""
Initialize or migrate the Wavecrest SQLite database.

Usage:
    python tools/db_init.py              # Create database with all tables
    python tools/db_init.py --seed       # Create database and insert seed data
    python tools/db_init.py --check      # Verify database integrity
    python tools/db_init.py --seed --check  # Create, seed, and verify
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import get_connection, DB_PATH

SCHEMA = """
-- Content pillars
CREATE TABLE IF NOT EXISTS content_pillars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    color_hex TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scripts board
CREATE TABLE IF NOT EXISTS scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    script_type TEXT NOT NULL CHECK(script_type IN ('influencer_reels', 'ad_reels', 'voiceover_reels', 'therapist_scripts', 'carousel_posts')),
    pillar_id INTEGER REFERENCES content_pillars(id),
    status TEXT NOT NULL DEFAULT 'backlog' CHECK(status IN ('backlog', 'todo', 'completed')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content calendar
CREATE TABLE IF NOT EXISTS content_calendar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    platform TEXT NOT NULL CHECK(platform IN ('instagram', 'facebook', 'both')),
    content_type TEXT NOT NULL CHECK(content_type IN ('still_image', 'ugc_video', 'therapist_video', 'carousel', 'story', 'reel')),
    pillar_id INTEGER REFERENCES content_pillars(id),
    script_id INTEGER REFERENCES scripts(id),
    caption TEXT,
    hashtags TEXT,
    media_path TEXT,
    status TEXT NOT NULL DEFAULT 'planned' CHECK(status IN ('planned', 'created', 'reviewed', 'scheduled', 'published')),
    meta_post_id TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Idea bank
CREATE TABLE IF NOT EXISTS idea_bank (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea TEXT NOT NULL,
    pillar_id INTEGER REFERENCES content_pillars(id),
    content_type TEXT,
    inspiration_source TEXT,
    inspiration_url TEXT,
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
    status TEXT DEFAULT 'new' CHECK(status IN ('new', 'developing', 'used', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Post performance metrics
CREATE TABLE IF NOT EXISTS posts_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calendar_id INTEGER REFERENCES content_calendar(id),
    meta_post_id TEXT NOT NULL,
    platform TEXT NOT NULL CHECK(platform IN ('instagram', 'facebook')),
    post_url TEXT,
    published_at TIMESTAMP,
    content_type TEXT,
    reach INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    video_views INTEGER DEFAULT 0,
    engagement_rate REAL DEFAULT 0.0,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Account-level snapshots
CREATE TABLE IF NOT EXISTS account_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL CHECK(platform IN ('instagram', 'facebook')),
    snapshot_date DATE NOT NULL,
    followers INTEGER,
    following INTEGER,
    total_posts INTEGER,
    reach_period INTEGER,
    impressions_period INTEGER,
    profile_views_period INTEGER,
    website_clicks_period INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, snapshot_date)
);

-- Competitor profiles
CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    handle TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL DEFAULT 'instagram',
    profile_url TEXT,
    notes TEXT
);

-- Competitor snapshots over time
CREATE TABLE IF NOT EXISTS competitor_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id INTEGER NOT NULL REFERENCES competitors(id),
    snapshot_date DATE NOT NULL,
    followers INTEGER,
    following INTEGER,
    total_posts INTEGER,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(competitor_id, snapshot_date)
);

-- Notable competitor posts
CREATE TABLE IF NOT EXISTS competitor_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id INTEGER NOT NULL REFERENCES competitors(id),
    post_url TEXT,
    posted_at TIMESTAMP,
    content_type TEXT,
    caption_snippet TEXT,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    estimated_engagement_rate REAL,
    content_theme TEXT,
    notes TEXT,
    is_notable INTEGER DEFAULT 0,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI analysis log
CREATE TABLE IF NOT EXISTS analysis_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_type TEXT NOT NULL,
    month_year TEXT,
    summary TEXT NOT NULL,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content suggestions (team submission board)
CREATE TABLE IF NOT EXISTS content_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    submitted_by TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
    channel TEXT NOT NULL DEFAULT 'organic' CHECK(channel IN ('organic', 'paid')),
    link_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Images attached to content suggestions
CREATE TABLE IF NOT EXISTS suggestion_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL REFERENCES content_suggestions(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CRM leads
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    source TEXT DEFAULT 'meta_ads',
    campaign_name TEXT,
    ad_name TEXT,
    form_name TEXT,
    stage TEXT NOT NULL DEFAULT 'new' CHECK(stage IN ('new','contacted','qualified','enrolled')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lead activity log
CREATE TABLE IF NOT EXISTS lead_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ad campaigns
CREATE TABLE IF NOT EXISTS ad_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meta_campaign_id TEXT,
    name TEXT NOT NULL,
    objective TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active','paused','completed')),
    daily_budget REAL,
    lifetime_budget REAL,
    start_date DATE,
    end_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ad sets
CREATE TABLE IF NOT EXISTS ad_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES ad_campaigns(id) ON DELETE CASCADE,
    meta_adset_id TEXT,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK(status IN ('active','paused','completed')),
    targeting_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual ads
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_set_id INTEGER NOT NULL REFERENCES ad_sets(id) ON DELETE CASCADE,
    meta_ad_id TEXT,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK(status IN ('active','paused','completed')),
    creative_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ad performance metrics (daily snapshots)
CREATE TABLE IF NOT EXISTS ad_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER REFERENCES ad_campaigns(id),
    ad_set_id INTEGER REFERENCES ad_sets(id),
    ad_id INTEGER REFERENCES ads(id),
    metric_date DATE NOT NULL,
    spend REAL DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0,
    cpc REAL DEFAULT 0,
    cpm REAL DEFAULT 0,
    roas REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SEED_DATA = """
-- Content pillars
INSERT OR IGNORE INTO content_pillars (name, description, color_hex) VALUES
    ('Education', 'Mental health tips, treatment approaches, and recovery education', '#4A90D9'),
    ('Affirming Messages', 'Positive, supportive, and affirming content for those in recovery', '#7B68EE'),
    ('Community', 'Highlighting the Wavecrest community, team, and SoCal culture', '#20B2AA'),
    ('Client Stories', 'UGC and testimonial content (with consent)', '#DDA0DD'),
    ('Treatment Info', 'Virtual IOP program details, services, and how to get help', '#F0A050');

-- Competitors
INSERT OR IGNORE INTO competitors (name, handle, platform, profile_url) VALUES
    ('Charlie Health', 'charliehealth', 'instagram', 'https://www.instagram.com/charliehealth/'),
    ('Novara Recovery Center', 'novararecoverycenter', 'instagram', 'https://www.instagram.com/novararecoverycenter/');
"""


def create_tables(conn):
    """Create all tables from the schema."""
    conn.executescript(SCHEMA)
    print("All tables created successfully.")


def seed_data(conn):
    """Insert seed data for pillars and competitors."""
    conn.executescript(SEED_DATA)
    print("Seed data inserted.")


def check_database(conn):
    """Verify database integrity and print table stats."""
    # Integrity check
    result = conn.execute("PRAGMA integrity_check").fetchone()
    status = result[0] if result else "unknown"
    print(f"Integrity check: {status}")

    # Table counts
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    print(f"\nTables ({len(tables)}):")
    for table in tables:
        name = table[0]
        count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name}: {count} rows")


def seed_scripts_from_json(conn):
    """Load scripts from seed JSON if scripts table is empty."""
    import json
    count = conn.execute("SELECT COUNT(*) FROM scripts").fetchone()[0]
    if count > 0:
        print(f"Scripts table already has {count} rows, skipping seed.", flush=True)
        return

    seed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_scripts.json")
    if not os.path.exists(seed_file):
        print(f"No seed_scripts.json found, skipping.", flush=True)
        return

    with open(seed_file) as f:
        scripts = json.load(f)

    for s in scripts:
        conn.execute(
            "INSERT INTO scripts (title, body, script_type, status, notes, pillar_id) VALUES (?, ?, ?, ?, ?, ?)",
            [s["title"], s["body"], s["script_type"], s["status"], s.get("notes"), s.get("pillar_id")],
        )
    conn.commit()
    print(f"Seeded {len(scripts)} scripts.", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Initialize the Wavecrest database")
    parser.add_argument("--seed", action="store_true", help="Insert seed data")
    parser.add_argument("--check", action="store_true", help="Verify database integrity")
    args = parser.parse_args()

    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = get_connection()
    try:
        create_tables(conn)
        seed_scripts_from_json(conn)
        if args.seed:
            seed_data(conn)
        if args.check:
            check_database(conn)
    finally:
        conn.close()

    print(f"\nDatabase location: {DB_PATH}", flush=True)


if __name__ == "__main__":
    main()
