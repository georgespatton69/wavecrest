"""Reusable metric card components."""

import streamlit as st


def metric_with_trend(label, value, delta=None, delta_color="normal"):
    """Display a metric with optional trend delta."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def kpi_row(metrics):
    """Display a row of KPI cards. metrics is a list of (label, value, delta) tuples."""
    cols = st.columns(len(metrics))
    for col, (label, value, *rest) in zip(cols, metrics):
        delta = rest[0] if rest else None
        with col:
            st.metric(label=label, value=value, delta=delta)
