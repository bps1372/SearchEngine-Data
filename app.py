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
@st.cache_data(ttl=600) # Cache 10 menit
def load_data(sheet_url):
    if "/edit" in sheet_url:
        csv_url = sheet_url.replace('/edit', '/export?format=csv')
        csv_url = csv_url.split('&')[0]
    else:
        csv_url = sheet_url
        
    df = pd.read_csv(csv_url)
    
    # --- PROSES FORMATTING DATA ---
    
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
            # Ubah spasi kosong menjadi NaN, lalu isi semua NaN dengan teks default
            df[col] = df[col].replace(r'^\s*$', np.nan, regex=True).fillna("tidak ada perubahan")
            
    # c. latitude_gc & longitude_gc: jika kosong/error -> null (NaN)
    for col in ['latitude_gc', 'longitude_gc']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

try:
    with st.spinner('Menarik dan memproses data...'):
        df_asli = load_data(SPREADSHEET_URL)
        
    # 3. UI Mesin Pencari
    st.markdown("### 🔍 Filter Pencarian")
    col1, col2 = st.columns(2)
    
    with col1:
        search_nama = st.text_input("Cari Nama Usaha (Awal):", placeholder="Ketik nama usaha di sini...").strip()
    with col2:
        search_gc = st.text_input("Cari Nama Usaha (Hasil GC):", placeholder="Ketik nama usaha GC di sini...").strip()

    # 4. Logika Pencarian Cepat
    df_hasil = df_asli.copy()
    
    if search_nama and 'nama_usaha' in df_hasil.columns:
        df_hasil = df_hasil[df_hasil['nama_usaha'].astype(str).str.contains(search_nama, case=False, na=False)]
        
    if search_gc and 'nama_usaha_gc' in df_hasil.columns:
        # Pengecualian: jangan cari teks "tidak ada perubahan" jika inputnya kosong
        if search_gc.lower() != "tidak ada perubahan":
            df_hasil = df_hasil[df_hasil['nama_usaha_gc'].astype(str).str.contains(search_gc, case=False, na=False)]

    # 5. Mengatur Kolom yang Ditampilkan Sesuai Permintaan
    kolom_tampil = [
        'nama_usaha', 'alamat_usaha', 'nmdesa', 'status_perusahaan',
        'gcs_result', 'gc_username', 'nama_usaha_gc', 'alamat_usaha_gc',
        'latitude_gc', 'longitude_gc'
    ]
    
    # Hanya ambil kolom yang benar-benar ada di data untuk mencegah error
    kolom_final = [k for k in kolom_tampil if k in df_hasil.columns]

    # 6. TAMPILAN TABEL HASIL
    st.divider()
    if search_nama or search_gc:
        st.success(f"Ditemukan **{len(df_hasil):,}** data.")
    else:
        st.info(f"Menampilkan seluruh data. Total: **{len(df_hasil):,}** baris.")
    
    st.dataframe(df_hasil[kolom_final], use_container_width=True, hide_index=True)

    # 7. TAMPILAN PETA (Otomatis memetakan titik yang memiliki latitude & longitude valid)
    if 'latitude_gc' in df_hasil.columns and 'longitude_gc' in df_hasil.columns:
        # Filter data yang koordinatnya tidak null
        df_peta = df_hasil.dropna(subset=['latitude_gc', 'longitude_gc'])
        
        if not df_peta.empty:
            with st.expander("📍 Lihat Sebaran Titik Lokasi (Ground Check)", expanded=False):
                # Rename kolom agar dikenali oleh st.map()
                df_peta = df_peta.rename(columns={'latitude_gc': 'latitude', 'longitude_gc': 'longitude'})
                st.map(df_peta[['latitude', 'longitude']])
        else:
            with st.expander("📍 Lihat Sebaran Titik Lokasi (Ground Check)", expanded=False):
                st.write("Tidak ada data koordinat yang valid untuk ditampilkan di peta pada pencarian ini.")

except Exception as e:
    st.error(f"Gagal memuat data. Pastikan link Spreadsheet sudah benar. Detail error: {e}")
