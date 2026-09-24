"""
Data Ingestion and Feature Engineering module for SPK x Data Mining.
Extracts fundamental and financial metrics for 30 non-financial IDX stocks (2020-2024).
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from backend.data.idx_parser import get_30_non_financial_data, parse_uploaded_reports_directory

logger = logging.getLogger("spk_mining.ingestion")

DEFAULT_30_TICKERS = [
    "ICBP", "INDF", "MYOR", "UNVR", "CPIN", "JPFA",
    "ADRO", "PTBA", "PGAS", "MEDC", "AKRA", "INDY",
    "ASII", "UNTR", "SMGR", "INTP", "INKP", "TKIM",
    "KLBF", "MIKA", "SILO", "HEAL", "TLKM", "EXCL",
    "ISAT", "JSMR", "ACES", "MAPI", "ERAA", "AMRT"
]

DEFAULT_TICKERS = DEFAULT_30_TICKERS

SECTOR_MAP = {
    "ICBP": "Consumer Non-Cyclical", "INDF": "Consumer Non-Cyclical", "MYOR": "Consumer Non-Cyclical", "UNVR": "Consumer Non-Cyclical", "CPIN": "Consumer Non-Cyclical", "JPFA": "Consumer Non-Cyclical",
    "ADRO": "Energy", "PTBA": "Energy", "PGAS": "Energy", "MEDC": "Energy", "AKRA": "Energy", "INDY": "Energy",
    "ASII": "Industrials", "UNTR": "Industrials",
    "SMGR": "Basic Materials", "INTP": "Basic Materials", "INKP": "Basic Materials", "TKIM": "Basic Materials",
    "KLBF": "Healthcare", "MIKA": "Healthcare", "SILO": "Healthcare", "HEAL": "Healthcare",
    "TLKM": "Telecommunication", "EXCL": "Telecommunication", "ISAT": "Telecommunication",
    "JSMR": "Infrastructure",
    "ACES": "Consumer Cyclical", "MAPI": "Consumer Cyclical", "ERAA": "Consumer Cyclical", "AMRT": "Consumer Cyclical"
}

CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'stocks_cache.json')

def save_cache(data: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(CACHE_FILE)), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_cache() -> List[Dict[str, Any]]:
    return parse_uploaded_reports_directory()

def fetch_live_stock_data(tickers: Optional[List[str]] = None) -> pd.DataFrame:
    data = load_cache()
    df = pd.DataFrame(data)
    if tickers:
        clean_tickers = [t.replace(".JK", "").upper() for t in tickers]
        df = df[df["ticker"].str.upper().isin(clean_tickers)]
    return df
