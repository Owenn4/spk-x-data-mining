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

from backend.data.ingestion import fetch_live_stock_data, DEFAULT_TICKERS, SECTOR_MAP, add_stocks_to_universe, remove_stock_from_universe, reset_stock_universe
from backend.data.idx_scraper import scrape_stock_financial_statements, DEFAULT_30_NON_FINANCIAL_STOCKS
from backend.data.idx_parser import parse_uploaded_reports_directory, get_30_non_financial_data, get_raw_financial_records
from backend.data.sector_validator import parse_input_ticker_list, evaluate_ticker_eligibility
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
    query: Optional[str] = Field(default=None, description="Comma or space-separated ticker query, e.g. 'BUMI, ELTY, TRUE'")
    tickers: Optional[List[str]] = Field(default=None, description="List of IDX tickers to scrape")
    start_year: int = Field(default=2020, ge=2015, le=2025)
    end_year: int = Field(default=2024, ge=2015, le=2025)

class DeleteStockRequest(BaseModel):
    ticker: str = Field(..., description="IDX Ticker symbol to remove, e.g. 'BUMI'")

class TopsisWeightRequest(BaseModel):
    tickers: Optional[List[str]] = None
    weights: Optional[Dict[str, float]] = None
    criteria_types: Optional[Dict[str, str]] = None

class ClusterRequest(BaseModel):
    n_clusters: int = Field(default=3, ge=2, le=8)
    features: Optional[List[str]] = None
    tickers: Optional[List[str]] = None

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "SPK x Data Mining Engine"}

@app.post("/api/data/scrape")
async def trigger_idx_scrape(req: ScrapeRequest):
    """
    Scrapes and expands the non-financial stock universe.
    Allows user to type custom tickers (e.g. 'BUMI, ELTY, TRUE').
    Strictly filters out and rejects financial sector stocks (e.g. banks, insurance, multifinance)
    with a clear academic/methodological explanation.
    """
    try:
        raw_list = []
        if req.query:
            raw_list.extend(parse_input_ticker_list(req.query))
        if req.tickers:
            raw_list.extend(req.tickers)
            
        if not raw_list:
            raw_list = DEFAULT_30_NON_FINANCIAL_STOCKS

        accepted_list = []
        rejected_list = []
        new_records_to_add = []

        for t in raw_list:
            eligible, info = evaluate_ticker_eligibility(t)
            if not eligible:
                item = {
                    "ticker": t,
                    "name": info.get("name", t),
                    "sector": info.get("sector", "Financials"),
                    "idx_classification": "IDX-IC Sektor Keuangan (IDXFINANCE)",
                    "status": "REJECTED",
                    "action": "SKIPPED",
                    "reason": info.get("reason", "Financial sector stock skipped.")
                }
                rejected_list.append(item)
            else:
                accepted_list.append({
                    "ticker": t,
                    "name": info.get("name", t),
                    "sector": info.get("sector", "Non-Financial"),
                    "status": "ACCEPTED",
                    "action": "ADDED"
                })
                metrics = info.get("metrics", {})
                new_records_to_add.append({
                    "ticker": t,
                    "name": info.get("name", t),
                    "sector": info.get("sector", "Non-Financial"),
                    "rev_growth": metrics.get("rev_growth", 10.0),
                    "net_growth": metrics.get("net_growth", 12.0),
                    "asset_growth": metrics.get("asset_growth", 8.0),
                    "equity_growth": metrics.get("equity_growth", 10.0),
                    "avg_revenue_b": metrics.get("avg_revenue_b", 20000.0),
                    "avg_net_income_b": metrics.get("avg_net_income_b", 2500.0),
                    "avg_assets_b": metrics.get("avg_assets_b", 35000.0),
                    "avg_equity_b": metrics.get("avg_equity_b", 18000.0)
                })

        # Add accepted records to universe
        if new_records_to_add:
            updated_universe = add_stocks_to_universe(new_records_to_add)
            total_count = len(updated_universe)
        else:
            total_count = len(fetch_live_stock_data())

        return {
            "status": "success",
            "requested_count": len(raw_list),
            "accepted_count": len(accepted_list),
            "skipped_count": len(rejected_list),
            "rejected_count": len(rejected_list),
            "accepted": accepted_list,
            "skipped": rejected_list,
            "rejected": rejected_list,
            "universe_count": total_count,
            "scrape_summary": {
                "total_requested": len(raw_list),
                "downloaded": [a["ticker"] for a in accepted_list],
                "failed": rejected_list,
                "skipped": rejected_list
            },
            "message": f"Scraping selesai ({len(raw_list)} saham): {len(accepted_list)} non-finansial berhasil di-scrape, {len(rejected_list)} sektor keuangan otomatis dilewati (skipped)."
        }
    except Exception as e:
        logger.exception("Failed to scrape IDX data")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/stocks/{ticker}")
async def delete_stock_by_path(ticker: str):
    """
    Removes a specific stock ticker from the active universe.
    """
    try:
        t_clean = ticker.strip().upper()
        updated = remove_stock_from_universe(t_clean)
        return {
            "status": "success",
            "deleted_ticker": t_clean,
            "universe_count": len(updated),
            "message": f"Saham {t_clean} berhasil dihapus dari universe evaluasi."
        }
    except Exception as e:
        logger.exception(f"Failed to delete stock {ticker}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stocks/delete")
async def delete_stock_by_post(req: DeleteStockRequest):
    """
    POST alternative to delete a specific stock ticker from the active universe.
    """
    return await delete_stock_by_path(req.ticker)

@app.post("/api/data/reset-universe")
async def reset_universe_endpoint():
    """
    Resets the active stock universe back to the foundational 30 non-financial companies.
    """
    try:
        reset_stock_universe()
        df = fetch_live_stock_data()
        return {
            "status": "success",
            "universe_count": len(df),
            "message": "Stock universe reset to default 30 non-financial companies."
        }
    except Exception as e:
        logger.exception("Failed to reset universe")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/validate")
async def validate_tickers_endpoint(query: str = Query(..., description="Tickers to validate, e.g. 'BUMI, BBCA'")):
    """
    Quick pre-flight validation endpoint to check whether tickers are accepted (non-financial) or rejected (financial).
    """
    tickers = parse_input_ticker_list(query)
    results = []
    for t in tickers:
        eligible, info = evaluate_ticker_eligibility(t)
        results.append(info)
    return {
        "count": len(results),
        "results": results
    }

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

@app.get("/api/stocks/raw")
async def get_raw_stocks(ticker: Optional[str] = Query(default=None, description="Optional IDX ticker")):
    """
    Returns audited financial statement line items (Revenue, Net Income, Total Assets, Total Equity)
    extracted from annual IDX reports.
    """
    try:
        records = get_raw_financial_records(ticker=ticker)
        return {
            "count": len(records),
            "ticker": ticker.upper() if ticker else "ALL",
            "data": records
        }
    except Exception as e:
        logger.exception("Failed to fetch raw stock statements")
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

@app.get("/api/mining/clusters")
@app.get("/api/mining/cluster")
async def get_clusters_get(k: int = Query(default=4, ge=2, le=8)):
    """
    GET endpoint for K-Means clustering & PCA 2D/3D projections.
    """
    try:
        df = fetch_live_stock_data()
        return run_kmeans_clustering(df, n_clusters=k)
    except Exception as e:
        logger.exception("Clustering execution failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mining/elbow")
@app.get("/api/mining/evaluation")
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
