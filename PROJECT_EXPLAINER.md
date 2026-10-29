# SPK x Data Mining: Quantitative Equity Decision Platform

An institutional-grade decision support platform that combines **Unsupervised Machine Learning (K-Means Clustering & PCA)** with **Multi-Criteria Decision Making (TOPSIS)** to evaluate and rank 30 non-financial publicly listed companies on the Indonesia Stock Exchange (IDX / BEI).

---

## 1. What This Project Is About

Investors and portfolio analysts frequently struggle with two conflicting challenges when screening equities:
1. **Behavioral Cohort Bias:** Financial indicators (growth, margins, leverage) vary widely across industries. Without grouping, high-capital businesses look artificially worse than low-asset operators.
2. **Subjective Ranking Dilemmas:** Picking the "best" company across multiple competing metrics (e.g., higher profit growth vs. lower leverage vs. higher equity expansion) requires rigorous mathematical multi-criteria trade-offs.

This platform bridges both paradigms:
- **Data Mining (Clustering):** Automatically groups 30 audited non-financial Indonesian companies into distinct behavioral cohorts (e.g., Aggressive Compounders, Defensive Titans, Capital Intensive) based on their 5-year financial growth trajectory (2020–2024).
- **SPK / Decision Support (TOPSIS):** Computes an algorithmic ranking using the *Technique for Order Preference by Similarity to Ideal Solution* (TOPSIS), allowing analysts to adjust weights dynamically according to their investment strategy.

> **Why Non-Financial Equities Only?**  
> Commercial banks and financial institutions operate with inherently distinct leverage structures (customer deposits as liabilities, loans as assets). Including them alongside real-sector firms distorts variance scaling, pulls K-Means centroids into extreme leverage outliers, and skews TOPSIS Ideal Best ($A^+$) vectors.

---

## 2. Core Methodologies & Mathematical Formulation

```
                     [ Audited IDX Financials (2020–2024) ]
                                       │
                                       ▼
                     [ 5-Year CAGR Growth Vector Derivation ]
                      (Revenue, Net Income, Assets, Equity)
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
     [ K-Means Clustering ]                        [ TOPSIS Ranking ]
  • StandardScaler Normalization                • Vector Normalization (r_ij)
  • Optimal k Search (Silhouette & Elbow)       • Weight Matrix Application (v_ij)
  • PCA 2D/3D Dimensionality Reduction         • Ideal Solutions (A+ / A-)
  • Behavioral Cluster Profiles                 • Euclidean Distances (D+ / D-)
                │                               • Relative Closeness (V_i)
                └──────────────────────┬──────────────────────┘
                                       ▼
                    [ High-Density Quantitative Cockpit ]
                     • Tactile Weight Sliders & Presets
                     • Interactive 2D/3D PCA Scatter
                     • Real-time Ranked Table & Audit Matrix
```

### A. Feature Extraction: 5-Year Compound Growth (CAGR)
Using audited financial reports from 2020 through 2024, the engine calculates the Compound Annual Growth Rate (CAGR) across four foundational balance-sheet indicators:

$$\text{CAGR} = \left( \frac{\text{Value}_{2024}}{\text{Value}_{2020}} \right)^{\frac{1}{4}} - 1$$

- **Revenue Growth ($C_1$):** Top-line business expansion rate.
- **Net Income Growth ($C_2$):** Bottom-line profitability trajectory.
- **Asset Growth ($C_3$):** Balance sheet capital expansion.
- **Equity Growth ($C_4$):** Long-term shareholder value compounding.

---

### B. Machine Learning Engine: K-Means & PCA (`backend/mining/clustering.py`)

1. **Feature Standardization ($Z$-Score):**
   $$z = \frac{x - \mu}{\sigma}$$
   Prevents large-nominal metrics from dominating distance metrics.

2. **Optimal Cluster Selection ($k$ Evaluation):**
   - **Elbow Method:** Evaluates sum of squared distances to cluster centers (Inertia) across $k \in [2, 6]$.
   - **Silhouette Analysis:** Measures cohesion within clusters vs. separation between clusters to automatically select the optimal $k$ (`best_k`).

3. **Dimensionality Reduction (PCA):**
   - Projects 4-dimensional normalized financial vectors down to 2D ($PC_1, PC_2$) and 3D coordinates.
   - Captures over 65–75% of cumulative explained variance for visualization on the scatter plot.

4. **Cluster Profiling:**
   - Classifies equities into intuitive cohorts (e.g., *Cluster 0: High-Margin Compounders*, *Cluster 1: Leveraged Expansion*, *Cluster 2: Stable Value*).

---

### C. SPK Engine: TOPSIS Ranking (`backend/spk/topsis.py`)

1. **Vector Normalization Matrix ($R$):**
   $$r_{ij} = \frac{x_{ij}}{\sqrt{\sum_{k=1}^{m} x_{kj}^2}}$$
   where $m = 30$ alternative companies, $n = 4$ growth criteria.

2. **Weighted Normalized Matrix ($V$):**
   $$v_{ij} = w_j \cdot r_{ij}, \quad \text{where } \sum_{j=1}^n w_j = 1.0$$

3. **Identification of Ideal Solutions:**
   - **Positive Ideal Solution ($A^+$):** The best performance across all criteria:
     $$A^+ = \{ v_1^+, v_2^+, \dots, v_n^+ \} = \{ \max_i(v_{ij}) \mid j \in \text{Benefit} \}$$
   - **Negative Ideal Solution ($A^-$):** The worst performance across all criteria:
     $$A^- = \{ v_1^-, v_2^-, \dots, v_n^- \} = \{ \min_i(v_{ij}) \mid j \in \text{Benefit} \}$$

4. **Euclidean Distance Computation:**
   $$D_i^+ = \sqrt{\sum_{j=1}^n (v_{ij} - v_j^+)^2}, \quad D_i^- = \sqrt{\sum_{j=1}^n (v_{ij} - v_j^-)^2}$$

5. **Relative Closeness Score ($V_i$):**
   $$V_i = \frac{D_i^-}{D_i^+ + D_i^-}, \quad V_i \in [0, 1]$$
   - $V_i = 1$: Hypothetical company equal to the Positive Ideal Solution.
   - $V_i = 0$: Hypothetical company equal to the Negative Ideal Solution.
   Companies are ranked in descending order of $V_i$.

---

## 3. System Architecture & Components

```
SPK X Data Mining/
├── backend/
│   ├── main.py                  # FastAPI application entrypoint & static mounting
│   ├── api/
│   │   └── routes.py            # REST endpoints (Stocks, Clusters, TOPSIS, Evaluation)
│   ├── data/
│   │   ├── idx_scraper.py       # Automated scraper for IDX financial reports (.xlsx)
│   │   ├── idx_parser.py        # Bilingual Excel/XML balance sheet parser
│   │   └── ingestion.py         # CAGR derivation & cached 30-stock universe
│   ├── mining/
│   │   └── clustering.py        # K-Means, Silhouette evaluation, PCA 2D/3D
│   └── spk/
│       └── topsis.py            # Matrix normalization, weighted scoring, ideal distances
├── frontend/
│   └── static/
│       └── index.html           # High-density quantitative cockpit (No build step required)
├── tests/
│   └── test_engine.py           # Automated test suite (Scraper, Parser, K-Means, TOPSIS)
├── data/                        # Raw IDX .xlsx financial statements (2020–2024)
└── requirements.txt             # Core dependencies (FastAPI, scikit-learn, numpy, pandas)
```

### Core API Endpoints (`backend/api/routes.py`):
| Endpoint | Method | Description |
|---|---|---|
| `/api/stocks` | `GET` | Returns 30 audited equities with raw balance sheet growth and historical metrics. |
| `/api/mining/clusters` | `GET` | Computes K-Means clustering ($k=2..6$) with PCA projections and cluster centroid labels. |
| `/api/mining/evaluation` | `GET` | Returns Elbow curve inertia values and Silhouette scores for optimal $k$ diagnosis. |
| `/api/spk/topsis/calculate` | `POST` | Accepts custom criteria weights, recalculates TOPSIS matrices, and returns real-time rankings. |
| `/api/portfolio/summary` | `GET` | Summarizes sector concentration, aggregate growth, and top-tier recommendations. |

---

## 4. Frontend Cockpit & Ergonomics

The user interface (`frontend/static/index.html`) is built as a single-page quantitative workstation designed for speed, high data density, and zero latency:
- **Typography:** Dual-tier typography using `Space Grotesk` (clean display headings) and `JetBrains Mono` with `tabular-nums` for precision alignment of financial figures.
- **Tactile Weight Mixer:** Interactive range sliders with automatic normalization and quick presets:
  - *Balanced LQ45* (Equalized baseline weights)
  - *Aggressive Growth* (Heavy weight on Net Income & Revenue CAGR)
  - *Defensive Quality* (Prioritizes balance sheet stability and Equity compounding)
  - *Asset Expansion* (Highlights companies reinvesting heavily in operational assets)
- **Interactive Visualizations:**
  - **PCA Cluster Scatter:** 2D interactive coordinate plane mapping corporate similarities.
  - **Radar Dossier:** Multi-dimensional spider chart comparing individual stocks against the universe average.
  - **Elbow & Silhouette Diagnostics:** Visual confirmation of mathematical cluster validity.
- **Audit Matrix Modal:** Full academic inspection window exposing step-by-step mathematical matrices ($R$, $V$, $D^+$, $D^-$) for thesis and defense verification.
- **Keyboard Ergonomics:**
  - `/` or `s` : Quick-focus ticker search filter
  - `1`, `2`, `3` : Switch cockpit view tabs (PCA Scatter, Weights Mixer, Pipeline Diagnostics)
  - `m` : Open TOPSIS step matrix audit modal
  - `e` : Export universe data to JSON
  - `Esc` : Dismiss active modals and slide-out drawers

---

## 5. How to Run & Verify

### Prerequisites
- Python 3.10+
- Active virtual environment (`.venv`)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Test Suite
```bash
pytest tests/test_engine.py -v
```
All unit and regression tests verify scraper parsing, standard scaling, K-Means convergence, and TOPSIS vector calculations.

### 3. Launch Development Server
```bash
uvicorn backend.main:app --reload --port 8000
```
Open **`http://localhost:8000`** in any modern web browser to access the live terminal.
