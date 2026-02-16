"""
Scripts Manager — Manage therapist interview and UGC scripts.
"""

import streamlit as st
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "dashboard"))

from db_helpers import execute_query, insert_row, update_row, delete_row
from styles.theme import COLORS, STATUS_COLORS, get_custom_css, status_badge, pillar_badge

st.set_page_config(page_title="Scripts | Wavecrest", page_icon="📝", layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)

st.markdown("## Script Manager")
st.markdown(
    f"<p style='color:{COLORS['text_secondary']}'>Manage therapist spokesperson and UGC creator scripts. "
    f"Add scripts from monthly interviews, select the best ones for your content calendar.</p>",
    unsafe_allow_html=True,
)

# Filters
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    filter_type = st.selectbox("Type", ["All", "Therapist", "UGC"])
with col_f2:
    filter_status = st.selectbox("Status", ["All", "Draft", "Selected", "Scheduled", "Used", "Archived"])
with col_f3:
    pillars = execute_query("SELECT id, name FROM content_pillars ORDER BY name")
    pillar_names = ["All"] + [p["name"] for p in pillars]
    filter_pillar = st.selectbox("Pillar", pillar_names)
with col_f4:
    search_keyword = st.text_input("Search", placeholder="Search scripts...")

# Build query
sql = """
    SELECT s.*, cp.name as pillar_name, cp.color_hex as pillar_color
    FROM scripts s
    LEFT JOIN content_pillars cp ON s.pillar_id = cp.id
    WHERE 1=1
"""
params = []

if filter_type != "All":
    sql += " AND s.script_type = ?"
    params.append(filter_type.lower())
if filter_status != "All":
    sql += " AND s.status = ?"
    params.append(filter_status.lower())
if filter_pillar != "All":
    pillar_id = next((p["id"] for p in pillars if p["name"] == filter_pillar), None)
    if pillar_id:
        sql += " AND s.pillar_id = ?"
        params.append(pillar_id)
if search_keyword:
    sql += " AND (s.title LIKE ? OR s.body LIKE ?)"
    params.extend([f"%{search_keyword}%", f"%{search_keyword}%"])

sql += " ORDER BY CASE s.status WHEN 'draft' THEN 1 WHEN 'selected' THEN 2 WHEN 'scheduled' THEN 3 WHEN 'used' THEN 4 WHEN 'archived' THEN 5 END, s.created_at DESC"

scripts = execute_query(sql, params)

# Summary
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
all_scripts = execute_query("SELECT status, COUNT(*) as count FROM scripts GROUP BY status")
status_counts = {r["status"]: r["count"] for r in all_scripts}
with col_s1:
    st.metric("Draft", status_counts.get("draft", 0))
with col_s2:
    st.metric("Selected", status_counts.get("selected", 0))
with col_s3:
    st.metric("Scheduled", status_counts.get("scheduled", 0))
with col_s4:
    st.metric("Used", status_counts.get("used", 0))

st.markdown("---")

# Script cards
if not scripts:
    st.info("No scripts found. Add scripts from your therapist interviews and UGC sessions below.")
else:
    for s in scripts:
        type_emoji = "🎤" if s["script_type"] == "therapist" else "📱"
        with st.expander(f"{type_emoji} **{s['title']}** — {s['status'].title()} — {s['pillar_name'] or 'No pillar'}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Type:** {'Therapist' if s['script_type'] == 'therapist' else 'UGC'}")
                if s["source_session_date"]:
                    st.markdown(f"**Session Date:** {s['source_session_date']}")
                st.markdown("**Script:**")
                st.text_area("", value=s["body"], height=150, disabled=True, key=f"body_{s['id']}", label_visibility="collapsed")
                if s["notes"]:
                    st.markdown(f"**Notes:** {s['notes']}")

            with col2:
                st.markdown(f"**Status:** {s['status'].title()}")
                st.markdown(f"**ID:** {s['id']}")
                st.markdown(f"**Created:** {s['created_at'][:10]}")

                # Quick status actions
                st.markdown("**Quick Actions:**")
                status_flow = {
                    "draft": "selected",
                    "selected": "scheduled",
                    "scheduled": "used",
                }
                next_status = status_flow.get(s["status"])
                if next_status:
                    if st.button(f"Move to {next_status.title()}", key=f"advance_{s['id']}"):
                        update_row("scripts", s["id"], {"status": next_status})
                        st.rerun()

                if s["status"] != "archived":
                    if st.button("Archive", key=f"archive_{s['id']}"):
                        update_row("scripts", s["id"], {"status": "archived"})
                        st.rerun()

# Add new script form
st.markdown("---")
st.markdown("### Add New Script")

with st.form("add_script", clear_on_submit=True):
    fc1, fc2 = st.columns(2)
    with fc1:
        new_title = st.text_input("Title", placeholder="e.g., Anxiety Coping Techniques")
        new_type = st.selectbox("Script Type", ["therapist", "ugc"],
                                 format_func=lambda x: "Therapist" if x == "therapist" else "UGC")
    with fc2:
        pillar_options = {p["name"]: p["id"] for p in pillars}
        new_pillar = st.selectbox("Pillar", ["None"] + list(pillar_options.keys()), key="new_script_pillar")
        new_session_date = st.date_input("Session Date (optional)", value=None)

    new_body = st.text_area("Script Body", height=200,
                             placeholder="Write or paste the full script here...")
    new_notes = st.text_input("Notes (optional)")

    if st.form_submit_button("Add Script"):
        if new_title and new_body:
            data = {
                "title": new_title,
                "body": new_body,
                "script_type": new_type,
                "status": "draft",
                "notes": new_notes or None,
            }
            if new_pillar != "None":
                data["pillar_id"] = pillar_options[new_pillar]
            if new_session_date:
                data["source_session_date"] = new_session_date.isoformat()

            insert_row("scripts", data)
            st.success(f"Script '{new_title}' added as draft!")
            st.rerun()
        else:
            st.error("Title and script body are required.")
