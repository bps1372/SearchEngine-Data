import streamlit as st
import pandas as pd
import numpy as np
import io

# 1. Konfigurasi Halaman Website
st.set_page_config(page_title="Portal Data Usaha & GC", page_icon="🏢", layout="wide")

# ==========================================
# INJEKSI CSS UNTUK TAMPILAN PROFESIONAL
# ==========================================
custom_css = """
<style>
    /* 1. Sembunyikan elemen bawaan Streamlit (Header, Footer, Menu) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 2. Mengurangi jarak kosong di bagian atas halaman */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* 3. Membuat Banner Header Custom (Warna Gradient Modern) */
    .custom-header {
        background: linear-gradient(135deg, #0f172a 0%, #3b82f6 100%);
        padding: 30px 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .custom-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        color: white;
    }
    .custom-header p {
        margin: 5px 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* 4. Styling Input Pencarian (Lebih membulat dan elegan) */
    div[data-baseweb="input"] {
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #f8fafc !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    
    /* 5. Styling Tombol Download */
    .stDownloadButton button {
        background-color: #10b981;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stDownloadButton button:hover {
        background-color: #059669;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);
        color: white;
        transform: translateY(-1px);
    }
    
    /* 6. Kotak Info & Success dibuat lebih rapi */
    div[data-testid="stAlert"] {
        border-radius: 8px !important;
        border: none !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Menampilkan Banner Header Custom (Pengganti st.title)
st.markdown("""
<div class="custom-header">
    <h1>🏢 Portal Direktori Usaha & Ground Check</h1>
    <p>Sistem Pencarian Data Terpadu Berbasis Real-Time</p>
</div>
""", unsafe_allow_html=True)

# --- LINK SPREADSHEET ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1mAGNiRuyP0XH-apFUsCCWAjVTMAH8S2raFkG0XjYqJ8/edit?usp=sharing"

# 2. Fungsi Penarikan & Transformasi Data
@st.cache_data(ttl=600)
def load_data(sheet_url):
    csv_url = sheet_url.split('/edit')[0] + '/export?format=csv'
    df = pd.read_csv(csv_url)
    
    # a. Mapping gcs_result
    mapping_gcs = {1: "1 - Ditemukan", 3: "3 - Tutup", 4: "4 - Ganda", 99: "99 - Tidak Ditemukan"}
    if 'gcs_result' in df.columns:
        df['gcs_result'] = pd.to_numeric(df['gcs_result'], errors='coerce').map(mapping_gcs).fillna(df['gcs_result'])
        
    # b. nama_usaha_gc & alamat_usaha_gc
    for col in ['nama_usaha_gc', 'alamat_usaha_gc']:
        if col in df.columns:
            df[col] = df[col].replace(r'^\s*$', np.nan, regex=True).fillna("tidak ada perubahan")
            
    # c. Format latitude & longitude
    for col in ['latitude_gc', 'longitude_gc']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

# Fungsi konversi ke Excel
@st.cache_data
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Hasil Pencarian')
    return output.getvalue()

try:
    with st.spinner('Sinkronisasi data dengan server...'):
        df_asli = load_data(SPREADSHEET_URL)
        
    # 3. UI Mesin Pencari
    st.markdown("### 🔍 Parameter Pencarian")
    
    search_query = st.text_input(
        "Masukkan Nama Usaha (Data Awal / Hasil GC):", 
        placeholder="Ketik kata kunci di sini lalu tekan Enter..."
    ).strip()

    # 4. Logika Pencarian Cepat
    df_hasil = df_asli.copy()
    
    if search_query:
        mask = pd.Series(False, index=df_hasil.index)
        
        if 'nama_usaha' in df_hasil.columns:
            mask |= df_hasil['nama_usaha'].astype(str).str.contains(search_query, case=False, na=False)
            
        if 'nama_usaha_gc' in df_hasil.columns and search_query.lower() != "tidak ada perubahan":
            mask |= df_hasil['nama_usaha_gc'].astype(str).str.contains(search_query, case=False, na=False)
            
        df_hasil = df_hasil[mask]

    # 5. Mengatur Kolom yang Ditampilkan
    kolom_tampil = [
        'nama_usaha', 'alamat_usaha', 'nmdesa', 'status_perusahaan',
        'gcs_result', 'gc_username', 'nama_usaha_gc', 'alamat_usaha_gc',
        'latitude_gc', 'longitude_gc'
    ]
    kolom_final = [k for k in kolom_tampil if k in df_hasil.columns]

    # 6. TAMPILAN TABEL & DOWNLOAD
    st.markdown("<br>", unsafe_allow_html=True) # Tambah sedikit spasi
    col_metrik, col_download = st.columns([3, 1])
    
    with col_metrik:
        if search_query:
            st.success(f"Ditemukan **{len(df_hasil):,}** entri data yang relevan.")
        else:
            st.info(f"Status: Menampilkan keseluruhan database (**{len(df_hasil):,}** entri aktif).")
            
    with col_download:
        excel_data = convert_df_to_excel(df_hasil[kolom_final])
        st.download_button(
            label="📥 Unduh Rekap (Excel)",
            data=excel_data,
            file_name="rekap_data_gc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Menampilkan tabel
    st.dataframe(df_hasil[kolom_final], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Gagal memuat sistem database. Detail teknis: {e}")
