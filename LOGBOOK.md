# Logbook Perkembangan Proyek: Integrasi K-Means Clustering & TOPSIS untuk Pemilihan Saham IDX

Dokumen ini berisi pencatatan berkala, kendala, solusi metodologis, dan pencapaian teknis selama perancangan serta implementasi sistem pendukung keputusan (SPK) dan data mining saham non-keuangan di Bursa Efek Indonesia (BEI / IDX) periode 2020–2024 / 2021–2025.

---

## Log Aktivitas Mingguan & Milestone

### 1. Analisis & Inisialisasi Proyek
* **Aktivitas:** Perumusan Masalah, Studi Literatur, dan Inisialisasi Workspace Arsitektur
* **Kendala (Obstacles):**
  Adanya perbedaan fundamental pada struktur neraca keuangan antara sektor perbankan/finansial dengan sektor riil (non-keuangan). Pada sektor perbankan, simpanan nasabah dicatat sebagai liabilitas, serta rasio utang/leverage operasionalnya wajar mencapai 6x–10x ekuitas. Memasukkan emiten perbankan bersamaan dengan sektor riil akan menyebabkan *extreme outlier* yang mendistorsi standardisasi varians $Z$-Score K-Means dan menarik vektor Solusi Ideal Positif ($A^+$) TOPSIS secara tidak realistis.
* **Catatan & Solusi (Notes & Solutions):**
  Menetapkan batasan masalah penelitian secara ketat (*cohort selection*) mengacu pada klasifikasi resmi Bursa Efek Indonesia **IDX-IC (Sektor Keuangan / `IDXFINANCE`)**: mengeksklusikan perbankan/lembaga keuangan dan memfokuskan analisis hanya pada 30 emiten sektor non-keuangan di BEI periode 2020–2024 agar perbandingan kinerja bersifat setara (*apples-to-apples comparison*). Menginisialisasi arsitektur proyek modular berbasis FastAPI backend dan High-Density Web Terminal UI.
* **Pencapaian (Achievements):**
  Terbentuknya rumusan masalah yang matang, batasan dataset 30 emiten non-keuangan, serta struktur repositori proyek yang siap untuk integrasi data mining dan SPK.

---

### 2. Pengumpulan Dataset (Data Acquisition)
* **Aktivitas:** Pengumpulan Laporan Keuangan Teraudit Emiten IDX Periode 2020–2024
* **Kendala (Obstacles):**
  Layanan API komersial penyedia data pasar modal historis mengenakan biaya langganan yang mahal untuk akses laporan keuangan multi-tahun. Pengunduhan manual puluhan laporan keuangan satu per satu juga sangat tidak efisien dan rentan *human error*, serta portal BEI (`idx.co.id`) dilindungi sistem WAF/Cloudflare yang membatasi bot otomatis.
* **Catatan & Solusi (Notes & Solutions):**
  Membangun modul pengunduh otomatis berbasis Playwright headless Edge (`backend/data/download.py`) dan *ingestion engine* (`backend/data/idx_scraper.py`) yang berinteraksi langsung dengan endpoint resmi Bursa Efek Indonesia. Sistem mampu menangani *session cookies*, memverifikasi ketersediaan laporan tahunan teraudit (*Audited Annual Statements / TW4*), dan mengunduh file `.xlsx` secara otomatis tanpa biaya API pihak ketiga.
* **Pencapaian (Achievements):**
  Berhasil mengumpulkan 150+ file laporan keuangan tahunan teraudit (30 emiten $\times$ 5 periode data) langsung dari publikasi resmi BEI ke folder `data/raw_reports/`.

---

### 3. Pre-Processing Data & Feature Extraction
* **Aktivitas:** Parsing Laporan Keuangan Multi-Sheet, Ekstraksi 4 Indikator Pertumbuhan, dan Normalisasi Satuan
* **Kendala (Obstacles):**
  Format pelaporan baris dan istilah akun akuntansi pada file Excel laporan keuangan IDX memiliki variasi penamaan antar emiten. Selain itu, satuan pelaporan antar emiten sangat beragam (ada yang melaporkan dalam satuan penuh, ribuan, jutaan, hingga miliaran rupiah, serta mata uang USD), dan terdapat potensi anomali nilai negatif saat laba bersih bertransisi dari rugi ke untung (*negative base*).
* **Catatan & Solusi (Notes & Solutions):**
  Mengembangkan parser otomatis berbasis OpenPyXL (`backend/data/extract.py` & `idx_parser.py`) yang secara presisi menyasar lembar resmi XBRL/Excel BEI:
  - Sheet `[1000000]` General Information: mendeteksi mata uang pelaporan (IDR/USD) dan tingkat pembulatan.
  - Sheet `[1210000]` Statement of Financial Position: mengekstrak Total Aset (*Total Assets*) dan Total Ekuitas (*Total Equity*).
  - Sheet `[1321000]` Statement of Profit or Loss: mengekstrak Pendapatan Usaha (*Revenue*) dan Laba Bersih (*Net Income*).
  
  Melakukan standarisasi satuan keuangan seragam ke basis **IDR Billion (Miliar Rupiah)**, menangani kasus *negative base* secara matematis ($\frac{V_t - V_{t-1}}{|V_{t-1}|} \times 100\%$), serta menghitung laju pertumbuhan tahunan (YoY Growth Rate) rata-rata selama 5 periode untuk 4 variabel utama:
  1. **Revenue Growth ($C_1$)**
  2. **Net Income Growth ($C_2$)**
  3. **Asset Growth ($C_3$)**
  4. **Equity Growth ($C_4$)**
* **Pencapaian (Achievements):**
  Dataset final 30 emiten non-keuangan yang bersih dan terverifikasi tanpa *missing value* (`data/financial_raw.csv`, `data/financial_raw.xlsx`, dan `data/kmeans_dataset_yoy.csv`), dilengkapi laporan audit integritas data sesuai standar CRISP-DM Tahap 3 (`data/data_quality_report.csv`).

---

### 4. Implementasi Algoritma Data Mining (K-Means Clustering & PCA)
* **Aktivitas:** Standarisasi Z-Score, Penentuan Nilai $k$ Optimal, dan Reduksi Dimensi PCA 2D
* **Kendala (Obstacles):**
  Skala pertumbuhan antar indikator memiliki sebaran varians yang berbeda, sehingga algoritma berbasis jarak Euclidean berisiko didominasi oleh fitur dengan angka ekstrem jika tidak distandarisasi. Selain itu, penentuan jumlah klaster ($k$) secara subjektif dapat menghasilkan segmentasi yang bias atau tumpang tindih (*overlapping*).
* **Catatan & Solusi (Notes & Solutions):**
  Menerapkan standarisasi data menggunakan `StandardScaler` ($Z$-Score, $\mu = 0, \sigma = 1$). Untuk menentukan jumlah klaster $k$ secara objektif dan matematis, diimplementasikan dua pengujian ilmiah pada modul `backend/mining/clustering.py`:
  - **Elbow Method (Inertia/WCSS):** Menemukan titik siku penurunan inersia paling efisien pada **$k=3$** (Inersia 30.72, berkurang drastis dari $k=2$ di 52.44).
  - **Silhouette Analysis:** Membuktikan bahwa **$k=3$** memiliki skor kohesi dan separasi tertinggi (**$s = 0.4368$**), jauh lebih tegas dibanding $k=4$ ($s = 0.3709$).
  
  Menerapkan algoritma **PCA (Principal Component Analysis)** untuk mereduksi 4 dimensi kriteria menjadi 2 komponen utama ($PC_1$ dan $PC_2$) yang mempertahankan **98.04% total varians terjelaskan**.
* **Pencapaian (Achievements):**
  Terbentuknya 3 profil klaster emiten yang jelas karakteristiknya:
  - **Klaster 0 — Steady Compounder & Value Creator (14 emiten):** Pertumbuhan stabil dan seimbang (omzet +10.1%, laba +12.7%, modal +10.9%).
  - **Klaster 1 — Aggressive High-Growth Expansion (12 emiten):** Pertumbuhan ekspansif dua digit (omzet +16.6%, laba +23.8%, aset +12.3%).
  - **Klaster 2 — Mature / Defensive Low-Growth (5 emiten):** Perusahaan mapan dengan pertumbuhan melambat (omzet +3.3%, laba +3.1%, aset +2.1%).

---

### 5. Implementasi Sistem Pendukung Keputusan (Metode TOPSIS)
* **Aktivitas:** Perumusan Kriteria, Normalisasi Matriks Keputusan, dan Perangkingan Preferensi TOPSIS
* **Kendala (Obstacles):**
  Dalam pengambilan keputusan investasi saham, analis memiliki preferensi strategi yang dinamis (misalnya strategi agresif yang mengutamakan laba vs strategi defensif yang mengutamakan modal ekuitas). Diperlukan mesin pengambil keputusan multi-kriteria yang adil dan dapat disimulasikan secara interaktif.
* **Catatan & Solusi (Notes & Solutions):**
  Membangun kalkulator TOPSIS matematis (`backend/spk/topsis.py`):
  1. Menetapkan ke-4 kriteria pertumbuhan sebagai **Benefit Criteria** (semakin tinggi pertumbuhan omzet, laba bersih, aset, dan ekuitas, semakin baik performa emiten).
  2. Menghitung matriks normalisasi vektor ($r_{ij} = \frac{x_{ij}}{\sqrt{\sum x_{kj}^2}}$).
  3. Mengalikan dengan bobot kriteria dinamis ($v_{ij} = w_j \cdot r_{ij}$, $\sum w_j = 1.0$).
  4. Menentukan Solusi Ideal Positif ($A^+$) dan Solusi Ideal Negatif ($A^-$).
  5. Menghitung jarak pemisahan Euclidean ($D_i^+$ dan $D_i^-$).
  6. Menghitung skor preferensi kedekatan relatif ($V_i = \frac{D_i^-}{D_i^+ + D_i^-}$).
  
  Menetapkan aturan rekomendasi keputusan:
  - $V_i \ge 0.65$: **Strong Buy / Top Pick**
  - $0.50 \le V_i < 0.65$: **Buy / Accumulate**
  - $V_i < 0.30$: **Reduce / Avoid**
* **Pencapaian (Achievements):**
  Dihasilkannya skor preferensi $V_i$ (skala 0 hingga 1.000) dan peringkat urutan saham terbaik yang paling mendekati solusi ideal positif dan terjauh dari solusi ideal negatif secara deterministik.

---

### 6. Integrasi Sistem & Pembuatan Web Dashboard Terminal
* **Aktivitas:** Integrasi Pipeline Backend ke Web Terminal Kuantitatif Interaktif
* **Kendala (Obstacles):**
  Hasil perhitungan klastering dan perangkingan yang berupa matriks angka mentah sulit diinterpretasikan oleh pemangku kepentingan jika disajikan dalam format statis. Selain itu, penggunaan *library* grafik pihak ketiga yang berat (seperti Chart.js/Plotly CDN) dapat memperlambat rendering antarmuka dan menimbulkan dependensi eksternal.
* **Catatan & Solusi (Notes & Solutions):**
  Membangun antarmuka web interaktif berbasis FastAPI dan Native Modern CSS/SVG (`frontend/static/index.html`):
  - Menggunakan visualisasi **Native High-Precision SVG** berbobot ringan untuk grafik *PCA 2D Scatter Plot*, kurva evaluasi *Elbow*, dan diagram batang *Silhouette*.
  - Menyediakan *Tactile Weight Mixer* (slider bobot live) dengan *preset* strategi investasi (*Balanced LQ45*, *Aggressive Growth*, *Defensive Quality*, *Asset Expansion*) yang menghitung ulang peringkat TOPSIS secara *real-time* (< 2 ms) di memori peramban.
  - Menyediakan *Audit Matrix Modal (Hotkey 'm')* untuk transparansi akademis langkah matematis ($r_{ij}, v_{ij}, A^+, A^-, D^+, D^-$).
  - Menyediakan *Audited Statements Viewer* untuk memeriksa riwayat laporan keuangan asli emiten per tahunnya.
  - Menerapkan fitur penghapusan emiten (*Delete stock from universe*) dan tema *High-Contrast* (Light/Dark Mode, Hotkey 'd') dengan tipografi *Plus Jakarta Sans* dan *JetBrains Mono*.
* **Pencapaian (Achievements):**
  Sistem aplikasi web SPK x Data Mining terintegrasi penuh, *responsive*, berkinerja tinggi, lulus 100% unit test (`pytest`), dan siap didemonstrasikan untuk pengujian akademik.
