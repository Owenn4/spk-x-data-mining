# Project Briefing: SPK x Data Mining — IDX Non-Financial Stock Analysis Platform

## 1. Executive Summary
- **System Name:** SPK (Sistem Pendukung Keputusan / Decision Support System) x Data Mining Hybrid Platform
- **Objective:** Analyze, cluster, and rank 30 major Indonesian publicly listed companies (IDX / BEI) based on their 5-year audited financial growth trajectory (2020–2024).
- **Hybrid Methodology:** Combines **Unsupervised Machine Learning (K-Means Clustering)** for natural behavioral grouping with **Multi-Criteria Decision Making (TOPSIS)** for multidimensional performance ranking.
- **Delivery Format:** Full-stack interactive web application (FastAPI backend + React / Vite / TypeScript / Tailwind CSS frontend).

---

## 2. Domain Scope & Non-Financial Justification

### Dataset Universe:
30 Indonesian Public Listed Companies (Non-Financial Sectors: Consumer Non-Cyclicals, Infrastructure, Energy, Basic Materials, Retail, Healthcare, etc. — e.g., `ICBP`, `INDF`, `ASII`, `UNTR`, `ADRO`, `KLBF`, `MAPI`, `AMRT`).

### Justification for Excluding the Financial / Banking Sector:
1. **Incompatible Balance Sheet Mechanics:** Banks operate on high structural leverage where customer deposits are recorded as liabilities and loan portfolios represent assets. Real-sector firms rely on operating turnover and equity-to-debt funding for physical operations.
2. **Gross Revenue Incomparability:** Financial institutions do not report standard "Sales / Net Revenue" from product delivery; their top-line corresponds to Net Interest Income (NII) and premium income.
3. **Outlier & Clustering Distortion:** Merging financial and non-financial tickers causes banking assets and leverage metrics to act as extreme outliers. In Euclidean space, this skews K-Means centroid calculations and distorts the Positive ($A^+$) and Negative ($A^-$) Ideal Solutions in TOPSIS.

---

## 3. Data Specification & Features

- **Time Horizon:** 2020–2024 (5 Consecutive Years of Audited Annual Statements / `TW4` / `Tahunan`).
- **Data Source:** Indonesia Stock Exchange (IDX) official repository via `.xlsx` financial report files.
- **Primary Raw Financial Metrics:**
  1. **Revenue / Sales:** Top-line operating gross turnover.
  2. **Net Income / Profit:** Bottom-line net earnings after tax.
  3. **Total Assets:** Aggregated capital and asset base.
  4. **Total Equity:** Net book value / shareholder equity.

- **Derived Decision Variables (5-Year Growth Indicators):**
  $$\text{CAGR} = \left( \frac{\text{Value}_{2024}}{\text{Value}_{2020}} \right)^{\frac{1}{4}} - 1$$
  - $\text{Growth}_{\text{Revenue}}$: 5-Year Compound / Average Revenue Growth
  - $\text{Growth}_{\text{NetIncome}}$: 5-Year Compound / Average Net Income Growth
  - $\text{Growth}_{\text{Assets}}$: 5-Year Compound / Average Asset Base Growth
  - $\text{Growth}_{\text{Equity}}$: 5-Year Compound / Average Equity Accumulation Growth

---

## 4. Methodological Architecture

```
                       [ IDX Scraper / XLSX Batch Upload ]
                                        │
                                        ▼
                         [ Audited Report Parser Engine ]
                         (Extracts: Revenue, NI, Assets, Equity)
                                        │
                                        ▼
                         [ 5-Year Growth Calculation ]
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
       [ K-Means Clustering ]                        [ TOPSIS Ranking ]
  • Feature standardization (Z-score)           • Vector Normalization Matrix ($r_{ij}$)
  • Elbow Curve (Inertia) & Silhouette          • Weighted Normalized Matrix ($v_{ij}$)
  • Cluster profiling (High Growth,             • Euclidean Distance to $A^+$ and $A^-$
    Defensive/Stable, Moderate Capital)         • Relative Closeness Score ($R_i \in [0,1]$)
                 │                                             │
                 └──────────────────────┬──────────────────────┘
                                        ▼
                        [ Interactive Web Dashboard ]
                 • 2D/3D PCA Cluster Scatter Plot
                 • Real-time TOPSIS Weight Sliders
                 • Synchronized Comparison & Ranking Tables
```

### A. Data Mining Engine: K-Means Clustering
- **Feature Preprocessing:** Z-score standard scaling across the 4 growth dimensions.
- **Optimal Cluster Determination:** Integrated **Elbow Method (Inertia Curve)** and **Silhouette Coefficient Analysis** ($k = 2$ to $k = 6$).
- **Dimensionality Reduction:** Principal Component Analysis (PCA) projection to 2D/3D coordinate space for cluster boundary visualization.
- **Cluster Profiling:** Identifies distinct behavioral cohorts (e.g., Aggressive Growth, Steady Defensive, Asset-Heavy Accumulation).

### B. Decision Support System (SPK): TOPSIS Method
1. **Decision Matrix Construction:** $m \times n$ matrix for $m = 30$ stock alternatives and $n = 4$ criteria.
2. **Vector Normalization:**
   $$r_{ij} = \frac{x_{ij}}{\sqrt{\sum_{k=1}^{m} x_{kj}^2}}$$
3. **Weighted Normalization:**
   $$v_{ij} = w_j \cdot r_{ij}, \quad \text{where } \sum_{j=1}^{n} w_j = 1$$
4. **Ideal Solutions Computation:**
   - Positive-Ideal Solution ($A^+$): $\max(v_{ij})$ for benefit criteria.
   - Negative-Ideal Solution ($A^-$): $\min(v_{ij})$ for benefit criteria.
5. **Separation Distance Calculation:**
   $$D_i^+ = \sqrt{\sum_{j=1}^n (v_{ij} - v_j^+)^2}, \quad D_i^- = \sqrt{\sum_{j=1}^n (v_{ij} - v_j^-)^2}$$
6. **Relative Closeness Preference Ranking:**
   $$R_i = \frac{D_i^-}{D_i^+ + D_i^-}, \quad R_i \in [0, 1]$$

---

## 5. System Components & Repository Structure

- `backend/data/idx_scraper.py`: Automated retrieval engine querying IDX internal endpoints for audited annual `.xlsx` workbooks.
- `backend/data/idx_parser.py`: Robust XML/Excel extractor mapping bilingual Indonesian/English financial line items to standardized domain schemas.
- `backend/data/ingestion.py`: Growth vector derivation, fallback fixtures, and caching layers.
- `backend/mining/clustering.py`: K-Means training, silhouette evaluation, inertia curve computation, and PCA coordinates projection.
- `backend/spk/topsis.py`: Multi-criteria vector normalization, customizable weight scoring, and relative closeness ranking.
- `backend/api/routes.py`: REST API exposing dataset querying, file uploads, scraper execution, and dynamic TOPSIS weight re-evaluations.
- `tests/test_engine.py`: Unit and regression test suite covering parser extraction, matrix normalization, K-Means convergence, and TOPSIS mathematical precision.

---

## 6. Verification Status
- **Automated Test Coverage:** 100% Green across all core mathematical engines and ingestion workflows.
- **Scope Integrity:** 30 non-financial ticker cohort verified free of banking leverage skew.
