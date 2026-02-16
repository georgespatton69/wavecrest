"""
Wavecrest Social Media Dashboard
Main entry point for the Streamlit application.

Launch: streamlit run dashboard/app.py
"""

import streamlit as st
import os
import sys
import uuid
import html
from dotenv import load_dotenv

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))

from db_helpers import execute_query, insert_row, delete_row
from dashboard.styles.theme import COLORS, PRIORITY_COLORS, SCRIPT_CATEGORIES, LEAD_STAGES, AD_STATUS_COLORS, priority_badge, get_custom_css

UPLOADS_DIR = os.path.join(PROJECT_ROOT, "data", "uploads", "suggestions")

# Load environment variables
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def esc(text):
    """HTML-escape user-provided text to prevent XSS."""
    if not text:
        return ""
    return html.escape(str(text))


def safe_url(url):
    """Return URL only if it uses http/https scheme."""
    if not url:
        return ""
    url = str(url).strip()
    if url.startswith(("http://", "https://")):
        return url
    return ""


def check_password():
    """Simple password gate for the dashboard."""
    if st.session_state.get("authenticated"):
        return True
    dashboard_pw = os.getenv("DASHBOARD_PASSWORD", "")
    if not dashboard_pw:
        return True  # No password set — allow access (local dev)
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown(
            "<div style='text-align:center; padding-top:80px;'>"
            "<h2 style='color:#4A7C9B;'>Wavecrest</h2>"
            "<p style='color:#6B7B8D;'>Social Media Dashboard</p></div>",
            unsafe_allow_html=True,
        )
        password = st.text_input("Password", type="password", label_visibility="collapsed",
                                 placeholder="Enter team password")
        if st.button("Login", use_container_width=True):
            if password == dashboard_pw:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password")
    return False


# Page config
st.set_page_config(
    page_title="Wavecrest Social Media",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Auth gate
if not check_password():
    st.stop()

# Apply custom theme
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Header
st.markdown(
    f"""
    <div style="padding: 0 0 10px 0;">
        <h2 style="color: {COLORS['primary']}; margin: 0;">Wavecrest</h2>
        <p style="color: {COLORS['text_secondary']}; margin: 0; font-size: 0.9em;">
            Social Media Dashboard &mdash; @wavecrestbehavioral
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Content Suggestions", "Competitive Intel", "Scripts",
    "Lead Management", "Ad Performance",
])

# ---------------------------------------------------------------------------
# TAB 1: Content Suggestions
# ---------------------------------------------------------------------------
with tab1:
    st.markdown(
        f"<p style='color:{COLORS['text_secondary']}; margin-bottom: 4px;'>"
        "Submit content ideas for the team to review. Suggestions stay here until someone removes them.</p>",
        unsafe_allow_html=True,
    )

    # --- Add new suggestion form ---
    st.markdown("### Submit a Content Suggestion")

    with st.form("add_suggestion", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            new_name = st.text_input("Your Name *")
        with fc2:
            new_channel = st.selectbox(
                "Channel *", ["organic", "paid"],
                format_func=lambda x: x.title(),
            )
        with fc3:
            new_priority = st.selectbox(
                "Priority", ["medium", "high", "low"],
                format_func=lambda x: x.title(),
            )

        new_title = st.text_input("Title *", placeholder="Short title for your suggestion")
        new_desc = st.text_area(
            "Description", height=120, placeholder="Describe the content idea in detail..."
        )
        new_link = st.text_input("Link (optional)", placeholder="https://...")
        new_images = st.file_uploader(
            "Attach Images (optional)",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "gif", "webp"],
        )

        submitted = st.form_submit_button("Submit Suggestion")
        if submitted:
            if not new_name or not new_title:
                st.error("Name and Title are required.")
            else:
                # Insert suggestion
                data = {
                    "title": new_title,
                    "description": new_desc or None,
                    "submitted_by": new_name.strip(),
                    "priority": new_priority,
                    "channel": new_channel,
                    "link_url": new_link or None,
                }
                row_id = insert_row("content_suggestions", data)

                # Save uploaded images
                if new_images:
                    os.makedirs(UPLOADS_DIR, exist_ok=True)
                    for uploaded_file in new_images:
                        short_uuid = uuid.uuid4().hex[:8]
                        safe_name = uploaded_file.name.replace(" ", "_")
                        file_name = f"{row_id}_{short_uuid}_{safe_name}"
                        file_path = os.path.join(UPLOADS_DIR, file_name)

                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.read())

                        insert_row("suggestion_images", {
                            "suggestion_id": row_id,
                            "file_name": uploaded_file.name,
                            "file_path": file_path,
                        })

                st.success("Suggestion submitted!")
                st.rerun()

    # --- Filters ---
    st.markdown("---")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_priority = st.selectbox(
            "Filter by Priority", ["All", "High", "Medium", "Low"], key="sg_priority"
        )
    with col_f2:
        sort_order = st.selectbox(
            "Sort by", ["Newest First", "Priority"], key="sg_sort"
        )

    # --- Build query ---
    where = "WHERE 1=1"
    params = []
    if filter_priority != "All":
        where += " AND cs.priority = ?"
        params.append(filter_priority.lower())

    if sort_order == "Priority":
        order = "CASE cs.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END, cs.created_at DESC"
    else:
        order = "cs.created_at DESC"

    suggestions = execute_query(
        f"SELECT cs.* FROM content_suggestions cs {where} ORDER BY {order}", params
    )

    organic = [s for s in suggestions if s.get("channel", "organic") == "organic"]
    paid = [s for s in suggestions if s.get("channel") == "paid"]

    # --- Two-column layout: Organic | Paid ---
    col_organic, col_paid = st.columns(2)

    def render_suggestion_card(sg, column):
        """Render a single suggestion card inside the given column."""
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sg["priority"], "⚪")
        border_color = PRIORITY_COLORS.get(sg["priority"], COLORS["border"])
        created = sg["created_at"][:10] if sg["created_at"] else ""

        link_html = ""
        if sg.get("link_url"):
            validated_url = safe_url(sg["link_url"])
            if validated_url:
                link_html = (
                    f'<div style="margin-top:6px;">'
                    f'<a href="{esc(validated_url)}" target="_blank" rel="noopener noreferrer" '
                    f'style="color:{COLORS["primary"]}; font-size:0.85em; text-decoration:none;">'
                    f'🔗 {esc(sg["link_url"])}</a></div>'
                )

        desc_html = ""
        if sg.get("description"):
            desc_html = (
                f'<div style="margin-top:6px; color:{COLORS["text_primary"]}; '
                f'font-size:0.95em; white-space:pre-wrap;">{esc(sg["description"])}</div>'
            )

        with column:
            with st.container():
                st.markdown(
                    f"""<div style="background:{COLORS['surface']}; border:1px solid {COLORS['border']};
                        border-left:4px solid {border_color}; border-radius:8px; padding:14px; margin-bottom:4px;">
                        <div style="font-size:0.78em; color:{COLORS['text_light']};">
                            {priority_icon} {sg['priority'].title()} &bull;
                            Submitted by <b>{esc(sg['submitted_by'])}</b> &bull; {created}
                        </div>
                        <div style="margin-top:4px; font-weight:600; color:{COLORS['text_primary']}; font-size:1.05em;">
                            {esc(sg['title'])}
                        </div>
                        {desc_html}
                        {link_html}
                    </div>""",
                    unsafe_allow_html=True,
                )

                images = execute_query(
                    "SELECT * FROM suggestion_images WHERE suggestion_id = ?", [sg["id"]]
                )
                if images:
                    img_cols = st.columns(min(len(images), 3))
                    for idx, img in enumerate(images):
                        with img_cols[idx % len(img_cols)]:
                            if os.path.exists(img["file_path"]):
                                st.image(img["file_path"], width=150, caption=img["file_name"])

                if st.button("Delete", key=f"del_sg_{sg['id']}", type="secondary"):
                    for img in images:
                        try:
                            if os.path.exists(img["file_path"]):
                                os.remove(img["file_path"])
                        except OSError:
                            pass
                    delete_row("content_suggestions", sg["id"])
                    st.rerun()

    with col_organic:
        st.markdown(
            f"<h4 style='color:{COLORS['primary']}; border-bottom:3px solid {COLORS['primary']}; "
            f"padding-bottom:8px;'>Organic Social</h4>",
            unsafe_allow_html=True,
        )
        st.caption(f"{len(organic)} suggestion{'s' if len(organic) != 1 else ''}")

    with col_paid:
        st.markdown(
            f"<h4 style='color:{COLORS['accent']}; border-bottom:3px solid {COLORS['accent']}; "
            f"padding-bottom:8px;'>Paid Social</h4>",
            unsafe_allow_html=True,
        )
        st.caption(f"{len(paid)} suggestion{'s' if len(paid) != 1 else ''}")

    for sg in organic:
        render_suggestion_card(sg, col_organic)

    for sg in paid:
        render_suggestion_card(sg, col_paid)

# ---------------------------------------------------------------------------
# TAB 2: Competitive Intel
# ---------------------------------------------------------------------------
with tab2:
    import pandas as pd
    from datetime import datetime, timedelta

    st.markdown(
        f"<p style='color:{COLORS['text_secondary']}; margin-bottom: 4px;'>"
        "Track competitor activity across Instagram and Facebook.</p>",
        unsafe_allow_html=True,
    )

    # Check for data
    ci_competitors = execute_query("SELECT * FROM competitors ORDER BY name")
    ci_post_count = execute_query("SELECT COUNT(*) as count FROM competitor_posts")[0]["count"]

    if not ci_competitors:
        st.warning("No competitors being tracked yet.")
        if st.button("Load Demo Data"):
            from competitive_intel import load_demo_data
            result = load_demo_data()
            st.success(result["message"])
            st.rerun()
        st.stop()

    # Sub-tabs
    ci_tab1, ci_tab2, ci_tab3, ci_tab4 = st.tabs([
        "Overview", "Competitors", "Activity Feed", "Add Competitor"
    ])

    # === OVERVIEW ===
    with ci_tab1:
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        recent_posts = execute_query(
            "SELECT COUNT(*) as count FROM competitor_posts WHERE posted_at >= ?",
            [seven_days_ago],
        )[0]["count"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Competitors Tracked", len(ci_competitors))
        col2.metric("Total Posts Logged", ci_post_count)
        col3.metric("Posts (Last 7 Days)", recent_posts)

        # Avg engagement across all posts
        avg_eng = execute_query(
            "SELECT AVG(estimated_engagement_rate) as avg_er FROM competitor_posts "
            "WHERE estimated_engagement_rate IS NOT NULL"
        )
        avg_val = avg_eng[0]["avg_er"] if avg_eng and avg_eng[0]["avg_er"] else 0
        col4.metric("Avg Engagement", f"{avg_val:.2%}")

        # Activity timeline (last 30 days)
        posts_30d = execute_query("""
            SELECT cp.*, c.name as competitor_name
            FROM competitor_posts cp
            JOIN competitors c ON cp.competitor_id = c.id
            WHERE cp.posted_at >= ?
            ORDER BY cp.posted_at DESC
        """, [thirty_days_ago])

        if posts_30d:
            import plotly.express as px

            df = pd.DataFrame(posts_30d)
            df["date"] = pd.to_datetime(df["posted_at"]).dt.date

            # Daily activity bar chart
            daily = df.groupby("date").size().reset_index(name="count")
            fig1 = px.bar(
                daily, x="date", y="count",
                title="Daily Competitor Activity (Last 30 Days)",
            )
            fig1.update_layout(
                plot_bgcolor=COLORS["background"],
                paper_bgcolor=COLORS["surface"],
                margin=dict(l=20, r=20, t=40, b=20),
                height=280,
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Side-by-side: by competitor + by content type
            chart_c1, chart_c2 = st.columns(2)

            with chart_c1:
                by_comp = df.groupby("competitor_name").size().reset_index(name="count")
                fig2 = px.pie(by_comp, names="competitor_name", values="count",
                              title="Activity by Competitor")
                fig2.update_layout(
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["surface"],
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=300,
                )
                st.plotly_chart(fig2, use_container_width=True)

            with chart_c2:
                type_labels = {
                    "image": "Image", "carousel": "Carousel", "reel": "Reel",
                    "video": "Video", "story": "Story",
                }
                by_type = df.groupby("content_type").size().reset_index(name="count")
                by_type["content_type"] = by_type["content_type"].map(
                    lambda x: type_labels.get(x, x)
                )
                fig3 = px.bar(by_type, x="content_type", y="count",
                              title="Activity by Content Type")
                fig3.update_layout(
                    plot_bgcolor=COLORS["background"],
                    paper_bgcolor=COLORS["surface"],
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=300,
                )
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No recent activity to display. Load demo data to get started.")
            if st.button("Load Demo Data", key="demo_overview"):
                from competitive_intel import load_demo_data
                load_demo_data()
                st.rerun()

        # Log a competitor post
        st.markdown("---")
        st.markdown("### Log a Competitor Post")
        with st.expander("Add a notable post", expanded=False):
            with st.form("ci_log_post", clear_on_submit=True):
                lp_c1, lp_c2 = st.columns(2)
                with lp_c1:
                    lp_competitor = st.selectbox(
                        "Competitor",
                        ci_competitors,
                        format_func=lambda c: c["name"],
                        key="lp_comp",
                    )
                    lp_type = st.selectbox(
                        "Content Type",
                        ["image", "carousel", "reel", "video", "story"],
                        key="lp_type",
                    )
                    lp_theme = st.text_input("Content Theme", placeholder="e.g., education, testimonial", key="lp_theme")

                with lp_c2:
                    lp_url = st.text_input("Post URL", key="lp_url")
                    lp_likes = st.number_input("Likes", min_value=0, step=1, key="lp_likes")
                    lp_comments = st.number_input("Comments", min_value=0, step=1, key="lp_comments")

                lp_caption = st.text_area("Caption Snippet", height=80, key="lp_caption")
                lp_notes = st.text_input("Why is this post notable?", key="lp_notes")

                if st.form_submit_button("Log Post"):
                    if lp_competitor:
                        insert_row("competitor_posts", {
                            "competitor_id": lp_competitor["id"],
                            "post_url": lp_url or None,
                            "posted_at": datetime.now().isoformat(),
                            "content_type": lp_type,
                            "caption_snippet": lp_caption or None,
                            "likes": lp_likes,
                            "comments": lp_comments,
                            "content_theme": lp_theme or None,
                            "notes": lp_notes or None,
                        })
                        st.success("Post logged!")
                        st.rerun()

        # Notable posts section
        notable_posts = execute_query("""
            SELECT cp.*, c.name as competitor_name, c.handle
            FROM competitor_posts cp
            JOIN competitors c ON cp.competitor_id = c.id
            WHERE cp.is_notable = 1
            ORDER BY cp.posted_at DESC
        """)

        st.markdown("---")
        st.markdown(f"### ⭐ Notable Posts ({len(notable_posts)})")

        if notable_posts:
            for p in notable_posts:
                type_emoji = {
                    "image": "🖼️", "carousel": "🎠", "reel": "🎬",
                    "video": "📹", "story": "📱",
                }.get(p.get("content_type", ""), "📌")
                type_label = {
                    "image": "Image", "carousel": "Carousel", "reel": "Reel",
                    "video": "Video", "story": "Story",
                }.get(p.get("content_type", ""), p.get("content_type", ""))
                date_str = p["posted_at"][:10] if p.get("posted_at") else "Unknown"
                caption_short = (p.get("caption_snippet") or "No caption")[:60]

                with st.expander(
                    f"{type_emoji} {p['competitor_name']} — {date_str} — {caption_short}... "
                    f"({p.get('likes', 0)} likes)",
                    expanded=False,
                ):
                    st.markdown(
                        f"**{p['competitor_name']}** (@{p['handle']}) — {type_label}"
                    )
                    if p.get("caption_snippet"):
                        st.markdown(f"**Caption:** {p['caption_snippet']}")

                    mc1, mc2, mc3 = st.columns(3)
                    with mc1:
                        st.metric("Likes", p.get("likes", 0))
                    with mc2:
                        st.metric("Comments", p.get("comments", 0))
                    with mc3:
                        if p.get("estimated_engagement_rate"):
                            st.metric("Engagement", f"{p['estimated_engagement_rate']:.2%}")

                    if p.get("content_theme"):
                        st.markdown(f"**Theme:** {p['content_theme']}")
                    if p.get("notes"):
                        st.markdown(f"**Notes:** {p['notes']}")
                    # Instagram embed preview
                    notable_post_url = safe_url(p.get("post_url", ""))
                    if notable_post_url and "instagram.com/" in notable_post_url:
                        embed_url = esc(notable_post_url.rstrip("/") + "/embed/")
                        st.markdown(
                            f'<div style="display:flex; justify-content:center;">'
                            f'<iframe src="{embed_url}" width="400" height="760" '
                            f'frameborder="0" scrolling="no" allowtransparency="true">'
                            f'</iframe></div>',
                            unsafe_allow_html=True,
                        )
                    elif notable_post_url:
                        st.markdown(f"[View on Facebook]({notable_post_url})")

                    if st.button("Remove Notable", key=f"notable_overview_{p['id']}", type="secondary"):
                        execute_query(
                            "UPDATE competitor_posts SET is_notable = ? WHERE id = ?",
                            [0, p["id"]],
                        )
                        st.rerun()
        else:
            st.caption("No notable posts yet. Use the ⭐ Log as Notable button on any post in the Competitors or Activity Feed tabs.")

    # === COMPETITORS ===
    with ci_tab2:
        seven_days_ago_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        for comp in ci_competitors:
            comp_posts = execute_query(
                "SELECT COUNT(*) as count FROM competitor_posts WHERE competitor_id = ?",
                [comp["id"]],
            )[0]["count"]

            recent_comp = execute_query(
                "SELECT COUNT(*) as count FROM competitor_posts WHERE competitor_id = ? AND posted_at >= ?",
                [comp["id"], seven_days_ago_date],
            )[0]["count"]

            with st.expander(
                f"**{comp['name']}** — @{comp['handle']} ({comp_posts} posts, {recent_comp} this week)",
                expanded=False,
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Handle:** @{comp['handle']}")
                    st.markdown(f"**Platform:** {comp['platform'].title()}")
                    if comp.get("profile_url"):
                        st.markdown(f"[View Profile]({comp['profile_url']})")

                with col2:
                    if comp.get("notes"):
                        st.markdown(f"**Notes:** {comp['notes']}")

                # Latest snapshot
                snapshots = execute_query("""
                    SELECT * FROM competitor_snapshots
                    WHERE competitor_id = ?
                    ORDER BY snapshot_date DESC LIMIT 5
                """, [comp["id"]])

                if snapshots:
                    latest = snapshots[0]
                    sc1, sc2, sc3 = st.columns(3)
                    with sc1:
                        val = f"{latest['followers']:,}" if latest.get("followers") else "N/A"
                        st.metric("Followers", val)
                    with sc2:
                        st.metric("Total Posts", latest.get("total_posts", "N/A"))
                    with sc3:
                        if len(snapshots) > 1 and latest.get("followers") and snapshots[1].get("followers"):
                            growth = latest["followers"] - snapshots[1]["followers"]
                            st.metric("Follower Change", f"{growth:+d}")
                        else:
                            st.metric("Snapshots", len(snapshots))

                # Recent posts
                recent_posts_comp = execute_query("""
                    SELECT * FROM competitor_posts
                    WHERE competitor_id = ?
                    ORDER BY posted_at DESC LIMIT 5
                """, [comp["id"]])

                if recent_posts_comp:
                    st.markdown("**Recent Posts:**")
                    for p in recent_posts_comp:
                        type_emoji = {
                            "image": "🖼️", "carousel": "🎠", "reel": "🎬",
                            "video": "📹", "story": "📱",
                        }.get(p.get("content_type", ""), "📌")
                        type_label = {
                            "image": "Image", "carousel": "Carousel", "reel": "Reel",
                            "video": "Video", "story": "Story",
                        }.get(p.get("content_type", ""), p.get("content_type", ""))
                        date_str = p["posted_at"][:10] if p.get("posted_at") else "Unknown"
                        caption_preview = (p.get("caption_snippet") or "No caption")[:60]
                        notable_star = "⭐ " if p.get("is_notable") else ""

                        with st.expander(
                            f"{notable_star}{type_emoji} {date_str} — {caption_preview}... "
                            f"({p.get('likes', 0)} likes)",
                            expanded=False,
                        ):
                            st.markdown(f"**Type:** {type_label}")
                            if p.get("caption_snippet"):
                                st.markdown(f"**Caption:** {p['caption_snippet']}")
                            mc1, mc2, mc3 = st.columns(3)
                            with mc1:
                                st.metric("Likes", p.get("likes", 0))
                            with mc2:
                                st.metric("Comments", p.get("comments", 0))
                            with mc3:
                                if p.get("estimated_engagement_rate"):
                                    st.metric("Engagement", f"{p['estimated_engagement_rate']:.2%}")
                            if p.get("content_theme"):
                                st.markdown(f"**Theme:** {p['content_theme']}")
                            if p.get("notes"):
                                st.markdown(f"**Notes:** {p['notes']}")
                            # Instagram embed preview
                            comp_post_url = safe_url(p.get("post_url", ""))
                            if comp_post_url and "instagram.com/" in comp_post_url:
                                embed_url = esc(comp_post_url.rstrip("/") + "/embed/")
                                st.markdown(
                                    f'<div style="display:flex; justify-content:center;">'
                                    f'<iframe src="{embed_url}" width="400" height="760" '
                                    f'frameborder="0" scrolling="no" allowtransparency="true">'
                                    f'</iframe></div>',
                                    unsafe_allow_html=True,
                                )
                            elif comp_post_url:
                                st.markdown(f"[View on Facebook]({comp_post_url})")

                            # Notable toggle
                            is_notable = bool(p.get("is_notable"))
                            btn_label = "Remove Notable" if is_notable else "⭐ Log as Notable"
                            btn_type = "secondary" if is_notable else "primary"
                            if st.button(btn_label, key=f"notable_comp_{comp['id']}_{p['id']}", type=btn_type):
                                execute_query(
                                    "UPDATE competitor_posts SET is_notable = ? WHERE id = ?",
                                    [0 if is_notable else 1, p["id"]],
                                )
                                st.rerun()

                # Remove button
                if st.button(f"Remove {comp['name']}", key=f"ci_remove_{comp['id']}"):
                    delete_row("competitors", comp["id"])
                    st.rerun()

    # === ACTIVITY FEED ===
    with ci_tab3:
        # Filters
        fc1, fc2, fc3 = st.columns(3)

        with fc1:
            comp_names = ["All"] + [c["name"] for c in ci_competitors]
            ci_filter_comp = st.selectbox("Filter by Competitor", comp_names, key="ci_comp")

        with fc2:
            ci_filter_type = st.selectbox(
                "Filter by Type",
                ["All", "image", "carousel", "reel", "video", "story"],
                key="ci_type",
            )

        with fc3:
            ci_date_range = st.selectbox(
                "Date Range",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                key="ci_date",
            )

        # Build query
        feed_where = "WHERE 1=1"
        feed_params = []

        if ci_filter_comp != "All":
            comp_id = next(
                (c["id"] for c in ci_competitors if c["name"] == ci_filter_comp), None
            )
            if comp_id:
                feed_where += " AND cp.competitor_id = ?"
                feed_params.append(comp_id)

        if ci_filter_type != "All":
            feed_where += " AND cp.content_type = ?"
            feed_params.append(ci_filter_type)

        if ci_date_range != "All time":
            days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
            cutoff = (datetime.now() - timedelta(days=days_map[ci_date_range])).strftime("%Y-%m-%d")
            feed_where += " AND cp.posted_at >= ?"
            feed_params.append(cutoff)

        feed_posts = execute_query(f"""
            SELECT cp.*, c.name as competitor_name, c.handle
            FROM competitor_posts cp
            JOIN competitors c ON cp.competitor_id = c.id
            {feed_where}
            ORDER BY cp.posted_at DESC
            LIMIT 50
        """, feed_params)

        st.caption(f"{len(feed_posts)} posts")

        if feed_posts:
            for p in feed_posts:
                type_emoji = {
                    "image": "🖼️", "carousel": "🎠", "reel": "🎬",
                    "video": "📹", "story": "📱",
                }.get(p.get("content_type", ""), "📌")

                type_label = {
                    "image": "Image", "carousel": "Carousel", "reel": "Reel",
                    "video": "Video", "story": "Story",
                }.get(p.get("content_type", ""), p.get("content_type", ""))

                date_str = p["posted_at"][:10] if p.get("posted_at") else "Unknown"
                caption_short = (p.get("caption_snippet") or "No caption")[:50]
                notable_star = "⭐ " if p.get("is_notable") else ""

                with st.expander(
                    f"{notable_star}{type_emoji} {p['competitor_name']} — {date_str} — {caption_short}... "
                    f"({p.get('likes', 0)} likes)",
                    expanded=False,
                ):
                    st.markdown(
                        f"**{p['competitor_name']}** (@{p['handle']}) — {type_label}"
                    )
                    if p.get("caption_snippet"):
                        st.markdown(f"**Caption:** {p['caption_snippet']}")

                    mc1, mc2, mc3 = st.columns(3)
                    with mc1:
                        st.metric("Likes", p.get("likes", 0))
                    with mc2:
                        st.metric("Comments", p.get("comments", 0))
                    with mc3:
                        if p.get("estimated_engagement_rate"):
                            st.metric("Engagement", f"{p['estimated_engagement_rate']:.2%}")

                    if p.get("content_theme"):
                        st.markdown(f"**Theme:** {p['content_theme']}")
                    if p.get("notes"):
                        st.markdown(f"**Notes:** {p['notes']}")
                    # Instagram embed preview
                    feed_post_url = safe_url(p.get("post_url", ""))
                    if feed_post_url and "instagram.com/" in feed_post_url:
                        embed_url = esc(feed_post_url.rstrip("/") + "/embed/")
                        st.markdown(
                            f'<div style="display:flex; justify-content:center;">'
                            f'<iframe src="{embed_url}" width="400" height="760" '
                            f'frameborder="0" scrolling="no" allowtransparency="true">'
                            f'</iframe></div>',
                            unsafe_allow_html=True,
                        )
                    elif feed_post_url:
                        st.markdown(f"[View on Facebook]({feed_post_url})")

                    # Notable toggle
                    is_notable = bool(p.get("is_notable"))
                    btn_label = "Remove Notable" if is_notable else "⭐ Log as Notable"
                    btn_type = "secondary" if is_notable else "primary"
                    if st.button(btn_label, key=f"notable_feed_{p['id']}", type=btn_type):
                        execute_query(
                            "UPDATE competitor_posts SET is_notable = ? WHERE id = ?",
                            [0 if is_notable else 1, p["id"]],
                        )
                        st.rerun()
        else:
            st.info("No posts match your filters.")

    # === ADD COMPETITOR ===
    with ci_tab4:
        st.markdown("Track a new competitor on Instagram or Facebook.")

        with st.form("add_competitor", clear_on_submit=True):
            ac_c1, ac_c2 = st.columns(2)
            with ac_c1:
                ac_name = st.text_input("Company Name *", placeholder="Competitor Name")
                ac_handle = st.text_input("Handle *", placeholder="theirhandle (no @)")
            with ac_c2:
                ac_platform = st.selectbox("Platform", ["instagram", "facebook", "both"],
                                           format_func=lambda x: x.title())
                ac_url = st.text_input("Profile URL", placeholder="https://www.instagram.com/theirhandle/")

            ac_notes = st.text_area("Notes", placeholder="Why are they a competitor? What should we watch for?", height=80)

            if st.form_submit_button("Add Competitor"):
                if ac_name and ac_handle:
                    existing = execute_query(
                        "SELECT id FROM competitors WHERE handle = ?", [ac_handle]
                    )
                    if existing:
                        st.warning(f"A competitor with handle @{ac_handle} already exists.")
                    else:
                        insert_row("competitors", {
                            "name": ac_name,
                            "handle": ac_handle,
                            "platform": ac_platform,
                            "profile_url": ac_url or None,
                            "notes": ac_notes or None,
                        })
                        st.success(f"Now tracking {ac_name}!")
                        st.rerun()
                else:
                    st.error("Company Name and Handle are required.")

    # Footer actions
    st.markdown("---")
    ci_foot1, ci_foot2, ci_foot3 = st.columns(3)
    with ci_foot1:
        if st.button("Scan Instagram", key="ci_scan_ig"):
            with st.spinner("Scraping Instagram profiles... this may take a minute."):
                from ig_scraper import scan_all
                result = scan_all(max_posts=10)
            if result.get("success"):
                total_new = sum(r.get("posts_added", 0) for r in result.get("results", []))
                st.success(f"Scanned {result['competitors_scanned']} profiles, added {total_new} new posts.")
                st.rerun()
            else:
                st.error("Scan failed. Check competitor handles.")
    with ci_foot2:
        if st.button("Load Demo Data", key="ci_demo_footer"):
            from competitive_intel import load_demo_data
            result = load_demo_data()
            st.success(result["message"])
            st.rerun()
    with ci_foot3:
        if ci_post_count > 0:
            all_posts = execute_query("""
                SELECT c.name, c.handle, cp.posted_at, cp.content_type,
                       cp.caption_snippet, cp.likes, cp.comments,
                       cp.estimated_engagement_rate, cp.content_theme
                FROM competitor_posts cp
                JOIN competitors c ON cp.competitor_id = c.id
                ORDER BY cp.posted_at DESC
            """)
            if all_posts:
                csv_df = pd.DataFrame(all_posts)
                st.download_button(
                    "Export Activity CSV",
                    data=csv_df.to_csv(index=False),
                    file_name="competitor_activity.csv",
                    mime="text/csv",
                )

# ---------------------------------------------------------------------------
# TAB 3: Scripts Management
# ---------------------------------------------------------------------------
with tab3:
    scripts_tab_manage, scripts_tab_input = st.tabs(["Manage", "Input"])

    with scripts_tab_manage:
        st.markdown(
            f"<p style='color:{COLORS['text_secondary']}; margin-bottom: 4px;'>"
            "Manage scripts across categories. Move scripts to Completed when done.</p>",
            unsafe_allow_html=True,
        )

        # Load all scripts
        all_scripts = execute_query("""
            SELECT s.*, cp.name as pillar_name
            FROM scripts s
            LEFT JOIN content_pillars cp ON s.pillar_id = cp.id
            ORDER BY s.created_at DESC
        """)

        # Group scripts by category and status
        category_keys = list(SCRIPT_CATEGORIES.keys())
        todo_by_cat = {k: [] for k in category_keys}
        backlog_by_cat = {k: [] for k in category_keys}
        completed_scripts = []

        for s in all_scripts:
            if s["status"] == "completed":
                completed_scripts.append(s)
            elif s["status"] == "todo" and s["script_type"] in todo_by_cat:
                todo_by_cat[s["script_type"]].append(s)
            elif s["status"] == "backlog" and s["script_type"] in backlog_by_cat:
                backlog_by_cat[s["script_type"]].append(s)

        # --- Two-column Kanban ---
        col_todo, col_done = st.columns(2)

        with col_todo:
            st.markdown(
                f"<h4 style='color:{COLORS['text_primary']}; border-bottom:2px solid {COLORS['primary']}; "
                f"padding-bottom:8px;'>Todos</h4>",
                unsafe_allow_html=True,
            )

            for cat_key in category_keys:
                cat_info = SCRIPT_CATEGORIES[cat_key]
                cat_scripts = todo_by_cat[cat_key]
                count = len(cat_scripts)

                with st.expander(f"{cat_info['label']}  ({count})", expanded=False):
                    if cat_scripts:
                        for s in cat_scripts:
                            notes_html = ""
                            if s.get("notes"):
                                notes_html = (
                                    f'<br><span style="color:{COLORS["text_light"]}; '
                                    f'font-size:0.85em;">{esc(s["notes"])}</span>'
                                )
                            sc1, sc2, sc3 = st.columns([4, 1, 1])
                            with sc1:
                                st.markdown(
                                    f"<div style='background:{COLORS['background']}; "
                                    f"border:1px solid {COLORS['border']}; "
                                    f"border-left:3px solid {cat_info['color']}; "
                                    f"border-radius:8px; padding:8px 12px; "
                                    f"margin-bottom:4px; font-size:0.9em; "
                                    f"color:{COLORS['text_primary']};'>"
                                    f"<b>{esc(s['title'])}</b>{notes_html}</div>",
                                    unsafe_allow_html=True,
                                )
                            with sc2:
                                if st.button("✅", key=f"complete_{s['id']}", help="Mark completed"):
                                    execute_query(
                                        "UPDATE scripts SET status = 'completed', "
                                        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                        [s["id"]],
                                    )
                                    st.rerun()
                            with sc3:
                                if st.button("↩️", key=f"backlog_{s['id']}", help="Move back to Scripts"):
                                    execute_query(
                                        "UPDATE scripts SET status = 'backlog', "
                                        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                        [s["id"]],
                                    )
                                    st.rerun()
                    else:
                        st.caption("No scripts in this category.")

                    if cat_key == "ad_reels":
                        st.markdown("---")
                        st.markdown(
                            "**Quick creative direction** (what to film so these convert)\n\n"
                            "Best-performing visuals for 25–59:\n"
                            "- therapist on camera (clean background, direct eye contact, calm tone)\n"
                            '- "day-in-the-life" UGC (coffee walk, school drop-off vibe, laptop at kitchen table)\n'
                            '- simple text overlays: "Virtual IOP / Evenings & Weekends / Insurance"\n\n'
                            "Always put these words on-screen early (first 2–3 seconds):\n"
                            '"Virtual IOP" · "From home" · "Evenings/Weekends" · "Insurance"'
                        )

        with col_done:
            st.markdown(
                f"<h4 style='color:{COLORS['success']}; border-bottom:2px solid {COLORS['success']}; "
                f"padding-bottom:8px;'>Completed</h4>",
                unsafe_allow_html=True,
            )

            if completed_scripts:
                for s in completed_scripts:
                    cat_info = SCRIPT_CATEGORIES.get(
                        s["script_type"], {"label": "Unknown", "color": COLORS["border"]}
                    )
                    sc1, sc2 = st.columns([4, 1])
                    with sc1:
                        st.markdown(
                            f"<div style='background:{COLORS['surface']}; "
                            f"border:1px solid {COLORS['border']}; "
                            f"border-left:3px solid {COLORS['success']}; "
                            f"border-radius:8px; padding:8px 12px; "
                            f"margin-bottom:4px; font-size:0.9em; "
                            f"color:{COLORS['text_secondary']};'>"
                            f"<s>{esc(s['title'])}</s>"
                            f"<br><span style='font-size:0.8em; "
                            f"color:{COLORS['text_light']};'>"
                            f"{cat_info['label']}</span></div>",
                            unsafe_allow_html=True,
                        )
                    with sc2:
                        if st.button("↩️", key=f"undo_{s['id']}", help="Move back to Todo"):
                            execute_query(
                                "UPDATE scripts SET status = 'todo', "
                                "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                [s["id"]],
                            )
                            st.rerun()
            else:
                st.caption("No completed scripts yet.")

        # --- Bottom half: Scripts Library ---
        st.markdown("---")
        st.markdown(
            f"<h4 style='color:{COLORS['text_primary']}; border-bottom:2px solid {COLORS['border']}; "
            f"padding-bottom:8px;'>Scripts</h4>",
            unsafe_allow_html=True,
        )

        for cat_key in category_keys:
            cat_info = SCRIPT_CATEGORIES[cat_key]
            cat_scripts = backlog_by_cat[cat_key]
            count = len(cat_scripts)

            with st.expander(f"{cat_info['label']}  ({count})", expanded=False):
                if cat_scripts:
                    for s in cat_scripts:
                        with st.expander(f"{s['title']}", expanded=False):
                            edit_key = f"editing_{s['id']}"
                            if st.session_state.get(edit_key, False):
                                with st.form(f"edit_form_{s['id']}"):
                                    new_title = st.text_input("Title", value=s["title"])
                                    new_body = st.text_area("Body", value=s["body"], height=200)
                                    fc1, fc2 = st.columns(2)
                                    with fc1:
                                        save = st.form_submit_button("Save", use_container_width=True)
                                    with fc2:
                                        cancel = st.form_submit_button("Cancel", use_container_width=True)
                                    if save:
                                        execute_query(
                                            "UPDATE scripts SET title = ?, body = ?, "
                                            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                            [new_title.strip(), new_body, s["id"]],
                                        )
                                        st.session_state[edit_key] = False
                                        st.rerun()
                                    if cancel:
                                        st.session_state[edit_key] = False
                                        st.rerun()
                            else:
                                st.markdown(s["body"])
                                bc1, bc2, bc3 = st.columns(3)
                                with bc1:
                                    if st.button("✏️ Edit", key=f"edit_{s['id']}", use_container_width=True):
                                        st.session_state[edit_key] = True
                                        st.rerun()
                                with bc2:
                                    if st.button("📋 Move to Todos", key=f"to_todo_{s['id']}", use_container_width=True):
                                        execute_query(
                                            "UPDATE scripts SET status = 'todo', "
                                            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                            [s["id"]],
                                        )
                                        st.rerun()
                                with bc3:
                                    if st.button("🗑️ Delete", key=f"delete_{s['id']}", use_container_width=True):
                                        execute_query("DELETE FROM scripts WHERE id = ?", [s["id"]])
                                        st.rerun()
                else:
                    st.caption("No scripts in this category yet.")

                if cat_key == "ad_reels":
                    st.markdown("---")
                    st.markdown(
                        "**Quick creative direction** (what to film so these convert)\n\n"
                        "Best-performing visuals for 25–59:\n"
                        "- therapist on camera (clean background, direct eye contact, calm tone)\n"
                        '- "day-in-the-life" UGC (coffee walk, school drop-off vibe, laptop at kitchen table)\n'
                        '- simple text overlays: "Virtual IOP / Evenings & Weekends / Insurance"\n\n'
                        "Always put these words on-screen early (first 2–3 seconds):\n"
                        '"Virtual IOP" · "From home" · "Evenings/Weekends" · "Insurance"'
                    )

    with scripts_tab_input:
        _, script_center, _ = st.columns([1, 2, 1])
        with script_center:
            st.markdown(
                f"<h4 style='color:{COLORS['text_primary']}; text-align:center; "
                f"margin-bottom:8px;'>Scripts</h4>",
                unsafe_allow_html=True,
            )

            selected_category = st.selectbox(
                "Select a script category",
                [None] + list(SCRIPT_CATEGORIES.keys()),
                format_func=lambda k: "Select a category..." if k is None else SCRIPT_CATEGORIES[k]["label"],
                key="script_category_select",
            )
            # Hide search input and show pointer cursor on dropdown
            st.markdown(
                "<style>"
                "div[data-baseweb='select'] input { opacity: 0 !important; width: 0 !important; padding: 0 !important; }"
                "div[data-baseweb='select'] { cursor: pointer !important; }"
                "div[data-baseweb='select'] * { cursor: pointer !important; }"
                "</style>",
                unsafe_allow_html=True,
            )

            # --- Category-specific forms ---
            if selected_category == "influencer_reels":
                with st.form("influencer_reels_form", clear_on_submit=True):
                    st.markdown(f"**{SCRIPT_CATEGORIES['influencer_reels']['label']}**")
                    ir_title = st.text_input("Title *")
                    ir_hook = st.text_area("Hook (0–5s) *", height=80, placeholder="Opening hook to grab attention...")
                    ir_promise = st.text_area("Promise (5–10s) *", height=80, placeholder="What the viewer will get...")
                    ir_value = st.text_area("Value (10–65s) *", height=150, placeholder="Main content / value delivery...")
                    ir_cta = st.text_area("CTA (65–90s) *", height=80, placeholder="Call to action / close...")
                    ir_extra = st.text_area("Extra (optional)", height=80, placeholder="Any additional notes...")

                    if st.form_submit_button("Add Script", use_container_width=True):
                        if not ir_title or not ir_hook or not ir_promise or not ir_value or not ir_cta:
                            st.error("Title, Hook, Promise, Value, and CTA are all required.")
                        else:
                            body = (
                                f"**Hook (0–5s):**\n{ir_hook}\n\n"
                                f"**Promise (5–10s):**\n{ir_promise}\n\n"
                                f"**Value (10–65s):**\n{ir_value}\n\n"
                                f"**CTA (65–90s):**\n{ir_cta}"
                            )
                            if ir_extra:
                                body += f"\n\n**Extra:**\n{ir_extra}"
                            insert_row("scripts", {
                                "title": ir_title.strip(),
                                "body": body,
                                "script_type": "influencer_reels",
                                "status": "backlog",
                                "notes": None,
                            })
                            st.success("Script added to Influencer Focused Reels!")
                            st.rerun()

            if selected_category == "ad_reels":
                with st.form("ad_reels_form", clear_on_submit=True):
                    st.markdown(f"**{SCRIPT_CATEGORIES['ad_reels']['label']}**")
                    ar_title = st.text_input("Title *")
                    ar_hook = st.text_area("Hook *", height=80, placeholder="Opening hook...")
                    ar_value = st.text_area("Value *", height=150, placeholder="Core value / message...")
                    ar_cta = st.text_area("CTA *", height=80, placeholder="Call to action...")

                    if st.form_submit_button("Add Script", use_container_width=True):
                        if not ar_title or not ar_hook or not ar_value or not ar_cta:
                            st.error("Title, Hook, Value, and CTA are all required.")
                        else:
                            body = (
                                f"**Hook:**\n{ar_hook}\n\n"
                                f"**Value:**\n{ar_value}\n\n"
                                f"**CTA:**\n{ar_cta}"
                            )
                            insert_row("scripts", {
                                "title": ar_title.strip(),
                                "body": body,
                                "script_type": "ad_reels",
                                "status": "backlog",
                                "notes": None,
                            })
                            st.success("Script added to Ad Focused Reels!")
                            st.rerun()

            if selected_category == "voiceover_reels":
                with st.form("voiceover_reels_form", clear_on_submit=True):
                    st.markdown(f"**{SCRIPT_CATEGORIES['voiceover_reels']['label']}**")
                    vr_title = st.text_input("Title *")
                    vr_broll = st.text_area("B-Roll *", height=100, placeholder="B-roll direction / visuals...")
                    vr_vo = st.text_area("VO *", height=150, placeholder="Voiceover script...")

                    if st.form_submit_button("Add Script", use_container_width=True):
                        if not vr_title or not vr_broll or not vr_vo:
                            st.error("Title, B-Roll, and VO are all required.")
                        else:
                            body = (
                                f"**B-Roll:**\n{vr_broll}\n\n"
                                f"**VO:**\n{vr_vo}"
                            )
                            insert_row("scripts", {
                                "title": vr_title.strip(),
                                "body": body,
                                "script_type": "voiceover_reels",
                                "status": "backlog",
                                "notes": None,
                            })
                            st.success("Script added to Voiceover Reels!")
                            st.rerun()

            if selected_category == "therapist_scripts":
                with st.form("therapist_scripts_form", clear_on_submit=True):
                    st.markdown(f"**{SCRIPT_CATEGORIES['therapist_scripts']['label']}**")
                    ts_question = st.text_input("Question *")
                    ts_hooks = st.text_area("Hooks *", height=150, placeholder="Hooks for the therapist script...")
                    ts_subquestions = st.text_area("Sub-Questions (optional)", height=100, placeholder="Any follow-up or sub-questions...")

                    if st.form_submit_button("Add Script", use_container_width=True):
                        if not ts_question or not ts_hooks:
                            st.error("Question and Hooks are required.")
                        else:
                            body = f"**Hooks:**\n{ts_hooks}"
                            if ts_subquestions:
                                body += f"\n\n**Sub-Questions:**\n{ts_subquestions}"
                            insert_row("scripts", {
                                "title": ts_question.strip(),
                                "body": body,
                                "script_type": "therapist_scripts",
                                "status": "backlog",
                                "notes": None,
                            })
                            st.success("Script added to Therapist Scripts!")
                            st.rerun()

            if selected_category == "carousel_posts":
                with st.form("carousel_posts_form", clear_on_submit=True):
                    st.markdown(f"**{SCRIPT_CATEGORIES['carousel_posts']['label']}**")
                    cp_title = st.text_input("Title *")
                    cp_slide1 = st.text_area("Slide 1 — Hook *", height=80, placeholder="Opening slide / hook...")
                    cp_slide2 = st.text_area("Slide 2 *", height=80, placeholder="Slide 2 content...")
                    cp_slide3 = st.text_area("Slide 3 *", height=80, placeholder="Slide 3 content...")
                    cp_slide4 = st.text_area("Slide 4 *", height=80, placeholder="Slide 4 content...")
                    cp_slide5 = st.text_area("Slide 5 *", height=80, placeholder="Slide 5 content...")
                    cp_caption = st.text_area("Caption *", height=100, placeholder="Post caption...")

                    if st.form_submit_button("Add Script", use_container_width=True):
                        if not cp_title or not cp_slide1 or not cp_slide2 or not cp_slide3 or not cp_slide4 or not cp_slide5 or not cp_caption:
                            st.error("All fields are required.")
                        else:
                            body = (
                                f"**Slide 1 (Hook):**\n{cp_slide1}\n\n"
                                f"**Slide 2:**\n{cp_slide2}\n\n"
                                f"**Slide 3:**\n{cp_slide3}\n\n"
                                f"**Slide 4:**\n{cp_slide4}\n\n"
                                f"**Slide 5:**\n{cp_slide5}\n\n"
                                f"**Caption:**\n{cp_caption}"
                            )
                            insert_row("scripts", {
                                "title": cp_title.strip(),
                                "body": body,
                                "script_type": "carousel_posts",
                                "status": "backlog",
                                "notes": None,
                            })
                            st.success("Script added to Carousel Posts!")
                            st.rerun()

# ---------------------------------------------------------------------------
# TAB 4: Lead Management (CRM)
# ---------------------------------------------------------------------------
with tab4:
    from datetime import datetime, timedelta
    from tools.meta_api import MetaAPI

    meta_api = MetaAPI()

    # API status banner + sync button
    if meta_api.is_leads_configured():
        sync_col1, sync_col2 = st.columns([4, 1])
        with sync_col1:
            st.success("Meta API connected — leads will auto-import on sync")
        with sync_col2:
            if st.button("Sync Leads", key="sync_leads_btn", use_container_width=True):
                with st.spinner("Pulling leads from Meta..."):
                    count = meta_api.sync_leads()
                st.success(f"Synced {count} new leads!")
                st.rerun()
    else:
        st.info("Add META_ACCESS_TOKEN and META_PAGE_ID to .env to auto-import leads from Meta")

    # Load all leads
    all_leads = execute_query("""
        SELECT * FROM leads ORDER BY created_at DESC
    """)

    stage_keys = list(LEAD_STAGES.keys())
    leads_by_stage = {k: [] for k in stage_keys}
    for lead in all_leads:
        if lead["stage"] in leads_by_stage:
            leads_by_stage[lead["stage"]].append(lead)

    # --- Pipeline Kanban ---
    cols = st.columns(4)
    for i, stage_key in enumerate(stage_keys):
        stage_info = LEAD_STAGES[stage_key]
        stage_leads = leads_by_stage[stage_key]

        with cols[i]:
            st.markdown(
                f"<h4 style='color:{stage_info['color']}; border-bottom:2px solid {stage_info['color']}; "
                f"padding-bottom:8px;'>{stage_info['label']} ({len(stage_leads)})</h4>",
                unsafe_allow_html=True,
            )

            if stage_leads:
                for lead in stage_leads:
                    date_str = lead["created_at"][:10] if lead.get("created_at") else ""
                    campaign_text = lead.get("campaign_name") or ""
                    if campaign_text:
                        campaign_text = f" — {campaign_text}"

                    with st.expander(f"{lead['name']}", expanded=False):
                        if lead.get("email"):
                            st.markdown(f"**Email:** {lead['email']}")
                        if lead.get("phone"):
                            st.markdown(f"**Phone:** {lead['phone']}")
                        if lead.get("campaign_name"):
                            st.markdown(f"**Campaign:** {lead['campaign_name']}")
                        if lead.get("ad_name"):
                            st.markdown(f"**Ad:** {lead['ad_name']}")
                        if lead.get("form_name"):
                            st.markdown(f"**Form:** {lead['form_name']}")
                        if lead.get("source"):
                            st.markdown(f"**Source:** {lead['source']}")
                        if lead.get("notes"):
                            st.markdown(f"**Notes:** {lead['notes']}")
                        st.caption(f"Added: {date_str}")

                        # Activity log
                        activities = execute_query(
                            "SELECT * FROM lead_activity WHERE lead_id = ? ORDER BY created_at DESC",
                            [lead["id"]],
                        )
                        if activities:
                            st.markdown("**Activity:**")
                            for act in activities:
                                act_date = act["created_at"][:16] if act.get("created_at") else ""
                                st.caption(f"{act_date} — {act['action']}: {act.get('details', '')}")

                        # Stage movement buttons
                        stage_idx = stage_keys.index(lead["stage"])
                        btn_cols = st.columns(3)
                        with btn_cols[0]:
                            if stage_idx > 0:
                                prev_stage = stage_keys[stage_idx - 1]
                                if st.button("←", key=f"lead_back_{lead['id']}", help=f"Move to {LEAD_STAGES[prev_stage]['label']}"):
                                    execute_query(
                                        "UPDATE leads SET stage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                        [prev_stage, lead["id"]],
                                    )
                                    insert_row("lead_activity", {
                                        "lead_id": lead["id"],
                                        "action": "Stage changed",
                                        "details": f"{stage_info['label']} → {LEAD_STAGES[prev_stage]['label']}",
                                    })
                                    st.rerun()
                        with btn_cols[1]:
                            if stage_idx < len(stage_keys) - 1:
                                next_stage = stage_keys[stage_idx + 1]
                                if st.button("→", key=f"lead_fwd_{lead['id']}", help=f"Move to {LEAD_STAGES[next_stage]['label']}"):
                                    execute_query(
                                        "UPDATE leads SET stage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                        [next_stage, lead["id"]],
                                    )
                                    insert_row("lead_activity", {
                                        "lead_id": lead["id"],
                                        "action": "Stage changed",
                                        "details": f"{stage_info['label']} → {LEAD_STAGES[next_stage]['label']}",
                                    })
                                    st.rerun()
                        with btn_cols[2]:
                            if st.button("🗑️", key=f"lead_del_{lead['id']}", help="Delete lead"):
                                execute_query("DELETE FROM lead_activity WHERE lead_id = ?", [lead["id"]])
                                execute_query("DELETE FROM leads WHERE id = ?", [lead["id"]])
                                st.rerun()
            else:
                st.caption("No leads")

    # --- Add Lead Form ---
    st.markdown("---")
    _, lead_center, _ = st.columns([1, 2, 1])
    with lead_center:
        st.markdown(
            f"<h4 style='color:{COLORS['text_primary']}; text-align:center; "
            f"margin-bottom:8px;'>Add Lead</h4>",
            unsafe_allow_html=True,
        )
        with st.form("add_lead_form", clear_on_submit=True):
            lead_name = st.text_input("Name *")
            lc1, lc2 = st.columns(2)
            with lc1:
                lead_email = st.text_input("Email")
            with lc2:
                lead_phone = st.text_input("Phone")
            lc3, lc4 = st.columns(2)
            with lc3:
                lead_campaign = st.text_input("Campaign Name")
            with lc4:
                lead_ad = st.text_input("Ad Name")
            lead_notes = st.text_area("Notes", height=80)

            if st.form_submit_button("Add Lead", use_container_width=True):
                if not lead_name:
                    st.error("Name is required.")
                else:
                    new_id = insert_row("leads", {
                        "name": lead_name.strip(),
                        "email": lead_email.strip() or None,
                        "phone": lead_phone.strip() or None,
                        "campaign_name": lead_campaign.strip() or None,
                        "ad_name": lead_ad.strip() or None,
                        "notes": lead_notes.strip() or None,
                        "stage": "new",
                        "source": "manual",
                    })
                    insert_row("lead_activity", {
                        "lead_id": new_id,
                        "action": "Lead created",
                        "details": "Manually added",
                    })
                    st.success(f"Lead '{lead_name}' added!")
                    st.rerun()

# ---------------------------------------------------------------------------
# TAB 5: Ad Performance
# ---------------------------------------------------------------------------
with tab5:
    from datetime import datetime, timedelta
    import plotly.express as px
    from tools.meta_api import MetaAPI

    meta_ads_api = MetaAPI()

    # API status banner + sync button
    if meta_ads_api.is_configured():
        ad_sync_col1, ad_sync_col2 = st.columns([4, 1])
        with ad_sync_col1:
            st.success("Meta API connected — campaigns and metrics will auto-sync")
        with ad_sync_col2:
            if st.button("Sync All", key="sync_ads_btn", use_container_width=True):
                with st.spinner("Syncing campaigns, ad sets, ads & metrics from Meta..."):
                    camp_count = meta_ads_api.sync_campaigns()
                    metric_count = meta_ads_api.sync_metrics(days=30)
                st.success(f"Synced {camp_count} campaigns, {metric_count} metric entries!")
                st.rerun()
    else:
        st.info("Add META_ACCESS_TOKEN and META_AD_ACCOUNT_ID to .env to auto-sync ad performance data")

    ad_perf_tab1, ad_perf_tab2, ad_perf_tab3 = st.tabs(["Overview", "Campaigns", "Log Metrics"])

    # === OVERVIEW ===
    with ad_perf_tab1:
        # Date range filter
        date_options = ["Last 7 days", "Last 30 days", "Last 90 days", "All time"]
        ad_date_range = st.selectbox("Date Range", date_options, key="ad_overview_date")

        metric_where = ""
        metric_params = []
        if ad_date_range != "All time":
            days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
            cutoff = (datetime.now() - timedelta(days=days_map[ad_date_range])).strftime("%Y-%m-%d")
            metric_where = "WHERE metric_date >= ?"
            metric_params = [cutoff]

        metrics_data = execute_query(f"""
            SELECT
                COALESCE(SUM(spend), 0) as total_spend,
                COALESCE(SUM(impressions), 0) as total_impressions,
                COALESCE(SUM(clicks), 0) as total_clicks,
                COALESCE(SUM(conversions), 0) as total_conversions
            FROM ad_metrics
            {metric_where}
        """, metric_params)

        m = metrics_data[0] if metrics_data else {}

        total_impressions = m.get("total_impressions", 0)
        total_clicks = m.get("total_clicks", 0)
        total_spend = m.get("total_spend", 0)
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
        with mc1:
            st.metric("Total Spend", f"${total_spend:,.2f}")
        with mc2:
            st.metric("Impressions", f"{total_impressions:,}")
        with mc3:
            st.metric("Clicks", f"{total_clicks:,}")
        with mc4:
            st.metric("Conversions", f"{m.get('total_conversions', 0):,}")
        with mc5:
            st.metric("Avg CTR", f"{avg_ctr:.2f}%")
        with mc6:
            st.metric("Avg CPC", f"${avg_cpc:.2f}")

        # Spend over time chart
        daily_metrics = execute_query(f"""
            SELECT metric_date, SUM(spend) as daily_spend, SUM(clicks) as daily_clicks,
                   SUM(impressions) as daily_impressions, SUM(conversions) as daily_conversions
            FROM ad_metrics
            {metric_where}
            GROUP BY metric_date
            ORDER BY metric_date
        """, metric_params)

        if daily_metrics:
            fig_spend = px.line(
                daily_metrics,
                x="metric_date",
                y="daily_spend",
                title="Daily Spend",
                labels={"metric_date": "Date", "daily_spend": "Spend ($)"},
            )
            fig_spend.update_layout(
                plot_bgcolor=COLORS["surface"],
                paper_bgcolor=COLORS["background"],
                font_color=COLORS["text_primary"],
            )
            st.plotly_chart(fig_spend, use_container_width=True)

            # Campaign comparison
            campaign_metrics = execute_query(f"""
                SELECT ac.name, SUM(am.spend) as spend, SUM(am.clicks) as clicks,
                       SUM(am.impressions) as impressions, SUM(am.conversions) as conversions
                FROM ad_metrics am
                JOIN ad_campaigns ac ON am.campaign_id = ac.id
                {metric_where}
                GROUP BY ac.name
            """, metric_params)

            if campaign_metrics:
                fig_camp = px.bar(
                    campaign_metrics,
                    x="name",
                    y="spend",
                    title="Spend by Campaign",
                    labels={"name": "Campaign", "spend": "Spend ($)"},
                    color="name",
                )
                fig_camp.update_layout(
                    plot_bgcolor=COLORS["surface"],
                    paper_bgcolor=COLORS["background"],
                    font_color=COLORS["text_primary"],
                    showlegend=False,
                )
                st.plotly_chart(fig_camp, use_container_width=True)
        else:
            st.caption("No metrics data yet. Log metrics in the 'Log Metrics' tab.")

    # === CAMPAIGNS ===
    with ad_perf_tab2:
        campaigns = execute_query("SELECT * FROM ad_campaigns ORDER BY created_at DESC")

        if campaigns:
            for camp in campaigns:
                status_color = AD_STATUS_COLORS.get(camp["status"], "#94A3B5")
                budget_text = ""
                if camp.get("daily_budget"):
                    budget_text = f"${camp['daily_budget']:.2f}/day"
                elif camp.get("lifetime_budget"):
                    budget_text = f"${camp['lifetime_budget']:.2f} lifetime"

                date_range = ""
                if camp.get("start_date"):
                    date_range = f"{camp['start_date']}"
                    if camp.get("end_date"):
                        date_range += f" → {camp['end_date']}"

                with st.expander(
                    f"**{camp['name']}** — {camp['status'].title()} {budget_text}",
                    expanded=False,
                ):
                    cc1, cc2, cc3 = st.columns(3)
                    with cc1:
                        st.markdown(
                            f"**Status:** <span style='color:{status_color};'>{camp['status'].title()}</span>",
                            unsafe_allow_html=True,
                        )
                    with cc2:
                        if camp.get("objective"):
                            st.markdown(f"**Objective:** {camp['objective']}")
                    with cc3:
                        if date_range:
                            st.markdown(f"**Dates:** {date_range}")

                    if camp.get("notes"):
                        st.markdown(f"**Notes:** {camp['notes']}")

                    # Campaign-level metrics
                    camp_metrics = execute_query("""
                        SELECT COALESCE(SUM(spend),0) as spend, COALESCE(SUM(impressions),0) as imps,
                               COALESCE(SUM(clicks),0) as clicks, COALESCE(SUM(conversions),0) as convs
                        FROM ad_metrics WHERE campaign_id = ?
                    """, [camp["id"]])
                    if camp_metrics and camp_metrics[0]["spend"] > 0:
                        cm = camp_metrics[0]
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric("Spend", f"${cm['spend']:,.2f}")
                        with m2:
                            st.metric("Impressions", f"{cm['imps']:,}")
                        with m3:
                            st.metric("Clicks", f"{cm['clicks']:,}")
                        with m4:
                            st.metric("Conversions", f"{cm['convs']:,}")

                    # Ad Sets under this campaign
                    ad_sets = execute_query(
                        "SELECT * FROM ad_sets WHERE campaign_id = ? ORDER BY created_at DESC",
                        [camp["id"]],
                    )

                    if ad_sets:
                        st.markdown("**Ad Sets:**")
                        for aset in ad_sets:
                            aset_status_color = AD_STATUS_COLORS.get(aset["status"], "#94A3B5")
                            with st.expander(
                                f"{aset['name']} — {aset['status'].title()}",
                                expanded=False,
                            ):
                                st.markdown(
                                    f"**Status:** <span style='color:{aset_status_color};'>{aset['status'].title()}</span>",
                                    unsafe_allow_html=True,
                                )
                                if aset.get("targeting_summary"):
                                    st.markdown(f"**Targeting:** {aset['targeting_summary']}")

                                # Ads under this ad set
                                ads_list = execute_query(
                                    "SELECT * FROM ads WHERE ad_set_id = ? ORDER BY created_at DESC",
                                    [aset["id"]],
                                )
                                if ads_list:
                                    st.markdown("**Ads:**")
                                    for ad in ads_list:
                                        ad_color = AD_STATUS_COLORS.get(ad["status"], "#94A3B5")
                                        creative_html = ""
                                        if ad.get("creative_summary"):
                                            creative_html = (
                                                f'<br><span style="font-size:0.85em; color:{COLORS["text_light"]};">'
                                                f'{esc(ad["creative_summary"])}</span>'
                                            )
                                        st.markdown(
                                            f"<div style='background:{COLORS['background']}; "
                                            f"border:1px solid {COLORS['border']}; "
                                            f"border-left:3px solid {ad_color}; "
                                            f"border-radius:8px; padding:8px 12px; "
                                            f"margin-bottom:4px; font-size:0.9em; "
                                            f"color:{COLORS['text_primary']};'>"
                                            f"<b>{esc(ad['name'])}</b> — "
                                            f"<span style='color:{ad_color};'>{ad['status'].title()}</span>"
                                            f"{creative_html}</div>",
                                            unsafe_allow_html=True,
                                        )
                                else:
                                    st.caption("No ads in this ad set.")

                                # Add Ad form
                                with st.form(f"add_ad_{aset['id']}", clear_on_submit=True):
                                    st.markdown("**Add Ad**")
                                    ad_name = st.text_input("Ad Name *", key=f"ad_name_{aset['id']}")
                                    ad_creative = st.text_input("Creative Summary", key=f"ad_creative_{aset['id']}")
                                    if st.form_submit_button("Add Ad"):
                                        if ad_name:
                                            insert_row("ads", {
                                                "ad_set_id": aset["id"],
                                                "name": ad_name.strip(),
                                                "creative_summary": ad_creative.strip() or None,
                                            })
                                            st.success(f"Ad '{ad_name}' added!")
                                            st.rerun()
                                        else:
                                            st.error("Ad name is required.")

                    # Add Ad Set form
                    with st.form(f"add_adset_{camp['id']}", clear_on_submit=True):
                        st.markdown("**Add Ad Set**")
                        aset_name = st.text_input("Ad Set Name *", key=f"aset_name_{camp['id']}")
                        aset_targeting = st.text_input("Targeting Summary", key=f"aset_target_{camp['id']}")
                        if st.form_submit_button("Add Ad Set"):
                            if aset_name:
                                insert_row("ad_sets", {
                                    "campaign_id": camp["id"],
                                    "name": aset_name.strip(),
                                    "targeting_summary": aset_targeting.strip() or None,
                                })
                                st.success(f"Ad Set '{aset_name}' added!")
                                st.rerun()
                            else:
                                st.error("Ad set name is required.")
        else:
            st.caption("No campaigns yet.")

        # Add Campaign form
        st.markdown("---")
        _, camp_center, _ = st.columns([1, 2, 1])
        with camp_center:
            st.markdown(
                f"<h4 style='color:{COLORS['text_primary']}; text-align:center; "
                f"margin-bottom:8px;'>Add Campaign</h4>",
                unsafe_allow_html=True,
            )
            with st.form("add_campaign_form", clear_on_submit=True):
                camp_name = st.text_input("Campaign Name *")
                camp_obj = st.text_input("Objective", placeholder="e.g. Lead generation, Conversions...")
                cc1, cc2 = st.columns(2)
                with cc1:
                    camp_daily = st.number_input("Daily Budget ($)", min_value=0.0, step=1.0, value=0.0)
                with cc2:
                    camp_lifetime = st.number_input("Lifetime Budget ($)", min_value=0.0, step=1.0, value=0.0)
                cc3, cc4 = st.columns(2)
                with cc3:
                    camp_start = st.date_input("Start Date", value=None, key="camp_start")
                with cc4:
                    camp_end = st.date_input("End Date", value=None, key="camp_end")
                camp_notes = st.text_area("Notes", height=80, key="camp_notes")

                if st.form_submit_button("Add Campaign", use_container_width=True):
                    if not camp_name:
                        st.error("Campaign name is required.")
                    else:
                        insert_row("ad_campaigns", {
                            "name": camp_name.strip(),
                            "objective": camp_obj.strip() or None,
                            "daily_budget": camp_daily if camp_daily > 0 else None,
                            "lifetime_budget": camp_lifetime if camp_lifetime > 0 else None,
                            "start_date": str(camp_start) if camp_start else None,
                            "end_date": str(camp_end) if camp_end else None,
                            "notes": camp_notes.strip() or None,
                        })
                        st.success(f"Campaign '{camp_name}' added!")
                        st.rerun()

    # === LOG METRICS ===
    with ad_perf_tab3:
        _, log_center, _ = st.columns([1, 2, 1])
        with log_center:
            st.markdown(
                f"<h4 style='color:{COLORS['text_primary']}; text-align:center; "
                f"margin-bottom:8px;'>Log Daily Metrics</h4>",
                unsafe_allow_html=True,
            )

            all_campaigns = execute_query("SELECT id, name FROM ad_campaigns ORDER BY name")

            if not all_campaigns:
                st.caption("Add a campaign first in the Campaigns tab.")
            else:
                with st.form("log_metrics_form", clear_on_submit=True):
                    log_campaign = st.selectbox(
                        "Campaign *",
                        all_campaigns,
                        format_func=lambda c: c["name"],
                        key="log_campaign",
                    )

                    # Get ad sets for selected campaign
                    camp_ad_sets = []
                    if log_campaign:
                        camp_ad_sets = execute_query(
                            "SELECT id, name FROM ad_sets WHERE campaign_id = ? ORDER BY name",
                            [log_campaign["id"]],
                        )

                    log_adset = None
                    if camp_ad_sets:
                        log_adset = st.selectbox(
                            "Ad Set (optional)",
                            [None] + camp_ad_sets,
                            format_func=lambda a: "— All —" if a is None else a["name"],
                            key="log_adset",
                        )

                    log_ad = None
                    if log_adset:
                        adset_ads = execute_query(
                            "SELECT id, name FROM ads WHERE ad_set_id = ? ORDER BY name",
                            [log_adset["id"]],
                        )
                        if adset_ads:
                            log_ad = st.selectbox(
                                "Ad (optional)",
                                [None] + adset_ads,
                                format_func=lambda a: "— All —" if a is None else a["name"],
                                key="log_ad",
                            )

                    log_date = st.date_input("Date *", key="log_date")

                    lm1, lm2 = st.columns(2)
                    with lm1:
                        log_spend = st.number_input("Spend ($)", min_value=0.0, step=0.01, key="log_spend")
                        log_clicks = st.number_input("Clicks", min_value=0, step=1, key="log_clicks")
                    with lm2:
                        log_impressions = st.number_input("Impressions", min_value=0, step=1, key="log_imps")
                        log_conversions = st.number_input("Conversions", min_value=0, step=1, key="log_convs")

                    if st.form_submit_button("Log Metrics", use_container_width=True):
                        if not log_campaign:
                            st.error("Campaign is required.")
                        else:
                            # Auto-calculate CTR, CPC, CPM
                            calc_ctr = (log_clicks / log_impressions * 100) if log_impressions > 0 else 0
                            calc_cpc = (log_spend / log_clicks) if log_clicks > 0 else 0
                            calc_cpm = (log_spend / log_impressions * 1000) if log_impressions > 0 else 0

                            insert_row("ad_metrics", {
                                "campaign_id": log_campaign["id"],
                                "ad_set_id": log_adset["id"] if log_adset else None,
                                "ad_id": log_ad["id"] if log_ad else None,
                                "metric_date": str(log_date),
                                "spend": log_spend,
                                "impressions": log_impressions,
                                "clicks": log_clicks,
                                "conversions": log_conversions,
                                "ctr": calc_ctr,
                                "cpc": calc_cpc,
                                "cpm": calc_cpm,
                            })
                            st.success("Metrics logged!")
                            st.rerun()
