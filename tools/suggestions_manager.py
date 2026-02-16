"""
Manage Wavecrest content suggestions.

Usage:
    python tools/suggestions_manager.py add --title "Beach content series" \
        --description "5-part meditation series at local beaches" \
        --submitted-by "Sarah" --priority high --link "https://example.com"
    python tools/suggestions_manager.py list [--priority high] [--submitted-by "Sarah"]
    python tools/suggestions_manager.py view --id 5
    python tools/suggestions_manager.py delete --id 5

Outputs JSON to stdout by default. Use --pretty for formatted output.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import insert_row, delete_row, execute_query

VALID_PRIORITIES = ["low", "medium", "high"]

UPLOADS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "uploads", "suggestions"
)


def add_suggestion(args):
    """Add a new content suggestion."""
    data = {
        "title": args.title,
        "description": args.description or None,
        "submitted_by": args.submitted_by,
        "priority": args.priority or "medium",
        "link_url": args.link or None,
    }

    row_id = insert_row("content_suggestions", data)
    result = execute_query("SELECT * FROM content_suggestions WHERE id = ?", [row_id])
    print(json.dumps(result[0], indent=2, default=str))


def list_suggestions(args):
    """List suggestions with optional filters."""
    sql = "SELECT * FROM content_suggestions WHERE 1=1"
    params = []

    if args.priority:
        sql += " AND priority = ?"
        params.append(args.priority)
    if args.submitted_by:
        sql += " AND submitted_by LIKE ?"
        params.append(f"%{args.submitted_by}%")

    sql += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END, created_at DESC"
    rows = execute_query(sql, params)

    if args.pretty:
        if not rows:
            print("No suggestions found.")
            return
        print(f"\n{'ID':<5} {'Priority':<9} {'Submitted By':<15} {'Title'}")
        print("-" * 70)
        for r in rows:
            title_preview = r["title"][:40]
            print(f"{r['id']:<5} {r['priority']:<9} {r['submitted_by']:<15} {title_preview}")
        print(f"\nTotal: {len(rows)} suggestions")
    else:
        print(json.dumps(rows, indent=2, default=str))


def view_suggestion(args):
    """View a single suggestion with its images."""
    result = execute_query("SELECT * FROM content_suggestions WHERE id = ?", [args.id])
    if not result:
        print(json.dumps({"error": f"Suggestion {args.id} not found"}))
        return

    suggestion = result[0]
    images = execute_query(
        "SELECT * FROM suggestion_images WHERE suggestion_id = ?", [args.id]
    )
    suggestion["images"] = images
    print(json.dumps(suggestion, indent=2, default=str))


def delete_suggestion(args):
    """Delete a suggestion and its associated image files."""
    # Find and remove image files from disk
    images = execute_query(
        "SELECT file_path FROM suggestion_images WHERE suggestion_id = ?", [args.id]
    )
    for img in images:
        try:
            if os.path.exists(img["file_path"]):
                os.remove(img["file_path"])
        except OSError:
            pass

    success = delete_row("content_suggestions", args.id)
    print(json.dumps({"deleted": success, "id": args.id, "images_removed": len(images)}))


def main():
    parser = argparse.ArgumentParser(description="Wavecrest Content Suggestions Manager")
    parser.add_argument("--pretty", action="store_true", help="Human-readable output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add
    add_p = subparsers.add_parser("add", help="Add a suggestion")
    add_p.add_argument("--title", required=True, help="Suggestion title")
    add_p.add_argument("--description", help="Detailed description")
    add_p.add_argument("--submitted-by", required=True, help="Team member name")
    add_p.add_argument("--priority", choices=VALID_PRIORITIES, default="medium")
    add_p.add_argument("--link", help="Reference URL")

    # List
    list_p = subparsers.add_parser("list", help="List suggestions")
    list_p.add_argument("--priority", choices=VALID_PRIORITIES)
    list_p.add_argument("--submitted-by", help="Filter by submitter (partial match)")

    # View
    view_p = subparsers.add_parser("view", help="View a suggestion with images")
    view_p.add_argument("--id", type=int, required=True)

    # Delete
    del_p = subparsers.add_parser("delete", help="Delete a suggestion and its images")
    del_p.add_argument("--id", type=int, required=True)

    args = parser.parse_args()

    commands = {
        "add": add_suggestion,
        "list": list_suggestions,
        "view": view_suggestion,
        "delete": delete_suggestion,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
