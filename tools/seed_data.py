"""
Seed the database with initial scripts data.
Only inserts if the scripts table is empty (safe to run multiple times).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import execute_query, insert_row

SEED_DIR = os.path.dirname(os.path.abspath(__file__))


def seed_scripts():
    """Load scripts from seed file if table is empty."""
    count = execute_query("SELECT COUNT(*) as count FROM scripts")[0]["count"]
    if count > 0:
        print(f"Scripts table already has {count} rows, skipping seed.")
        return

    seed_file = os.path.join(SEED_DIR, "seed_scripts.json")
    if not os.path.exists(seed_file):
        print("No seed_scripts.json found, skipping.")
        return

    with open(seed_file) as f:
        scripts = json.load(f)

    for s in scripts:
        insert_row("scripts", {
            "title": s["title"],
            "body": s["body"],
            "script_type": s["script_type"],
            "status": s["status"],
            "notes": s.get("notes"),
            "pillar_id": s.get("pillar_id"),
        })

    print(f"Seeded {len(scripts)} scripts.")


if __name__ == "__main__":
    seed_scripts()
