"""
Wavecrest Behavioral Health — Dashboard Theme

Clean, professional design matching wavecrestbh.com branding.
"""

# Brand colors — matched to wavecrestbh.com
COLORS = {
    "primary": "#204CE5",           # Wavecrest blue
    "primary_light": "#6B8CF5",     # Light blue
    "primary_dark": "#044AD3",      # Dark blue (hover)
    "accent": "#399F4B",            # Green accent
    "accent_light": "#6BBF78",      # Light green
    "background": "#F2F3F5",        # Light gray background
    "surface": "#FFFFFF",           # White cards
    "text_primary": "#112337",      # Dark navy headings
    "text_secondary": "#585E6A",    # Medium gray body
    "text_light": "#686E77",        # Muted gray
    "success": "#399F4B",           # Green
    "warning": "#E8A87C",           # Soft coral
    "error": "#C02B0A",             # Red
    "border": "#E5E7EB",            # Cool gray border
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
    "planned": "#686E77",
    "created": "#204CE5",
    "reviewed": "#7B68EE",
    "scheduled": "#E8A87C",
    "published": "#399F4B",
    # Script statuses
    "draft": "#686E77",
    "selected": "#204CE5",
    "used": "#399F4B",
    "archived": "#686E77",
    # Idea statuses
    "new": "#204CE5",
    "developing": "#E8A87C",
    "rejected": "#C02B0A",
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
            font-weight: 600;
        }}

        /* Metric cards */
        div[data-testid="stMetric"] {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab"] {{
            color: {COLORS['text_secondary']};
            font-weight: 500;
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLORS['primary']} !important;
            border-bottom-color: {COLORS['primary']} !important;
        }}

        /* Primary buttons */
        .stButton > button[kind="primary"] {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 500;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: {COLORS['primary_dark']};
            color: white;
        }}

        /* Secondary buttons */
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
            border-radius: 10px;
            background-color: {COLORS['surface']};
        }}

        /* Form submit button */
        .stFormSubmitButton > button {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 500;
        }}
        .stFormSubmitButton > button:hover {{
            background-color: {COLORS['primary_dark']};
            color: white;
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

        /* ===== MOBILE RESPONSIVE ===== */
        @media (max-width: 768px) {{
            /* Stack all column layouts vertically */
            [data-testid="stHorizontalBlock"] {{
                flex-wrap: wrap !important;
            }}
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
                flex: 1 1 100% !important;
                width: 100% !important;
                min-width: 100% !important;
            }}

            /* Reduce main container padding */
            .stMainBlockContainer {{
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }}
            section.main > div {{
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }}
            .block-container {{
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
                padding-top: 1rem !important;
            }}

            /* Tabs: smaller text, horizontal scroll */
            .stTabs [data-baseweb="tab-list"] {{
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch;
                gap: 0 !important;
                flex-wrap: nowrap !important;
            }}
            .stTabs [data-baseweb="tab"] {{
                font-size: 0.78em !important;
                padding: 8px 10px !important;
                white-space: nowrap !important;
            }}

            /* Metric cards: compact on mobile */
            div[data-testid="stMetric"] {{
                padding: 10px !important;
            }}
            div[data-testid="stMetric"] label {{
                font-size: 0.75em !important;
            }}
            div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
                font-size: 1.2em !important;
            }}

            /* Instagram embeds: responsive */
            iframe {{
                max-width: 100% !important;
                height: auto !important;
                min-height: 500px !important;
                aspect-ratio: 400 / 760;
            }}

            /* Buttons: larger tap targets */
            .stButton > button {{
                min-height: 44px !important;
                font-size: 0.9em !important;
            }}
            .stFormSubmitButton > button {{
                min-height: 44px !important;
            }}

            /* Expanders: tighter spacing */
            div[data-testid="stExpander"] {{
                margin-bottom: 4px !important;
            }}

            /* Headers: slightly smaller */
            h1 {{
                font-size: 1.5em !important;
            }}
            h2 {{
                font-size: 1.3em !important;
            }}
            h3 {{
                font-size: 1.1em !important;
            }}

            /* Prevent iOS auto-zoom on form inputs */
            input, select, textarea {{
                font-size: 16px !important;
            }}

            /* Plotly charts: no overflow */
            .js-plotly-plot {{
                max-width: 100% !important;
                overflow-x: auto !important;
            }}
        }}
    </style>
    """


# Script category display config
SCRIPT_CATEGORIES = {
    "influencer_reels": {"label": "Influencer Focused Reels", "color": "#204CE5"},
    "ad_reels": {"label": "Ad Focused Reels", "color": "#E8A87C"},
    "voiceover_reels": {"label": "Voiceover Reels", "color": "#7B68EE"},
    "therapist_scripts": {"label": "Therapist Scripts", "color": "#399F4B"},
    "carousel_posts": {"label": "Carousel Posts", "color": "#DDA0DD"},
    "suggestions": {"label": "Suggestions", "color": "#044AD3"},
}

# Lead pipeline stages
LEAD_STAGES = {
    "new": {"label": "New", "color": "#204CE5"},
    "contacted": {"label": "Contacted", "color": "#E8A87C"},
    "qualified": {"label": "Qualified", "color": "#7B68EE"},
    "enrolled": {"label": "Enrolled", "color": "#399F4B"},
}

# Ad status colors
AD_STATUS_COLORS = {
    "active": "#399F4B",
    "paused": "#E8A87C",
    "completed": "#686E77",
}

PRIORITY_COLORS = {
    "high": "#C02B0A",      # Red (matches error)
    "medium": "#E8A87C",    # Soft coral (matches warning)
    "low": "#399F4B",       # Green (matches success)
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
