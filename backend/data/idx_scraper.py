"""
IDX Financial Report Downloader & Scraper.
Fetches audited annual financial statements (.xlsx) directly from IDX.co.id
for designated Indonesian non-financial tickers over 2020-2024.
"""

import os
import re
import time
import logging
from typing import List, Dict, Optional, Any
import requests

logger = logging.getLogger("spk_mining.idx_scraper")

# Default 30 representative Non-Financial IDX stocks across sectors
DEFAULT_30_NON_FINANCIAL_STOCKS = [
    # Consumer Non-Cyclicals / Food & Beverage
    "ICBP", "INDF", "MYOR", "UNVR", "CPIN", "JPFA",
    # Energy / Mining
    "ADRO", "PTBA", "PGAS", "MEDC", "AKRA", "INDY",
    # Basic Materials & Industrials
    "ASII", "UNTR", "SMGR", "INTP", "INKP", "TKIM",
    # Healthcare / Pharmaceuticals
    "KLBF", "MIKA", "SILO", "HEAL",
    # Telecommunications / Infrastructure
    "TLKM", "EXCL", "ISAT", "JSMR",
    # Retail / Consumer Cyclicals
    "ACES", "MAPI", "ERAA", "AMRT"
]

IDX_BASE_URL = "https://www.idx.co.id"
IDX_REPORT_SEARCH_URL = "https://www.idx.co.id/primary/ListedCompany/GetFinancialReport"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan/",
}

def query_idx_report_files(ticker: str, year: int, period: str = "audit") -> List[Dict[str, str]]:
    """
    Queries the IDX GetFinancialReport endpoint for annual statements of a specific ticker and year.
    period: 'audit' or 'TW4' / 'Tahunan'
    """
    params = {
        "indexFrom": 0,
        "pageSize": 10,
        "year": str(year),
        "periode": period,
        "kodeEmiten": ticker.upper(),
        "jenisLaporan": "saham"
    }

    try:
        resp = requests.get(IDX_REPORT_SEARCH_URL, headers=HEADERS, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("Results", [])
            downloadable_files = []
            for item in results:
                attachments = item.get("Attachments", [])
                for att in attachments:
                    file_path = att.get("File_Path", "")
                    file_name = att.get("File_Name", "")
                    # Filter specifically for xlsx or xls financial statement workbooks
                    if file_path.lower().endswith(".xlsx") or file_path.lower().endswith(".xls"):
                        downloadable_files.append({
                            "ticker": ticker.upper(),
                            "year": year,
                            "file_name": file_name,
                            "file_url": f"{IDX_BASE_URL}{file_path}" if not file_path.startswith("http") else file_path
                        })
            return downloadable_files
    except Exception as e:
        logger.warning(f"Failed to query IDX reports for {ticker} ({year}): {e}")

    return []

def download_file(file_url: str, save_path: str) -> bool:
    """
    Downloads a binary file from IDX and saves it locally.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        resp = requests.get(file_url, headers=HEADERS, stream=True, timeout=30)
        if resp.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        logger.error(f"Download failed for {file_url}: {e}")
    return False

def scrape_stock_financial_statements(
    tickers: Optional[List[str]] = None,
    start_year: int = 2020,
    end_year: int = 2024,
    output_dir: str = "data/raw_reports"
) -> Dict[str, Any]:
    """
    Scrapes annual audited reports for the provided tickers between start_year and end_year.
    """
    target_tickers = tickers or DEFAULT_30_NON_FINANCIAL_STOCKS
    download_summary = {"total_requested": len(target_tickers), "downloaded": [], "failed": []}

    for ticker in target_tickers:
        ticker = ticker.upper()
        ticker_dir = os.path.join(output_dir, ticker)
        os.makedirs(ticker_dir, exist_ok=True)

        for yr in range(start_year, end_year + 1):
            files = query_idx_report_files(ticker, yr, period="audit")
            if not files:
                # Fallback to 'TW4' or 'Tahunan' period if 'audit' tag was not matched
                files = query_idx_report_files(ticker, yr, period="TW4")

            if files:
                for target_file in files:
                    file_name = target_file["file_name"] or f"FinancialStatement-{yr}-Tahunan-{ticker}.xlsx"
                    save_path = os.path.join(ticker_dir, file_name)
                    if not os.path.exists(save_path):
                        success = download_file(target_file["file_url"], save_path)
                        if success:
                            download_summary["downloaded"].append(save_path)
                        else:
                            download_summary["failed"].append({"ticker": ticker, "year": yr, "url": target_file["file_url"]})
                        time.sleep(0.5)  # respectful scraping delay
            else:
                download_summary["failed"].append({"ticker": ticker, "year": yr, "reason": "No XLSX metadata found"})

    return download_summary
