
import streamlit as st
import pandas as pd
import numpy as np
import io

# 1. Konfigurasi Halaman Website
st.set_page_config(page_title="Pencarian Data Usaha & GC", page_icon="🏢", layout="wide")
st.title("⚡ Mesin Pencari Data Usaha & Ground Check")

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
            
    # c. PERBAIKAN: latitude_gc & longitude_gc agar tidak kosong
    for col in ['latitude_gc', 'longitude_gc']:
        if col in df.columns:
            # Ubah jadi string -> Ganti koma dengan titik -> Baru ubah ke angka numerik
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
    with st.spinner('Menarik data dari server Google...'):
        df_asli = load_data(SPREADSHEET_URL)
        
    # 3. UI Mesin Pencari (Sekarang Hanya 1 Kolom)
    st.markdown("### 🔍 Filter Pencarian")
    
    search_query = st.text_input(
        "Cari Nama Usaha atau Nama Usaha GC:", 
        placeholder="Ketik nama usaha di sini..."
    ).strip()

    # 4. Logika Pencarian Cepat (Gabungan OR)
    df_hasil = df_asli.copy()
    
    if search_query:
        # Menyiapkan filter kosong
        mask = pd.Series(False, index=df_hasil.index)
        
        # Cari di kolom nama_usaha
        if 'nama_usaha' in df_hasil.columns:
            mask |= df_hasil['nama_usaha'].astype(str).str.contains(search_query, case=False, na=False)
            
        # Cari di kolom nama_usaha_gc (Kecuali jika user iseng ngetik 'tidak ada perubahan')
        if 'nama_usaha_gc' in df_hasil.columns and search_query.lower() != "tidak ada perubahan":
            mask |= df_hasil['nama_usaha_gc'].astype(str).str.contains(search_query, case=False, na=False)
            
        # Terapkan filter
        df_hasil = df_hasil[mask]

    # 5. Mengatur Kolom yang Ditampilkan
    kolom_tampil = [
        'nama_usaha', 'alamat_usaha', 'nmdesa', 'status_perusahaan',
        'gcs_result', 'gc_username', 'nama_usaha_gc', 'alamat_usaha_gc',
        'latitude_gc', 'longitude_gc'
    ]
    kolom_final = [k for k in kolom_tampil if k in df_hasil.columns]

    # 6. TAMPILAN TABEL & DOWNLOAD
    st.divider()
    col_metrik, col_download = st.columns([3, 1])
    
    with col_metrik:
        if search_query:
            st.success(f"Ditemukan **{len(df_hasil):,}** data yang sesuai.")
        else:
            st.info(f"Menampilkan seluruh data. Total: **{len(df_hasil):,}** baris.")
            
    with col_download:
        excel_data = convert_df_to_excel(df_hasil[kolom_final])
        st.download_button(
            label="📥 Download Hasil (Excel)",
            data=excel_data,
            file_name="hasil_pencarian_gc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Menampilkan tabel
    st.dataframe(df_hasil[kolom_final], use_container_width=True, hide_index=True)

    # 7. TAMPILAN PETA (Sekarang koordinat harusnya terbaca)
    if 'latitude_gc' in df_hasil.columns and 'longitude_gc' in df_hasil.columns:
        df_peta = df_hasil.dropna(subset=['latitude_gc', 'longitude_gc'])
        if not df_peta.empty:
            with st.expander("📍 Lihat Sebaran Titik Lokasi Ground Check", expanded=False):
                df_peta = df_peta.rename(columns={'latitude_gc': 'latitude', 'longitude_gc': 'longitude'})
                st.map(df_peta[['latitude', 'longitude']])

except Exception as e:
    st.error(f"Gagal memuat data. Detail error: {e}")
