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


def log(msg):
    print(msg, flush=True)


def seed_scripts():
    """Load scripts from seed file if table is empty."""
    try:
        count = execute_query("SELECT COUNT(*) as count FROM scripts")[0]["count"]
        if count > 0:
            log(f"Scripts table already has {count} rows, skipping seed.")
            return

        seed_file = os.path.join(SEED_DIR, "seed_scripts.json")
        if not os.path.exists(seed_file):
            log(f"No seed_scripts.json found at {seed_file}, skipping.")
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

        log(f"Seeded {len(scripts)} scripts.")
    except Exception as e:
        log(f"Seed error: {e}")


if __name__ == "__main__":
    seed_scripts()
