# Blueprint & Implementation Roadmap
## SPK Pemilihan Saham: Integrasi K-Means Clustering & TOPSIS (Web-Based)

---

### 1. Architectural Overview & Pipeline
```
[Data Ingestion (yfinance / IDX Excel)]
              │
              ▼
[Data Preprocessing & Feature Engineering]
  - Extract: Revenue, Net Income, Total Assets, ROE (3-4 Years)
  - Calculate YoY Growth Rates (ΔRev, ΔNetInc, ΔAsset) & Efficiency
  - Clean Outliers / Handle Missing Data / Robust Scaling
              │
              ▼
[Stage 1: K-Means Clustering Engine]
  - Elbow Method (WCSS/Inertia) & Silhouette Score (Finding optimal k)
  - Cluster Segmentation (e.g., Aggressive Growth, Stable/Stagnant, Distressed)
  - 2D/3D PCA & Radar Profile Vector Generation
              │
              ▼
[Stage 2: Decision Support Engine (TOPSIS)]
  - User-driven or Entropy-weighted Criteria Configuration
  - Vector Normalization (R Matrix) & Weighted Matrix (Y Matrix)
  - Positive Ideal Solution (A+) & Negative Ideal Solution (A-)
  - Closeness Coefficient (Vi) & Final Stock Ranking
              │
              ▼
[Interactive Web Dashboard]
  - Cluster Visualizer (PCA Scatter + Financial Radar)
  - Dynamic Weight Sliders & Live Recalculation
  - Ranked Leaderboard with Detailed Formula Breakdown (Lecturer-friendly)
```

---

### 2. Implementation Milestones

#### Phase 1: Data Ingestion & Preprocessing Core
- [ ] Implement `ingest_idx.py` using `yfinance` to pull multi-year financials for LQ45 / Kompas100 tickers (`.JK`).
- [ ] Build preprocessing pipeline: compute YoY growth rates ($\Delta \text{Revenue}$, $\Delta \text{Net Income}$, $\Delta \text{Asset}$) and average ROE.
- [ ] Export clean benchmark dataset to `data/idx_financials_clean.csv`.

#### Phase 2: K-Means Clustering & Dimensionality Reduction
- [ ] Implement `kmeans_engine.py`: Scikit-Learn pipeline with `StandardScaler` / `RobustScaler`.
- [ ] Add evaluation utilities: Silhouette Analysis and Elbow Curve data generators.
- [ ] Add PCA projection (2D/3D coordinates) and cluster centroid profiling for frontend charts.

#### Phase 3: TOPSIS Decision Engine
- [ ] Implement `topsis_engine.py`:
  - Step 1: Decision Matrix Normalization ($r_{ij} = \frac{x_{ij}}{\sqrt{\sum x_{ij}^2}}$).
  - Step 2: Weighted Normalization ($y_{ij} = w_j \cdot r_{ij}$).
  - Step 3: Determine $A^+$ and $A^-$.
  - Step 4: Separation Measures ($D_i^+$ and $D_i^-$).
  - Step 5: Relative Closeness ($V_i = \frac{D_i^-}{D_i^+ + D_i^-}$).
- [ ] Support both within-cluster ranking and global ranking modes.

#### Phase 4: Backend API (FastAPI)
- [ ] `GET /api/stocks`: List available tickers and raw/processed metrics.
- [ ] `POST /api/clustering/run`: Run K-Means with configurable $k$ and return cluster assignments + PCA coordinates.
- [ ] `POST /api/topsis/rank`: Compute TOPSIS ranking with dynamic user weights.
- [ ] `GET /api/evaluation`: Return Silhouette scores, Elbow points, and cluster summaries.

#### Phase 5: Interactive Web Frontend (Vite + React / Tailwind / Chart.js or Plotly)
- [ ] **Overview & Dataset Table:** Filterable grid of stock metrics.
- [ ] **Cluster Explorer:** Interactive PCA Scatter Plot with tooltips + Cluster Radar chart.
- [ ] **Weight Calibration & TOPSIS Ranking:** Live sliders for criteria weights + animated rank table showing step-by-step matrix math.

---

### 3. Verification & Validation Metrics
- **Clustering Quality:** Silhouette Coefficient $> 0.40$, distinct separation on PCA.
- **TOPSIS Determinism:** Mathematical validation comparing computed $V_i$ against known manual spreadsheet benchmarks.
- **API Performance:** Sub-100ms response time for dynamic weight re-ranking.
