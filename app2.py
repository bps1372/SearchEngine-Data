import streamlit as st
import pandas as pd
import numpy as np
import io

# 1. Konfigurasi Halaman Website
st.set_page_config(page_title="Portal Data Usaha & GC", page_icon="🏢", layout="wide")

# ==========================================
# INJEKSI CSS TEMA BIRU TERANG & BERSIH
# ==========================================
custom_css = """
<style>
    /* 1. Sembunyikan elemen bawaan Streamlit (Header, Footer, Menu) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 2. Memaksa Background Aplikasi menjadi Biru Sangat Muda (Ice Blue) */
    .stApp {
        background-color: #F0F6FF !important;
    }

    /* 3. Memaksa warna teks utama menjadi biru gelap agar kontras */
    h1, h2, h3, h4, h5, h6, p, label {
        color: #0F172A !important;
    }
    
    /* 4. Membuat Banner Header Custom (Biru Elegan) */
    .custom-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 30px 20px;
        border-radius: 12px;
        color: white !important;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.2);
    }
    .custom-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        color: white !important;
    }
    .custom-header p {
        margin: 5px 0 0 0;
        font-size: 1.1rem;
        color: #DBEAFE !important;
    }
    
    /* 5. Styling Input Box (Terang dan Border Biru Muda) */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #BFDBFE !important;
        border-radius: 8px !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    .stTextInput input:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 1px #2563EB !important;
    }
    
    /* 6. Styling Tombol Download (Biru Terang ke Biru Gelap) */
    .stDownloadButton button {
        background-color: #2563EB !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stDownloadButton button:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 4px 8px rgba(37, 99, 235, 0.3) !important;
        transform: translateY(-1px);
    }
    
    /* 7. Kotak Info (Warna Biru Lembut) */
    div[data-testid="stAlert"] {
        background-color: #DBEAFE !important;
        color: #1E3A8A !important;
        border-radius: 8px !important;
        border: 1px solid #BFDBFE !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Menampilkan Banner Header Custom
st.markdown("""
<div class="custom-header">
    <h1>🏢 Portal Direktori Usaha & Ground Check SBR Lanjutan</h1>
    <h2>BPS Kota Solok</h2>
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
    st.markdown("### 🔍 Search")
    
    search_query = st.text_input(
        "Masukkan Nama Usaha (Data Awal / Hasil GC):", 
        placeholder="Ketik kata kunci di sini lalu tekan Enter..."
    ).strip()

    # 4. Logika Pencarian
    df_hasil = df_asli.copy()
    
    if search_query:
        mask = pd.Series(False, index=df_hasil.index)
        
        if 'nama_usaha' in df_hasil.columns:
            mask |= df_hasil['nama_usaha'].astype(str).str.contains(search_query, case=False, na=False)
            
        if 'nama_usaha_gc' in df_hasil.columns and search_query.lower() != "tidak ada perubahan":
            mask |= df_hasil['nama_usaha_gc'].astype(str).str.contains(search_query, case=False, na=False)
            
        df_hasil = df_hasil[mask]

    # 5. Kolom yang Ditampilkan
    kolom_tampil = [
        'nama_usaha', 'alamat_usaha', 'nmdesa', 'status_perusahaan',
        'gcs_result', 'gc_username', 'nama_usaha_gc', 'alamat_usaha_gc',
        'latitude_gc', 'longitude_gc'
    ]
    kolom_final = [k for k in kolom_tampil if k in df_hasil.columns]

    # 6. TAMPILAN TABEL & METRIK
    st.markdown("<br>", unsafe_allow_html=True)
    col_metrik, col_download = st.columns([3, 1])
    
    with col_metrik:
        if search_query:
            st.success(f"Ditemukan **{len(df_hasil):,}** entri data yang relevan.")
        else:
            st.info(f"Status: Menampilkan keseluruhan database (**{len(df_hasil):,}** entri aktif).")
            
    with col_download:
        excel_data = convert_df_to_excel(df_hasil[kolom_final])
        st.download_button(
            label="📥 Download (Excel)",
            data=excel_data,
            file_name="rekap_data_gc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # TABEL DITAMPILKAN DI SINI (Akan selalu muncul baik saat ada pencarian atau tidak)
    st.dataframe(df_hasil[kolom_final], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Gagal memuat sistem database. Detail teknis: {e}")
