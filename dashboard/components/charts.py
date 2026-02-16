"""Reusable chart components with Wavecrest coastal theme."""

import plotly.graph_objects as go
import plotly.express as px
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from styles.theme import COLORS, PILLAR_COLORS


def apply_wavecrest_layout(fig):
    """Apply the Wavecrest coastal theme to a Plotly figure."""
    fig.update_layout(
        plot_bgcolor=COLORS["background"],
        paper_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text_primary"], family="Inter, sans-serif"),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=COLORS["border"],
        ),
    )
    fig.update_xaxes(gridcolor=COLORS["border"], linecolor=COLORS["border"])
    fig.update_yaxes(gridcolor=COLORS["border"], linecolor=COLORS["border"])
    return fig


def pillar_bar_chart(data, title="Posts by Pillar"):
    """Bar chart showing distribution across content pillars."""
    names = [d["pillar"] or "Unassigned" for d in data]
    counts = [d["count"] for d in data]
    bar_colors = [PILLAR_COLORS.get(n, COLORS["text_light"]) for n in names]

    fig = go.Figure(data=[
        go.Bar(x=names, y=counts, marker_color=bar_colors, text=counts, textposition="auto")
    ])
    fig.update_layout(title=title, xaxis_title="", yaxis_title="Posts")
    return apply_wavecrest_layout(fig)


def timeline_chart(dates, values, title="", line_color=None):
    """Simple line chart for time series data."""
    color = line_color or COLORS["primary"]
    fig = go.Figure(data=[
        go.Scatter(
            x=dates, y=values, mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color),
        )
    ])
    fig.update_layout(title=title, xaxis_title="", yaxis_title="")
    return apply_wavecrest_layout(fig)


def engagement_donut(data, title="Content Type Mix"):
    """Donut chart for content type or engagement distribution."""
    labels = [d["label"] for d in data]
    values = [d["value"] for d in data]
    colors = [PILLAR_COLORS.get(l, COLORS["primary_light"]) for l in labels]

    fig = go.Figure(data=[
        go.Pie(
            labels=labels, values=values, hole=0.5,
            marker=dict(colors=colors),
            textposition="outside",
        )
    ])
    fig.update_layout(title=title)
    return apply_wavecrest_layout(fig)
