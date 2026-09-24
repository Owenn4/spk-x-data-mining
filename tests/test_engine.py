import unittest
import pandas as pd
import numpy as np
from backend.data.ingestion import load_cache, fetch_live_stock_data
from backend.mining.clustering import (
    run_kmeans_clustering,
    compute_elbow_and_silhouette,
    CLUSTER_FEATURES
)
from backend.spk.topsis import (
    run_topsis,
    DEFAULT_CRITERIA
)

class TestSPKDataMiningSuite(unittest.TestCase):
    def setUp(self):
        self.cached_data = load_cache()
        self.df = pd.DataFrame(self.cached_data)

    def test_cache_integrity(self):
        self.assertGreater(len(self.cached_data), 0, "Cache must contain stock entries")
        sample = self.cached_data[0]
        required_fields = ["ticker", "name", "sector", "market_cap_t", "per", "pbv", "roe", "der"]
        for field in required_fields:
            self.assertIn(field, sample, f"Missing field {field} in stock record")

    def test_kmeans_clustering_execution(self):
        result = run_kmeans_clustering(self.df, n_clusters=4)
        self.assertIn("clustered_stocks", result)
        self.assertIn("cluster_profiles", result)
        self.assertIn("overall_silhouette", result)
        self.assertIn("explained_variance_2d_percent", result)
        
        self.assertEqual(len(result["clustered_stocks"]), len(self.df))
        clusters = [s["cluster"] for s in result["clustered_stocks"]]
        self.assertTrue(set(clusters).issubset({0, 1, 2, 3}))

    def test_elbow_and_silhouette_curves(self):
        evaluation = compute_elbow_and_silhouette(self.df, k_min=2, k_max=6)
        self.assertIn("k_range", evaluation)
        self.assertIn("inertias", evaluation)
        self.assertIn("silhouette_scores", evaluation)
        self.assertIn("recommended_k", evaluation)
        self.assertEqual(len(evaluation["k_range"]), len(evaluation["inertias"]))
        self.assertEqual(len(evaluation["k_range"]), len(evaluation["silhouette_scores"]))

    def test_topsis_calculations(self):
        result = run_topsis(self.df)
        self.assertIn("ranked_stocks", result)
        self.assertIn("step_matrices", result)
        
        ranked = result["ranked_stocks"]
        self.assertEqual(len(ranked), len(self.df))
        
        for item in ranked:
            self.assertGreaterEqual(item["topsis_score"], 0.0)
            self.assertLessEqual(item["topsis_score"], 1.0)
            self.assertIn("recommendation", item)
            self.assertIn("rank", item)

        scores = [item["topsis_score"] for item in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_custom_weights_topsis(self):
        custom_weights = {
            "per": 0.05,
            "pbv": 0.05,
            "roe": 0.40,
            "npm": 0.30,
            "der": 0.05,
            "div_yield": 0.05,
            "rev_growth": 0.05,
            "net_growth": 0.05
        }
        result = run_topsis(self.df, custom_weights=custom_weights)
        self.assertEqual(len(result["ranked_stocks"]), len(self.df))

if __name__ == "__main__":
    unittest.main()
