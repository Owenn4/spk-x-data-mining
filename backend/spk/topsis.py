"""
TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) Engine
for Multi-Criteria Decision Making (SPK) on Indonesian Stock Portfolio Selection.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("spk_mining.topsis")

# Default criteria definitions based on 5-Year Audited CAGR Metrics (2020-2024):
# type: 'benefit' (higher is better) or 'cost' (lower is better)
DEFAULT_CRITERIA = {
    "rev_growth": {"type": "benefit", "weight": 0.30, "label": "5-Yr Revenue CAGR (%)"},
    "net_growth": {"type": "benefit", "weight": 0.35, "label": "5-Yr Net Income CAGR (%)"},
    "asset_growth": {"type": "benefit", "weight": 0.15, "label": "5-Yr Total Asset CAGR (%)"},
    "equity_growth": {"type": "benefit", "weight": 0.20, "label": "5-Yr Total Equity CAGR (%)"}
}

def run_topsis(
    df: pd.DataFrame,
    custom_weights: Optional[Dict[str, float]] = None,
    criteria_types: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Computes step-by-step TOPSIS ranking:
    1. Construct Decision Matrix X
    2. Vector Normalization: R_ij = x_ij / sqrt(sum(x_kj^2))
    3. Weighted Normalized Matrix: V_ij = w_j * R_ij
    4. Ideal Positive (A+) and Ideal Negative (A-) Solutions
    5. Separation Measures: D_i+ and D_i-
    6. Relative Closeness to Ideal Solution: C_i = D_i- / (D_i+ + D_i-)
    7. Final Ranking & Decision Recommendations
    """
    clean_df = df.copy().reset_index(drop=True)
    criteria_keys = list(DEFAULT_CRITERIA.keys())

    # Build weights and types
    weights = {}
    types = {}
    for k in criteria_keys:
        types[k] = (criteria_types or {}).get(k, DEFAULT_CRITERIA[k]["type"])
        weights[k] = (custom_weights or {}).get(k, DEFAULT_CRITERIA[k]["weight"])

    # Normalize weights to sum to 1.0
    total_w = sum(weights.values())
    if total_w > 0:
        weights = {k: v / total_w for k, v in weights.items()}

    # 1. Decision Matrix
    X = clean_df[criteria_keys].fillna(0).values.astype(float)
    # Avoid zero-division in columns
    col_norms = np.sqrt(np.sum(X**2, axis=0))
    col_norms[col_norms == 0] = 1.0

    # 2. Vector Normalization
    R = X / col_norms

    # 3. Weighted Normalized Matrix
    w_vec = np.array([weights[k] for k in criteria_keys])
    V = R * w_vec

    # 4. Ideal Positive (A+) and Ideal Negative (A-)
    a_plus = np.zeros(len(criteria_keys))
    a_minus = np.zeros(len(criteria_keys))

    for j, k in enumerate(criteria_keys):
        if types[k] == "benefit":
            a_plus[j] = np.max(V[:, j])
            a_minus[j] = np.min(V[:, j])
        else:  # cost
            a_plus[j] = np.min(V[:, j])
            a_minus[j] = np.max(V[:, j])

    # 5. Separation Measures (Euclidean distance)
    d_plus = np.sqrt(np.sum((V - a_plus)**2, axis=1))
    d_minus = np.sqrt(np.sum((V - a_minus)**2, axis=1))

    # 6. Closeness Coefficient C_i
    denoms = d_plus + d_minus
    c_scores = np.where(denoms == 0, 0.0, d_minus / denoms)

    clean_df["topsis_score"] = [round(float(s), 4) for s in c_scores]
    clean_df["d_plus"] = [round(float(d), 4) for d in d_plus]
    clean_df["d_minus"] = [round(float(d), 4) for d in d_minus]

    # 7. Final Ranking
    clean_df["rank"] = clean_df["topsis_score"].rank(ascending=False, method="min").astype(int)
    ranked_df = clean_df.sort_values(by="rank", ascending=True).reset_index(drop=True)

    # Decision classification
    def categorize_recommendation(score: float) -> str:
        if score >= 0.65:
            return "Strong Buy / Top Pick"
        elif score >= 0.50:
            return "Buy / Accumulate"
        elif score >= 0.35:
            return "Hold / Neutral"
        else:
            return "Underperform / Avoid"

    ranked_df["recommendation"] = ranked_df["topsis_score"].apply(categorize_recommendation)

    # Step-by-step intermediate matrices for full mathematical audit
    step_matrices = {
        "criteria": criteria_keys,
        "weights": {k: round(v, 4) for k, v in weights.items()},
        "criteria_types": types,
        "ideal_positive": [round(float(x), 4) for x in a_plus],
        "ideal_negative": [round(float(x), 4) for x in a_minus],
        "column_norms": {k: round(float(col_norms[idx]), 4) for idx, k in enumerate(criteria_keys)}
    }

    return {
        "ranked_stocks": ranked_df.to_dict(orient="records"),
        "step_matrices": step_matrices
    }
