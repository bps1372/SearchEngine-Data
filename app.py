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
    
    # Mapping gcs_result
    mapping_gcs = {1: "1 - Ditemukan", 3: "3 - Tutup", 4: "4 - Ganda", 99: "99 - Tidak Ditemukan"}
    if 'gcs_result' in df.columns:
        df['gcs_result'] = pd.to_numeric(df['gcs_result'], errors='coerce').map(mapping_gcs).fillna(df['gcs_result'])
        
    # nama_usaha_gc & alamat_usaha_gc
    for col in ['nama_usaha_gc', 'alamat_usaha_gc']:
        if col in df.columns:
            df[col] = df[col].replace(r'^\s*$', np.nan, regex=True).fillna("tidak ada perubahan")
            
    # latitude_gc & longitude_gc
    for col in ['latitude_gc', 'longitude_gc']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

# Fungsi untuk mengkonversi DataFrame ke format Excel di dalam memori
@st.cache_data
def convert_df_to_excel(df):
    output = io.BytesIO()
    # Menggunakan engine openpyxl untuk menulis file .xlsx
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Hasil Pencarian')
    return output.getvalue()

try:
    with st.spinner('Menarik data dari server Google...'):
        df_asli = load_data(SPREADSHEET_URL)
        
    # 3. UI Mesin Pencari
    st.markdown("### 🔍 Filter Pencarian")
    
    # -- Tambahan: Pencarian Gabungan (Umum) --
    search_umum = st.text_input(
        "Cari Kata Kunci Umum (Nama Usaha, Alamat, Desa, atau Status):", 
        placeholder="Contoh: Maju Jaya, atau Solok, atau Aktif..."
    ).strip()
    
    # Pencarian Spesifik
    col1, col2 = st.columns(2)
    with col1:
        search_nama = st.text_input("Cari Nama Usaha (Awal):", placeholder="Ketik nama usaha di sini...").strip()
    with col2:
        search_gc = st.text_input("Cari Nama Usaha (Hasil GC):", placeholder="Ketik nama usaha GC di sini...").strip()

    # 4. Logika Pencarian Cepat
    df_hasil = df_asli.copy()
    
    # A. Filter Umum (Mencari di 4 kolom sekaligus)
    if search_umum:
        kolom_umum = ['nama_usaha', 'alamat_usaha', 'nmdesa', 'status_perusahaan']
        # Buat mask (penyaring) kosong
        mask_umum = pd.Series(False, index=df_hasil.index)
        for col in kolom_umum:
            if col in df_hasil.columns:
                # Gabungkan hasil pencarian di tiap kolom menggunakan logika OR (|)
                mask_umum |= df_hasil[col].astype(str).str.contains(search_umum, case=False, na=False)
        # Terapkan penyaring ke dataframe
        df_hasil = df_hasil[mask_umum]
    
    # B. Filter berdasar Nama Usaha Awal
    if search_nama and 'nama_usaha' in df_hasil.columns:
        df_hasil = df_hasil[df_hasil['nama_usaha'].astype(str).str.contains(search_nama, case=False, na=False)]
        
    # C. Filter berdasar Nama Usaha GC
    if search_gc and 'nama_usaha_gc' in df_hasil.columns:
        if search_gc.lower() != "tidak ada perubahan":
            df_hasil = df_hasil[df_hasil['nama_usaha_gc'].astype(str).str.contains(search_gc, case=False, na=False)]

    # 5. Mengatur Kolom yang Ditampilkan
    kolom_tampil = [
        'nama_usaha', 'alamat_usaha', 'nmdesa', 'status_perusahaan',
        'gcs_result', 'gc_username', 'nama_usaha_gc', 'alamat_usaha_gc',
        'latitude_gc', 'longitude_gc'
    ]
    kolom_final = [k for k in kolom_tampil if k in df_hasil.columns]

    # 6. TAMPILAN TABEL HASIL & TOMBOL DOWNLOAD
    st.divider()
    
    # Header baris untuk metrik dan tombol agar sejajar
    col_metrik, col_download = st.columns([3, 1])
    
    with col_metrik:
        if search_umum or search_nama or search_gc:
            st.success(f"Ditemukan **{len(df_hasil):,}** data yang sesuai.")
        else:
            st.info(f"Menampilkan seluruh data. Total: **{len(df_hasil):,}** baris.")
            
    with col_download:
        # Menyiapkan file Excel hanya dari data yang sudah terfilter
        excel_data = convert_df_to_excel(df_hasil[kolom_final])
        st.download_button(
            label="📥 Download Hasil (Excel)",
            data=excel_data,
            file_name="hasil_pencarian_gc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Tampilkan tabel
    st.dataframe(df_hasil[kolom_final], use_container_width=True, hide_index=True)

    # 7. TAMPILAN PETA
    if 'latitude_gc' in df_hasil.columns and 'longitude_gc' in df_hasil.columns:
        df_peta = df_hasil.dropna(subset=['latitude_gc', 'longitude_gc'])
        if not df_peta.empty:
            with st.expander("📍 Lihat Sebaran Titik Lokasi Ground Check", expanded=False):
                df_peta = df_peta.rename(columns={'latitude_gc': 'latitude', 'longitude_gc': 'longitude'})
                st.map(df_peta[['latitude', 'longitude']])

except Exception as e:
    st.error(f"Gagal memuat data. Detail error: {e}")
