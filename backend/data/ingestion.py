"""
Data Ingestion and Feature Engineering module for SPK x Data Mining.
Extracts fundamental and financial metrics for IDX (LQ45 / Kompas100) stocks using yfinance
with an offline fallback cache.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

try:
    import yfinance as yf
except ImportError:
    yf = None

logger = logging.getLogger("spk_mining.ingestion")

DEFAULT_TICKERS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK",
    "TLKM.JK", "ICBP.JK", "INDF.JK", "UNVR.JK", "KLBF.JK",
    "ADRO.JK", "PTBA.JK", "ITMG.JK", "PGAS.JK", "ANTM.JK",
    "MDKA.JK", "INCO.JK", "BRIS.JK", "CPIN.JK", "GOTO.JK",
    "AMRT.JK", "TOWR.JK", "TBIG.JK", "SMGR.JK", "INTP.JK"
]

SECTOR_MAP = {
    "BBCA.JK": "Finance", "BBRI.JK": "Finance", "BMRI.JK": "Finance", "BBNI.JK": "Finance", "BRIS.JK": "Finance",
    "ASII.JK": "Consumer Cyclical", "AMRT.JK": "Consumer Cyclical",
    "TLKM.JK": "Telecommunication", "TOWR.JK": "Infrastructure", "TBIG.JK": "Infrastructure",
    "ICBP.JK": "Consumer Non-Cyclical", "INDF.JK": "Consumer Non-Cyclical", "UNVR.JK": "Consumer Non-Cyclical", "KLBF.JK": "Healthcare", "CPIN.JK": "Consumer Non-Cyclical",
    "ADRO.JK": "Energy", "PTBA.JK": "Energy", "ITMG.JK": "Energy", "PGAS.JK": "Energy",
    "ANTM.JK": "Basic Materials", "MDKA.JK": "Basic Materials", "INCO.JK": "Basic Materials",
    "SMGR.JK": "Basic Materials", "INTP.JK": "Basic Materials", "GOTO.JK": "Technology"
}

FALLBACK_DATA = [
    {"ticker": "BBCA.JK", "name": "Bank Central Asia", "sector": "Finance", "per": 22.4, "pbv": 4.6, "roe": 21.8, "der": 4.8, "npm": 45.2, "div_yield": 2.1, "rev_growth": 14.5, "net_growth": 18.2, "market_cap_t": 1200.5},
    {"ticker": "BBRI.JK", "name": "Bank Rakyat Indonesia", "sector": "Finance", "per": 13.5, "pbv": 2.3, "roe": 18.5, "der": 5.4, "npm": 32.1, "div_yield": 4.8, "rev_growth": 11.2, "net_growth": 14.6, "market_cap_t": 750.2},
    {"ticker": "BMRI.JK", "name": "Bank Mandiri", "sector": "Finance", "per": 11.8, "pbv": 2.1, "roe": 19.4, "der": 5.1, "npm": 34.8, "div_yield": 5.2, "rev_growth": 13.1, "net_growth": 17.5, "market_cap_t": 630.0},
    {"ticker": "BBNI.JK", "name": "Bank Negara Indonesia", "sector": "Finance", "per": 9.2, "pbv": 1.2, "roe": 14.6, "der": 4.9, "npm": 28.4, "div_yield": 5.0, "rev_growth": 8.7, "net_growth": 11.4, "market_cap_t": 205.0},
    {"ticker": "BRIS.JK", "name": "Bank Syariah Indonesia", "sector": "Finance", "per": 17.8, "pbv": 2.8, "roe": 16.9, "der": 6.2, "npm": 26.5, "div_yield": 1.2, "rev_growth": 16.4, "net_growth": 24.1, "market_cap_t": 120.0},
    {"ticker": "ASII.JK", "name": "Astra International", "sector": "Consumer Cyclical", "per": 7.4, "pbv": 1.0, "roe": 15.2, "der": 0.9, "npm": 10.4, "div_yield": 6.8, "rev_growth": 5.4, "net_growth": 3.8, "market_cap_t": 210.0},
    {"ticker": "TLKM.JK", "name": "Telkom Indonesia", "sector": "Telecommunication", "per": 14.2, "pbv": 2.4, "roe": 18.1, "der": 0.8, "npm": 16.5, "div_yield": 4.5, "rev_growth": 3.2, "net_growth": 4.1, "market_cap_t": 320.0},
    {"ticker": "ICBP.JK", "name": "Indofood CBP", "sector": "Consumer Non-Cyclical", "per": 15.6, "pbv": 2.7, "roe": 17.4, "der": 0.7, "npm": 12.8, "div_yield": 3.1, "rev_growth": 7.8, "net_growth": 9.5, "market_cap_t": 130.0},
    {"ticker": "INDF.JK", "name": "Indofood Sukses Makmur", "sector": "Consumer Non-Cyclical", "per": 6.8, "pbv": 1.0, "roe": 14.8, "der": 1.1, "npm": 8.9, "div_yield": 4.2, "rev_growth": 6.5, "net_growth": 8.1, "market_cap_t": 62.0},
    {"ticker": "UNVR.JK", "name": "Unilever Indonesia", "sector": "Consumer Non-Cyclical", "per": 24.1, "pbv": 18.5, "roe": 78.4, "der": 2.4, "npm": 12.1, "div_yield": 4.9, "rev_growth": -2.1, "net_growth": -8.5, "market_cap_t": 95.0},
    {"ticker": "KLBF.JK", "name": "Kalbe Farma", "sector": "Healthcare", "per": 22.0, "pbv": 3.4, "roe": 15.8, "der": 0.2, "npm": 10.5, "div_yield": 2.4, "rev_growth": 6.2, "net_growth": 7.0, "market_cap_t": 72.0},
    {"ticker": "ADRO.JK", "name": "Adaro Energy", "sector": "Energy", "per": 4.5, "pbv": 0.9, "roe": 22.5, "der": 0.4, "npm": 28.5, "div_yield": 12.5, "rev_growth": -8.4, "net_growth": -15.2, "market_cap_t": 115.0},
    {"ticker": "PTBA.JK", "name": "Bukit Asam", "sector": "Energy", "per": 5.8, "pbv": 1.3, "roe": 24.1, "der": 0.5, "npm": 18.2, "div_yield": 14.0, "rev_growth": 4.1, "net_growth": -5.6, "market_cap_t": 32.0},
    {"ticker": "ITMG.JK", "name": "Indo Tambangraya", "sector": "Energy", "per": 4.2, "pbv": 1.1, "roe": 27.8, "der": 0.3, "npm": 24.1, "div_yield": 15.2, "rev_growth": -12.1, "net_growth": -18.4, "market_cap_t": 30.5},
    {"ticker": "PGAS.JK", "name": "Perusahaan Gas Negara", "sector": "Energy", "per": 7.1, "pbv": 0.8, "roe": 11.2, "der": 0.9, "npm": 8.4, "div_yield": 7.1, "rev_growth": 2.5, "net_growth": 3.8, "market_cap_t": 38.0},
    {"ticker": "ANTM.JK", "name": "Aneka Tambang", "sector": "Basic Materials", "per": 12.4, "pbv": 1.4, "roe": 12.1, "der": 0.4, "npm": 7.2, "div_yield": 3.5, "rev_growth": 8.9, "net_growth": 10.2, "market_cap_t": 37.0},
    {"ticker": "MDKA.JK", "name": "Merdeka Copper Gold", "sector": "Basic Materials", "per": 45.0, "pbv": 3.8, "roe": 3.2, "der": 1.2, "npm": 2.1, "div_yield": 0.0, "rev_growth": 28.5, "net_growth": -5.1, "market_cap_t": 58.0},
    {"ticker": "INCO.JK", "name": "Vale Indonesia", "sector": "Basic Materials", "per": 14.5, "pbv": 1.2, "roe": 8.9, "der": 0.2, "npm": 18.5, "div_yield": 2.0, "rev_growth": -4.2, "net_growth": -2.8, "market_cap_t": 41.0},
    {"ticker": "CPIN.JK", "name": "Charoen Pokphand", "sector": "Consumer Non-Cyclical", "per": 28.5, "pbv": 3.1, "roe": 11.5, "der": 0.6, "npm": 4.8, "div_yield": 1.8, "rev_growth": 9.4, "net_growth": 15.1, "market_cap_t": 84.0},
    {"ticker": "GOTO.JK", "name": "GoTo Gojek Tokopedia", "sector": "Technology", "per": -8.5, "pbv": 0.7, "roe": -12.4, "der": 0.1, "npm": -35.2, "div_yield": 0.0, "rev_growth": 15.8, "net_growth": 45.0, "market_cap_t": 68.0},
    {"ticker": "AMRT.JK", "name": "Sumber Alfaria Trijaya", "sector": "Consumer Cyclical", "per": 34.0, "pbv": 8.2, "roe": 26.5, "der": 1.3, "npm": 3.4, "div_yield": 1.1, "rev_growth": 11.8, "net_growth": 16.2, "market_cap_t": 118.0},
    {"ticker": "TOWR.JK", "name": "Sarana Menara Nusantara", "sector": "Infrastructure", "per": 12.1, "pbv": 2.5, "roe": 21.4, "der": 2.8, "npm": 29.5, "div_yield": 3.8, "rev_growth": 7.2, "net_growth": 5.4, "market_cap_t": 44.0},
    {"ticker": "TBIG.JK", "name": "Tower Bersama Infrastructure", "sector": "Infrastructure", "per": 26.5, "pbv": 3.9, "roe": 15.2, "der": 3.5, "npm": 23.1, "div_yield": 2.2, "rev_growth": 5.1, "net_growth": 4.0, "market_cap_t": 42.0},
    {"ticker": "SMGR.JK", "name": "Semen Indonesia", "sector": "Basic Materials", "per": 13.8, "pbv": 0.8, "roe": 5.9, "der": 0.8, "npm": 5.8, "div_yield": 4.1, "rev_growth": 1.2, "net_growth": -2.1, "market_cap_t": 28.0},
    {"ticker": "INTP.JK", "name": "Indocement", "sector": "Basic Materials", "per": 16.2, "pbv": 1.2, "roe": 7.8, "der": 0.2, "npm": 10.1, "div_yield": 3.9, "rev_growth": 2.8, "net_growth": 1.5, "market_cap_t": 31.0}
]

CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'stocks_cache.json')

def save_cache(data: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(CACHE_FILE)), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_cache() -> List[Dict[str, Any]]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f'Failed to read cache: {e}')
    return FALLBACK_DATA

def fetch_live_stock_data(tickers: Optional[List[str]] = None) -> pd.DataFrame:
    tickers = tickers or DEFAULT_TICKERS
    records = []
    if yf is None:
        logger.info('yfinance not installed or unavailable, using fallback data.')
        df = pd.DataFrame(load_cache())
        return df[df['ticker'].isin(tickers)] if tickers else df

    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            per = info.get('trailingPE') or info.get('forwardPE')
            pbv = info.get('priceToBook')
            roe = info.get('returnOnEquity')
            if roe is not None:
                roe = roe * 100.0
            der = info.get('debtToEquity')
            if der is not None:
                der = der / 100.0
            npm = info.get('profitMargins')
            if npm is not None:
                npm = npm * 100.0
            div_yield = info.get('dividendYield')
            if div_yield is not None:
                div_yield = div_yield * 100.0
            rev_growth = info.get('revenueGrowth')
            if rev_growth is not None:
                rev_growth = rev_growth * 100.0
            net_growth = info.get('earningsGrowth')
            if net_growth is not None:
                net_growth = net_growth * 100.0
            market_cap = info.get('marketCap', 0) / 1e12

            fallback_match = next((item for item in FALLBACK_DATA if item['ticker'] == ticker), None)
            record = {
                'ticker': ticker,
                'name': info.get('shortName') or (fallback_match['name'] if fallback_match else ticker),
                'sector': info.get('sector') or SECTOR_MAP.get(ticker, 'General'),
                'per': round(per, 2) if per is not None else (fallback_match['per'] if fallback_match else 15.0),
                'pbv': round(pbv, 2) if pbv is not None else (fallback_match['pbv'] if fallback_match else 2.0),
                'roe': round(roe, 2) if roe is not None else (fallback_match['roe'] if fallback_match else 15.0),
                'der': round(der, 2) if der is not None else (fallback_match['der'] if fallback_match else 1.0),
                'npm': round(npm, 2) if npm is not None else (fallback_match['npm'] if fallback_match else 12.0),
                'div_yield': round(div_yield, 2) if div_yield is not None else (fallback_match['div_yield'] if fallback_match else 3.0),
                'rev_growth': round(rev_growth, 2) if rev_growth is not None else (fallback_match['rev_growth'] if fallback_match else 5.0),
                'net_growth': round(net_growth, 2) if net_growth is not None else (fallback_match['net_growth'] if fallback_match else 5.0),
                'market_cap_t': round(market_cap, 2) if market_cap > 0 else (fallback_match['market_cap_t'] if fallback_match else 50.0)
            }
            records.append(record)
        except Exception as err:
            logger.warning(f'Error fetching live info for {ticker}: {err}. Using fallback.')
            fallback_match = next((item for item in FALLBACK_DATA if item['ticker'] == ticker), None)
            if fallback_match:
                records.append(fallback_match)

    if not records:
        records = load_cache()

    save_cache(records)
    return pd.DataFrame(records)
