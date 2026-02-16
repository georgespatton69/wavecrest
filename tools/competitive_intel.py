"""
Competitive Intelligence Tool for Wavecrest.
Track competitor activities across Instagram and Facebook.

Usage:
    python tools/competitive_intel.py --list
    python tools/competitive_intel.py --add "Name" --handle "handle" --platform instagram
    python tools/competitive_intel.py --demo
    python tools/competitive_intel.py --summary

Outputs JSON to stdout by default. Use --pretty for formatted output.
"""

import argparse
import json
import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import execute_query, insert_row, update_row, delete_row


def list_competitors():
    """List all tracked competitors."""
    return execute_query("SELECT * FROM competitors ORDER BY name")


def add_competitor(name, handle, platform="instagram", profile_url=None, notes=None):
    """Add a competitor to track."""
    data = {
        "name": name,
        "handle": handle,
        "platform": platform,
    }
    if profile_url:
        data["profile_url"] = profile_url
    if notes:
        data["notes"] = notes

    row_id = insert_row("competitors", data)
    return execute_query("SELECT * FROM competitors WHERE id = ?", [row_id])[0]


def remove_competitor(competitor_id):
    """Remove a competitor."""
    return delete_row("competitors", competitor_id)


def log_post(competitor_id, post_url=None, posted_at=None, content_type="image",
             caption_snippet=None, likes=0, comments=0, engagement_rate=None,
             content_theme=None, notes=None):
    """Log a notable competitor post."""
    data = {
        "competitor_id": competitor_id,
        "post_url": post_url,
        "posted_at": posted_at or datetime.now().isoformat(),
        "content_type": content_type,
        "caption_snippet": caption_snippet,
        "likes": likes,
        "comments": comments,
        "estimated_engagement_rate": engagement_rate,
        "content_theme": content_theme,
        "notes": notes,
    }
    return insert_row("competitor_posts", data)


def log_snapshot(competitor_id, followers=None, following=None,
                 total_posts=None, bio=None, snapshot_date=None):
    """Log a competitor account snapshot."""
    data = {
        "competitor_id": competitor_id,
        "snapshot_date": snapshot_date or datetime.now().strftime("%Y-%m-%d"),
        "followers": followers,
        "following": following,
        "total_posts": total_posts,
        "bio": bio,
    }
    return insert_row("competitor_snapshots", data)


def load_demo_data():
    """Load realistic demo data for behavioral health competitors on Instagram/Facebook."""
    # Ensure default competitors exist
    existing = execute_query("SELECT * FROM competitors")
    existing_names = {c["name"] for c in existing}

    competitors_data = [
        {
            "name": "Charlie Health",
            "handle": "charliehealth",
            "platform": "instagram",
            "profile_url": "https://www.instagram.com/charliehealth/",
            "notes": "Virtual mental health treatment for teens and young adults. Major national brand."
        },
        {
            "name": "Novara Recovery Center",
            "handle": "novararecoverycenter",
            "platform": "instagram",
            "profile_url": "https://www.instagram.com/novararecoverycenter/",
            "notes": "Local SoCal recovery center. Direct competitor in the behavioral health space."
        },
        {
            "name": "Heading Health",
            "handle": "headinghealth",
            "platform": "instagram",
            "profile_url": "https://www.instagram.com/headinghealth/",
            "notes": "Mental health treatment center. Strong social media presence with educational content."
        },
        {
            "name": "Innerwell",
            "handle": "innerwell",
            "platform": "instagram",
            "profile_url": "https://www.instagram.com/innerwell/",
            "notes": "Virtual mental health platform. Clean, modern branding."
        },
    ]

    comp_ids = {}
    for c in competitors_data:
        if c["name"] not in existing_names:
            row_id = insert_row("competitors", c)
            comp_ids[c["name"]] = row_id
        else:
            match = next(e for e in existing if e["name"] == c["name"])
            comp_ids[c["name"]] = match["id"]

    # Sample Instagram post captions
    ig_captions = [
        "Recovery isn't linear, and that's okay. Every step forward counts.",
        "Meet our team! Our therapists bring decades of combined experience.",
        "5 signs you might benefit from an IOP program (swipe to learn more)",
        "Client spotlight: 'Finding Wavecrest changed my life' - testimonial",
        "Mental health tip: grounding techniques for anxiety (save this!)",
        "We're proud to serve the SoCal community. Here's what makes us different.",
        "New blog post: Understanding the difference between IOP and PHP",
        "Behind the scenes at our facility - take a virtual tour!",
        "Self-care Sunday: 3 mindfulness exercises you can do right now",
        "Celebrating our team's dedication to client-centered care",
        "Did you know? Virtual IOP can be just as effective as in-person.",
        "Breaking the stigma: why asking for help is a sign of strength",
        "Our holistic approach includes yoga, meditation, and evidence-based therapy",
        "Happy holidays from our family to yours. You're not alone.",
        "FAQ: What to expect during your first week in our program",
    ]

    content_themes = [
        "education", "community", "client_stories", "treatment_info",
        "affirming_messages", "team_spotlight", "tips", "awareness",
    ]

    content_types = ["image", "carousel", "reel", "video", "story"]

    end_date = datetime.now()
    posts_added = 0
    snapshots_added = 0

    for comp_name, comp_id in comp_ids.items():
        # Generate 6-12 posts over past 30 days
        num_posts = random.randint(6, 12)
        for _ in range(num_posts):
            days_ago = random.randint(0, 30)
            post_date = end_date - timedelta(days=days_ago)
            ctype = random.choice(content_types)
            likes = random.randint(15, 800)
            comments = random.randint(0, int(likes * 0.15))
            followers_est = random.randint(2000, 50000)
            engagement = (likes + comments) / followers_est if followers_est else 0

            log_post(
                competitor_id=comp_id,
                posted_at=post_date.isoformat(),
                content_type=ctype,
                caption_snippet=random.choice(ig_captions),
                likes=likes,
                comments=comments,
                engagement_rate=round(engagement, 4),
                content_theme=random.choice(content_themes),
                notes=None,
            )
            posts_added += 1

        # Generate weekly snapshots for past 4 weeks
        for weeks_ago in range(4):
            snap_date = (end_date - timedelta(weeks=weeks_ago)).strftime("%Y-%m-%d")
            base_followers = random.randint(2000, 45000)
            growth = weeks_ago * random.randint(-50, 200)

            try:
                log_snapshot(
                    competitor_id=comp_id,
                    followers=base_followers - growth,
                    following=random.randint(200, 1500),
                    total_posts=random.randint(100, 800),
                    snapshot_date=snap_date,
                )
                snapshots_added += 1
            except Exception:
                pass  # UNIQUE constraint if snapshot already exists for that date

    return {
        "success": True,
        "message": f"Loaded {len(comp_ids)} competitors, {posts_added} posts, {snapshots_added} snapshots",
    }


def get_summary():
    """Get summary of competitive intelligence data."""
    competitors = list_competitors()
    total_posts = execute_query("SELECT COUNT(*) as count FROM competitor_posts")[0]["count"]

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    recent_posts = execute_query(
        "SELECT COUNT(*) as count FROM competitor_posts WHERE posted_at >= ?",
        [seven_days_ago]
    )[0]["count"]

    return {
        "competitors_tracked": len(competitors),
        "total_posts": total_posts,
        "recent_posts_7d": recent_posts,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wavecrest Competitive Intelligence")
    parser.add_argument("--pretty", action="store_true", help="Human-readable output")
    parser.add_argument("--list", action="store_true", help="List tracked competitors")
    parser.add_argument("--add", type=str, help="Add a competitor by name")
    parser.add_argument("--handle", type=str, help="Social media handle")
    parser.add_argument("--platform", type=str, default="instagram", choices=["instagram", "facebook", "both"])
    parser.add_argument("--remove", type=int, help="Remove a competitor by ID")
    parser.add_argument("--demo", action="store_true", help="Load demo data")
    parser.add_argument("--summary", action="store_true", help="Show activity summary")

    args = parser.parse_args()

    if args.list:
        comps = list_competitors()
        print(json.dumps(comps, indent=2, default=str))

    elif args.add:
        if not args.handle:
            print(json.dumps({"error": "--handle is required when adding a competitor"}))
        else:
            result = add_competitor(args.add, args.handle, args.platform)
            print(json.dumps(result, indent=2, default=str))

    elif args.remove:
        success = remove_competitor(args.remove)
        print(json.dumps({"deleted": success, "id": args.remove}))

    elif args.demo:
        result = load_demo_data()
        print(json.dumps(result, indent=2, default=str))

    elif args.summary:
        result = get_summary()
        print(json.dumps(result, indent=2, default=str))

    else:
        parser.print_help()
