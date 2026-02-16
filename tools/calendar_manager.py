"""
Manage the Wavecrest content calendar.

Usage:
    python tools/calendar_manager.py add --date 2026-03-05 --platform both \
        --type still_image --pillar Education --caption "Your mental health matters."
    python tools/calendar_manager.py list --month 2026-03
    python tools/calendar_manager.py update --id 42 --status published
    python tools/calendar_manager.py delete --id 42
    python tools/calendar_manager.py summary --month 2026-03

Outputs JSON to stdout by default. Use --pretty for formatted tables.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import get_connection, insert_row, update_row, delete_row, execute_query

VALID_PLATFORMS = ["instagram", "facebook", "both"]
VALID_CONTENT_TYPES = ["still_image", "ugc_video", "therapist_video", "carousel", "story", "reel"]
VALID_STATUSES = ["planned", "created", "reviewed", "scheduled", "published"]


def get_pillar_id(name):
    """Look up a content pillar by name (case-insensitive)."""
    rows = execute_query("SELECT id FROM content_pillars WHERE LOWER(name) = LOWER(?)", [name])
    return rows[0]["id"] if rows else None


def add_entry(args):
    """Add a new calendar entry."""
    pillar_id = None
    if args.pillar:
        pillar_id = get_pillar_id(args.pillar)
        if pillar_id is None:
            print(json.dumps({"error": f"Unknown pillar: {args.pillar}"}))
            return

    data = {
        "scheduled_date": args.date,
        "platform": args.platform,
        "content_type": args.type,
        "pillar_id": pillar_id,
        "caption": args.caption,
        "hashtags": args.hashtags,
        "status": args.status or "planned",
        "notes": args.notes,
    }
    if args.time:
        data["scheduled_time"] = args.time
    if args.script_id:
        data["script_id"] = args.script_id
    if args.media_path:
        data["media_path"] = args.media_path

    row_id = insert_row("content_calendar", data)
    result = execute_query("SELECT * FROM content_calendar WHERE id = ?", [row_id])
    print(json.dumps(result[0], indent=2, default=str))


def list_entries(args):
    """List calendar entries, optionally filtered."""
    sql = """
        SELECT cc.*, cp.name as pillar_name, cp.color_hex as pillar_color
        FROM content_calendar cc
        LEFT JOIN content_pillars cp ON cc.pillar_id = cp.id
        WHERE 1=1
    """
    params = []

    if args.month:
        sql += " AND strftime('%Y-%m', cc.scheduled_date) = ?"
        params.append(args.month)
    if args.platform:
        sql += " AND cc.platform = ?"
        params.append(args.platform)
    if args.type:
        sql += " AND cc.content_type = ?"
        params.append(args.type)
    if args.status:
        sql += " AND cc.status = ?"
        params.append(args.status)

    sql += " ORDER BY cc.scheduled_date, cc.scheduled_time"
    rows = execute_query(sql, params)

    if args.pretty:
        if not rows:
            print("No calendar entries found.")
            return
        print(f"\n{'Date':<12} {'Time':<6} {'Platform':<10} {'Type':<16} {'Pillar':<18} {'Status':<10} {'Caption'}")
        print("-" * 100)
        for r in rows:
            caption_preview = (r["caption"] or "")[:40]
            print(f"{r['scheduled_date']:<12} {(r['scheduled_time'] or '--'):<6} {r['platform']:<10} {r['content_type']:<16} {(r['pillar_name'] or '--'):<18} {r['status']:<10} {caption_preview}")
        print(f"\nTotal: {len(rows)} entries")
    else:
        print(json.dumps(rows, indent=2, default=str))


def update_entry(args):
    """Update fields on an existing calendar entry."""
    data = {}
    if args.date:
        data["scheduled_date"] = args.date
    if args.time:
        data["scheduled_time"] = args.time
    if args.platform:
        data["platform"] = args.platform
    if args.type:
        data["content_type"] = args.type
    if args.pillar:
        pillar_id = get_pillar_id(args.pillar)
        if pillar_id is None:
            print(json.dumps({"error": f"Unknown pillar: {args.pillar}"}))
            return
        data["pillar_id"] = pillar_id
    if args.caption:
        data["caption"] = args.caption
    if args.hashtags:
        data["hashtags"] = args.hashtags
    if args.status:
        data["status"] = args.status
    if args.notes:
        data["notes"] = args.notes
    if args.script_id:
        data["script_id"] = args.script_id
    if args.media_path:
        data["media_path"] = args.media_path

    if not data:
        print(json.dumps({"error": "No fields to update"}))
        return

    success = update_row("content_calendar", args.id, data)
    if success:
        result = execute_query("SELECT * FROM content_calendar WHERE id = ?", [args.id])
        print(json.dumps(result[0], indent=2, default=str))
    else:
        print(json.dumps({"error": f"Entry {args.id} not found"}))


def delete_entry(args):
    """Delete a calendar entry."""
    success = delete_row("content_calendar", args.id)
    print(json.dumps({"deleted": success, "id": args.id}))


def summary(args):
    """Show content mix summary for a month."""
    month = args.month
    rows = execute_query("""
        SELECT
            COUNT(*) as total_posts,
            COUNT(CASE WHEN platform = 'instagram' OR platform = 'both' THEN 1 END) as instagram_posts,
            COUNT(CASE WHEN platform = 'facebook' OR platform = 'both' THEN 1 END) as facebook_posts
        FROM content_calendar
        WHERE strftime('%Y-%m', scheduled_date) = ?
    """, [month])

    by_type = execute_query("""
        SELECT content_type, COUNT(*) as count
        FROM content_calendar
        WHERE strftime('%Y-%m', scheduled_date) = ?
        GROUP BY content_type ORDER BY count DESC
    """, [month])

    by_pillar = execute_query("""
        SELECT cp.name as pillar, COUNT(*) as count
        FROM content_calendar cc
        LEFT JOIN content_pillars cp ON cc.pillar_id = cp.id
        WHERE strftime('%Y-%m', cc.scheduled_date) = ?
        GROUP BY cp.name ORDER BY count DESC
    """, [month])

    by_status = execute_query("""
        SELECT status, COUNT(*) as count
        FROM content_calendar
        WHERE strftime('%Y-%m', scheduled_date) = ?
        GROUP BY status ORDER BY count DESC
    """, [month])

    result = {
        "month": month,
        "totals": rows[0] if rows else {},
        "by_content_type": by_type,
        "by_pillar": by_pillar,
        "by_status": by_status,
    }

    if args.pretty:
        t = result["totals"]
        print(f"\n=== Content Calendar Summary: {month} ===")
        print(f"Total posts: {t.get('total_posts', 0)}")
        print(f"Instagram: {t.get('instagram_posts', 0)} | Facebook: {t.get('facebook_posts', 0)}")
        print(f"\nBy content type:")
        for r in by_type:
            print(f"  {r['content_type']}: {r['count']}")
        print(f"\nBy pillar:")
        for r in by_pillar:
            print(f"  {r['pillar'] or 'Unassigned'}: {r['count']}")
        print(f"\nBy status:")
        for r in by_status:
            print(f"  {r['status']}: {r['count']}")
    else:
        print(json.dumps(result, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Wavecrest Content Calendar Manager")
    parser.add_argument("--pretty", action="store_true", help="Human-readable output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add
    add_p = subparsers.add_parser("add", help="Add a calendar entry")
    add_p.add_argument("--date", required=True, help="Scheduled date (YYYY-MM-DD)")
    add_p.add_argument("--time", help="Scheduled time (HH:MM)")
    add_p.add_argument("--platform", required=True, choices=VALID_PLATFORMS)
    add_p.add_argument("--type", required=True, choices=VALID_CONTENT_TYPES)
    add_p.add_argument("--pillar", help="Content pillar name")
    add_p.add_argument("--caption", help="Post caption")
    add_p.add_argument("--hashtags", help="Hashtags")
    add_p.add_argument("--status", choices=VALID_STATUSES, default="planned")
    add_p.add_argument("--script-id", type=int, help="Associated script ID")
    add_p.add_argument("--media-path", help="Path to media file")
    add_p.add_argument("--notes", help="Notes")

    # List
    list_p = subparsers.add_parser("list", help="List calendar entries")
    list_p.add_argument("--month", help="Filter by month (YYYY-MM)")
    list_p.add_argument("--platform", choices=VALID_PLATFORMS)
    list_p.add_argument("--type", choices=VALID_CONTENT_TYPES)
    list_p.add_argument("--status", choices=VALID_STATUSES)

    # Update
    update_p = subparsers.add_parser("update", help="Update a calendar entry")
    update_p.add_argument("--id", type=int, required=True, help="Entry ID")
    update_p.add_argument("--date", help="New date")
    update_p.add_argument("--time", help="New time")
    update_p.add_argument("--platform", choices=VALID_PLATFORMS)
    update_p.add_argument("--type", choices=VALID_CONTENT_TYPES)
    update_p.add_argument("--pillar", help="New pillar name")
    update_p.add_argument("--caption", help="New caption")
    update_p.add_argument("--hashtags", help="New hashtags")
    update_p.add_argument("--status", choices=VALID_STATUSES)
    update_p.add_argument("--script-id", type=int)
    update_p.add_argument("--media-path")
    update_p.add_argument("--notes")

    # Delete
    del_p = subparsers.add_parser("delete", help="Delete a calendar entry")
    del_p.add_argument("--id", type=int, required=True)

    # Summary
    sum_p = subparsers.add_parser("summary", help="Month summary")
    sum_p.add_argument("--month", required=True, help="Month (YYYY-MM)")

    args = parser.parse_args()

    commands = {
        "add": add_entry,
        "list": list_entries,
        "update": update_entry,
        "delete": delete_entry,
        "summary": summary,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
