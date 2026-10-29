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

ACTIVE_UNIVERSE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'active_stock_universe.json')
CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'stocks_cache.json')

def get_active_universe() -> List[Dict[str, Any]]:
    """
    Returns the current active stock universe.
    Persists expanded universe if custom stocks have been added.
    """
    if os.path.exists(ACTIVE_UNIVERSE_FILE):
        try:
            with open(ACTIVE_UNIVERSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and isinstance(data, list):
                    for item in data:
                        t = item.get("ticker", "").upper()
                        s = item.get("sector")
                        if t and s:
                            SECTOR_MAP[t] = s
                    return [dict(x) for x in data]
        except Exception as e:
            logger.warning(f"Failed to read active universe file: {e}")

    # Fallback to default 30 non-financial stocks (create fresh shallow copies)
    default_data = [dict(x) for x in get_30_non_financial_data()]
    for item in default_data:
        t = item.get("ticker", "").upper()
        s = item.get("sector")
        if t and s:
            SECTOR_MAP[t] = s
    return default_data

def add_stocks_to_universe(new_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Appends eligible non-financial stock records to the active universe, avoiding duplicates.
    """
    current_universe = get_active_universe()
    existing_tickers = {r["ticker"].upper() for r in current_universe}
    
    added = []
    for rec in new_records:
        t = rec["ticker"].upper()
        if t not in existing_tickers:
            current_universe.append(dict(rec))
            existing_tickers.add(t)
            if rec.get("sector"):
                SECTOR_MAP[t] = rec["sector"]
            added.append(t)
            
    if added:
        os.makedirs(os.path.dirname(os.path.abspath(ACTIVE_UNIVERSE_FILE)), exist_ok=True)
        with open(ACTIVE_UNIVERSE_FILE, "w", encoding="utf-8") as f:
            json.dump(current_universe, f, indent=2)
        logger.info(f"Expanded universe by {len(added)} stocks: {added}. Total count: {len(current_universe)}")

    return current_universe

def remove_stock_from_universe(ticker: str) -> List[Dict[str, Any]]:
    """
    Removes a specific stock ticker from the active universe.
    Persists changes to ACTIVE_UNIVERSE_FILE.
    """
    current_universe = get_active_universe()
    t_target = ticker.strip().upper()
    filtered = [r for r in current_universe if r.get("ticker", "").upper() != t_target]
    
    os.makedirs(os.path.dirname(os.path.abspath(ACTIVE_UNIVERSE_FILE)), exist_ok=True)
    with open(ACTIVE_UNIVERSE_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2)
    logger.info(f"Removed stock {t_target} from active universe. New count: {len(filtered)}")
    return filtered

def reset_stock_universe() -> List[Dict[str, Any]]:
    """
    Resets the stock universe back to the default 30 non-financial companies.
    """
    if os.path.exists(ACTIVE_UNIVERSE_FILE):
        try:
            os.remove(ACTIVE_UNIVERSE_FILE)
        except Exception as e:
            logger.warning(f"Could not remove active universe file: {e}")
            
    default_data = [dict(x) for x in get_30_non_financial_data()[:30]]
    return default_data

def save_cache(data: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(CACHE_FILE)), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_cache() -> List[Dict[str, Any]]:
    return get_active_universe()

def fetch_live_stock_data(tickers: Optional[List[str]] = None) -> pd.DataFrame:
    data = load_cache()
    df = pd.DataFrame(data)
    if tickers:
        clean_tickers = [t.replace(".JK", "").upper() for t in tickers]
        df = df[df["ticker"].str.upper().isin(clean_tickers)]
    return df
