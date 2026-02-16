"""
Manage therapist and UGC scripts for Wavecrest social media.

Usage:
    python tools/scripts_manager.py add --title "Anxiety Tips" --body "..." \
        --type therapist --pillar Education --session-date 2026-02-01
    python tools/scripts_manager.py list --status draft --type therapist
    python tools/scripts_manager.py update --id 7 --status selected
    python tools/scripts_manager.py archive --older-than 90
    python tools/scripts_manager.py search --keyword "anxiety"

Outputs JSON to stdout by default. Use --pretty for formatted output.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import insert_row, update_row, delete_row, execute_query

VALID_TYPES = ["influencer_reels", "ad_reels", "voiceover_reels", "therapist_scripts", "carousel_posts"]
VALID_STATUSES = ["backlog", "todo", "completed"]


def get_pillar_id(name):
    rows = execute_query("SELECT id FROM content_pillars WHERE LOWER(name) = LOWER(?)", [name])
    return rows[0]["id"] if rows else None


def add_script(args):
    """Add a new script."""
    pillar_id = None
    if args.pillar:
        pillar_id = get_pillar_id(args.pillar)
        if pillar_id is None:
            print(json.dumps({"error": f"Unknown pillar: {args.pillar}"}))
            return

    data = {
        "title": args.title,
        "body": args.body,
        "script_type": args.type,
        "pillar_id": pillar_id,
        "status": "draft",
        "notes": args.notes,
    }
    if args.session_date:
        data["source_session_date"] = args.session_date

    row_id = insert_row("scripts", data)
    result = execute_query("""
        SELECT s.*, cp.name as pillar_name
        FROM scripts s LEFT JOIN content_pillars cp ON s.pillar_id = cp.id
        WHERE s.id = ?
    """, [row_id])
    print(json.dumps(result[0], indent=2, default=str))


def list_scripts(args):
    """List scripts with optional filters."""
    sql = """
        SELECT s.*, cp.name as pillar_name
        FROM scripts s
        LEFT JOIN content_pillars cp ON s.pillar_id = cp.id
        WHERE 1=1
    """
    params = []

    if args.type:
        sql += " AND s.script_type = ?"
        params.append(args.type)
    if args.status:
        sql += " AND s.status = ?"
        params.append(args.status)
    if args.pillar:
        pillar_id = get_pillar_id(args.pillar)
        if pillar_id:
            sql += " AND s.pillar_id = ?"
            params.append(pillar_id)

    sql += " ORDER BY s.created_at DESC"
    rows = execute_query(sql, params)

    if args.pretty:
        if not rows:
            print("No scripts found.")
            return
        print(f"\n{'ID':<5} {'Type':<10} {'Status':<10} {'Pillar':<18} {'Title':<40} {'Session Date'}")
        print("-" * 100)
        for r in rows:
            print(f"{r['id']:<5} {r['script_type']:<10} {r['status']:<10} {(r['pillar_name'] or '--'):<18} {r['title'][:38]:<40} {r['source_session_date'] or '--'}")
        print(f"\nTotal: {len(rows)} scripts")
    else:
        print(json.dumps(rows, indent=2, default=str))


def view_script(args):
    """View a single script with full body."""
    rows = execute_query("""
        SELECT s.*, cp.name as pillar_name
        FROM scripts s LEFT JOIN content_pillars cp ON s.pillar_id = cp.id
        WHERE s.id = ?
    """, [args.id])

    if not rows:
        print(json.dumps({"error": f"Script {args.id} not found"}))
        return

    if args.pretty:
        r = rows[0]
        print(f"\n=== Script #{r['id']}: {r['title']} ===")
        print(f"Type: {r['script_type']} | Status: {r['status']} | Pillar: {r['pillar_name'] or 'None'}")
        print(f"Session Date: {r['source_session_date'] or 'N/A'}")
        print(f"Created: {r['created_at']}")
        if r["notes"]:
            print(f"Notes: {r['notes']}")
        print(f"\n--- Script Body ---\n{r['body']}\n")
    else:
        print(json.dumps(rows[0], indent=2, default=str))


def update_script(args):
    """Update fields on an existing script."""
    data = {}
    if args.title:
        data["title"] = args.title
    if args.body:
        data["body"] = args.body
    if args.type:
        data["script_type"] = args.type
    if args.pillar:
        pillar_id = get_pillar_id(args.pillar)
        if pillar_id is None:
            print(json.dumps({"error": f"Unknown pillar: {args.pillar}"}))
            return
        data["pillar_id"] = pillar_id
    if args.status:
        data["status"] = args.status
    if args.notes:
        data["notes"] = args.notes

    if not data:
        print(json.dumps({"error": "No fields to update"}))
        return

    success = update_row("scripts", args.id, data)
    if success:
        result = execute_query("SELECT * FROM scripts WHERE id = ?", [args.id])
        print(json.dumps(result[0], indent=2, default=str))
    else:
        print(json.dumps({"error": f"Script {args.id} not found"}))


def delete_script(args):
    """Delete a script."""
    success = delete_row("scripts", args.id)
    print(json.dumps({"deleted": success, "id": args.id}))


def archive_old(args):
    """Archive scripts older than N days that are still in draft status."""
    result = execute_query("""
        UPDATE scripts SET status = 'archived', updated_at = CURRENT_TIMESTAMP
        WHERE status = 'draft'
        AND julianday('now') - julianday(created_at) > ?
    """, [args.older_than])
    # Count isn't directly available from execute_query for UPDATE, re-query
    archived = execute_query("""
        SELECT COUNT(*) as count FROM scripts
        WHERE status = 'archived'
        AND julianday('now') - julianday(updated_at) < 1
    """)
    print(json.dumps({"archived_count": archived[0]["count"] if archived else 0}))


def search_scripts(args):
    """Search scripts by keyword in title or body."""
    rows = execute_query("""
        SELECT s.*, cp.name as pillar_name
        FROM scripts s
        LEFT JOIN content_pillars cp ON s.pillar_id = cp.id
        WHERE (s.title LIKE ? OR s.body LIKE ?)
        ORDER BY s.created_at DESC
    """, [f"%{args.keyword}%", f"%{args.keyword}%"])

    if args.pretty:
        if not rows:
            print(f"No scripts matching '{args.keyword}'.")
            return
        print(f"\n{'ID':<5} {'Type':<10} {'Status':<10} {'Pillar':<18} {'Title'}")
        print("-" * 70)
        for r in rows:
            print(f"{r['id']:<5} {r['script_type']:<10} {r['status']:<10} {(r['pillar_name'] or '--'):<18} {r['title'][:38]}")
        print(f"\nFound: {len(rows)} scripts matching '{args.keyword}'")
    else:
        print(json.dumps(rows, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Wavecrest Scripts Manager")
    parser.add_argument("--pretty", action="store_true", help="Human-readable output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add
    add_p = subparsers.add_parser("add", help="Add a script")
    add_p.add_argument("--title", required=True)
    add_p.add_argument("--body", required=True, help="Full script text")
    add_p.add_argument("--type", required=True, choices=VALID_TYPES)
    add_p.add_argument("--pillar", help="Content pillar name")
    add_p.add_argument("--session-date", help="Source session date (YYYY-MM-DD)")
    add_p.add_argument("--notes")

    # List
    list_p = subparsers.add_parser("list", help="List scripts")
    list_p.add_argument("--type", choices=VALID_TYPES)
    list_p.add_argument("--status", choices=VALID_STATUSES)
    list_p.add_argument("--pillar")

    # View
    view_p = subparsers.add_parser("view", help="View a single script")
    view_p.add_argument("--id", type=int, required=True)

    # Update
    update_p = subparsers.add_parser("update", help="Update a script")
    update_p.add_argument("--id", type=int, required=True)
    update_p.add_argument("--title")
    update_p.add_argument("--body")
    update_p.add_argument("--type", choices=VALID_TYPES)
    update_p.add_argument("--pillar")
    update_p.add_argument("--status", choices=VALID_STATUSES)
    update_p.add_argument("--notes")

    # Delete
    del_p = subparsers.add_parser("delete", help="Delete a script")
    del_p.add_argument("--id", type=int, required=True)

    # Archive
    arch_p = subparsers.add_parser("archive", help="Archive old draft scripts")
    arch_p.add_argument("--older-than", type=int, required=True, help="Days threshold")

    # Search
    search_p = subparsers.add_parser("search", help="Search scripts by keyword")
    search_p.add_argument("--keyword", required=True)

    args = parser.parse_args()

    commands = {
        "add": add_script,
        "list": list_scripts,
        "view": view_script,
        "update": update_script,
        "delete": delete_script,
        "archive": archive_old,
        "search": search_scripts,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
