"""
Sync competitor data from local scrape to the live Railway site.

Usage:
    python tools/sync_competitors.py              # Pull from live, scrape, export, push
    python tools/sync_competitors.py --export-only # Export current local data without scraping
    python tools/sync_competitors.py --posts 15    # Scrape 15 posts per competitor (default 10)

Flow:
    1. Pull any new competitors added on the live site into local DB
    2. Scrape all tracked competitors via Instagram (runs locally, no rate limits)
    3. Export competitors + posts from local DB to seed_competitors.json
    4. Git commit and push — Railway auto-deploys with fresh data
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
SEED_FILE = os.path.join(TOOLS_DIR, "seed_competitors.json")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from db_helpers import execute_query, insert_row


def pull_from_live():
    """Pull new competitors from the live Railway site into local DB."""
    railway_url = os.getenv("RAILWAY_URL", "")
    sync_key = os.getenv("SYNC_API_KEY", "")

    if not railway_url or not sync_key:
        print("RAILWAY_URL or SYNC_API_KEY not set in .env, skipping live pull.")
        return

    import requests
    url = f"{railway_url.rstrip('/')}?api=competitors&key={sync_key}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        # Streamlit wraps the JSON in HTML — extract the text content
        # The JSON is rendered inside a <pre> tag by st.text()
        text = resp.text
        # Find the JSON array in the response
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            print("Could not parse competitor data from live site.")
            return
        live_comps = json.loads(text[start:end])
    except Exception as e:
        print(f"Could not reach live site: {e}")
        return

    # Add any competitors from live that don't exist locally
    local_handles = {c["handle"] for c in execute_query("SELECT handle FROM competitors")}
    added = 0
    for c in live_comps:
        if c["handle"] not in local_handles:
            insert_row("competitors", {
                "name": c["name"],
                "handle": c["handle"],
                "platform": c["platform"],
                "profile_url": c.get("profile_url"),
                "notes": c.get("notes"),
            })
            added += 1
            print(f"  Added @{c['handle']} from live site")

    if added:
        print(f"Pulled {added} new competitor(s) from live site.")
    else:
        print("Live site has no new competitors.")


def scrape_all(max_posts=10):
    """Run the Instagram scraper on all tracked competitors."""
    from ig_scraper import scan_all
    print("Scraping all competitors from Instagram...")
    result = scan_all(max_posts=max_posts)
    total_new = sum(r.get("posts_added", 0) for r in result.get("results", []))
    print(f"Done. {result['competitors_scanned']} competitors scanned, {total_new} new posts added.")
    return result


def export_to_json():
    """Export competitor data from local DB to seed JSON.

    Remaps DB competitor IDs to 1-based seed array positions so that
    seed_competitors_from_json() can match posts to competitors on a
    fresh Railway database where IDs start at 1.
    """
    competitors = execute_query(
        "SELECT id, name, handle, platform, profile_url, notes FROM competitors ORDER BY id"
    )
    posts = execute_query(
        "SELECT competitor_id, post_url, posted_at, content_type, caption_snippet, "
        "likes, comments, estimated_engagement_rate, content_theme, notes, is_notable "
        "FROM competitor_posts ORDER BY id"
    )

    # Build mapping: real DB id → 1-based seed index
    id_map = {}
    for i, c in enumerate(competitors, start=1):
        id_map[c["id"]] = i

    # Remap post competitor_ids to seed indices
    for p in posts:
        p["competitor_id"] = id_map.get(p["competitor_id"], p["competitor_id"])

    # Strip the DB id from competitor dicts (seed only needs name/handle/etc)
    seed_comps = [{k: v for k, v in c.items() if k != "id"} for c in competitors]

    data = {"competitors": seed_comps, "posts": posts}

    with open(SEED_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Exported {len(seed_comps)} competitors and {len(posts)} posts to seed_competitors.json")
    return data


def push_to_git():
    """Commit and push the updated seed file."""
    os.chdir(PROJECT_ROOT)

    # Check if there are changes
    result = subprocess.run(
        ["git", "diff", "--name-only", "tools/seed_competitors.json"],
        capture_output=True, text=True,
    )
    if not result.stdout.strip():
        print("No changes to push — seed file is up to date.")
        return False

    subprocess.run(["git", "add", "tools/seed_competitors.json"], check=True)
    subprocess.run(
        ["git", "commit", "-m", "Update competitor data from local scrape"],
        check=True,
    )
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("Pushed to git. Railway will auto-deploy in ~2 minutes.")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync competitor data to live site")
    parser.add_argument("--export-only", action="store_true", help="Export local data without scraping first")
    parser.add_argument("--posts", type=int, default=10, help="Max posts per competitor (default 10)")
    parser.add_argument("--no-push", action="store_true", help="Export only, don't push to git")
    args = parser.parse_args()

    # Step 1: Pull new competitors from live site
    if not args.export_only:
        pull_from_live()

    # Step 2: Scrape all competitors
    if not args.export_only:
        scrape_all(max_posts=args.posts)

    # Step 3: Export to seed JSON
    export_to_json()

    # Step 4: Push to git
    if not args.no_push:
        push_to_git()
    else:
        print("Skipping git push (--no-push).")
