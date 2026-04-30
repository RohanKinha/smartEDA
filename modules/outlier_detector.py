"""
Outlier Detection Module for SmartEDA
Implements IQR and Z-score based outlier detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


def detect_outliers_iqr(df: pd.DataFrame, multiplier: float = 1.5) -> Dict[str, Any]:
    """
    Detect outliers using the Inter-Quartile Range (IQR) method.
    Returns per-column stats and a combined outlier flag DataFrame.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return {"summary": pd.DataFrame(), "flagged_rows": pd.DataFrame()}

    summary_rows = []
    outlier_flags = pd.DataFrame(index=df.index)

    for col in numeric_cols:
        series = df[col].dropna()
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - multiplier * IQR
        upper = Q3 + multiplier * IQR
        mask = (df[col] < lower) | (df[col] > upper)
        outlier_count = mask.sum()
        outlier_flags[col] = mask

        summary_rows.append({
            "Column": col,
            "Q1": round(Q1, 4),
            "Q3": round(Q3, 4),
            "IQR": round(IQR, 4),
            "Lower Bound": round(lower, 4),
            "Upper Bound": round(upper, 4),
            "Outlier Count": int(outlier_count),
            "Outlier %": round(outlier_count / len(df) * 100, 2),
        })

    summary_df = pd.DataFrame(summary_rows).sort_values("Outlier Count", ascending=False)

    # Rows where ANY column is an outlier
    any_outlier = outlier_flags.any(axis=1)
    flagged_df = df[any_outlier].copy()
    flagged_df.insert(0, "Row Index", flagged_df.index)

    return {
        "summary": summary_df,
        "flagged_rows": flagged_df.reset_index(drop=True),
        "n_flagged": int(any_outlier.sum()),
        "bounds": {
            row["Column"]: (row["Lower Bound"], row["Upper Bound"])
            for _, row in summary_df.iterrows()
        },
    }


def detect_outliers_zscore(df: pd.DataFrame, threshold: float = 3.0) -> Dict[str, Any]:
    """
    Detect outliers using Z-score method.
    Rows with |z| > threshold for any numeric column are flagged.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return {"summary": pd.DataFrame(), "flagged_rows": pd.DataFrame()}

    summary_rows = []
    outlier_flags = pd.DataFrame(index=df.index)

    for col in numeric_cols:
        series = df[col]
        mean = series.mean()
        std = series.std()
        if std == 0:
            outlier_flags[col] = False
            continue
        z_scores = (series - mean) / std
        mask = z_scores.abs() > threshold
        outlier_count = mask.sum()
        outlier_flags[col] = mask

        summary_rows.append({
            "Column": col,
            "Mean": round(mean, 4),
            "Std Dev": round(std, 4),
            "Threshold": threshold,
            "Outlier Count": int(outlier_count),
            "Outlier %": round(outlier_count / len(df) * 100, 2),
            "Max |Z-Score|": round(z_scores.abs().max(), 4),
        })

    summary_df = pd.DataFrame(summary_rows).sort_values("Outlier Count", ascending=False)

    any_outlier = outlier_flags.any(axis=1)
    flagged_df = df[any_outlier].copy()
    flagged_df.insert(0, "Row Index", flagged_df.index)

    return {
        "summary": summary_df,
        "flagged_rows": flagged_df.reset_index(drop=True),
        "n_flagged": int(any_outlier.sum()),
    }


def outlier_summary_text(iqr_result: Dict, zscore_result: Dict) -> str:
    """Generate a brief text summary of outlier detection results."""
    lines = ["=== OUTLIER DETECTION SUMMARY ==="]
    lines.append(f"IQR Method: {iqr_result.get('n_flagged', 0)} rows flagged as outliers")
    lines.append(f"Z-Score Method: {zscore_result.get('n_flagged', 0)} rows flagged as outliers")

    if not iqr_result["summary"].empty:
        top = iqr_result["summary"].iloc[0]
        lines.append(f"Most outlier-prone column (IQR): {top['Column']} → {top['Outlier Count']} outliers ({top['Outlier %']}%)")

    return "\n".join(lines)
