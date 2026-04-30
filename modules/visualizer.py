"""
Visualization Module for SmartEDA
Generates all Plotly charts for the automated visualization dashboard.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional, Dict


# ── Color palette consistent with SmartEDA's dark theme ──────────────────────
ACCENT = "#6C63FF"
PALETTE = px.colors.qualitative.Vivid
HEATMAP_COLORS = "RdBu_r"


def plot_distribution_histograms(df: pd.DataFrame, numeric_cols: List[str]) -> List[go.Figure]:
    """
    Generate distribution histograms with box plot overlays for each numeric column.
    Returns a list of Plotly Figure objects.
    """
    figures = []
    for col in numeric_cols:
        series = df[col].dropna()
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.75, 0.25],
            shared_xaxes=True,
            vertical_spacing=0.03,
        )
        # Histogram
        fig.add_trace(
            go.Histogram(
                x=series,
                name=col,
                marker_color=ACCENT,
                opacity=0.85,
                nbinsx=40,
            ),
            row=1, col=1,
        )
        # Box plot
        fig.add_trace(
            go.Box(
                x=series,
                name=col,
                marker_color=ACCENT,
                boxmean=True,
                orientation="h",
            ),
            row=2, col=1,
        )
        fig.update_layout(
            title=f"Distribution of {col}",
            template="plotly_dark",
            paper_bgcolor="rgba(26,29,46,0.95)",
            plot_bgcolor="rgba(26,29,46,0.95)",
            font=dict(family="Inter, sans-serif", color="#FAFAFA"),
            showlegend=False,
            height=420,
            margin=dict(l=40, r=20, t=50, b=30),
        )
        figures.append((col, fig))
    return figures


def plot_correlation_heatmap(corr_matrix: pd.DataFrame) -> Optional[go.Figure]:
    """Generate an annotated Pearson correlation heatmap."""
    if corr_matrix.empty or corr_matrix.shape[0] < 2:
        return None

    z = corr_matrix.values
    labels = corr_matrix.columns.tolist()

    # Round annotations
    text = [[f"{v:.2f}" for v in row] for row in z]

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=labels,
            y=labels,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=11),
            colorscale=HEATMAP_COLORS,
            zmid=0,
            zmin=-1,
            zmax=1,
            colorbar=dict(title="r", tickvals=[-1, -0.5, 0, 0.5, 1]),
        )
    )
    fig.update_layout(
        title="Pearson Correlation Heatmap",
        template="plotly_dark",
        paper_bgcolor="rgba(26,29,46,0.95)",
        plot_bgcolor="rgba(26,29,46,0.95)",
        font=dict(family="Inter, sans-serif", color="#FAFAFA"),
        height=max(400, 60 * len(labels)),
        margin=dict(l=100, r=20, t=60, b=100),
        xaxis=dict(tickangle=45),
    )
    return fig


def plot_categorical_bar_charts(df: pd.DataFrame, categorical_cols: List[str]) -> List[tuple]:
    """Generate bar charts showing value count distributions for categorical columns."""
    figures = []
    for col in categorical_cols:
        vc = df[col].value_counts().head(15).reset_index()
        vc.columns = ["Value", "Count"]
        vc["Percentage"] = (vc["Count"] / len(df) * 100).round(1)

        fig = px.bar(
            vc,
            x="Value",
            y="Count",
            text="Percentage",
            color="Count",
            color_continuous_scale=[[0, "#2D2B55"], [0.5, ACCENT], [1, "#A8A4FF"]],
            title=f"Value Distribution: {col}",
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            marker_line_color="rgba(0,0,0,0)",
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(26,29,46,0.95)",
            plot_bgcolor="rgba(26,29,46,0.95)",
            font=dict(family="Inter, sans-serif", color="#FAFAFA"),
            height=380,
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=40, r=20, t=60, b=80),
            xaxis=dict(tickangle=30),
        )
        figures.append((col, fig))
    return figures


def plot_missing_values(missing_df: pd.DataFrame) -> Optional[go.Figure]:
    """Generate a bar chart showing missing value percentages per column."""
    has_missing = missing_df[missing_df["Missing Count"] > 0].copy()
    if has_missing.empty:
        return None

    has_missing = has_missing.sort_values("Missing %", ascending=True)
    colors = [
        "#FF4B4B" if pct > 50 else "#FFB347" if pct > 20 else ACCENT
        for pct in has_missing["Missing %"]
    ]

    fig = go.Figure(
        go.Bar(
            x=has_missing["Missing %"],
            y=has_missing["Column"],
            orientation="h",
            marker_color=colors,
            text=[f"{v}%" for v in has_missing["Missing %"]],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Missing Values by Column",
        xaxis_title="Missing %",
        template="plotly_dark",
        paper_bgcolor="rgba(26,29,46,0.95)",
        plot_bgcolor="rgba(26,29,46,0.95)",
        font=dict(family="Inter, sans-serif", color="#FAFAFA"),
        height=max(300, 35 * len(has_missing)),
        margin=dict(l=150, r=80, t=60, b=40),
        xaxis=dict(range=[0, min(100, has_missing["Missing %"].max() * 1.2)]),
    )
    return fig


def plot_scatter_high_correlation(
    df: pd.DataFrame,
    top_correlations: pd.DataFrame,
    max_plots: int = 6,
) -> List[tuple]:
    """Generate scatter plots for highly correlated column pairs."""
    figures = []
    if top_correlations.empty:
        return figures

    shown = 0
    for _, row in top_correlations.iterrows():
        if shown >= max_plots:
            break
        col_a, col_b = row["Column A"], row["Column B"]
        corr_val = row["Correlation"]

        if col_a not in df.columns or col_b not in df.columns:
            continue

        plot_df = df[[col_a, col_b]].dropna()
        if len(plot_df) == 0:
            continue

        # Try to add a color dimension from the first categorical col
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        color_col = cat_cols[0] if cat_cols else None

        if color_col and color_col in df.columns:
            plot_df2 = df[[col_a, col_b, color_col]].dropna()
            fig = px.scatter(
                plot_df2,
                x=col_a,
                y=col_b,
                color=color_col,
                trendline="ols",
                color_discrete_sequence=PALETTE,
                title=f"{col_a} vs {col_b}  (r = {corr_val})",
                opacity=0.75,
            )
        else:
            fig = px.scatter(
                plot_df,
                x=col_a,
                y=col_b,
                trendline="ols",
                color_discrete_sequence=[ACCENT],
                title=f"{col_a} vs {col_b}  (r = {corr_val})",
                opacity=0.75,
            )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(26,29,46,0.95)",
            plot_bgcolor="rgba(26,29,46,0.95)",
            font=dict(family="Inter, sans-serif", color="#FAFAFA"),
            height=400,
            margin=dict(l=60, r=20, t=60, b=50),
        )
        figures.append((f"{col_a}_vs_{col_b}", fig))
        shown += 1
    return figures


def plot_outlier_boxplots(df: pd.DataFrame, iqr_bounds: Dict, numeric_cols: List[str]) -> List[tuple]:
    """
    Plot box plots showing IQR bounds and outlier points per column.
    """
    figures = []
    for col in numeric_cols[:12]:  # limit to 12 columns
        series = df[col].dropna()
        if series.empty:
            continue

        fig = go.Figure()
        fig.add_trace(go.Box(
            y=series,
            name=col,
            marker_color=ACCENT,
            boxmean=True,
            boxpoints="outliers",
            jitter=0.3,
            pointpos=-1.6,
            marker=dict(
                outliercolor="#FF4B4B",
                size=4,
                line=dict(width=1, color="#FF4B4B"),
            ),
        ))

        # Add bound lines if available
        if col in iqr_bounds:
            lower, upper = iqr_bounds[col]
            fig.add_hline(y=lower, line_dash="dot", line_color="#FFB347",
                          annotation_text=f"Lower: {lower:.2f}", annotation_position="right")
            fig.add_hline(y=upper, line_dash="dot", line_color="#FFB347",
                          annotation_text=f"Upper: {upper:.2f}", annotation_position="right")

        fig.update_layout(
            title=f"Outlier Box Plot: {col}",
            template="plotly_dark",
            paper_bgcolor="rgba(26,29,46,0.95)",
            plot_bgcolor="rgba(26,29,46,0.95)",
            font=dict(family="Inter, sans-serif", color="#FAFAFA"),
            height=350,
            showlegend=False,
            margin=dict(l=60, r=100, t=60, b=40),
        )
        figures.append((col, fig))
    return figures


def plot_pairplot_matrix(df: pd.DataFrame, numeric_cols: List[str], max_cols: int = 5) -> Optional[go.Figure]:
    """Generate a scatter matrix for numeric columns (limited to max_cols)."""
    cols = numeric_cols[:max_cols]
    if len(cols) < 2:
        return None

    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    color_col = cat_cols[0] if cat_cols else None

    plot_df = df[cols + ([color_col] if color_col else [])].dropna()

    fig = px.scatter_matrix(
        plot_df,
        dimensions=cols,
        color=color_col,
        color_discrete_sequence=PALETTE,
        title="Scatter Matrix (Pair Plot)",
        opacity=0.6,
    )
    fig.update_traces(diagonal_visible=False, showupperhalf=False)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(26,29,46,0.95)",
        plot_bgcolor="rgba(26,29,46,0.95)",
        font=dict(family="Inter, sans-serif", color="#FAFAFA", size=10),
        height=600,
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig
