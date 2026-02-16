"""
Ideas — Content idea bank with kanban-style organization.
"""

import streamlit as st
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "dashboard"))

from db_helpers import execute_query, insert_row, update_row, delete_row
from styles.theme import COLORS, PILLAR_COLORS, get_custom_css

st.set_page_config(page_title="Ideas | Wavecrest", page_icon="💡", layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)

st.markdown("## Content Idea Bank")
st.markdown(
    f"<p style='color:{COLORS['text_secondary']}'>Brainstorm, organize, and track content ideas. "
    f"Move ideas through the pipeline from New to Developing to Used.</p>",
    unsafe_allow_html=True,
)

# Filters
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    pillars = execute_query("SELECT id, name FROM content_pillars ORDER BY name")
    pillar_names = ["All"] + [p["name"] for p in pillars]
    filter_pillar = st.selectbox("Pillar", pillar_names, key="idea_pillar")
with col_f2:
    filter_priority = st.selectbox("Priority", ["All", "High", "Medium", "Low"], key="idea_priority")
with col_f3:
    filter_source = st.text_input("Source filter", placeholder="e.g., competitor, trending", key="idea_source")

# Build filter clause
where = "WHERE ib.status NOT IN ('rejected')"
params = []
if filter_pillar != "All":
    pillar_id = next((p["id"] for p in pillars if p["name"] == filter_pillar), None)
    if pillar_id:
        where += " AND ib.pillar_id = ?"
        params.append(pillar_id)
if filter_priority != "All":
    where += " AND ib.priority = ?"
    params.append(filter_priority.lower())
if filter_source:
    where += " AND ib.inspiration_source LIKE ?"
    params.append(f"%{filter_source}%")

# Kanban columns
st.markdown("---")
col_new, col_dev, col_used = st.columns(3)

for col, status, header, color in [
    (col_new, "new", "New Ideas", COLORS["primary"]),
    (col_dev, "developing", "Developing", COLORS["accent"]),
    (col_used, "used", "Used", COLORS["success"]),
]:
    with col:
        st.markdown(
            f"<h4 style='color:{color}; border-bottom:3px solid {color}; padding-bottom:8px;'>{header}</h4>",
            unsafe_allow_html=True,
        )

        ideas = execute_query(f"""
            SELECT ib.*, cp.name as pillar_name, cp.color_hex as pillar_color
            FROM idea_bank ib
            LEFT JOIN content_pillars cp ON ib.pillar_id = cp.id
            {where} AND ib.status = ?
            ORDER BY CASE ib.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
                     ib.created_at DESC
        """, params + [status])

        st.caption(f"{len(ideas)} ideas")

        for idea in ideas:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(idea["priority"], "⚪")
            pillar_label = idea["pillar_name"] or "No pillar"
            pillar_color = idea.get("pillar_color") or COLORS["text_light"]

            with st.container():
                st.markdown(
                    f"""<div style="background:{COLORS['surface']}; border:1px solid {COLORS['border']};
                        border-left:4px solid {pillar_color}; border-radius:8px; padding:12px; margin-bottom:8px;">
                        <div style="font-size:0.75em; color:{COLORS['text_light']};">
                            {priority_icon} {idea['priority'].title()} &bull; {pillar_label}
                            {f" &bull; Source: {idea['inspiration_source']}" if idea.get('inspiration_source') else ""}
                        </div>
                        <div style="margin-top:6px; color:{COLORS['text_primary']};">{idea['idea']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                # Action buttons
                bcol1, bcol2, bcol3 = st.columns(3)
                if status == "new":
                    with bcol1:
                        if st.button("Develop", key=f"dev_{idea['id']}", use_container_width=True):
                            update_row("idea_bank", idea["id"], {"status": "developing"})
                            st.rerun()
                    with bcol2:
                        if st.button("Reject", key=f"rej_{idea['id']}", use_container_width=True):
                            update_row("idea_bank", idea["id"], {"status": "rejected"})
                            st.rerun()
                elif status == "developing":
                    with bcol1:
                        if st.button("Mark Used", key=f"use_{idea['id']}", use_container_width=True):
                            update_row("idea_bank", idea["id"], {"status": "used"})
                            st.rerun()
                    with bcol2:
                        if st.button("Back to New", key=f"back_{idea['id']}", use_container_width=True):
                            update_row("idea_bank", idea["id"], {"status": "new"})
                            st.rerun()

# Add new idea form
st.markdown("---")
st.markdown("### Add New Idea")

with st.form("add_idea", clear_on_submit=True):
    new_idea = st.text_area("Content Idea", height=80, placeholder="Describe your content idea...")

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        pillar_options = {p["name"]: p["id"] for p in pillars}
        new_pillar = st.selectbox("Pillar", ["None"] + list(pillar_options.keys()), key="new_idea_pillar")
    with fc2:
        new_priority = st.selectbox("Priority", ["medium", "high", "low"],
                                     format_func=lambda x: x.title())
    with fc3:
        new_source = st.text_input("Source", placeholder="e.g., competitor:charliehealth, trending")

    new_url = st.text_input("Reference URL (optional)")

    if st.form_submit_button("Add Idea"):
        if new_idea:
            data = {
                "idea": new_idea,
                "priority": new_priority,
                "status": "new",
                "inspiration_source": new_source or None,
                "inspiration_url": new_url or None,
            }
            if new_pillar != "None":
                data["pillar_id"] = pillar_options[new_pillar]

            insert_row("idea_bank", data)
            st.success("Idea added to the bank!")
            st.rerun()
        else:
            st.error("Please describe your content idea.")

# Show rejected ideas (collapsed)
rejected = execute_query("""
    SELECT ib.*, cp.name as pillar_name
    FROM idea_bank ib
    LEFT JOIN content_pillars cp ON ib.pillar_id = cp.id
    WHERE ib.status = 'rejected'
    ORDER BY ib.updated_at DESC LIMIT 20
""")
if rejected:
    with st.expander(f"Rejected Ideas ({len(rejected)})"):
        for idea in rejected:
            st.markdown(f"- ~~{idea['idea']}~~ *({idea['pillar_name'] or 'No pillar'})*")
            if st.button("Restore", key=f"restore_{idea['id']}"):
                update_row("idea_bank", idea["id"], {"status": "new"})
                st.rerun()
