"""
Wavecrest Behavioral Health — Dashboard Theme

Southern California coastal aesthetic: calming blues, warm sand tones,
clean and peaceful. Inspired by the ASMR/peaceful content direction.
"""

# Brand colors
COLORS = {
    "primary": "#4A7C9B",           # Coastal blue
    "primary_light": "#7BA7BC",     # Light coastal blue
    "primary_dark": "#2C5F7C",      # Deep ocean
    "accent": "#D4A373",            # Warm sand / golden hour
    "accent_light": "#E8C9A0",      # Light sand
    "background": "#F7F5F2",        # Warm off-white
    "surface": "#FFFFFF",           # Clean white
    "text_primary": "#2C3E50",      # Deep navy-gray
    "text_secondary": "#6B7B8D",    # Muted blue-gray
    "text_light": "#94A3B5",        # Soft gray
    "success": "#7CB89E",           # Seafoam green
    "warning": "#E8A87C",           # Soft coral
    "error": "#D4726A",             # Muted red
    "border": "#E2DED8",            # Warm gray border
}

# Content pillar colors (match database seed)
PILLAR_COLORS = {
    "Education": "#4A90D9",
    "Affirming Messages": "#7B68EE",
    "Community": "#20B2AA",
    "Client Stories": "#DDA0DD",
    "Treatment Info": "#F0A050",
}

# Status colors
STATUS_COLORS = {
    "planned": "#94A3B5",
    "created": "#4A90D9",
    "reviewed": "#7B68EE",
    "scheduled": "#E8A87C",
    "published": "#7CB89E",
    # Script statuses
    "draft": "#94A3B5",
    "selected": "#4A90D9",
    "used": "#7CB89E",
    "archived": "#C4BDB5",
    # Idea statuses
    "new": "#4A90D9",
    "developing": "#E8A87C",
    "rejected": "#D4726A",
}

# Content type labels (human-readable)
CONTENT_TYPE_LABELS = {
    "still_image": "Still Image",
    "ugc_video": "UGC Video",
    "therapist_video": "Therapist Video",
    "carousel": "Carousel",
    "story": "Story",
    "reel": "Reel",
}

PLATFORM_LABELS = {
    "instagram": "Instagram",
    "facebook": "Facebook",
    "both": "Both",
}


def get_custom_css():
    """Return custom CSS for the Streamlit app."""
    return f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {COLORS['background']};
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {COLORS['surface']};
            border-right: 1px solid {COLORS['border']};
        }}

        /* Headers */
        h1, h2, h3 {{
            color: {COLORS['text_primary']} !important;
        }}

        /* Metric cards */
        div[data-testid="stMetric"] {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab"] {{
            color: {COLORS['text_secondary']};
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLORS['primary']} !important;
            border-bottom-color: {COLORS['primary']} !important;
        }}

        /* Buttons */
        .stButton > button {{
            border-radius: 8px;
            border: 1px solid {COLORS['border']};
            font-weight: 500;
        }}
        .stButton > button:hover {{
            border-color: {COLORS['primary']};
            color: {COLORS['primary']};
        }}

        /* Cards / containers */
        div[data-testid="stExpander"] {{
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            background-color: {COLORS['surface']};
        }}

        /* Status badges */
        .status-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }}

        /* Pillar tag */
        .pillar-tag {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
            color: white;
        }}
    </style>
    """


# Script category display config
SCRIPT_CATEGORIES = {
    "influencer_reels": {"label": "Influencer Focused Reels", "color": "#4A90D9"},
    "ad_reels": {"label": "Ad Focused Reels", "color": "#E8A87C"},
    "voiceover_reels": {"label": "Voiceover Reels", "color": "#7B68EE"},
    "therapist_scripts": {"label": "Therapist Scripts", "color": "#20B2AA"},
    "carousel_posts": {"label": "Carousel Posts", "color": "#DDA0DD"},
}

# Lead pipeline stages
LEAD_STAGES = {
    "new": {"label": "New", "color": "#4A90D9"},
    "contacted": {"label": "Contacted", "color": "#E8A87C"},
    "qualified": {"label": "Qualified", "color": "#7B68EE"},
    "enrolled": {"label": "Enrolled", "color": "#20B2AA"},
}

# Ad status colors
AD_STATUS_COLORS = {
    "active": "#7CB89E",
    "paused": "#E8A87C",
    "completed": "#94A3B5",
}

PRIORITY_COLORS = {
    "high": "#D4726A",      # Muted red (matches error)
    "medium": "#E8A87C",    # Soft coral (matches warning)
    "low": "#7CB89E",       # Seafoam green (matches success)
}


def priority_badge(priority):
    """Generate HTML for a colored priority badge."""
    color = PRIORITY_COLORS.get(priority, "#94A3B5")
    return f'<span class="status-badge" style="background-color: {color}20; color: {color};">{priority.title()}</span>'


def status_badge(status):
    """Generate HTML for a colored status badge."""
    color = STATUS_COLORS.get(status, "#94A3B5")
    return f'<span class="status-badge" style="background-color: {color}20; color: {color};">{status.title()}</span>'


def pillar_badge(pillar_name):
    """Generate HTML for a colored pillar badge."""
    color = PILLAR_COLORS.get(pillar_name, "#94A3B5")
    return f'<span class="pillar-tag" style="background-color: {color};">{pillar_name}</span>'
