"""
FastAPI Routes for SPK x Data Mining platform.
Exposes REST endpoints for ingestion, K-Means clustering, PCA coordinates,
and TOPSIS ranking with customizable criteria weights.
"""

import os
import shutil
import zipfile
import logging
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.data.ingestion import fetch_live_stock_data, DEFAULT_TICKERS, SECTOR_MAP
from backend.data.idx_scraper import scrape_stock_financial_statements, DEFAULT_30_NON_FINANCIAL_STOCKS
from backend.data.idx_parser import parse_uploaded_reports_directory, get_30_non_financial_data
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

class ScrapeRequest(BaseModel):
    tickers: Optional[List[str]] = Field(default=None, description="List of IDX tickers to scrape")
    start_year: int = Field(default=2020, ge=2015, le=2025)
    end_year: int = Field(default=2024, ge=2015, le=2025)

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

@app.post("/api/data/scrape")
async def trigger_idx_scrape(req: ScrapeRequest):
    """
    Directly initiates scraping of audited annual financial statements from IDX.co.id.
    """
    try:
        tickers = req.tickers or DEFAULT_30_NON_FINANCIAL_STOCKS
        summary = scrape_stock_financial_statements(
            tickers=tickers,
            start_year=req.start_year,
            end_year=req.end_year
        )
        # Trigger parsing of newly downloaded reports
        parsed = parse_uploaded_reports_directory()
        return {
            "status": "success",
            "scrape_summary": summary,
            "parsed_count": len(parsed)
        }
    except Exception as e:
        logger.exception("Failed to scrape IDX data")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/upload")
async def upload_financial_statements(file: UploadFile = File(...)):
    """
    Accepts .xlsx workbook or .zip archive of financial statements,
    extracts/saves them to data/raw_reports, and parses 5-year CAGR metrics.
    """
    upload_dir = "data/raw_reports"
    os.makedirs(upload_dir, exist_ok=True)
    filename = file.filename or "uploaded_file"

    try:
        temp_path = os.path.join(upload_dir, filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted_files = []
        if filename.lower().endswith(".zip"):
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if not member.startswith("__MACOSX") and (member.lower().endswith(".xlsx") or member.lower().endswith(".xls")):
                        zip_ref.extract(member, upload_dir)
                        extracted_files.append(member)
            if os.path.exists(temp_path):
                os.remove(temp_path)
        elif filename.lower().endswith(".xlsx") or filename.lower().endswith(".xls"):
            extracted_files.append(filename)
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(status_code=400, detail="Invalid file format. Only .xlsx, .xls, and .zip are supported.")

        # Re-parse raw directory
        parsed_data = parse_uploaded_reports_directory(upload_dir)
        return {
            "status": "success",
            "message": f"Successfully processed {len(extracted_files)} report files.",
            "extracted_files": extracted_files,
            "total_parsed_stocks": len(parsed_data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to upload/parse statements")
        raise HTTPException(status_code=500, detail=str(e))

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
