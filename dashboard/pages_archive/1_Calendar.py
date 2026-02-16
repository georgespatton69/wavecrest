"""
Content Calendar — Monthly view of planned and published social media posts.
"""

import streamlit as st
import os
import sys
import calendar
from datetime import datetime, date

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "dashboard"))

from db_helpers import execute_query, insert_row, update_row, delete_row
from styles.theme import (
    COLORS, PILLAR_COLORS, STATUS_COLORS, CONTENT_TYPE_LABELS,
    PLATFORM_LABELS, get_custom_css, status_badge, pillar_badge,
)

st.set_page_config(page_title="Calendar | Wavecrest", page_icon="📅", layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)

st.markdown("## Content Calendar")

# Month selector
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
with col_nav2:
    today = date.today()
    selected_year = st.selectbox("Year", range(2025, 2028), index=today.year - 2025, label_visibility="collapsed")
    selected_month = st.selectbox("Month", range(1, 13), index=today.month - 1,
                                  format_func=lambda m: calendar.month_name[m], label_visibility="collapsed")

month_str = f"{selected_year}-{selected_month:02d}"

# Fetch posts for the month
posts = execute_query("""
    SELECT cc.*, cp.name as pillar_name, cp.color_hex as pillar_color
    FROM content_calendar cc
    LEFT JOIN content_pillars cp ON cc.pillar_id = cp.id
    WHERE strftime('%Y-%m', cc.scheduled_date) = ?
    ORDER BY cc.scheduled_date, cc.scheduled_time
""", [month_str])

# Summary stats
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    st.metric("Total Posts", len(posts))
with col_s2:
    ig_count = sum(1 for p in posts if p["platform"] in ("instagram", "both"))
    st.metric("Instagram", ig_count)
with col_s3:
    fb_count = sum(1 for p in posts if p["platform"] in ("facebook", "both"))
    st.metric("Facebook", fb_count)
with col_s4:
    published = sum(1 for p in posts if p["status"] == "published")
    st.metric("Published", published)

st.markdown("---")

# Calendar grid
cal = calendar.Calendar(firstweekday=6)  # Start on Sunday
month_days = cal.monthdayscalendar(selected_year, selected_month)

# Group posts by day
posts_by_day = {}
for p in posts:
    day = int(p["scheduled_date"].split("-")[2])
    posts_by_day.setdefault(day, []).append(p)

# Render calendar header
day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
header_cols = st.columns(7)
for i, name in enumerate(day_names):
    with header_cols[i]:
        st.markdown(f"<div style='text-align:center; color:{COLORS['text_secondary']}; font-weight:600; font-size:0.85em;'>{name}</div>", unsafe_allow_html=True)

# Render calendar weeks
for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.markdown("<div style='min-height:80px;'></div>", unsafe_allow_html=True)
            else:
                day_posts = posts_by_day.get(day, [])
                is_today = (day == today.day and selected_month == today.month and selected_year == today.year)
                border = f"2px solid {COLORS['primary']}" if is_today else f"1px solid {COLORS['border']}"

                # Build dots for each post
                dots = ""
                for p in day_posts:
                    color = p.get("pillar_color") or COLORS["text_light"]
                    dots += f'<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:{color}; margin:1px;"></span>'

                st.markdown(
                    f"""<div style="min-height:80px; border:{border}; border-radius:8px;
                        padding:6px; background:{COLORS['surface']}; margin:2px 0;">
                        <div style="font-weight:{'700' if is_today else '400'}; color:{COLORS['primary'] if is_today else COLORS['text_primary']}; font-size:0.9em;">{day}</div>
                        <div style="margin-top:4px;">{dots}</div>
                        <div style="color:{COLORS['text_light']}; font-size:0.7em;">{len(day_posts)} post{'s' if len(day_posts) != 1 else '' if day_posts else ''}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

st.markdown("---")

# Detailed post list
st.markdown("### Post Details")

filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    filter_platform = st.selectbox("Platform", ["All"] + list(PLATFORM_LABELS.values()), key="cal_plat")
with filter_col2:
    filter_type = st.selectbox("Content Type", ["All"] + list(CONTENT_TYPE_LABELS.values()), key="cal_type")
with filter_col3:
    filter_status = st.selectbox("Status", ["All", "Planned", "Created", "Reviewed", "Scheduled", "Published"], key="cal_status")

# Apply filters
filtered = posts
if filter_platform != "All":
    key = [k for k, v in PLATFORM_LABELS.items() if v == filter_platform][0]
    filtered = [p for p in filtered if p["platform"] == key or p["platform"] == "both"]
if filter_type != "All":
    key = [k for k, v in CONTENT_TYPE_LABELS.items() if v == filter_type][0]
    filtered = [p for p in filtered if p["content_type"] == key]
if filter_status != "All":
    filtered = [p for p in filtered if p["status"] == filter_status.lower()]

if not filtered:
    st.info("No posts found for this month. Use the form below to add content.")
else:
    for p in filtered:
        with st.expander(
            f"**{p['scheduled_date']}** — {CONTENT_TYPE_LABELS.get(p['content_type'], p['content_type'])} — "
            f"{PLATFORM_LABELS.get(p['platform'], p['platform'])} — "
            f"{p['pillar_name'] or 'No pillar'}"
        ):
            col_d1, col_d2 = st.columns([3, 1])
            with col_d1:
                st.markdown(f"**Caption:** {p['caption'] or '*No caption yet*'}")
                if p["hashtags"]:
                    st.markdown(f"**Hashtags:** {p['hashtags']}")
                if p["notes"]:
                    st.markdown(f"**Notes:** {p['notes']}")
            with col_d2:
                st.markdown(f"**Status:** {p['status'].title()}")
                st.markdown(f"**ID:** {p['id']}")

                # Status update buttons
                new_status = st.selectbox(
                    "Update status", ["planned", "created", "reviewed", "scheduled", "published"],
                    index=["planned", "created", "reviewed", "scheduled", "published"].index(p["status"]),
                    key=f"status_{p['id']}"
                )
                if new_status != p["status"]:
                    if st.button("Save", key=f"save_{p['id']}"):
                        update_row("content_calendar", p["id"], {"status": new_status})
                        st.rerun()

# Add new post form
st.markdown("---")
st.markdown("### Add New Post")

with st.form("add_post", clear_on_submit=True):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        new_date = st.date_input("Date", value=date(selected_year, selected_month, 1))
        new_time = st.time_input("Time (optional)", value=None)
    with fc2:
        new_platform = st.selectbox("Platform", list(PLATFORM_LABELS.keys()),
                                     format_func=lambda x: PLATFORM_LABELS[x])
        new_type = st.selectbox("Content Type", list(CONTENT_TYPE_LABELS.keys()),
                                 format_func=lambda x: CONTENT_TYPE_LABELS[x])
    with fc3:
        pillars = execute_query("SELECT id, name FROM content_pillars ORDER BY name")
        pillar_options = {p["name"]: p["id"] for p in pillars}
        new_pillar = st.selectbox("Pillar", ["None"] + list(pillar_options.keys()))

    new_caption = st.text_area("Caption", height=80)
    new_hashtags = st.text_input("Hashtags")
    new_notes = st.text_input("Notes")

    if st.form_submit_button("Add to Calendar"):
        data = {
            "scheduled_date": new_date.isoformat(),
            "platform": new_platform,
            "content_type": new_type,
            "caption": new_caption or None,
            "hashtags": new_hashtags or None,
            "notes": new_notes or None,
            "status": "planned",
        }
        if new_time:
            data["scheduled_time"] = new_time.strftime("%H:%M")
        if new_pillar != "None":
            data["pillar_id"] = pillar_options[new_pillar]

        insert_row("content_calendar", data)
        st.success("Post added to calendar!")
        st.rerun()
