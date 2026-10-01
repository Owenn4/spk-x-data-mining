# Logbook Perkembangan Proyek: Integrasi K-Means Clustering & TOPSIS untuk Pemilihan Saham IDX

Dokumen ini berisi pencatatan berkala, kendala, solusi metodologis, dan pencapaian teknis selama perancangan serta implementasi sistem pendukung keputusan dan data mining saham non-keuangan BEI (2020–2024).

---

## Log Aktivitas Mingguan & Milestone

### 1. Analisis & Inisialisasi Proyek
* **Aktivitas:** Perumusan Masalah, Studi Literatur, dan Inisialisasi Workspace Arsitektur
* **Kendala (Obstacles):**
  Adanya perbedaan fundamental pada struktur neraca keuangan antara sektor perbankan/finansial dengan sektor riil (non-keuangan). Pada sektor perbankan, simpanan nasabah dicatat sebagai liabilitas, sehingga rasio DER (*Debt to Equity Ratio*) dan CR (*Current Ratio*) bernilai sangat ekstrem (outlier) yang berisiko merusak normalisasi matriks dan akurasi klastering.
* **Catatan & Solusi (Notes & Solutions):**
  Menetapkan batasan masalah penelitian secara ketat (*cohort selection*): mengeksklusikan sektor perbankan dan memfokuskan analisis hanya pada 30 emiten sektor non-keuangan di BEI periode 2020–2024 agar perbandingan rasio keuangan bersifat setara (*apple-to-apple comparison*). Menginisialisasi workspace proyek dengan arsitektur modular (FastAPI backend dan Modern Web UI).
* **Pencapaian (Achievements):**
  Terbentuknya rumusan masalah yang matang, batasan dataset 30 emiten non-keuangan, serta struktur repositori proyek yang siap untuk integrasi data mining dan SPK.

---

### 2. Pengumpulan Dataset (Data Acquisition)
* **Aktivitas:** Pengumpulan Data Fundamental Emiten IDX Periode 2020–2024
* **Kendala (Obstacles):**
  Layanan API komersial penyedia data pasar modal historis (seperti Bloomberg, Refinitiv, atau Financial Modeling Prep) mengenakan biaya langganan yang mahal untuk akses laporan keuangan komprehensif 5 tahun. Selain itu, pengunduhan manual puluhan laporan keuangan satu per satu sangat tidak efisien dan rentan *human error*.
* **Catatan & Solusi (Notes & Solutions):**
  Membangun modul *automated web scraping* dan *ingestion engine* mandiri (`backend/data/idx_scraper.py`) yang berinteraksi langsung dengan portal resmi Bursa Efek Indonesia (`idx.co.id`). Sistem mengunduh laporan keuangan tahunan teraudit berformat `.xlsx` secara otomatis dan legal tanpa biaya API pihak ketiga.
* **Pencapaian (Achievements):**
  Berhasil mengumpulkan 150 file laporan keuangan tahunan teraudit (30 emiten x 5 tahun: 2020–2024) langsung dari sumber data primer BEI.

---

### 3. Pre-processing & Feature Extraction
* **Aktivitas:** Parsing Laporan Keuangan, Ekstraksi Rasio, dan Agregasi Rata-rata 5 Tahun
* **Kendala (Obstacles):**
  Format pelaporan baris dan istilah akun akuntansi pada file Excel laporan keuangan IDX sering kali memiliki variasi penamaan antar emiten. Terdapat pula potensi nilai hilang (*missing values*) atau nilai ekstrem sementara akibat dampak anomali pasar.
* **Catatan & Solusi (Notes & Solutions):**
  Mengembangkan parser otomatis (`idx_parser.py`) dengan pemetaan regex untuk mengekstrak 6 rasio fundamental utama: **Current Ratio (CR)**, **Debt to Equity Ratio (DER)**, **Return on Equity (ROE)**, **Price to Earnings Ratio (PER)**, **Price to Book Value (PBV)**, dan **Earning Per Share (EPS)**. Melakukan agregasi nilai rata-rata 5 tahun (2020–2024) untuk mencerminkan stabilitas kinerja jangka panjang.
* **Pencapaian (Achievements):**
  Dataset final 30 emiten non-keuangan dengan 6 fitur rasio fundamental yang bersih, terverifikasi tanpa *missing value*, dan tersimpan dalam struktur matriks siap olah.

---

### 4. Implementasi Algoritma Data Mining (K-Means Clustering)
* **Aktivitas:** Standarisasi Data, Penentuan Jumlah Klaster Optimal, dan Eksekusi K-Means
* **Kendala (Obstacles):**
  Skala satuan antar rasio memiliki rentang yang sangat berbeda (misalnya EPS dalam rupiah/satuan ratusan, sedangkan PBV dan ROE dalam rasio/desimal), sehingga algoritma berbasis jarak Euclidean berisiko didominasi oleh fitur dengan skala besar. Selain itu, penentuan nilai $k$ (jumlah klaster) yang subjektif dapat menghasilkan segmentasi yang tidak optimal.
* **Catatan & Solusi (Notes & Solutions):**
  Menerapkan standarisasi data menggunakan *StandardScaler* ($z$-score). Untuk menentukan jumlah klaster $k$ secara objektif dan matematis, diimplementasikan pengujian kombinasi metode **Elbow Method (Inertia/WCSS)** dan **Silhouette Score Analysis**.
* **Pencapaian (Achievements):**
  Terbentuknya 3 klaster emiten yang jelas karakteristiknya (Cluster 0: *Moderate/Stable Growth*, Cluster 1: *High Undervalued/Growth Potential*, Cluster 2: *High Leverage/Volatile*) dengan validasi nilai Silhouette Score optimal ($k=3$).

---

### 5. Implementasi Sistem Pendukung Keputusan (Metode TOPSIS)
* **Aktivitas:** Pembobotan Kriteria, Normalisasi Matriks Keputusan, dan Perankingan TOPSIS
* **Kendala (Obstacles):**
  Klasifikasi sifat kriteria yang berlawanan (*benefit* vs *cost*): kriteria seperti ROE, EPS, dan CR diharapkan maksimal (*benefit*), sedangkan PER, PBV, dan DER idealnya lebih rendah atau terkontrol (*cost*). Pemilihan alternatif terbaik dari klaster unggulan membutuhkan pembobotan yang konsisten.
* **Catatan & Solusi (Notes & Solutions):**
  Membangun kalkulator TOPSIS matematis (`topsis.py`): menghitung matriks ternormalisasi ($r_{ij}$), matriks ternormalisasi terbobot ($y_{ij}$), menentukan Solusi Ideal Positif ($A^+$) dan Solusi Ideal Negatif ($A^-$), serta menghitung jarak Euclidean ($D_i^+, D_i^-$) untuk mendapatkan nilai preferensi relatif ($V_i$).
* **Pencapaian (Achievements):**
  Dihasilkannya skor preferensi $V_i$ (0 hingga 1) dan peringkat urutan saham terbaik yang paling mendekati solusi ideal positif dan terjauh dari solusi ideal negatif.

---

### 6. Integrasi Sistem & Pembuatan Dashboard Visualisasi
* **Aktivitas:** Integrasi Pipeline Backend ke Web Studio Interaktif
* **Kendala (Obstacles):**
  Hasil perhitungan klastering dan perankingan yang berupa matriks angka mentah sulit dipahami oleh pemangku kepentingan (*stakeholders*) atau pengguna awam jika disajikan tanpa visualisasi interaktif.
* **Catatan & Solusi (Notes & Solutions):**
  Membangun antarmuka web interaktif dengan FastAPI dan modern HTML/CSS/Chart.js yang menyajikan visualisasi grafik *Scatter Plot Clustering*, kurva evaluasi *Elbow/Silhouette*, tabel matriks normalisasi TOPSIS, serta scoreboard peringkat rekomendasi saham secara *real-time*.
* **Pencapaian (Achievements):**
  Sistem aplikasi web SPK x Data Mining terintegrasi penuh, *responsive*, mampu menjalankan simulasi perubahan bobot kriteria, dan siap didemonstrasikan untuk pengujian akademik.
