"""
Analytics — Track organic performance of @wavecrestbehavioral.
"""

import streamlit as st
import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "dashboard"))

from db_helpers import execute_query
from styles.theme import COLORS, CONTENT_TYPE_LABELS, get_custom_css

st.set_page_config(page_title="Analytics | Wavecrest", page_icon="📊", layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)

st.markdown("## Performance Analytics")
st.markdown(
    f"<p style='color:{COLORS['text_secondary']}'>Track how @wavecrestbehavioral is performing on Instagram and Facebook.</p>",
    unsafe_allow_html=True,
)

# Check for data
snapshots = execute_query("SELECT * FROM account_snapshots ORDER BY snapshot_date DESC LIMIT 30")
post_data = execute_query("SELECT * FROM posts_performance ORDER BY published_at DESC LIMIT 50")
analyses = execute_query("SELECT * FROM analysis_log ORDER BY created_at DESC LIMIT 5")

if not snapshots and not post_data:
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align:center; padding:60px 20px; color:{COLORS['text_secondary']};">
            <h3 style="color:{COLORS['text_primary']};">No Analytics Data Yet</h3>
            <p>Connect the Meta Graph API to start tracking performance.</p>
            <p style="font-size:0.85em;">
                <b>To get started:</b><br>
                1. Follow <code>workflows/meta_api_setup.md</code> to create a Meta Developer app<br>
                2. Add your API credentials to <code>.env</code><br>
                3. Run <code>python3 tools/meta_fetch_insights.py --snapshot</code> to pull data
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # Account overview
    if snapshots:
        latest = snapshots[0]
        previous = snapshots[1] if len(snapshots) > 1 else None

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            delta = None
            if previous and latest.get("followers") and previous.get("followers"):
                delta = f"{latest['followers'] - previous['followers']:+d}"
            st.metric("Followers", f"{latest.get('followers', 'N/A'):,}" if latest.get("followers") else "N/A", delta=delta)
        with col2:
            st.metric("Reach (Period)", f"{latest.get('reach_period', 'N/A'):,}" if latest.get("reach_period") else "N/A")
        with col3:
            st.metric("Impressions (Period)", f"{latest.get('impressions_period', 'N/A'):,}" if latest.get("impressions_period") else "N/A")
        with col4:
            st.metric("Profile Views", f"{latest.get('profile_views_period', 'N/A'):,}" if latest.get("profile_views_period") else "N/A")

        st.markdown("---")

        # Follower trend
        if len(snapshots) > 1:
            st.markdown("### Follower Trend")
            df_snap = pd.DataFrame(snapshots)
            if "followers" in df_snap.columns and df_snap["followers"].notna().any():
                import plotly.graph_objects as go
                fig = go.Figure(data=[
                    go.Scatter(
                        x=df_snap["snapshot_date"], y=df_snap["followers"],
                        mode="lines+markers",
                        line=dict(color=COLORS["primary"], width=2),
                        marker=dict(size=6),
                    )
                ])
                fig.update_layout(
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["surface"],
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=300,
                )
                st.plotly_chart(fig, use_container_width=True)

    # Post performance table
    if post_data:
        st.markdown("### Post Performance")
        df = pd.DataFrame(post_data)
        display_cols = ["published_at", "platform", "content_type", "reach", "impressions",
                        "likes", "comments", "shares", "saves", "engagement_rate"]
        available_cols = [c for c in display_cols if c in df.columns]
        df_display = df[available_cols].copy()
        if "engagement_rate" in df_display.columns:
            df_display["engagement_rate"] = df_display["engagement_rate"].apply(lambda x: f"{x:.2%}" if x else "0%")
        if "content_type" in df_display.columns:
            df_display["content_type"] = df_display["content_type"].map(CONTENT_TYPE_LABELS).fillna(df_display["content_type"])
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # AI Analysis
    if analyses:
        st.markdown("### AI Analysis")
        for a in analyses[:3]:
            with st.expander(f"**{a['analysis_type'].replace('_', ' ').title()}** — {a.get('month_year', 'N/A')} — {a['created_at'][:10]}"):
                st.markdown(a["summary"])
                if a.get("recommendations"):
                    st.markdown("**Recommendations:**")
                    st.markdown(a["recommendations"])

# Manual snapshot entry (always visible)
st.markdown("---")
st.markdown("### Log Account Snapshot")
st.caption("Manually enter current account metrics if the Meta API is not yet connected.")

with st.form("manual_snapshot", clear_on_submit=True):
    sc1, sc2 = st.columns(2)
    with sc1:
        snap_platform = st.selectbox("Platform", ["instagram", "facebook"])
        snap_followers = st.number_input("Followers", min_value=0, step=1)
        snap_total_posts = st.number_input("Total Posts", min_value=0, step=1)
    with sc2:
        snap_reach = st.number_input("Reach (last 28 days)", min_value=0, step=1)
        snap_impressions = st.number_input("Impressions (last 28 days)", min_value=0, step=1)
        snap_profile_views = st.number_input("Profile Views (last 28 days)", min_value=0, step=1)

    if st.form_submit_button("Save Snapshot"):
        from db_helpers import insert_row
        from datetime import date
        try:
            insert_row("account_snapshots", {
                "platform": snap_platform,
                "snapshot_date": date.today().isoformat(),
                "followers": snap_followers or None,
                "total_posts": snap_total_posts or None,
                "reach_period": snap_reach or None,
                "impressions_period": snap_impressions or None,
                "profile_views_period": snap_profile_views or None,
            })
            st.success("Snapshot saved!")
            st.rerun()
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                st.warning("A snapshot for today already exists. Only one per platform per day.")
            else:
                st.error(f"Error: {e}")
