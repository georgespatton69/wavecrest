"""
Manage the Wavecrest content idea bank.

Usage:
    python tools/ideas_manager.py add --idea "5 signs you need a mental health day" \
        --pillar Education --source "competitor:charliehealth" --priority high
    python tools/ideas_manager.py list --status new --priority high
    python tools/ideas_manager.py promote --id 12
    python tools/ideas_manager.py use --id 12
    python tools/ideas_manager.py reject --id 12

Outputs JSON to stdout by default. Use --pretty for formatted output.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import insert_row, update_row, delete_row, execute_query

VALID_PRIORITIES = ["low", "medium", "high"]
VALID_STATUSES = ["new", "developing", "used", "rejected"]


def get_pillar_id(name):
    rows = execute_query("SELECT id FROM content_pillars WHERE LOWER(name) = LOWER(?)", [name])
    return rows[0]["id"] if rows else None


def add_idea(args):
    """Add a new idea to the bank."""
    pillar_id = None
    if args.pillar:
        pillar_id = get_pillar_id(args.pillar)
        if pillar_id is None:
            print(json.dumps({"error": f"Unknown pillar: {args.pillar}"}))
            return

    data = {
        "idea": args.idea,
        "pillar_id": pillar_id,
        "priority": args.priority or "medium",
        "status": "new",
    }
    if args.content_type:
        data["content_type"] = args.content_type
    if args.source:
        data["inspiration_source"] = args.source
    if args.url:
        data["inspiration_url"] = args.url

    row_id = insert_row("idea_bank", data)
    result = execute_query("""
        SELECT ib.*, cp.name as pillar_name
        FROM idea_bank ib LEFT JOIN content_pillars cp ON ib.pillar_id = cp.id
        WHERE ib.id = ?
    """, [row_id])
    print(json.dumps(result[0], indent=2, default=str))


def list_ideas(args):
    """List ideas with optional filters."""
    sql = """
        SELECT ib.*, cp.name as pillar_name
        FROM idea_bank ib
        LEFT JOIN content_pillars cp ON ib.pillar_id = cp.id
        WHERE 1=1
    """
    params = []

    if args.status:
        sql += " AND ib.status = ?"
        params.append(args.status)
    if args.priority:
        sql += " AND ib.priority = ?"
        params.append(args.priority)
    if args.pillar:
        pillar_id = get_pillar_id(args.pillar)
        if pillar_id:
            sql += " AND ib.pillar_id = ?"
            params.append(pillar_id)
    if args.source:
        sql += " AND ib.inspiration_source LIKE ?"
        params.append(f"%{args.source}%")

    sql += " ORDER BY CASE ib.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END, ib.created_at DESC"
    rows = execute_query(sql, params)

    if args.pretty:
        if not rows:
            print("No ideas found.")
            return
        print(f"\n{'ID':<5} {'Priority':<9} {'Status':<12} {'Pillar':<18} {'Idea'}")
        print("-" * 90)
        for r in rows:
            idea_preview = r["idea"][:45]
            print(f"{r['id']:<5} {r['priority']:<9} {r['status']:<12} {(r['pillar_name'] or '--'):<18} {idea_preview}")
        print(f"\nTotal: {len(rows)} ideas")
    else:
        print(json.dumps(rows, indent=2, default=str))


def update_idea(args):
    """Update fields on an existing idea."""
    data = {}
    if args.idea:
        data["idea"] = args.idea
    if args.pillar:
        pillar_id = get_pillar_id(args.pillar)
        if pillar_id is None:
            print(json.dumps({"error": f"Unknown pillar: {args.pillar}"}))
            return
        data["pillar_id"] = pillar_id
    if args.priority:
        data["priority"] = args.priority
    if args.status:
        data["status"] = args.status
    if args.content_type:
        data["content_type"] = args.content_type
    if args.source:
        data["inspiration_source"] = args.source
    if args.url:
        data["inspiration_url"] = args.url

    if not data:
        print(json.dumps({"error": "No fields to update"}))
        return

    success = update_row("idea_bank", args.id, data)
    if success:
        result = execute_query("SELECT * FROM idea_bank WHERE id = ?", [args.id])
        print(json.dumps(result[0], indent=2, default=str))
    else:
        print(json.dumps({"error": f"Idea {args.id} not found"}))


def promote_idea(args):
    """Move an idea from 'new' to 'developing'."""
    success = update_row("idea_bank", args.id, {"status": "developing"})
    print(json.dumps({"promoted": success, "id": args.id, "new_status": "developing"}))


def use_idea(args):
    """Mark an idea as 'used'."""
    success = update_row("idea_bank", args.id, {"status": "used"})
    print(json.dumps({"used": success, "id": args.id, "new_status": "used"}))


def reject_idea(args):
    """Mark an idea as 'rejected'."""
    success = update_row("idea_bank", args.id, {"status": "rejected"})
    print(json.dumps({"rejected": success, "id": args.id, "new_status": "rejected"}))


def delete_idea(args):
    """Delete an idea."""
    success = delete_row("idea_bank", args.id)
    print(json.dumps({"deleted": success, "id": args.id}))


def main():
    parser = argparse.ArgumentParser(description="Wavecrest Idea Bank Manager")
    parser.add_argument("--pretty", action="store_true", help="Human-readable output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add
    add_p = subparsers.add_parser("add", help="Add an idea")
    add_p.add_argument("--idea", required=True, help="The content idea")
    add_p.add_argument("--pillar", help="Content pillar name")
    add_p.add_argument("--content-type", help="Suggested content format")
    add_p.add_argument("--source", help="Inspiration source (e.g., competitor:charliehealth)")
    add_p.add_argument("--url", help="Reference URL")
    add_p.add_argument("--priority", choices=VALID_PRIORITIES, default="medium")

    # List
    list_p = subparsers.add_parser("list", help="List ideas")
    list_p.add_argument("--status", choices=VALID_STATUSES)
    list_p.add_argument("--priority", choices=VALID_PRIORITIES)
    list_p.add_argument("--pillar")
    list_p.add_argument("--source", help="Filter by source (partial match)")

    # Update
    update_p = subparsers.add_parser("update", help="Update an idea")
    update_p.add_argument("--id", type=int, required=True)
    update_p.add_argument("--idea")
    update_p.add_argument("--pillar")
    update_p.add_argument("--priority", choices=VALID_PRIORITIES)
    update_p.add_argument("--status", choices=VALID_STATUSES)
    update_p.add_argument("--content-type")
    update_p.add_argument("--source")
    update_p.add_argument("--url")

    # Shortcuts
    promote_p = subparsers.add_parser("promote", help="Move idea to 'developing'")
    promote_p.add_argument("--id", type=int, required=True)

    use_p = subparsers.add_parser("use", help="Mark idea as 'used'")
    use_p.add_argument("--id", type=int, required=True)

    reject_p = subparsers.add_parser("reject", help="Mark idea as 'rejected'")
    reject_p.add_argument("--id", type=int, required=True)

    del_p = subparsers.add_parser("delete", help="Delete an idea")
    del_p.add_argument("--id", type=int, required=True)

    args = parser.parse_args()

    commands = {
        "add": add_idea,
        "list": list_ideas,
        "update": update_idea,
        "promote": promote_idea,
        "use": use_idea,
        "reject": reject_idea,
        "delete": delete_idea,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
