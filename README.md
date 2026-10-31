# SPK x Data Mining: Quantitative Equity Decision Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4%2B-F7931E.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/tests-7%2F7%20passed-brightgreen.svg)]()

Platform Sistem Pendukung Keputusan (SPK) berbasis institusional yang mengintegrasikan **Unsupervised Machine Learning (K-Means Clustering & PCA)** dengan **Multi-Criteria Decision Making (TOPSIS)** untuk mengevaluasi dan merangking emiten saham sektor non-keuangan di Bursa Efek Indonesia (BEI / IDX) berdasarkan kinerja pertumbuhan finansial tahunan 5 periode (2020–2024 / 2021–2025).

---

## 1. Latar Belakang & Batasan Penelitian

Dalam menyaring dan menganalisis performa saham, analis menghadapi dua tantangan utama:
1. **Behavioral Cohort Bias:** Karakteristik keuangan antar industri sangat bervariasi. Membandingkan seluruh saham secara acak tanpa segmentasi kelompok membuat perusahaan padat modal terlihat bias jika dibandingkan dengan industri beraset ringan.
2. **Subjective Ranking Dilemma:** Menentukan emiten "terbaik" di antara kriteria yang saling bertolak belakang (pertumbuhan omzet vs laba bersih vs ekspansi aset vs pertumbuhan ekuitas modal) memerlukan trade-off multi-kriteria yang terukur secara matematis.

Platform ini menjembatani kedua paradigma:
- **Data Mining (K-Means & PCA):** Secara otomatis mengelompokkan emiten ke dalam kohort karakter pertumbuhan (misal: *Aggressive High-Growth*, *Steady Compounder*, dan *Mature / Defensive*) dengan reduksi dimensi 2D PCA.
- **SPK (TOPSIS):** Menghitung perangkingan objektif menggunakan metode *Technique for Order Preference by Similarity to Ideal Solution* (TOPSIS) dengan bobot kriteria yang dapat disimulasikan secara dinamis (*live interactive sliders*).

> **Mengapa Hanya Sektor Non-Keuangan? (Batasan Metodologis Resmi IDX-IC)**  
> Lembaga keuangan dan perbankan (Klasifikasi Resmi BEI: **IDX-IC Sektor Keuangan / `IDXFINANCE`**) memiliki struktur neraca yang berbeda secara fundamental: dana pihak ketiga (DPK/tabungan) dicatat sebagai liabilitas dan kredit dicatat sebagai aset, dengan rasio leverage normal mencapai 6x–10x ekuitas. Memasukkan sektor perbankan akan merusak standardisasi varians $Z$-Score pada K-Means dan mendistorsi Solusi Ideal Positif ($A^+$) TOPSIS secara tidak realistis. Oleh karena itu, batasan masalah secara ketat difokuskan pada sektor riil non-keuangan (*apples-to-apples comparison*).

---

## 2. Alur Metodologi & Formulasi Matematis

```
                  [ Audited IDX Financials (2020–2024 / 2021–2025) ]
                                          │
                                          ▼
                  [ Ekstraksi 4 Indikator Pertumbuhan Tahunan (YoY) ]
                        (Revenue, Net Income, Assets, Equity)
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
        [ K-Means Clustering ]                        [ TOPSIS Ranking ]
     • Standarisasi Z-Score                        • Normalisasi Vektor (r_ij)
     • Optimasi k (Elbow & Silhouette)             • Matriks Terbobot (v_ij)
     • Reduksi Dimensi PCA (PC1 & PC2)             • Solusi Ideal (A+ / A-)
     • Profil Kohort Karakter Emiten               • Jarak Euclidean (D+ / D-)
                   │                               • Nilai Preferensi / Skor (V_i)
                   └──────────────────────┬──────────────────────┘
                                          ▼
                      [ High-Density Quantitative Cockpit ]
                       • Bobot Kriteria Interaktif & Presets
                       • Peta Persebaran PCA 2D Interaktif
                       • Tabel Perangkingan & Audit Matrix Modal
```

### A. Ekstraksi Metrik Pertumbuhan Tahunan
Berdasarkan data laporan keuangan teraudit per tahun:
$$\text{YoY Growth} = \frac{\text{Nilai}_t - \text{Nilai}_{t-1}}{|\text{Nilai}_{t-1}|} \times 100\%$$
- **Revenue Growth ($C_1$):** Laju ekspansi omzet usaha (skala bisnis).
- **Net Income Growth ($C_2$):** Laju pertumbuhan profitabilitas bersih.
- **Asset Growth ($C_3$):** Laju ekspansi kapasitas dan aset riil.
- **Equity Growth ($C_4$):** Laju pemupukan modal bersih pemegang saham.

### B. Data Mining: K-Means & PCA (`backend/mining/clustering.py`)
1. **Standardisasi Fitur ($Z$-Score):**
   $$z = \frac{x - \mu}{\sigma}$$
2. **Validasi Jumlah Klaster ($k=3$):**
   - **Elbow Method:** Menemukan titik siku penurunan inersia paling efisien pada $k=3$ (Inersia 30.72 vs $k=2$ 52.44).
   - **Silhouette Analysis:** Memastikan pemisahan antar-kelompok tegas tanpa tumpang tindih ($s = 0.4368$ pada $k=3$).
3. **PCA 2D Dimensionality Reduction:**
   - Memproyeksikan 4 dimensi kriteria ke bidang 2D ($PC_1$ dan $PC_2$) dengan menangkap **98.04% total varians terjelaskan**.

### C. Sistem Pendukung Keputusan: TOPSIS (`backend/spk/topsis.py`)
1. **Normalisasi Vektor ($R$):**
   $$r_{ij} = \frac{x_{ij}}{\sqrt{\sum_{k=1}^m x_{kj}^2}}$$
2. **Matriks Normalisasi Terbobot ($V$):**
   $$v_{ij} = w_j \cdot r_{ij}, \quad \text{dengan } \sum w_j = 1.0$$
3. **Penentuan Solusi Ideal Positif ($A^+$) dan Negatif ($A^-$):**
   $$A^+ = \{ \max_i(v_{ij}) \}, \quad A^- = \{ \min_i(v_{ij}) \}$$
4. **Jarak Pemisahan Euclidean ($D_i^+$ dan $D_i^-$):**
   $$D_i^+ = \sqrt{\sum_{j=1}^n (v_{ij} - v_j^+)^2}, \quad D_i^- = \sqrt{\sum_{j=1}^n (v_{ij} - v_j^-)^2}$$
5. **Skor Kedekatan Relatif ($V_i$):**
   $$V_i = \frac{D_i^-}{D_i^+ + D_i^-}, \quad V_i \in [0, 1]$$

---

## 3. Struktur Direktori Proyek

```
SPK X Data Mining/
├── backend/
│   ├── main.py                  # Entrypoint server FastAPI & static mounting
│   ├── api/
│   │   └── routes.py            # Endpoint REST (Stocks, Clusters, TOPSIS, Delete)
│   ├── data/
│   │   ├── download.py          # Modul unduhan laporan keuangan IDX via Playwright Edge
│   │   ├── extract.py           # Ekstraktor openpyxl sheet [1000000], [1210000], [1321000]
│   │   ├── idx_parser.py        # Parser & penghubung dataset fundamental
│   │   ├── ingestion.py         # Universe manager & agregasi metrik
│   │   └── sector_validator.py  # Validator sektor IDX-IC (IDXFINANCE blacklist filter)
│   ├── mining/
│   │   └── clustering.py        # K-Means, Silhouette, Elbow, dan PCA
│   └── spk/
│       └── topsis.py            # Normalisasi matriks, pembobotan, dan skor Vi
├── frontend/
│   └── static/
│       └── index.html           # Single-page terminal cockpit (Plus Jakarta Sans, Light/Dark)
├── data/
│   ├── financial_raw.csv        # 151 baris data laporan keuangan 5 tahun audited
│   ├── financial_raw.xlsx       # Workbook data mentah audited
│   ├── kmeans_dataset_yoy.csv   # Dataset agregat rata-rata pertumbuhan YoY
│   └── data_quality_report.csv  # Laporan audit integritas data (CRISP-DM Tahap 3)
├── tests/
│   └── test_engine.py           # Unit test suite lengkap (7/7 passed)
├── LOGBOOK.md                   # Logbook perkembangan berkala dan solusi teknis
├── requirements.txt             # Dependensi Python
└── pytest.ini                   # Konfigurasi pengujian
```

---

## 4. Cara Menjalankan Aplikasi

### Prasyarat
- Python 3.10 atau versi yang lebih baru
- Virtual environment disarankan (`.venv`)

### 1. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 2. Jalankan Pengujian Otomatis
```bash
pytest tests/test_engine.py -v
```

### 3. Jalankan Server Web
```bash
uvicorn backend.main:app --reload --port 8000
```
Buka peramban (browser) dan akses **`http://localhost:8000`**.

---

## 5. Fitur Utama Terminal Web
- **3 Tab Analitik Utama:** `PCA scatter (1)`, `Weights (2)`, `Diagnostics (3)`.
- **Live Decision Re-Ranking:** Menggeser slider kriteria langsung menghitung ulang peringkat TOPSIS secara *real-time* di memori peramban.
- **Peta Persebaran PCA 2D:** Visualisasi interaktif titik klaster emiten lengkap dengan lingkar fokus (*focus ring*) dan identifikasi klaster.
- **Audit Matrix Modal (Hotkey `m`):** Menampilkan transparansi perhitungan matematis ($r_{ij}$, $v_{ij}$, $A^+$, $A^-$, $D^+$, $D^-$) untuk keperluan sidang/pertanggungjawaban akademis.
- **Audited Financial Statements Viewer:** Klik salah satu emiten untuk melihat riwayat data mentah hasil ekstraksi dari file Excel BEI per tahunnya.
- **Opsi Hapus Emiten:** Tombol `✕` pada tabel untuk menyimulasikan evaluasi jika emiten tertentu dikeluarkan dari universe.
- **Tema Gelap & Terang (Hotkey `d`):** Skema warna *High-Contrast* yang dirancang ergonomis untuk presentasi.
