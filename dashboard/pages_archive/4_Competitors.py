"""
Competitors — Monitor Charlie Health and Novara Recovery Center social media.
"""

import streamlit as st
import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "dashboard"))

from db_helpers import execute_query, insert_row
from styles.theme import COLORS, get_custom_css

st.set_page_config(page_title="Competitors | Wavecrest", page_icon="🔍", layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)

st.markdown("## Competitor Monitoring")
st.markdown(
    f"<p style='color:{COLORS['text_secondary']}'>Track Charlie Health and Novara Recovery Center to stay informed on industry trends.</p>",
    unsafe_allow_html=True,
)

# Load competitors
competitors = execute_query("SELECT * FROM competitors ORDER BY name")

if not competitors:
    st.warning("No competitors configured. Run `python3 tools/db_init.py --seed` to add defaults.")
    st.stop()

# Competitor tabs
tab_names = [c["name"] for c in competitors] + ["Comparison"]
tabs = st.tabs(tab_names)

for i, comp in enumerate(competitors):
    with tabs[i]:
        st.markdown(f"### {comp['name']}")
        st.markdown(f"**Handle:** @{comp['handle']} | **Platform:** {comp['platform'].title()}")
        if comp.get("profile_url"):
            st.markdown(f"[View Profile]({comp['profile_url']})")

        # Snapshots
        snapshots = execute_query("""
            SELECT * FROM competitor_snapshots
            WHERE competitor_id = ?
            ORDER BY snapshot_date DESC LIMIT 30
        """, [comp["id"]])

        if snapshots:
            latest = snapshots[0]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Followers", f"{latest.get('followers', 'N/A'):,}" if latest.get("followers") else "N/A")
            with col2:
                st.metric("Total Posts", latest.get("total_posts", "N/A"))
            with col3:
                if len(snapshots) > 1:
                    prev = snapshots[1]
                    if latest.get("followers") and prev.get("followers"):
                        growth = latest["followers"] - prev["followers"]
                        st.metric("Follower Change", f"{growth:+d}")
                    else:
                        st.metric("Snapshots", len(snapshots))
                else:
                    st.metric("Snapshots", len(snapshots))

            # Follower trend chart
            if len(snapshots) > 1:
                df = pd.DataFrame(snapshots)
                if "followers" in df.columns and df["followers"].notna().any():
                    import plotly.graph_objects as go
                    fig = go.Figure(data=[
                        go.Scatter(
                            x=df["snapshot_date"], y=df["followers"],
                            mode="lines+markers",
                            line=dict(color=COLORS["primary"], width=2),
                        )
                    ])
                    fig.update_layout(
                        title="Follower Trend",
                        plot_bgcolor=COLORS["background"],
                        paper_bgcolor=COLORS["surface"],
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=250,
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No snapshots yet. Log one below.")

        # Notable posts
        st.markdown("#### Notable Posts")
        posts = execute_query("""
            SELECT * FROM competitor_posts
            WHERE competitor_id = ?
            ORDER BY fetched_at DESC LIMIT 20
        """, [comp["id"]])

        if posts:
            for p in posts:
                with st.expander(f"{p.get('posted_at', 'Unknown date')[:10]} — {p.get('content_type', 'post')} — {p.get('likes', 0)} likes"):
                    if p.get("caption_snippet"):
                        st.markdown(f"**Caption:** {p['caption_snippet']}")
                    if p.get("content_theme"):
                        st.markdown(f"**Theme:** {p['content_theme']}")
                    if p.get("notes"):
                        st.markdown(f"**Notes:** {p['notes']}")
                    if p.get("post_url"):
                        st.markdown(f"[View Post]({p['post_url']})")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Likes", p.get("likes", 0))
                    with col2:
                        st.metric("Comments", p.get("comments", 0))
                    with col3:
                        if p.get("estimated_engagement_rate"):
                            st.metric("Est. Engagement", f"{p['estimated_engagement_rate']:.2%}")
        else:
            st.info("No competitor posts logged yet.")

        # Log snapshot form
        st.markdown("---")
        st.markdown(f"#### Log Snapshot for {comp['name']}")
        with st.form(f"snapshot_{comp['id']}", clear_on_submit=True):
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                snap_followers = st.number_input("Followers", min_value=0, step=1, key=f"sf_{comp['id']}")
            with sc2:
                snap_posts = st.number_input("Total Posts", min_value=0, step=1, key=f"sp_{comp['id']}")
            with sc3:
                snap_bio = st.text_input("Bio (if changed)", key=f"sb_{comp['id']}")

            if st.form_submit_button("Save Snapshot"):
                from datetime import date
                try:
                    insert_row("competitor_snapshots", {
                        "competitor_id": comp["id"],
                        "snapshot_date": date.today().isoformat(),
                        "followers": snap_followers or None,
                        "total_posts": snap_posts or None,
                        "bio": snap_bio or None,
                    })
                    st.success("Snapshot saved!")
                    st.rerun()
                except Exception as e:
                    if "UNIQUE constraint" in str(e):
                        st.warning("A snapshot for today already exists.")
                    else:
                        st.error(f"Error: {e}")

        # Log competitor post form
        st.markdown(f"#### Log Notable Post from {comp['name']}")
        with st.form(f"comp_post_{comp['id']}", clear_on_submit=True):
            pc1, pc2 = st.columns(2)
            with pc1:
                cp_url = st.text_input("Post URL", key=f"cpu_{comp['id']}")
                cp_type = st.selectbox("Content Type", ["image", "video", "carousel", "reel", "story"], key=f"cpt_{comp['id']}")
                cp_theme = st.text_input("Content Theme", placeholder="e.g., education, testimonial", key=f"cpth_{comp['id']}")
            with pc2:
                cp_likes = st.number_input("Likes", min_value=0, step=1, key=f"cpl_{comp['id']}")
                cp_comments = st.number_input("Comments", min_value=0, step=1, key=f"cpc_{comp['id']}")
                cp_caption = st.text_input("Caption Snippet", key=f"cpca_{comp['id']}")

            cp_notes = st.text_input("Why was this post notable?", key=f"cpn_{comp['id']}")

            if st.form_submit_button("Log Post"):
                insert_row("competitor_posts", {
                    "competitor_id": comp["id"],
                    "post_url": cp_url or None,
                    "content_type": cp_type,
                    "caption_snippet": cp_caption or None,
                    "likes": cp_likes,
                    "comments": cp_comments,
                    "content_theme": cp_theme or None,
                    "notes": cp_notes or None,
                })
                st.success("Post logged!")
                st.rerun()

# Comparison tab
with tabs[-1]:
    st.markdown("### Head-to-Head Comparison")

    # Get latest snapshots for each competitor
    comparison_data = []
    for comp in competitors:
        latest = execute_query("""
            SELECT * FROM competitor_snapshots
            WHERE competitor_id = ?
            ORDER BY snapshot_date DESC LIMIT 1
        """, [comp["id"]])
        if latest:
            comparison_data.append({
                "Competitor": comp["name"],
                "Handle": f"@{comp['handle']}",
                "Followers": latest[0].get("followers", "N/A"),
                "Total Posts": latest[0].get("total_posts", "N/A"),
                "Last Updated": latest[0]["snapshot_date"],
            })

    if comparison_data:
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)

        # Follower comparison chart
        all_snapshots = []
        for comp in competitors:
            snaps = execute_query("""
                SELECT snapshot_date, followers FROM competitor_snapshots
                WHERE competitor_id = ? AND followers IS NOT NULL
                ORDER BY snapshot_date
            """, [comp["id"]])
            for s in snaps:
                all_snapshots.append({"date": s["snapshot_date"], "followers": s["followers"], "competitor": comp["name"]})

        if len(all_snapshots) > 2:
            import plotly.express as px
            df = pd.DataFrame(all_snapshots)
            fig = px.line(df, x="date", y="followers", color="competitor",
                          title="Follower Growth Comparison")
            fig.update_layout(
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["surface"],
                margin=dict(l=20, r=20, t=40, b=20),
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Log snapshots for competitors to see a comparison.")
