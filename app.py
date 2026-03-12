import streamlit as st
import pandas as pd
import numpy as np

# 1. Konfigurasi Halaman Website
st.set_page_config(page_title="Pencarian Data Usaha & GC", page_icon="🏢", layout="wide")
st.title("⚡ Mesin Pencari Data Usaha & Ground Check")

# --- LINK SPREADSHEET DARI KAMU ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1mAGNiRuyP0XH-apFUsCCWAjVTMAH8S2raFkG0XjYqJ8/edit?usp=sharing"

# 2. Fungsi Penarikan & Transformasi Data
@st.cache_data(ttl=600) # Cache 10 menit untuk kecepatan maksimal
def load_data(sheet_url):
    # Trik: Memotong bagian '/edit...' dan menggantinya dengan export CSV
    # Ini memastikan pembacaan data jauh lebih cepat dari pada membaca format .xlsx
    csv_url = sheet_url.split('/edit')[0] + '/export?format=csv'
        
    # Membaca data ke Pandas
    df = pd.read_csv(csv_url)
    
    # --- PROSES FORMATTING DATA SESUAI PERMINTAAN ---
    
    # a. Mapping gcs_result (1 -> Ditemukan, 3 -> Tutup, dst)
    mapping_gcs = {
        1: "1 - Ditemukan",
        3: "3 - Tutup",
        4: "4 - Ganda",
        99: "99 - Tidak Ditemukan"
    }
    if 'gcs_result' in df.columns:
        df['gcs_result'] = pd.to_numeric(df['gcs_result'], errors='coerce').map(mapping_gcs).fillna(df['gcs_result'])
        
    # b. nama_usaha_gc & alamat_usaha_gc: jika kosong -> "tidak ada perubahan"
    for col in ['nama_usaha_gc', 'alamat_usaha_gc']:
        if col in df.columns:
            # Hapus spasi kosong yang tidak sengaja terketik, ubah jadi NaN, lalu isi teks default
            df[col] = df[col].replace(r'^\s*$', np.nan, regex=True).fillna("tidak ada perubahan")
            
    # c. latitude_gc & longitude_gc: pastikan format angka, jika error -> null (NaN)
    for col in ['latitude_gc', 'longitude_gc']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

try:
    # Memunculkan animasi loading saat pertama kali data ditarik
    with st.spinner('Menarik data dari server Google...'):
        df_asli = load_data(SPREADSHEET_URL)
        
    # 3. UI Mesin Pencari
    st.markdown("### 🔍 Filter Pencarian")
    col1, col2 = st.columns(2)
    
    with col1:
        search_nama = st.text_input("Cari Nama Usaha :", placeholder="Ketik nama usaha di sini...").strip()
    with col2:
        search_gc = st.text_input("Cari Nama Usaha (Hasil GC):", placeholder="Ketik nama usaha GC di sini...").strip()

    # 4. Logika Pencarian Cepat (Bekerja di RAM komputer/server)
    df_hasil = df_asli.copy()
    
    # Pencarian berdasar Nama Usaha
    if search_nama and 'nama_usaha' in df_hasil.columns:
        df_hasil = df_hasil[df_hasil['nama_usaha'].astype(str).str.contains(search_nama, case=False, na=False)]
        
    # Pencarian berdasar Nama Usaha GC
    if search_gc and 'nama_usaha_gc' in df_hasil.columns:
        # Abaikan pencarian jika user iseng mengetik "tidak ada perubahan"
        if search_gc.lower() != "tidak ada perubahan":
            df_hasil = df_hasil[df_hasil['nama_usaha_gc'].astype(str).str.contains(search_gc, case=False, na=False)]

    # 5. Mengatur Kolom yang Ditampilkan
    kolom_tampil = [
        'nama_usaha', 'alamat_usaha', 'nmdesa', 'status_perusahaan',
        'gcs_result', 'gc_username', 'nama_usaha_gc', 'alamat_usaha_gc',
        'latitude_gc', 'longitude_gc'
    ]
    
    # Amankan dari error jika ada kolom yang hilang di spreadsheet
    kolom_final = [k for k in kolom_tampil if k in df_hasil.columns]

    # 6. TAMPILAN TABEL HASIL
    st.divider()
    if search_nama or search_gc:
        st.success(f"Ditemukan **{len(df_hasil):,}** data.")
    else:
        st.info(f"Menampilkan seluruh data. Total: **{len(df_hasil):,}** baris.")
    
    st.dataframe(df_hasil[kolom_final], use_container_width=True, hide_index=True)

    # 7. TAMPILAN PETA TITIK KOORDINAT (GC)
    if 'latitude_gc' in df_hasil.columns and 'longitude_gc' in df_hasil.columns:
        df_peta = df_hasil.dropna(subset=['latitude_gc', 'longitude_gc'])
        
        if not df_peta.empty:
            with st.expander("📍 Lihat Sebaran Titik Lokasi Ground Check", expanded=False):
                df_peta = df_peta.rename(columns={'latitude_gc': 'latitude', 'longitude_gc': 'longitude'})
                st.map(df_peta[['latitude', 'longitude']])

except Exception as e:
    st.error(f"Gagal memuat data. Pastikan link bisa diakses publik. Detail error: {e}")
