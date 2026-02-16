"""
Instagram Scraper for Wavecrest Competitive Intelligence.
Pulls public profile data and recent posts using instaloader.

Usage:
    python tools/ig_scraper.py --profile charliehealth          # Scrape profile + recent posts
    python tools/ig_scraper.py --profile charliehealth --posts 5 # Limit to 5 posts
    python tools/ig_scraper.py --scan                            # Scrape all tracked competitors
    python tools/ig_scraper.py --scan --posts 10                 # Scrape all, 10 posts each

Requires: pip install instaloader
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import execute_query, insert_row

try:
    import instaloader
except ImportError:
    print(json.dumps({"error": "instaloader not installed. Run: pip install instaloader"}))
    sys.exit(1)


def scrape_profile(handle, max_posts=10):
    """
    Scrape a public Instagram profile for profile info and recent posts.
    Returns a dict with profile data and a list of posts.
    """
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    try:
        profile = instaloader.Profile.from_username(L.context, handle)
    except instaloader.exceptions.ProfileNotExistsException:
        return {"error": f"Profile @{handle} not found"}
    except instaloader.exceptions.ConnectionException as e:
        return {"error": f"Connection error for @{handle}: {str(e)}"}

    profile_data = {
        "handle": handle,
        "full_name": profile.full_name,
        "bio": profile.biography,
        "followers": profile.followers,
        "following": profile.followees,
        "total_posts": profile.mediacount,
        "is_private": profile.is_private,
        "profile_pic_url": profile.profile_pic_url,
        "external_url": profile.external_url,
    }

    posts = []
    if not profile.is_private:
        try:
            for i, post in enumerate(profile.get_posts()):
                if i >= max_posts:
                    break

                # Determine content type
                if post.typename == "GraphSidecar":
                    content_type = "carousel"
                elif post.is_video:
                    content_type = "video"
                else:
                    content_type = "image"

                caption = post.caption or ""

                posts.append({
                    "shortcode": post.shortcode,
                    "post_url": f"https://www.instagram.com/p/{post.shortcode}/",
                    "posted_at": post.date_utc.isoformat(),
                    "content_type": content_type,
                    "caption": caption,
                    "caption_snippet": caption[:200] if caption else None,
                    "likes": post.likes,
                    "comments": post.comments,
                    "video_view_count": post.video_view_count if post.is_video else None,
                    "engagement_rate": round(
                        (post.likes + post.comments) / profile.followers, 4
                    ) if profile.followers > 0 else 0,
                })
        except instaloader.exceptions.ConnectionException as e:
            profile_data["scrape_warning"] = f"Partial data: {str(e)}"

    profile_data["posts"] = posts
    profile_data["scraped_at"] = datetime.now().isoformat()
    return profile_data


def save_to_db(handle, data):
    """Save scraped data into the Wavecrest database."""
    if "error" in data:
        return data

    # Find the competitor in the database
    competitors = execute_query(
        "SELECT id FROM competitors WHERE handle = ?", [handle]
    )
    if not competitors:
        return {"error": f"Competitor @{handle} not found in database. Add them first."}

    comp_id = competitors[0]["id"]

    # Save/update snapshot
    today = datetime.now().strftime("%Y-%m-%d")
    existing_snap = execute_query(
        "SELECT id FROM competitor_snapshots WHERE competitor_id = ? AND snapshot_date = ?",
        [comp_id, today],
    )

    if existing_snap:
        # Update existing snapshot
        from db_helpers import update_row
        update_row("competitor_snapshots", existing_snap[0]["id"], {
            "followers": data.get("followers"),
            "following": data.get("following"),
            "total_posts": data.get("total_posts"),
            "bio": data.get("bio"),
        })
    else:
        insert_row("competitor_snapshots", {
            "competitor_id": comp_id,
            "snapshot_date": today,
            "followers": data.get("followers"),
            "following": data.get("following"),
            "total_posts": data.get("total_posts"),
            "bio": data.get("bio"),
        })

    # Save posts (skip duplicates by checking shortcode in post_url)
    posts_added = 0
    for post in data.get("posts", []):
        existing_post = execute_query(
            "SELECT id FROM competitor_posts WHERE competitor_id = ? AND post_url = ?",
            [comp_id, post["post_url"]],
        )
        if not existing_post:
            insert_row("competitor_posts", {
                "competitor_id": comp_id,
                "post_url": post["post_url"],
                "posted_at": post["posted_at"],
                "content_type": post["content_type"],
                "caption_snippet": post.get("caption_snippet"),
                "likes": post["likes"],
                "comments": post["comments"],
                "estimated_engagement_rate": post.get("engagement_rate"),
            })
            posts_added += 1

    return {
        "success": True,
        "handle": handle,
        "followers": data.get("followers"),
        "posts_scraped": len(data.get("posts", [])),
        "posts_added": posts_added,
        "posts_skipped_duplicates": len(data.get("posts", [])) - posts_added,
    }


def scan_all(max_posts=10):
    """Scrape all tracked competitors."""
    competitors = execute_query("SELECT handle FROM competitors ORDER BY name")
    results = []

    for comp in competitors:
        handle = comp["handle"]
        print(f"Scraping @{handle}...", file=sys.stderr)
        data = scrape_profile(handle, max_posts=max_posts)
        result = save_to_db(handle, data)
        results.append(result)
        print(f"  -> {result.get('posts_added', 0)} new posts", file=sys.stderr)

    return {
        "success": True,
        "competitors_scanned": len(results),
        "results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wavecrest Instagram Scraper")
    parser.add_argument("--profile", type=str, help="Instagram handle to scrape")
    parser.add_argument("--posts", type=int, default=10, help="Max posts to fetch (default 10)")
    parser.add_argument("--scan", action="store_true", help="Scrape all tracked competitors")
    parser.add_argument("--save", action="store_true", help="Save results to database")

    args = parser.parse_args()

    if args.profile:
        data = scrape_profile(args.profile, max_posts=args.posts)

        if args.save:
            result = save_to_db(args.profile, data)
            print(json.dumps(result, indent=2, default=str))
        else:
            print(json.dumps(data, indent=2, default=str))

    elif args.scan:
        result = scan_all(max_posts=args.posts)
        print(json.dumps(result, indent=2, default=str))

    else:
        parser.print_help()
