"""
FastAPI Routes for SPK x Data Mining platform.
Exposes REST endpoints for ingestion, K-Means clustering, PCA coordinates,
and TOPSIS ranking with customizable criteria weights.
"""

import logging
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.data.ingestion import fetch_live_stock_data, DEFAULT_TICKERS, SECTOR_MAP
from backend.mining.clustering import run_kmeans_clustering, compute_elbow_and_silhouette
from backend.spk.topsis import run_topsis, DEFAULT_CRITERIA

logger = logging.getLogger("spk_mining.api")

app = FastAPI(
    title="SPK x Data Mining - IDX Stock Evaluator",
    description="Hybrid Decision Support System & Machine Learning Clustering for IDX Stocks",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TopsisWeightRequest(BaseModel):
    tickers: Optional[List[str]] = None
    weights: Optional[Dict[str, float]] = None
    criteria_types: Optional[Dict[str, str]] = None

class ClusterRequest(BaseModel):
    n_clusters: int = Field(default=4, ge=2, le=8)
    features: Optional[List[str]] = None
    tickers: Optional[List[str]] = None

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "SPK x Data Mining Engine"}

@app.get("/api/stocks")
async def get_stocks(refresh: bool = False):
    """
    Returns latest stock data with fundamental metrics.
    """
    try:
        df = fetch_live_stock_data()
        return {
            "count": len(df),
            "sectors": list(set(SECTOR_MAP.values())),
            "data": df.to_dict(orient="records")
        }
    except Exception as e:
        logger.exception("Failed to fetch stock data")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mining/cluster")
async def cluster_stocks(req: ClusterRequest):
    """
    Executes K-Means clustering & PCA 2D/3D projections.
    """
    try:
        df = fetch_live_stock_data(tickers=req.tickers)
        result = run_kmeans_clustering(df, n_clusters=req.n_clusters, features=req.features)
        return result
    except Exception as e:
        logger.exception("Clustering execution failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mining/elbow")
async def get_elbow_evaluation():
    """
    Returns Elbow Inertia curve and Silhouette scores for k=2..8.
    """
    try:
        df = fetch_live_stock_data()
        return compute_elbow_and_silhouette(df)
    except Exception as e:
        logger.exception("Elbow evaluation failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/spk/topsis")
async def evaluate_topsis(req: TopsisWeightRequest):
    """
    Executes multi-criteria TOPSIS evaluation and ranking.
    """
    try:
        df = fetch_live_stock_data(tickers=req.tickers)
        result = run_topsis(df, custom_weights=req.weights, criteria_types=req.criteria_types)
        return result
    except Exception as e:
        logger.exception("TOPSIS ranking failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/spk/criteria")
async def get_default_criteria():
    """
    Returns default criteria definitions and weights.
    """
    return DEFAULT_CRITERIA
