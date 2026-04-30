"""
Data Profiler Module for SmartEDA
Computes comprehensive statistical metrics for any uploaded CSV dataset.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, Tuple, List


def load_csv(uploaded_file) -> pd.DataFrame:
    """
    Load a CSV file from Streamlit's UploadedFile object.
    Handles common encoding issues (BOM, latin-1, cp1252) and
    strips hidden whitespace from string columns to ensure
    accurate duplicate detection and profiling.
    """
    import io

    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)  # reset for potential re-read

    # Try encodings in order of preference
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    df = None
    last_err = None
    for enc in encodings:
        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), encoding=enc)
            break
        except Exception as e:
            last_err = e
            continue

    if df is None:
        raise ValueError(f"Failed to load CSV after trying multiple encodings: {last_err}")

    # Strip leading/trailing whitespace from ALL string columns
    # (invisible whitespace causes false-negatives in duplicate detection)
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.strip()

    # Also strip whitespace from column names themselves
    df.columns = df.columns.str.strip()

    return df


def get_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Separate columns into numeric and categorical."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    return {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
    }


def compute_missing_info(df: pd.DataFrame) -> pd.DataFrame:
    """Compute missing value counts and percentages per column."""
    total = len(df)
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / total * 100).round(2)
    result = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": missing_count.values,
        "Missing %": missing_pct.values,
        "Data Type": df.dtypes.values.astype(str),
    }).reset_index(drop=True)
    result = result.sort_values("Missing Count", ascending=False)
    return result


def compute_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute extended descriptive statistics for numeric columns:
    mean, median, std, min, max, skewness, kurtosis.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return pd.DataFrame()

    rows = []
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        rows.append({
            "Column": col,
            "Count": int(series.count()),
            "Mean": round(float(series.mean()), 4),
            "Median": round(float(series.median()), 4),
            "Std Dev": round(float(series.std()), 4),
            "Min": round(float(series.min()), 4),
            "Max": round(float(series.max()), 4),
            "Skewness": round(float(stats.skew(series)), 4),
            "Kurtosis": round(float(stats.kurtosis(series)), 4),
        })
    return pd.DataFrame(rows)


def compute_cardinality(df: pd.DataFrame) -> pd.DataFrame:
    """Compute unique value counts and cardinality ratio per column."""
    rows = []
    for col in df.columns:
        n_unique = df[col].nunique()
        total = len(df)
        rows.append({
            "Column": col,
            "Unique Values": n_unique,
            "Cardinality %": round(n_unique / total * 100, 2) if total > 0 else 0,
            "Sample Values": str(df[col].dropna().unique()[:5].tolist()),
        })
    return pd.DataFrame(rows)


def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Pearson correlation matrix for numeric columns."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return pd.DataFrame()
    return numeric_df.corr(method="pearson").round(4)


def get_top_correlations(corr_matrix: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Extract strongly correlated column pairs from the correlation matrix."""
    if corr_matrix.empty:
        return pd.DataFrame()
    pairs = []
    cols = corr_matrix.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr_matrix.iloc[i, j]
            if abs(val) >= threshold:
                pairs.append({
                    "Column A": cols[i],
                    "Column B": cols[j],
                    "Correlation": round(val, 4),
                    "Strength": _correlation_label(val),
                })
    df_pairs = pd.DataFrame(pairs)
    if not df_pairs.empty:
        df_pairs = df_pairs.sort_values("Correlation", key=abs, ascending=False)
    return df_pairs


def _correlation_label(val: float) -> str:
    abs_val = abs(val)
    sign = "positive" if val > 0 else "negative"
    if abs_val >= 0.9:
        return f"Very strong {sign}"
    elif abs_val >= 0.7:
        return f"Strong {sign}"
    elif abs_val >= 0.5:
        return f"Moderate {sign}"
    else:
        return f"Weak {sign}"


def compute_categorical_stats(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Compute value counts for each categorical column."""
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    result = {}
    for col in cat_cols:
        vc = df[col].value_counts().reset_index()
        vc.columns = ["Value", "Count"]
        vc["Percentage"] = (vc["Count"] / len(df) * 100).round(2)
        result[col] = vc.head(20)  # top 20 categories
    return result


def full_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run all profiling steps and return a comprehensive profile dictionary.
    This is the main entry point used by the app.
    """
    col_types = get_column_types(df)
    missing_info = compute_missing_info(df)
    desc_stats = compute_descriptive_stats(df)
    cardinality = compute_cardinality(df)
    corr_matrix = compute_correlations(df)
    top_corr = get_top_correlations(corr_matrix)
    cat_stats = compute_categorical_stats(df)
    # Duplicate detection: strict exact match across ALL columns.
    # A row is a duplicate only if every single column value is identical
    # to a previously seen row. This is the standard, universally expected
    # definition — no heuristics or column exclusions.
    duplicate_count = int(df.duplicated(keep='first').sum())

    profile = {
        "shape": df.shape,
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
        "column_types": col_types,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "duplicate_count": duplicate_count,
        "duplicate_pct": round(duplicate_count / len(df) * 100, 2) if len(df) > 0 else 0,
        "missing_info": missing_info,
        "desc_stats": desc_stats,
        "cardinality": cardinality,
        "corr_matrix": corr_matrix,
        "top_correlations": top_corr,
        "categorical_stats": cat_stats,
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 3),
    }
    return profile


def profile_to_text(profile: Dict[str, Any], df: pd.DataFrame) -> str:
    """
    Serialize the profile into a compact text string suitable for LLM context.
    """
    lines = []
    lines.append(f"=== DATASET PROFILE ===")
    lines.append(f"Shape: {profile['n_rows']} rows × {profile['n_cols']} columns")
    lines.append(f"Memory Usage: {profile['memory_usage_mb']} MB")
    lines.append(f"Duplicate Rows: {profile['duplicate_count']} ({profile['duplicate_pct']}%)")
    lines.append(f"\nColumn Types:")
    lines.append(f"  Numeric: {profile['column_types']['numeric']}")
    lines.append(f"  Categorical: {profile['column_types']['categorical']}")
    lines.append(f"  Datetime: {profile['column_types']['datetime']}")

    # Missing values
    missing_df = profile["missing_info"]
    high_missing = missing_df[missing_df["Missing %"] > 0]
    if not high_missing.empty:
        lines.append(f"\nColumns with Missing Values:")
        for _, row in high_missing.iterrows():
            lines.append(f"  {row['Column']}: {row['Missing Count']} missing ({row['Missing %']}%)")
    else:
        lines.append("\nNo missing values detected.")

    # Descriptive stats
    desc = profile["desc_stats"]
    if not desc.empty:
        lines.append(f"\nDescriptive Statistics (Numeric Columns):")
        for _, row in desc.iterrows():
            lines.append(
                f"  {row['Column']}: mean={row['Mean']}, median={row['Median']}, "
                f"std={row['Std Dev']}, min={row['Min']}, max={row['Max']}, "
                f"skewness={row['Skewness']}, kurtosis={row['Kurtosis']}"
            )

    # Cardinality
    lines.append(f"\nCardinality:")
    for _, row in profile["cardinality"].iterrows():
        lines.append(f"  {row['Column']}: {row['Unique Values']} unique values ({row['Cardinality %']}%)")

    # Top correlations
    top_c = profile["top_correlations"]
    if not top_c.empty:
        lines.append(f"\nTop Pearson Correlations (|r| >= 0.5):")
        for _, row in top_c.iterrows():
            lines.append(f"  {row['Column A']} ↔ {row['Column B']}: r={row['Correlation']} ({row['Strength']})")

    # Categorical top values
    cat_stats = profile["categorical_stats"]
    if cat_stats:
        lines.append(f"\nCategorical Column Summaries:")
        for col, vc_df in cat_stats.items():
            top3 = vc_df.head(3)
            vals = ", ".join([f"{r['Value']}({r['Count']})" for _, r in top3.iterrows()])
            lines.append(f"  {col}: top values → {vals}")

    # First few rows as sample
    lines.append(f"\nSample Data (first 3 rows):")
    lines.append(df.head(3).to_string(index=False))

    return "\n".join(lines)
