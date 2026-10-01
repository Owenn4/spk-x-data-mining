import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def create_presentation_docx():
    doc = docx.Document()

    # 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Color Palette
    COLOR_NAVY = RGBColor(26, 54, 93)      # #1A365D Primary
    COLOR_BLUE = RGBColor(43, 108, 176)    # #2B6CB0 Secondary Accent
    COLOR_DARK = RGBColor(45, 55, 72)      # #2D3748 Body text
    COLOR_MUTED = RGBColor(113, 128, 150)  # #718096 Captions/hints
    COLOR_BORDER = 'CBD5E0'
    COLOR_BG_BOX = 'F7FAFC'

    def set_cell_background(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(
            f'<w:tcMar {nsdecls("w")}>'
            f'<w:top w:w="{top}" w:type="dxa"/>'
            f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
            f'<w:left w:w="{left}" w:type="dxa"/>'
            f'<w:right w:w="{right}" w:type="dxa"/>'
            f'</w:tcMar>'
        )
        tcPr.append(tcMar)

    def add_title(title_text, subtitle_text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(0)
        run = p.add_run(title_text)
        run.font.name = 'Calibri'
        run.font.size = Pt(20)
        run.font.bold = True
        run.font.color.rgb = COLOR_NAVY
        
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_after = Pt(16)
        run2 = p2.add_run(subtitle_text)
        run2.font.name = 'Calibri'
        run2.font.size = Pt(11)
        run2.font.italic = True
        run2.font.color.rgb = COLOR_MUTED

    def add_deck_header(deck_num, title_text, subtitle_text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(20)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        
        run_badge = p.add_run(f'PPT {deck_num} | ')
        run_badge.font.name = 'Calibri'
        run_badge.font.size = Pt(14)
        run_badge.font.bold = True
        run_badge.font.color.rgb = COLOR_BLUE
        
        run = p.add_run(title_text)
        run.font.name = 'Calibri'
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = COLOR_NAVY

        p_sub = doc.add_paragraph()
        p_sub.paragraph_format.space_before = Pt(0)
        p_sub.paragraph_format.space_after = Pt(10)
        p_sub.paragraph_format.keep_with_next = True
        r_sub = p_sub.add_run(subtitle_text)
        r_sub.font.name = 'Calibri'
        r_sub.font.size = Pt(10)
        r_sub.font.italic = True
        r_sub.font.color.rgb = COLOR_MUTED

    def add_slide_box(slide_num, slide_title, what_to_say, key_concept):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        
        cell = table.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, COLOR_BG_BOX)
        set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
        
        # Left Accent Border
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'<w:top w:val="none"/>'
            f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{COLOR_BORDER}"/>'
            f'<w:bottom w:val="none"/>'
            f'<w:right w:val="none"/>'
            f'</w:tcBorders>'
        )
        tcPr.append(borders)
        
        # Header inside box
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        run_tag = p.add_run(f'Slide {slide_num}: {slide_title}\n')
        run_tag.font.name = 'Calibri'
        run_tag.font.size = Pt(11.5)
        run_tag.font.bold = True
        run_tag.font.color.rgb = COLOR_NAVY
        
        # What to say
        run_say_lbl = p.add_run('Cara Menyampaikan:\n')
        run_say_lbl.font.name = 'Calibri'
        run_say_lbl.font.size = Pt(10)
        run_say_lbl.font.bold = True
        run_say_lbl.font.color.rgb = COLOR_BLUE
        
        run_say = p.add_run(f'"{what_to_say}"\n\n')
        run_say.font.name = 'Calibri'
        run_say.font.size = Pt(10)
        run_say.font.color.rgb = COLOR_DARK
        
        # Key concept / Mindset
        run_key_lbl = p.add_run('Inti Pemahaman (Mindset): ')
        run_key_lbl.font.name = 'Calibri'
        run_key_lbl.font.size = Pt(9.5)
        run_key_lbl.font.bold = True
        run_key_lbl.font.color.rgb = COLOR_MUTED
        
        run_key = p.add_run(key_concept)
        run_key.font.name = 'Calibri'
        run_key.font.size = Pt(9.5)
        run_key.font.italic = True
        run_key.font.color.rgb = COLOR_DARK
        
        # Add spacing after table
        p_sp = doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(0)
        p_sp.paragraph_format.space_after = Pt(4)

    # DOCUMENT HEADER
    add_title(
        'Panduan & Naskah Presentasi SPK Kelompok 11',
        'Penjelasan Slide per Slide: Business Understanding, Data Understanding, & Data Preparation'
    )

    p_intro = doc.add_paragraph()
    p_intro.paragraph_format.space_after = Pt(12)
    r_in = p_intro.add_run(
        'Catatan Pembawaan: Naskah ini disusun sesuai urutan slide pada 3 presentasi utama (Business Understanding, '
        'Data Understanding, dan Week 3 - Data Preparation). Kamu tidak perlu menghafal kata demi kata secara kaku—cukup '
        'pahami alur dan baca poin "Cara Menyampaikan" dengan bahasa santai namun percaya diri. Setiap kotak juga dilengkapi '
        'dengan "Inti Pemahaman" agar kamu menguasai alasan logis di baliknya saat dosen bertanya.'
    )
    r_in.font.name = 'Calibri'
    r_in.font.size = Pt(10)
    r_in.font.color.rgb = COLOR_DARK

    # =========================================================================
    # PPT 1: BUSINESS UNDERSTANDING
    # =========================================================================
    add_deck_header('1', 'Business Understanding', 'Fokus: Latar belakang masalah investasi, tujuan bisnis, dan integrasi K-Means + TOPSIS.')

    add_slide_box(
        '1 & 2',
        'Judul & Anggota Kelompok',
        'Selamat pagi/siang Bapak/Ibu dosen dan rekan-rekan semua. Kami dari Kelompok 11 akan mempresentasikan progres proyek perancangan Sistem Pendukung Keputusan (SPK) berbasis Data Mining untuk pemilihan saham fundamental di Bursa Efek Indonesia.',
        'Sapa dosen dan ruangan secara profesional, buka dengan percaya diri.'
    )

    add_slide_box(
        '3',
        'Latar Belakang Masalah',
        'Di Bursa Efek Indonesia, terdapat lebih dari 900 perusahaan yang melantai. Bagi para investor, menyaring saham mana yang fundamentalnya benar-benar sehat itu memakan waktu yang sangat lama jika harus membaca laporan keuangan satu per satu secara manual. Akibatnya, banyak keputusan investasi yang hanya didasarkan pada spekulasi atau tren sesaat tanpa didukung analisis data yang kuat. Masalah efisiensi dan objektivitas inilah yang ingin kami selesaikan.',
        'Ratusan emiten membuat analisis manual melelahkan, rentan bias subjektif, dan sering terjebak tren semata.'
    )

    add_slide_box(
        '4',
        'Business Objective',
        'Tujuan bisnis dari sistem ini adalah membangun sebuah platform SPK otomatis yang mampu membantu investor menyaring, mengelompokkan, dan memilih saham-saham terbaik secara objektif. Sistem ini dirancang untuk mempercepat waktu analisis, meminimalkan risiko keputusan emosional, dan memberikan rekomendasi berbasis kinerja historis 5 tahun yang dapat dipertanggungjawabkan.',
        'Membantu investor mengambil keputusan berbasis data secara cepat, terstruktur, dan minim risiko.'
    )

    add_slide_box(
        '5',
        'Data Mining Objective (K-Means & TOPSIS)',
        'Untuk mencapai tujuan tersebut, kami menggabungkan dua metode: Pertama, K-Means Clustering untuk segmentasi awal, yaitu memilah puluhan saham ke dalam beberapa klaster kinerja (seperti saham bertumbuh konsisten, stabil, atau berkinerja rendah). Kedua, kami menerapkan metode SPK TOPSIS khusus pada klaster saham terbaik untuk meranking emiten yang paling optimal mendekati solusi ideal positif.',
        'K-Means menyaring klaster saham unggulan, lalu TOPSIS mengurutkan ranking 1, 2, 3 dari klaster tersebut.'
    )

    add_slide_box(
        '6 & 7',
        'Kriteria Sukses & Penutup Bagian',
        'Kriteria sukses proyek ini diukur dari dua aspek: Secara teknis, model K-Means harus menghasilkan pemisahan klaster yang optimal (divalidasi dengan Elbow Method dan Silhouette Score) dan TOPSIS menghasilkan urutan rekomendasi yang stabil. Secara bisnis, hasil rekomendasi harus logis dan merefleksikan emiten dengan fundamental yang terbukti tangguh di pasar modal.',
        'Sukses teknis (klaster & perankingan teruji) + sukses bisnis (membantu keputusan investasi nyata).'
    )

    # =========================================================================
    # PPT 2: DATA UNDERSTANDING
    # =========================================================================
    add_deck_header('2', 'Data Understanding', 'Fokus: Pengumpulan 30 saham non-keuangan, seleksi 4 pilar variabel, dan audit kualitas data.')

    add_slide_box(
        '1 & 2',
        'Mengumpulkan Data Awal (Objek, Sektor, Periode, Sumber)',
        'Pada tahap Data Understanding, kami mengumpulkan data sekunder dari 30 saham emiten non-keuangan di BEI selama periode 5 tahun (2020 hingga 2024). Kenapa kita fokus pada sektor non-keuangan? Karena sektor perbankan memiliki struktur neraca yang sangat berbeda, di mana dana nasabah dicatat sebagai liabilitas/utang sehingga tidak apple-to-apple jika disandingkan dengan industri riil. Periode 5 tahun dipilih untuk melihat ketahanan kinerja perusahaan dari masa pandemi 2020 hingga masa normalisasi di 2024.',
        '30 emiten non-keuangan (perbandingan adil), rentang 5 tahun 2020-2024 (siklus krisis hingga normalisasi), data resmi BEI.'
    )

    add_slide_box(
        '3',
        'Daftar 30 Saham Non-Keuangan',
        'Berikut adalah 30 emiten terpilih yang merepresentasikan berbagai sektor industri riil di BEI—mulai dari Industrials (ASII, UNTR), Infrastruktur & Telekomunikasi (TLKM, TOWR, EXCL), Energi (ADRO, PTBA, ITMG), Basic Materials (ANTM, INCO, SMGR), Konsumsi (INDF, ICBP, UNVR, AMRT), hingga Kesehatan (KLBF, MIKA). Seluruh emiten ini memiliki likuiditas dan transparansi publik yang tinggi.',
        'Diversifikasi lintas sektor riil dengan rekam jejak laporan keuangan publik yang transparan dan lengkap.'
    )

    add_slide_box(
        '4 & 5',
        'Mendeskripsikan Data Mentah ke Format Tabular',
        'Dari laporan keuangan mentah yang memuat ratusan pos akun akuntansi, kami menyederhanakan dan mengekstrak 4 variabel finansial utama per tahun: Revenue (Pendapatan), Net Income (Laba Bersih), Total Assets (Aset), dan Total Equity (Ekuitas). Data ini kami susun ke dalam format tabular tahunan terstruktur dari tahun 2020 sampai 2024.',
        'Menyaring 4 pilar inti: Revenue (pemasukan), Net Income (profit), Assets (kekayaan), Equity (modal bersih).'
    )

    add_slide_box(
        '6',
        'Eksplorasi Data (EDA)',
        'Melalui Exploratory Data Analysis, kami melihat sebaran dan pola perubahan kinerja tiap perusahaan. Di sini kita bisa mengamati dinamika industri—misalnya lonjakan kinerja sektor energi pada tahun 2022 akibat komoditas boom, atau stabilitas sektor konsumsi yang defensif pasca pandemi.',
        'Memahami variasi data, pola pertumbuhan, dan anomali tren sebelum melangkah ke pemodelan.'
    )

    add_slide_box(
        '7 & 8',
        'Memverifikasi Kualitas Data',
        'Kami juga melakukan verifikasi kualitas data secara ketat: Memastikan tidak ada data yang kosong (zero missing values) untuk 30 saham selama 5 tahun, memeriksa konsistensi satuan pelaporan (karena beberapa laporan menyajikan dalam ribuan, jutaan, atau Rupiah penuh), serta melakukan cross-check langsung dengan dokumen audit resmi BEI.',
        'Memastikan data lengkap, satuan seragam, dan angka akurat terverifikasi dari sumber primer.'
    )

    # =========================================================================
    # PPT 3: WEEK 3 - DATA PREPARATION
    # =========================================================================
    add_deck_header('3', 'Week 3 - Data Preparation (Data Preprocessing)', 'Fokus Utama Hari Ini: Seleksi Atribut, Pembersihan, Rekayasa CAGR 5 Tahun, dan Standardisasi Fitur.')

    add_slide_box(
        '1 & 2',
        'Seleksi Data (Data Selection)',
        'Memasuki tahap Data Preparation yang menjadi fokus utama hari ini, langkah pertama adalah Seleksi Data. Kami memusatkan ruang lingkup data pada 30 emiten non-keuangan dengan 4 variabel kunci yang mencerminkan pertumbuhan operasional murni (Revenue, Net Income, Assets, Equity) dari laporan audit tahunan 2020 hingga 2024.',
        'Menjaga fokus hanya pada data yang relevan secara fundamental dan membuang variabel yang menjadi noise.'
    )

    add_slide_box(
        '3',
        'Pembersihan Data (Data Cleaning)',
        'Langkah kedua adalah Pembersihan Data. Di tahap ini kami menyelaraskan periode tutup buku tahunan (seluruhnya per 31 Desember) dan mengonversi semua nilai moneter ke dalam skala satuan seragam (Rupiah penuh). Dengan demikian, tidak ada kesalahan perbandingan akibat perbedaan format penyajian akuntansi.',
        'Menyamakan periode pelaporan tahunan dan menyeragamkan satuan nominal agar tidak ada bias skala pembacaan.'
    )

    add_slide_box(
        '4',
        'Konstruksi Data (Feature Engineering: CAGR 5 Tahun)',
        'Langkah ketiga adalah Konstruksi Data, dan ini merupakan bagian paling fundamental. Jika kita hanya membandingkan angka nominal mentah, perusahaan besar akan selalu mendominasi perusahaan menengah meskipun pertumbuhannya lambat. Oleh karena itu, kami merekayasa data mentah menjadi laju pertumbuhan tahunan majemuk (Compound Annual Growth Rate / CAGR) dari 2020 hingga 2024 untuk ke-4 variabel. Dengan CAGR, kita menilai kecepatan dan kualitas pertumbuhan perusahaan secara adil, bukan hanya melihat besar kecilnya nominal awal.',
        'Nominal mentah diubah menjadi laju pertumbuhan (%) 5 tahun (CAGR), sehingga evaluasi performa bisnis 100% fair.'
    )

    add_slide_box(
        '5 & 6',
        'Integrasi Data & Format Standardisasi (K-Means Ready)',
        'Langkah terakhir adalah Integrasi dan Pemformatan. Seluruh matriks pertumbuhan 30 saham digabungkan ke dalam satu dataset terstruktur. Sebelum masuk ke K-Means, data melalui tahap Standardisasi Fitur (StandardScaler) agar semua variabel memiliki rata-rata 0 dan variansi 1. Ini sangat penting agar perhitungan jarak Euclidean pada algoritma K-Means tidak timpang atau terdistorsi oleh variabel dengan rentang nilai yang lebih lebar. Dataset terstandarisasi inilah yang kini siap digunakan untuk tahap Modeling.',
        'Menggabungkan matriks pertumbuhan + Standardisasi Z-Score agar jarak algoritma K-Means akurat tanpa bias rentang variabel.'
    )

    # =========================================================================
    # FAQ / DOSEN CHEAT SHEET
    # =========================================================================
    p_faq_title = doc.add_paragraph()
    p_faq_title.paragraph_format.space_before = Pt(20)
    p_faq_title.paragraph_format.space_after = Pt(4)
    p_faq_title.paragraph_format.keep_with_next = True
    r_fq = p_faq_title.add_run('Ringkasan Cepat: Jawaban Tangkas Jika Dosen Bertanya')
    r_fq.font.name = 'Calibri'
    r_fq.font.size = Pt(13)
    r_fq.font.bold = True
    r_fq.font.color.rgb = COLOR_NAVY

    faq_items = [
        (
            '1. Mengapa memisahkan sektor perbankan/keuangan?',
            'Karena bisnis bank adalah intermediasi keuangan di mana dana tabungan nasabah dicatat sebagai kewajiban (utang/liabilitas), bukan modal murni operasional seperti manufaktur. Jika digabung, rasio keuangan bank akan menjadi anomali (outlier) yang mengacaukan klaster K-Means.'
        ),
        (
            '2. Mengapa memilih rentang waktu 5 tahun (2020–2024)?',
            'Rentang 5 tahun mencakup siklus ekonomi yang utuh—menguji bagaimana perusahaan bertahan menghadapi krisis pandemi 2020 hingga bagaimana mereka melakukan pemulihan dan ekspansi di 2024.'
        ),
        (
            '3. Mengapa menggunakan CAGR (Pertumbuhan), bukan nilai nominal rupiah?',
            'Agar tercipta perbandingan yang adil (fair comparison). Perusahaan raksasa seperti Astra tentu punya aset ratusan triliun, tapi belum tentu tumbuh secepat perusahaan menengah. CAGR mengukur laju kesehatan pertumbuhan, bukan sekadar ukuran modal.'
        ),
        (
            '4. Mengapa perlu Standardisasi (StandardScaler) sebelum K-Means?',
            'Karena K-Means menggunakan perhitungan jarak Euclidean. Jika tidak distandarisasi ke mean 0 dan variansi 1, atribut dengan angka absolut lebih besar akan mendominasi dan mengaburkan pengaruh variabel lainnya.'
        )
    ]

    for q, a in faq_items:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(6)
        p_q.paragraph_format.space_after = Pt(2)
        p_q.paragraph_format.keep_with_next = True
        r_q = p_q.add_run(q)
        r_q.font.name = 'Calibri'
        r_q.font.size = Pt(10.5)
        r_q.font.bold = True
        r_q.font.color.rgb = COLOR_BLUE

        p_a = doc.add_paragraph()
        p_a.paragraph_format.space_before = Pt(0)
        p_a.paragraph_format.space_after = Pt(6)
        r_a = p_a.add_run(a)
        r_a.font.name = 'Calibri'
        r_a.font.size = Pt(10)
        r_a.font.color.rgb = COLOR_DARK

    doc.save('/home/tazume/projects/SPK X Data Mining/Naskah_Presentasi_SPK.docx')
    print('Successfully generated Naskah_Presentasi_SPK.docx')

if __name__ == '__main__':
    create_presentation_docx()
