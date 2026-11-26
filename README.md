# Pemodelan Aksesibilitas Jaringan Logistik Perikanan Tangkap Pesisir Kabupaten Cilacap

Repositori data spasial, skrip analisis Python, matriks aksesibilitas, dan visualisasi kartografi untuk Tugas Besar / UAS Mata Kuliah **Sistem Informasi Geografi (SIG)** — Program Studi Teknik Informatika, Fakultas Teknik dan Sains, Universitas Muhammadiyah Purwokerto (2026).

- **Dosen Pengampu:** Dr. Dimara Kusuma Hakim, S.T., M.Cs.
- **Tim Penyusun:** Eky Febriansyah, Ibrahim Khafid Yourdani, Dava Riski Kurniawan
- **Kerangka Kerja:** *Operational Spatial Data Mining Framework* (OSDMF — *Flow & Distribution Layer*)
- **Tautan Repositori:** https://github.com/ekyfebriansyah4-ops/uas-sig-aksesibilitas-tpi-cilacap

## Daftar Berkas Luaran

1. `analisis_aksesibilitas_tpi_cilacap.py` — Skrip pemodelan jaringan jalan OpenStreetMap (`osmnx`), perhitungan rute tercepat Dijkstra (`networkx`), simulasi jam sibuk pelelangan pagi ($1{,}45\times$), deteksi koridor *bottleneck*, dan ekspor GeoPackage.
2. `Hasil_Aksesibilitas_TPI_Cilacap.gpkg` — Basis data spasial terpadu berformat GeoPackage (EPSG:4326) berisi 5 *layer* vektor (`jaringan_jalan`, `titik_tpi`, `titik_pasar`, `rute_tercepat`, `koridor_bottleneck`) siap buka di QGIS.
3. `Tabel_Aksesibilitas_TPI_Cilacap.csv` — Matriks kuantitatif jarak tempuh (km), waktu tempuh normal (menit), waktu tempuh jam sibuk (menit), dan kecepatan rata-rata operasional untuk 12 relasi asal-tujuan (3 TPI $\times$ 4 Pasar).
4. `Gambar_1_Workflow_OSDMF.png` — Diagram alur kerja 5 tahap *Operational Spatial Data Mining Framework* (OSDMF) (300 DPI).
5. `Gambar_2_Peta_Aksesibilitas_TPI_Cilacap.png` — Peta tematik rute tercepat distribusi perikanan tangkap dari 3 TPI menuju 4 pasar utama di Kabupaten Cilacap (300 DPI).
6. `Gambar_3_Peta_Bottleneck_dan_Grafik_Cilacap.png` — Peta identifikasi koridor kritis (*bottleneck*) dan grafik perbandingan waktu tempuh normal vs jam sibuk per TPI (300 DPI).
