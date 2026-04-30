"""
Utility Helpers for SmartEDA
Shared formatting and display helpers used across the app.
"""

import pandas as pd
import numpy as np
from typing import Any


def fmt_number(val: Any, decimals: int = 2) -> str:
    """Format a number nicely for display (handles int, float, NaN)."""
    try:
        if pd.isna(val):
            return "N/A"
        if isinstance(val, (int, np.integer)):
            return f"{int(val):,}"
        return f"{float(val):,.{decimals}f}"
    except Exception:
        return str(val)


def pct_bar(pct: float, width: int = 20) -> str:
    """Generate a simple text percentage bar."""
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled) + f" {pct:.1f}%"


def truncate_df_for_display(df: pd.DataFrame, max_rows: int = 500) -> pd.DataFrame:
    """Return a copy of the DataFrame limited to max_rows for safe display."""
    if len(df) > max_rows:
        return df.head(max_rows)
    return df


def get_quality_badge(missing_pct: float, duplicate_pct: float) -> tuple[str, str]:
    """
    Return (label, color_hex) quality badge based on missing value and duplicate rates.
    """
    score = 100 - missing_pct - (duplicate_pct * 0.5)
    if score >= 90:
        return "Excellent", "#00C853"
    elif score >= 75:
        return "Good", "#64DD17"
    elif score >= 55:
        return "Fair", "#FFD600"
    else:
        return "Poor", "#FF1744"


def skewness_label(skew: float) -> str:
    """Return a human-readable label for a skewness value."""
    if abs(skew) < 0.5:
        return "approximately symmetric"
    elif skew > 1.0:
        return "highly right-skewed (positive)"
    elif skew > 0.5:
        return "moderately right-skewed"
    elif skew < -1.0:
        return "highly left-skewed (negative)"
    else:
        return "moderately left-skewed"


def dtype_icon(dtype_str: str) -> str:
    """Return an emoji icon for a data type string."""
    dtype_str = dtype_str.lower()
    if "int" in dtype_str or "float" in dtype_str:
        return "🔢"
    elif "object" in dtype_str or "string" in dtype_str:
        return "🔤"
    elif "bool" in dtype_str:
        return "☑️"
    elif "datetime" in dtype_str:
        return "📅"
    elif "category" in dtype_str:
        return "🏷️"
    else:
        return "❓"


def safe_divide(a, b, default=0):
    """Safe division that returns default if b is 0."""
    try:
        return a / b if b != 0 else default
    except Exception:
        return default


CARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Reset and base */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Animated gradient header */
.smarteda-header {
    background: linear-gradient(135deg, #6C63FF 0%, #3B28CC 40%, #9B59B6 100%);
    background-size: 200% 200%;
    animation: gradientShift 6s ease infinite;
    border-radius: 18px;
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(108, 99, 255, 0.35);
}
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.smarteda-header h1 {
    color: #fff;
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 0;
    text-shadow: 0 2px 16px rgba(0,0,0,0.3);
}
.smarteda-header p {
    color: rgba(255,255,255,0.85);
    font-size: 1.05rem;
    margin: 0.5rem 0 0;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(145deg, #1A1D2E, #22253A);
    border: 1px solid rgba(108, 99, 255, 0.25);
    border-radius: 14px;
    padding: 1.2rem 1rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 28px rgba(108, 99, 255, 0.3);
}
.metric-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #8B86C8;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-size: 2rem;
    font-weight: 800;
    color: #6C63FF;
    line-height: 1;
}
.metric-sub {
    font-size: 0.75rem;
    color: #7A7A9A;
    margin-top: 0.3rem;
}

/* Quality badge */
.quality-badge {
    display: inline-block;
    padding: 0.35rem 1rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* Info box */
.info-box {
    background: rgba(108, 99, 255, 0.08);
    border-left: 4px solid #6C63FF;
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    color: #C8C4FF;
    font-size: 0.92rem;
}

/* Section divider */
.section-divider {
    height: 2px;
    background: linear-gradient(90deg, #6C63FF, transparent);
    border-radius: 2px;
    margin: 1.5rem 0;
}

/* Chat bubbles */
.chat-user {
    background: linear-gradient(135deg, #3B28CC, #6C63FF);
    color: white;
    padding: 0.85rem 1.1rem;
    border-radius: 18px 18px 4px 18px;
    margin: 0.5rem 0 0.5rem auto;
    max-width: 80%;
    font-size: 0.93rem;
    box-shadow: 0 4px 12px rgba(108,99,255,0.3);
}
.chat-assistant {
    background: linear-gradient(145deg, #1A1D2E, #22253A);
    border: 1px solid rgba(108, 99, 255, 0.2);
    color: #E0DEFC;
    padding: 0.85rem 1.1rem;
    border-radius: 18px 18px 18px 4px;
    margin: 0.5rem auto 0.5rem 0;
    max-width: 85%;
    font-size: 0.93rem;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(26, 29, 46, 0.6);
    padding: 0.5rem 0.8rem;
    border-radius: 14px;
    border: 1px solid rgba(108, 99, 255, 0.15);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 0.5rem 1.1rem;
    font-weight: 600;
    font-size: 0.88rem;
    color: #8B86C8;
    background: transparent;
    border: none;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6C63FF, #3B28CC) !important;
    color: #fff !important;
    box-shadow: 0 4px 14px rgba(108, 99, 255, 0.4);
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1A1D2E; }
::-webkit-scrollbar-thumb { background: #6C63FF; border-radius: 3px; }

/* Override Streamlit defaults */
.stDataFrame { border-radius: 10px; overflow: hidden; }
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1A1D2E, #22253A);
    border: 1px solid rgba(108, 99, 255, 0.25);
    border-radius: 12px;
    padding: 1rem;
}
</style>
"""
