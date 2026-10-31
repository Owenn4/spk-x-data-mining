import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_logbook_docx():
    doc = docx.Document()
    
    # Page Setup - Margins 1 inch
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    # Styles & Colors
    PRIMARY = RGBColor(30, 41, 59)      # Slate 800
    ACCENT = RGBColor(14, 116, 144)     # Cyan 700
    TEXT_DARK = RGBColor(51, 65, 85)    # Slate 700
    MUTED = RGBColor(100, 116, 139)     # Slate 500
    
    # Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("LOGBOOK PERKEMBANGAN PROYEK")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = PRIMARY

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(14)
    run_sub = p_sub.add_run("Sistem Pendukung Keputusan & Data Mining: Integrasi K-Means Clustering dan TOPSIS untuk Pemilihan Saham BEI (2020–2024)")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(10.5)
    run_sub.font.color.rgb = ACCENT
    run_sub.font.bold = True

    # Info Box / Meta
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(16)
    r_meta = p_meta.add_run("Nama Pengembang: Mitaz (Tazume)  |  Dataset: 30 Emiten Non-Keuangan IDX (Revenue, Net Income, Assets, Equity)  |  Metode: K-Means & TOPSIS")
    r_meta.font.name = "Arial"
    r_meta.font.size = Pt(9)
    r_meta.font.color.rgb = MUTED
    r_meta.font.italic = True

    # Section 1: Detailed Milestones
    milestones = [
        {
            "num": "1",
            "title": "Creating Workspace & Mempelajari Langkah2 Pengerjaan",
            "kendala": "Adanya perbedaan fundamental pada struktur neraca keuangan antara sektor perbankan/finansial dengan sektor riil (non-keuangan). Pada sektor perbankan, simpanan nasabah dicatat sebagai liabilitas, serta rasio utang/leverage operasionalnya wajar mencapai 6x–10x ekuitas. Memasukkan emiten perbankan bersamaan dengan sektor riil akan menyebabkan extreme outlier yang mendistorsi standardisasi varians Z-Score K-Means dan menarik vektor Solusi Ideal Positif (A+) TOPSIS secara tidak realistis.",
            "catatan": "Menetapkan batasan masalah penelitian secara ketat (cohort selection) mengacu pada klasifikasi resmi Bursa Efek Indonesia IDX-IC (Sektor Keuangan / IDXFINANCE): mengeksklusikan perbankan/lembaga keuangan dan memfokuskan analisis hanya pada 30 emiten sektor non-keuangan di BEI periode 2020–2024 agar perbandingan kinerja bersifat setara (apples-to-apples comparison). Menginisialisasi arsitektur proyek modular berbasis FastAPI backend dan High-Density Web Terminal UI.",
            "pencapaian": "Terbentuknya rumusan masalah yang matang, batasan dataset 30 emiten non-keuangan, serta struktur repositori proyek yang siap untuk integrasi data mining dan SPK.",
            "tools": "Python 3.10+, VS Code, Git, FastAPI",
            "hasil": "Workspace Terstruktur & Dokumen Batasan Masalah"
        },
        {
            "num": "2",
            "title": "Mencari Dataset (Data Acquisition)",
            "kendala": "Layanan direct API komersial penyedia data pasar modal historis mengenakan biaya langganan berbayar yang mahal untuk akses laporan keuangan multi-tahun (2020–2024). Pengunduhan manual satu per satu juga sangat tidak efisien dan rentan human error, serta portal BEI (idx.co.id) dilindungi sistem WAF/Cloudflare yang membatasi bot otomatis.",
            "catatan": "Membangun modul automated web scraping berbasis Playwright headless Edge (backend/data/download.py) dan ingestion engine (backend/data/idx_scraper.py) yang berinteraksi langsung dengan endpoint resmi Bursa Efek Indonesia. Sistem mampu menangani session cookies, memverifikasi ketersediaan laporan tahunan teraudit (Audited Annual Statements / TW4), dan mengunduh file .xlsx secara otomatis tanpa biaya API pihak ketiga.",
            "pencapaian": "Berhasil mengumpulkan 150+ file laporan keuangan tahunan teraudit (30 emiten x 5 periode data: 2020–2024) langsung dari sumber data primer BEI ke folder data/raw_reports/.",
            "tools": "Playwright (Headless Edge), Asyncio, idx.co.id API",
            "hasil": "150+ File Excel (.xlsx) Laporan Keuangan Audited IDX"
        },
        {
            "num": "3",
            "title": "Pre-Processing Data & Feature Extraction",
            "kendala": "Format pelaporan baris dan istilah akun akuntansi pada file Excel laporan keuangan IDX memiliki variasi penamaan antar emiten. Selain itu, satuan pelaporan sangat beragam (satuan penuh, ribuan, jutaan, miliaran rupiah, dan USD), serta terdapat potensi anomali nilai negatif saat laba bersih bertransisi dari rugi ke untung (negative base).",
            "catatan": "Mengembangkan parser otomatis berbasis OpenPyXL (backend/data/extract.py & idx_parser.py) yang secara presisi menyasar lembar resmi XBRL/Excel BEI: Sheet [1000000] General Information (deteksi mata uang IDR/USD dan pembulatan), Sheet [1210000] Balance Sheet (Total Aset dan Total Ekuitas), dan Sheet [1321000] Income Statement (Revenue dan Net Income). Melakukan normalisasi ke basis seragam IDR Billion (Miliar Rupiah), menangani kasus negative base secara matematis, serta menghitung rata-rata pertumbuhan tahunan (YoY Growth Rate) 4 variabel: Revenue Growth (C1), Net Income Growth (C2), Asset Growth (C3), dan Equity Growth (C4).",
            "pencapaian": "Dataset final 30 emiten non-keuangan yang bersih dan terverifikasi tanpa missing value (financial_raw.csv, financial_raw.xlsx, kmeans_dataset_yoy.csv), dilengkapi laporan audit mutu data CRISP-DM Tahap 3 (data_quality_report.csv).",
            "tools": "Pandas, NumPy, OpenPyXL, Scikit-Learn",
            "hasil": "Dataset Bersih (Cleaned 30 Emiten x 4 Indikator Pertumbuhan)"
        },
        {
            "num": "4",
            "title": "Implementasi Algoritma Data Mining (K-Means Clustering & PCA)",
            "kendala": "Skala pertumbuhan antar indikator memiliki sebaran varians yang berbeda, sehingga algoritma berbasis jarak Euclidean berisiko didominasi oleh fitur berskala besar jika tidak distandarisasi. Penentuan jumlah klaster (k) secara subjektif juga dapat menurunkan validitas segmentasi.",
            "catatan": "Menerapkan standarisasi data menggunakan StandardScaler (z-score, mu=0, sigma=1). Menguji kombinasi Elbow Method (Inertia/WCSS) dan Silhouette Score Analysis pada backend/mining/clustering.py yang membuktikan secara objektif bahwa k=3 adalah titik optimal (Inersia 30.72 dan skor Silhouette tertinggi s=0.4368). Mengintegrasikan Principal Component Analysis (PCA) 2D (PC1 dan PC2) yang mempertahankan 98.04% total varians terjelaskan.",
            "pencapaian": "Terbentuknya 3 profil klaster emiten yang jelas karakteristiknya: Klaster 0 (Steady Compounder & Value Creator), Klaster 1 (Aggressive High-Growth Expansion), dan Klaster 2 (Mature / Defensive Low-Growth).",
            "tools": "Scikit-Learn (KMeans, StandardScaler, PCA, Silhouette Score)",
            "hasil": "Segmentasi Klaster Saham (k=3), Koordinat PCA 2D, & Grafik Evaluasi"
        },
        {
            "num": "5",
            "title": "Implementasi Sistem Pendukung Keputusan (Metode TOPSIS)",
            "kendala": "Dalam pengambilan keputusan investasi saham, analis memiliki preferensi strategi yang dinamis (misal strategi agresif berfokus pada laba vs strategi defensif berfokus pada ekuitas). Diperlukan mesin pengambil keputusan multi-kriteria yang adil, matematis, dan dapat disimulasikan secara interaktif.",
            "catatan": "Membangun kalkulator TOPSIS matematis (backend/spk/topsis.py): menetapkan ke-4 kriteria pertumbuhan sebagai Benefit Criteria (semakin tinggi laju pertumbuhan omzet, laba bersih, aset, dan ekuitas, semakin baik performa emiten). Menghitung matriks normalisasi vektor (r_ij), matriks normalisasi terbobot (v_ij), menentukan Solusi Ideal Positif (A+) dan Solusi Ideal Negatif (A-), serta menghitung jarak Euclidean (D_i+, D_i-) untuk menghasilkan skor preferensi kedekatan relatif (V_i).",
            "pencapaian": "Dihasilkannya skor preferensi V_i (skala 0 hingga 1.000) dan peringkat rekomendasi bertingkat (Strong Buy / Top Pick, Buy / Accumulate, Reduce / Avoid) secara deterministik.",
            "tools": "NumPy, SciPy, Custom Python TOPSIS Engine",
            "hasil": "Scoreboard & Peringkat Rekomendasi Saham TOPSIS"
        },
        {
            "num": "6",
            "title": "Integrasi Sistem & Pembuatan Web Dashboard Terminal",
            "kendala": "Hasil perhitungan klastering dan perankingan yang berupa matriks angka mentah sulit dipahami oleh pengambil keputusan jika disajikan statis. Selain itu, penggunaan library grafik pihak ketiga yang berat (seperti Chart.js/Plotly CDN) dapat memperlambat rendering antarmuka dan menimbulkan dependensi eksternal.",
            "catatan": "Membangun antarmuka web interaktif berbasis FastAPI dan Native Modern CSS/SVG (frontend/static/index.html): menggunakan visualisasi Native High-Precision SVG untuk grafik PCA Scatter Plot, kurva Elbow, dan diagram Silhouette. Menyediakan Tactile Weight Mixer (slider bobot live), Audit Matrix Modal (Hotkey 'm'), Audited Financial Statements Viewer, opsi hapus emiten, serta tema High-Contrast (Light/Dark Mode, Hotkey 'd') dengan tipografi Plus Jakarta Sans dan JetBrains Mono.",
            "pencapaian": "Sistem aplikasi web SPK x Data Mining terintegrasi penuh, responsive, berkinerja instan (< 2 ms di memori browser), lulus 100% unit test (pytest), dan siap didemonstrasikan untuk pengujian akademik.",
            "tools": "FastAPI, Uvicorn, Native Modern SVG/CSS/JS, Plus Jakarta Sans",
            "hasil": "Web Terminal Interaktif & REST API Endpoints"
        }
    ]

    for m in milestones:
        h = doc.add_heading(level=2)
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(6)
        r_h = h.add_run(f"Milestone {m['num']}: {m['title']}")
        r_h.font.name = "Arial"
        r_h.font.size = Pt(12)
        r_h.font.bold = True
        r_h.font.color.rgb = PRIMARY

        # Table for milestone details
        table = doc.add_table(rows=5, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        col_widths = [Inches(1.8), Inches(4.9)]
        row_data = [
            ("Kendala", m["kendala"]),
            ("Catatan & Solusi", m["catatan"]),
            ("Pencapaian", m["pencapaian"]),
            ("Tools / AI / Tech", m["tools"]),
            ("Hasil Akhir", m["hasil"])
        ]

        for i, (label, val) in enumerate(row_data):
            row = table.rows[i]
            # Left cell (Label)
            c0 = row.cells[0]
            c0.width = col_widths[0]
            set_cell_background(c0, "F1F5F9")
            set_cell_margins(c0, top=80, bottom=80, left=100, right=100)
            p0 = c0.paragraphs[0]
            p0.paragraph_format.space_after = Pt(0)
            p0.paragraph_format.space_before = Pt(0)
            r0 = p0.add_run(label)
            r0.font.name = "Arial"
            r0.font.size = Pt(9.5)
            r0.font.bold = True
            r0.font.color.rgb = PRIMARY

            # Right cell (Value)
            c1 = row.cells[1]
            c1.width = col_widths[1]
            set_cell_background(c1, "FFFFFF")
            set_cell_margins(c1, top=80, bottom=80, left=100, right=100)
            p1 = c1.paragraphs[0]
            p1.paragraph_format.space_after = Pt(0)
            p1.paragraph_format.space_before = Pt(0)
            r1 = p1.add_run(val)
            r1.font.name = "Arial"
            r1.font.size = Pt(9.5)
            r1.font.color.rgb = TEXT_DARK

        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Save to disk
    output_path = "LOGBOOK_SPK_DATA_MINING.docx"
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

if __name__ == "__main__":
    create_logbook_docx()
