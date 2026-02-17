"""
Sync competitor data from local scrape to the live Railway site.

Usage:
    python tools/sync_competitors.py              # Scrape all competitors, export, push to live
    python tools/sync_competitors.py --export-only # Export current local data without scraping
    python tools/sync_competitors.py --posts 15    # Scrape 15 posts per competitor (default 10)

Flow:
    1. Scrape all tracked competitors via Instagram (runs locally, no rate limits)
    2. Export competitors + posts from local DB to seed_competitors.json
    3. Git commit and push — Railway auto-deploys with fresh data
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import execute_query

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
SEED_FILE = os.path.join(TOOLS_DIR, "seed_competitors.json")


def scrape_all(max_posts=10):
    """Run the Instagram scraper on all tracked competitors."""
    from ig_scraper import scan_all
    print("Scraping all competitors from Instagram...")
    result = scan_all(max_posts=max_posts)
    total_new = sum(r.get("posts_added", 0) for r in result.get("results", []))
    print(f"Done. {result['competitors_scanned']} competitors scanned, {total_new} new posts added.")
    return result


def export_to_json():
    """Export competitor data from local DB to seed JSON."""
    competitors = execute_query(
        "SELECT name, handle, platform, profile_url, notes FROM competitors ORDER BY id"
    )
    posts = execute_query(
        "SELECT competitor_id, post_url, posted_at, content_type, caption_snippet, "
        "likes, comments, estimated_engagement_rate, content_theme, notes, is_notable "
        "FROM competitor_posts ORDER BY id"
    )

    data = {"competitors": competitors, "posts": posts}

    with open(SEED_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Exported {len(competitors)} competitors and {len(posts)} posts to seed_competitors.json")
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

    if not args.export_only:
        scrape_all(max_posts=args.posts)

    export_to_json()

    if not args.no_push:
        push_to_git()
    else:
        print("Skipping git push (--no-push).")
