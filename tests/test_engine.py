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
        required_fields = ["ticker", "name", "sector", "rev_growth", "net_growth", "asset_growth", "equity_growth"]
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
            "rev_growth": 0.40,
            "net_growth": 0.30,
            "asset_growth": 0.15,
            "equity_growth": 0.15
        }
        result = run_topsis(self.df, custom_weights=custom_weights)
        self.assertEqual(len(result["ranked_stocks"]), len(self.df))

    def test_api_routes_integration(self):
        from fastapi.testclient import TestClient
        from backend.api.routes import app
        
        client = TestClient(app)
        
        # Health check
        res_health = client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "ok")
        
        # Stocks endpoint
        res_stocks = client.get("/api/stocks")
        self.assertEqual(res_stocks.status_code, 200)
        stocks_data = res_stocks.json()
        self.assertIn("data", stocks_data)
        self.assertGreaterEqual(len(stocks_data["data"]), 30)
        
        # Scrape endpoint with simulated mock tickers
        res_scrape = client.post("/api/data/scrape", json={"tickers": ["ICBP", "INDF"], "start_year": 2020, "end_year": 2024})
        self.assertEqual(res_scrape.status_code, 200)
        self.assertIn("scrape_summary", res_scrape.json())

        # Upload endpoint test (with empty/mock files)
        import io
        fake_file = io.BytesIO(b"fake financial content")
        res_upload = client.post("/api/data/upload", files={"file": ("report_ICBP_2024.xlsx", fake_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        self.assertEqual(res_upload.status_code, 200)
        self.assertIn("extracted_files", res_upload.json())

        # Raw financial statements endpoint test
        res_raw = client.get("/api/stocks/raw?ticker=ACES")
        self.assertEqual(res_raw.status_code, 200)
        self.assertIn("data", res_raw.json())
        self.assertGreater(len(res_raw.json()["data"]), 0)

    def test_custom_stock_scraping_and_financial_rejection(self):
        from fastapi.testclient import TestClient
        from backend.api.routes import app

        client = TestClient(app)

        # 1. Validation test: Non-financial vs Financial
        res_val = client.get("/api/stocks/validate?query=BUMI, ELTY, TRUE, BBCA, BMRI")
        self.assertEqual(res_val.status_code, 200)
        results = {r["ticker"]: r for r in res_val.json()["results"]}
        self.assertEqual(results["BUMI"]["status"], "ACCEPTED")
        self.assertEqual(results["ELTY"]["status"], "ACCEPTED")
        self.assertEqual(results["TRUE"]["status"], "ACCEPTED")
        self.assertEqual(results["BBCA"]["status"], "REJECTED")
        self.assertEqual(results["BMRI"]["status"], "REJECTED")
        self.assertIn("Sektor Keuangan", results["BBCA"]["reason"])

        # 2. Scrape test: expands universe with mixed non-financial and financial tickers
        res_scrape = client.post("/api/data/scrape", json={"query": "BUMI, BBCA, ELTY, BMRI, TRUE"})
        self.assertEqual(res_scrape.status_code, 200)
        scrape_json = res_scrape.json()
        accepted_tickers = [x["ticker"] for x in scrape_json["accepted"]]
        rejected_tickers = [x["ticker"] for x in scrape_json["rejected"]]
        skipped_tickers = [x["ticker"] for x in scrape_json["skipped"]]
        self.assertIn("BUMI", accepted_tickers)
        self.assertIn("ELTY", accepted_tickers)
        self.assertIn("TRUE", accepted_tickers)
        self.assertIn("BBCA", rejected_tickers)
        self.assertIn("BMRI", rejected_tickers)
        self.assertIn("BBCA", skipped_tickers)
        self.assertIn("BMRI", skipped_tickers)
        self.assertEqual(scrape_json["accepted_count"], 3)
        self.assertEqual(scrape_json["skipped_count"], 2)
        self.assertGreaterEqual(scrape_json["universe_count"], 33)

        # 3. Individual stock deletion test (DELETE and POST)
        res_del1 = client.delete("/api/stocks/TRUE")
        self.assertEqual(res_del1.status_code, 200)
        self.assertEqual(res_del1.json()["deleted_ticker"], "TRUE")
        
        res_del2 = client.post("/api/stocks/delete", json={"ticker": "ELTY"})
        self.assertEqual(res_del2.status_code, 200)
        self.assertEqual(res_del2.json()["deleted_ticker"], "ELTY")

        res_check = client.get("/api/stocks")
        tickers_now = [s["ticker"] for s in res_check.json()["data"]]
        self.assertNotIn("TRUE", tickers_now)
        self.assertNotIn("ELTY", tickers_now)
        self.assertIn("BUMI", tickers_now)

        # 4. Reset universe test
        res_reset = client.post("/api/data/reset-universe")
        self.assertEqual(res_reset.status_code, 200)
        res_stocks = client.get("/api/stocks")
        self.assertEqual(res_stocks.json()["count"], 30)


if __name__ == "__main__":
    unittest.main()
