"""
Clustering and Dimensionality Reduction module for SPK x Data Mining.
Implements K-Means clustering, PCA (2D & 3D), Elbow Method, and Silhouette Analysis
for stock fundamental metrics.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, silhouette_samples

logger = logging.getLogger("spk_mining.clustering")

CLUSTER_FEATURES = ["rev_growth", "net_growth", "asset_growth", "equity_growth"]

def compute_elbow_and_silhouette(
    df: pd.DataFrame,
    features: Optional[List[str]] = None,
    k_min: int = 2,
    k_max: int = 8
) -> Dict[str, Any]:
    features = features or CLUSTER_FEATURES
    X = df[features].copy().fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    k_max = min(k_max, len(df) - 1)
    k_range = list(range(k_min, k_max + 1))
    
    inertias = []
    silhouette_scores = []

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        inertias.append(float(kmeans.inertia_))
        score = float(silhouette_score(X_scaled, labels))
        silhouette_scores.append(round(score, 4))

    best_k = k_range[int(np.argmax(silhouette_scores))]

    return {
        "k_range": k_range,
        "inertias": [round(x, 2) for x in inertias],
        "silhouette_scores": silhouette_scores,
        "recommended_k": best_k
    }

def label_cluster_profile(mean_metrics: Dict[str, float]) -> str:
    rev = mean_metrics.get("rev_growth", 0.0)
    net = mean_metrics.get("net_growth", 0.0)
    asset = mean_metrics.get("asset_growth", 0.0)
    equity = mean_metrics.get("equity_growth", 0.0)

    if rev > 15.0 and net > 20.0:
        return "Aggressive High-Growth Expansion"
    elif rev > 10.0 and net > 10.0 and equity > 10.0:
        return "Steady Compounder & Value Creator"
    elif asset > 10.0 and equity > 12.0 and net < 10.0:
        return "Capital & Asset Accumulator"
    elif rev < 5.0 or net < 5.0:
        return "Mature / Defensive Low-Growth"
    else:
        return "Moderate Balanced Compounder"

def run_kmeans_clustering(
    df: pd.DataFrame,
    n_clusters: int = 3,
    features: Optional[List[str]] = None
) -> Dict[str, Any]:
    features = features or CLUSTER_FEATURES
    clean_df = df.copy().reset_index(drop=True)
    X = clean_df[features].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=15)
    cluster_labels = kmeans.fit_predict(X_scaled)
    clean_df["cluster"] = cluster_labels

    sil_score = float(silhouette_score(X_scaled, cluster_labels))
    sample_sil_values = silhouette_samples(X_scaled, cluster_labels)
    clean_df["silhouette"] = [round(float(s), 4) for s in sample_sil_values]

    pca_2d = PCA(n_components=2, random_state=42)
    coords_2d = pca_2d.fit_transform(X_scaled)
    clean_df["pca_x"] = [round(float(x), 4) for x in coords_2d[:, 0]]
    clean_df["pca_y"] = [round(float(y), 4) for y in coords_2d[:, 1]]

    pca_3d = PCA(n_components=3, random_state=42)
    coords_3d = pca_3d.fit_transform(X_scaled)
    clean_df["pca_z"] = [round(float(z), 4) for z in coords_3d[:, 2]]

    explained_var_2d = [round(float(v) * 100, 2) for v in pca_2d.explained_variance_ratio_]
    explained_var_3d = [round(float(v) * 100, 2) for v in pca_3d.explained_variance_ratio_]

    cluster_profiles = []
    for c_id in range(n_clusters):
        c_stocks = clean_df[clean_df["cluster"] == c_id]
        if len(c_stocks) == 0:
            continue
        
        means = {f: round(float(c_stocks[f].mean()), 2) for f in features}
        label = label_cluster_profile(means)
        
        cluster_profiles.append({
            "cluster_id": c_id,
            "label": label,
            "count": len(c_stocks),
            "tickers": c_stocks["ticker"].tolist(),
            "mean_metrics": means,
            "avg_silhouette": round(float(c_stocks["silhouette"].mean()), 4)
        })

    loadings_2d = {
        features[i]: {
            "PC1": round(float(pca_2d.components_[0, i]), 4),
            "PC2": round(float(pca_2d.components_[1, i]), 4)
        }
        for i in range(len(features))
    }

    return {
        "n_clusters": n_clusters,
        "overall_silhouette": round(sil_score, 4),
        "explained_variance_2d_percent": explained_var_2d,
        "explained_variance_3d_percent": explained_var_3d,
        "cluster_profiles": cluster_profiles,
        "pca_loadings": loadings_2d,
        "clustered_stocks": clean_df.to_dict(orient="records")
    }
