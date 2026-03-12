import streamlit as st
import pandas as pd
import numpy as np

# 1. Konfigurasi Halaman Website
st.set_page_config(page_title="Pencarian Data Usaha & GC", page_icon="🏢", layout="wide")
st.title("⚡ Mesin Pencari Data Usaha & Ground Check")

# --- MASUKKAN LINK SPREADSHEET DI SINI ---
# Pastikan spreadsheet sudah di-set "Anyone with the link" (Viewer)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1mAGNiRuyP0XH-apFUsCCWAjVTMAH8S2raFkG0XjYqJ8/edit?usp=sharing"

# 2. Fungsi Penarikan & Transformasi Data
@st.cache_data(ttl=600) # Cache 10 menit agar tetap cepat
def load_data(sheet_url):
    # Menggunakan trik export CSV agar proses tarik data dari Google Sheets super cepat
    if "/edit" in sheet_url:
        csv_url = sheet_url.replace('/edit', '/export?format=csv')
        csv_url = csv_url.split('&')[0]
    else:
        csv_url = sheet_url
        
    # Membaca data
    df = pd.read_csv(csv_url)
    
    # --- PROSES FORMATTING DATA SESUAI PERMINTAAN ---
    
    # a. Mapping gcs_result menjadi teks yang mudah dibaca
    mapping_gcs = {
        1: "1 - Ditemukan",
        3: "3 - Tutup",
        4: "4 - Ganda",
        99: "99 - Tidak Ditemukan"
    }
    if 'gcs_result' in df.columns:
        # Ubah ke numerik lalu map ke dictionary di atas
        df['gcs_result'] = pd.to_numeric(df['gcs_result'], errors='coerce').map(mapping_gcs).fillna(df['gcs_result'])
        
    # b. Jika nama_usaha_gc atau alamat_usaha_gc kosong, isi dengan "tidak ada perubahan"
    # Menggunakan regex untuk mendeteksi sel yang benar-benar kosong atau hanya berisi spasi
    for col in ['nama_usaha_gc', 'alamat_usaha_gc']:
        if col in df.columns:
            df[col] = df[col].replace(r'^\s*$', np.nan, regex=True).fillna("tidak ada perubahan")
            
    # c. Pastikan latitude_gc dan longitude_gc menjadi null (NaN) jika kosong
    for col in ['latitude_gc', 'longitude_gc']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

try:
    with st.spinner('Menarik dan memproses data dari server...'):
        df_asli = load_data(SPREADSHEET_URL)
        
    # 3. UI Mesin Pencari (Berdasarkan 2 Parameter)
    st.markdown("### 🔍 Filter Pencarian")
    col1, col2 = st.columns(2)
    
    with col1:
        search_nama = st.text_input("Cari Nama Usaha (Data Awal):", placeholder="Ketik di sini...").strip()
    with col2:
        search_gc = st.text_input("Cari Nama Usaha GC:", placeholder="Ketik di sini...").strip()

    # 4. Logika Pencarian Cepat
    df_hasil = df_asli.copy()
    
    # Filter by nama_usaha
    if search_nama and 'nama_usaha' in df_hasil.columns:
        df_hasil = df_hasil[df_hasil['nama_usaha'].astype(str).str.contains(search_nama, case=False, na=False)]
        
    # Filter by nama_usaha_gc
    if search_gc and 'nama_usaha_gc' in df_hasil.columns:
        df_hasil = df_hasil[df_hasil['nama_usaha_gc'].astype(str).str.contains(search_gc, case=False, na=False)]

    # 5. Mengatur Kolom yang Ditampilkan
    kolom_tampil = [
        'nama_usaha', 'alamat_usaha', 'nmdesa', 'status_perusahaan',
        'gcs_result', 'gc_username', 'nama_usaha_gc', 'alamat_usaha_gc',
        'latitude_gc', 'longitude_gc'
    ]
    
    # Memastikan script tidak error jika ada kolom yang salah ketik di spreadsheet
    kolom_final = [k for k in kolom_tampil if k in df_hasil.columns]

    # 6. Menampilkan Hasil
    st.divider()
    if search_nama or search_gc:
        st.success(f"Ditemukan **{len(df_hasil):,}** data yang cocok.")
    else:
        st.info(f"Menampilkan seluruh data. Total: **{len(df_hasil):,}** baris.")
    
    # Tampilkan DataFrame (tabel website)
    st.dataframe(df_hasil[kolom_final], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Gagal memuat data. Pastikan link Spreadsheet benar dan nama kolom (header) sama persis. Detail: {e}")
