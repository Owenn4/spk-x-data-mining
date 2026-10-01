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
    r_meta = p_meta.add_run("Nama Pengembang: Mitaz (Tazume)  |  Dataset: 30 Emiten Non-Keuangan IDX (CR, DER, ROE, PER, PBV, EPS)  |  Metode: K-Means & TOPSIS")
    r_meta.font.name = "Arial"
    r_meta.font.size = Pt(9)
    r_meta.font.color.rgb = MUTED
    r_meta.font.italic = True

    # Section 1: Detailed Milestones
    milestones = [
        {
            "num": "1",
            "title": "Creating Workspace & Mempelajari Langkah2 Pengerjaan",
            "kendala": "Adanya perbedaan fundamental pada struktur neraca keuangan antara sektor perbankan/finansial dengan sektor riil (non-keuangan). Pada sektor perbankan, simpanan nasabah dicatat sebagai liabilitas, sehingga rasio DER (Debt to Equity Ratio) dan CR (Current Ratio) bernilai sangat ekstrem (outlier) yang berisiko merusak normalisasi matriks dan akurasi klastering.",
            "catatan": "Menetapkan batasan masalah penelitian secara ketat (cohort selection): mengeksklusikan sektor perbankan dan memfokuskan analisis hanya pada 30 emiten sektor non-keuangan di BEI periode 2020–2024 agar perbandingan rasio keuangan bersifat setara (apple-to-apple comparison). Menginisialisasi workspace proyek dengan arsitektur modular (FastAPI backend dan Modern Web UI).",
            "pencapaian": "Terbentuknya rumusan masalah yang matang, batasan dataset 30 emiten non-keuangan, serta struktur repositori proyek yang siap untuk integrasi data mining dan SPK.",
            "tools": "Python 3.12, VS Code, Git, Google Sheets",
            "hasil": "Workspace Terstruktur & Dokumen Batasan Masalah"
        },
        {
            "num": "2",
            "title": "Mencari Dataset (Data Acquisition)",
            "kendala": "Layanan direct API komersial penyedia data pasar modal historis (seperti Bloomberg, Refinitiv, atau Financial Modeling Prep) mengenakan biaya langganan berbayar yang mahal untuk akses laporan keuangan multi-tahun (2020–2024). Pengunduhan manual satu per satu juga sangat tidak efisien dan rentan human error.",
            "catatan": "Membangun modul automated web scraping dan ingestion engine mandiri (backend/data/idx_scraper.py) yang berinteraksi langsung dengan portal resmi Bursa Efek Indonesia (idx.co.id). Sistem mengunduh laporan keuangan tahunan teraudit berformat .xlsx secara otomatis dan legal tanpa biaya API pihak ketiga.",
            "pencapaian": "Berhasil mengumpulkan 150 file laporan keuangan tahunan teraudit (30 emiten x 5 tahun: 2020–2024) langsung dari sumber data primer BEI.",
            "tools": "Python Scraper (Requests, BeautifulSoup), idx.co.id",
            "hasil": "150 File Excel (.xlsx) Laporan Keuangan IDX"
        },
        {
            "num": "3",
            "title": "Pre-Processing Data & Feature Extraction",
            "kendala": "Format pelaporan baris dan istilah akun akuntansi pada file Excel laporan keuangan IDX memiliki variasi penamaan antar emiten. Terdapat pula potensi nilai hilang (missing values) atau nilai ekstrem sementara akibat dampak fluktuasi pasar satu tahun tertentu.",
            "catatan": "Mengembangkan parser otomatis (idx_parser.py) dengan pemetaan regex untuk mengekstrak 6 rasio fundamental utama: Current Ratio (CR), Debt to Equity Ratio (DER), Return on Equity (ROE), Price to Earnings Ratio (PER), Price to Book Value (PBV), dan Earning Per Share (EPS). Melakukan agregasi nilai rata-rata 5 tahun (2020–2024) untuk mencerminkan stabilitas kinerja jangka panjang.",
            "pencapaian": "Dataset final 30 emiten non-keuangan dengan 6 fitur rasio fundamental yang bersih, terverifikasi tanpa missing value, dan tersimpan dalam struktur matriks siap olah.",
            "tools": "Pandas, NumPy, OpenPyXL, Regex",
            "hasil": "Dataset Bersih (Cleaned 30 Emiten x 6 Rasio)"
        },
        {
            "num": "4",
            "title": "Implementasi Algoritma Data Mining (K-Means Clustering)",
            "kendala": "Skala satuan antar rasio memiliki rentang yang sangat berbeda (misalnya EPS dalam ratusan/ribuan rupiah, sedangkan PBV dan ROE dalam desimal), sehingga algoritma berbasis jarak Euclidean berisiko didominasi oleh fitur berskala besar. Penentuan jumlah klaster (k) secara subjektif juga dapat menurunkan validitas segmentasi.",
            "catatan": "Menerapkan standarisasi data menggunakan StandardScaler (z-score). Untuk menentukan jumlah klaster k secara objektif dan matematis, diimplementasikan pengujian kombinasi metode Elbow Method (Inertia/WCSS) dan Silhouette Score Analysis.",
            "pencapaian": "Terbentuknya 3 klaster emiten yang jelas karakteristiknya (Cluster 0: Moderate/Stable Growth, Cluster 1: High Undervalued/Growth Potential, Cluster 2: High Leverage/Volatile) dengan validasi nilai Silhouette Score optimal pada k=3.",
            "tools": "Scikit-Learn (KMeans, StandardScaler, Silhouette Score)",
            "hasil": "Segmentasi Klaster Saham (k=3) & Grafik Evaluasi"
        },
        {
            "num": "5",
            "title": "Implementasi Sistem Pendukung Keputusan (Metode TOPSIS)",
            "kendala": "Klasifikasi sifat kriteria yang berlawanan (benefit vs cost): kriteria seperti ROE, EPS, dan CR diharapkan maksimal (benefit), sedangkan PER, PBV, dan DER idealnya lebih rendah atau terkontrol (cost). Pemilihan alternatif terbaik dari klaster unggulan membutuhkan pembobotan yang objektif dan konsisten.",
            "catatan": "Membangun kalkulator TOPSIS matematis (topsis.py): menghitung matriks ternormalisasi (r_ij), matriks ternormalisasi terbobot (y_ij), menentukan Solusi Ideal Positif (A+) dan Solusi Ideal Negatif (A-), serta menghitung jarak Euclidean (D_i+, D_i-) untuk mendapatkan nilai preferensi relatif (V_i).",
            "pencapaian": "Dihasilkannya skor preferensi V_i (skala 0 hingga 1) dan peringkat urutan saham terbaik yang paling mendekati solusi ideal positif dan terjauh dari solusi ideal negatif.",
            "tools": "NumPy, SciPy, Custom Python TOPSIS Engine",
            "hasil": "Scoreboard & Peringkat Rekomendasi Saham TOPSIS"
        },
        {
            "num": "6",
            "title": "Integrasi Sistem & Pembuatan Web Dashboard Studio",
            "kendala": "Hasil perhitungan klastering dan perankingan yang berupa matriks angka mentah sulit dipahami oleh pengambil keputusan atau pengguna awam jika disajikan tanpa visualisasi interaktif.",
            "catatan": "Membangun antarmuka web interaktif dengan FastAPI dan Modern Web UI (Chart.js) yang menyajikan visualisasi grafik Scatter Plot Clustering, kurva evaluasi Elbow/Silhouette, tabel matriks normalisasi TOPSIS, serta scoreboard peringkat rekomendasi saham secara real-time.",
            "pencapaian": "Sistem aplikasi web SPK x Data Mining terintegrasi penuh, responsive, mampu menjalankan simulasi perubahan bobot kriteria, dan siap didemonstrasikan untuk pengujian akademik.",
            "tools": "FastAPI, Uvicorn, Chart.js, Vanilla CSS/JS Modern",
            "hasil": "Web Dashboard Interaktif & API Endpoint"
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
