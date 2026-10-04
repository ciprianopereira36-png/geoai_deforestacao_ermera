import os
import rasterio
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from mpl_toolkits.axes_grid1 import make_axes_locatable

# 1. Inisialisasi Path Direktori
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")
VECTOR_DIR = os.path.join(BASE_DIR, "vector")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

defor_path = os.path.join(RAW_DIR, "deforestation_alert_ermera.tif")
suco_shp_path = os.path.join(VECTOR_DIR, "Ermera_suco_boundary.shp")
muni_shp_path = os.path.join(VECTOR_DIR, "Ermera_munisipality_boundary.shp")

print("--- MEMULAI ANALISIS DEFORESTASI TINGKAT SUCO ERMERA ---")

# 2. Baca Data Batas Vektor Suco & Munisípiu
gdf_suco = gpd.read_file(suco_shp_path)
gdf_muni = gpd.read_file(muni_shp_path)

# Deteksi kolom nama suco otomatis
suco_col = None
for col in ['SUCO', 'NAME_2', 'ADMIN2', 'NAM_SUCO', 'NAME', 'suco', 'Suco']:
    if col in gdf_suco.columns:
        suco_col = col
        break
if suco_col is None:
    suco_col = gdf_suco.columns[0]
print(f"Kolom identitas Suco yang digunakan: '{suco_col}'")

# 3. Baca Raster Deforestasi & Ekstrak Titik Koordinat
with rasterio.open(defor_path) as src_defor:
    defor_data = src_defor.read(1)
    crs = src_defor.crs
    
    # Hitung luas satu piksel dalam meter persegi
    if crs.is_geographic:
        lat_tengah = (src_defor.bounds.bottom + src_defor.bounds.top) / 2.0
        deg_to_m_y = 111320.0
        deg_to_m_x = 111320.0 * np.cos(np.radians(lat_tengah))
        res_x_m = abs(src_defor.res[0]) * deg_to_m_x
        res_y_m = abs(src_defor.res[1]) * deg_to_m_y
    else:
        res_x_m, res_y_m = abs(src_defor.res[0]), abs(src_defor.res[1])

    pixel_area_ha = (res_x_m * res_y_m) / 10000.0

    # Ambil koordinat titik bernilai 1 (Deforestasi)
    rows, cols = np.where(defor_data == 1)
    xs, ys = rasterio.transform.xy(src_defor.transform, rows, cols)

# Buat GeoDataFrame dari titik-titik deforestasi
points_geom = [Point(x, y) for x, y in zip(xs, ys)]
gdf_points = gpd.GeoDataFrame(geometry=points_geom, crs=crs)

# Samakan sistem proyeksi jika berbeda
if gdf_suco.crs != crs:
    gdf_suco = gdf_suco.to_crs(crs)
if gdf_muni.crs != crs:
    gdf_muni = gdf_muni.to_crs(crs)

# 4. Spatial Join (Hitung Titik Deforestasi di Setiap Poligon Suco)
joined = gpd.sjoin(gdf_points, gdf_suco, how="inner", predicate="within")
counts = joined[suco_col].value_counts().rename('jumlah_titik')

# Gabungkan hasil hitungan ke GeoDataFrame Suco
gdf_suco = gdf_suco.merge(counts, left_on=suco_col, right_index=True, how='left')
gdf_suco['jumlah_titik'] = gdf_suco['jumlah_titik'].fillna(0).astype(int)
gdf_suco['luas_defor_ha'] = (gdf_suco['jumlah_titik'] * pixel_area_ha).round(2)

# Ekspor tabel rekapitulasi ke CSV
csv_out = os.path.join(OUTPUT_DIR, "rekapitulasi_deforestasi_per_suco.csv")
rekap_df = gdf_suco[[suco_col, 'jumlah_titik', 'luas_defor_ha']].sort_values(by='luas_defor_ha', ascending=False)
rekap_df.to_csv(csv_out, index=False)
print(f"Tabel rekapitulasi disimpan di: {csv_out}")

# Tampilkan 5 Suco Terdampak Tertinggi di Terminal
print("\n--- TOP 5 SUCO PALING TERDAMPAK DEFORESTASI ---")
print(rekap_df.head(5).to_string(index=False))

# 5. Visualisasi Kartografi Poligon Suco (Peta Choropleth)
fig, ax = plt.subplots(figsize=(12, 13), dpi=300)

divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="3%", pad=0.15)

# Plot Poligon Suco berdasarkan luasan deforestasi
plot_suco = gdf_suco.plot(
    column='luas_defor_ha',
    cmap='YlOrRd',
    linewidth=0.6,
    edgecolor='gray',
    legend=True,
    cax=cax,
    legend_kwds={'label': 'Luas Deforestasi per Suco (Hektare)'},
    ax=ax
)

# Overlay batas terluar Munisípiu Ermera (Garis hitam tegas)
gdf_muni.boundary.plot(ax=ax, color='black', linewidth=1.5, zorder=3)

# Tambahkan label nama suco pada titik centroid suco
for idx, row in gdf_suco.iterrows():
    if row['geometry'] is not None and not row['geometry'].is_empty:
        c = row['geometry'].centroid
        # Tampilkan nama suco dengan teks kecil jika luas deforestasi > 0
        if row['luas_defor_ha'] > 2.0:
            ax.annotate(
                text=f"{row[suco_col]}\n({row['luas_defor_ha']} ha)",
                xy=(c.x, c.y),
                horizontalalignment='center',
                fontsize=6.5,
                fontweight='bold',
                color='#1A1A1A',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.6, edgecolor='none')
            )

# Format Peta
ax.set_title("Distribusi Area Alert Deforestasi per Suco di Munisípiu Ermera (2025–2026)\n"
             "Analisis Spasial Poligon Suco berbasis GeoAI & Sentinel-2", 
             fontsize=12, fontweight='bold', pad=14)
ax.set_xlabel("Bujur / Longitude (°E)", fontsize=9)
ax.set_ylabel("Lintang / Latitude (°S)", fontsize=9)
ax.grid(True, linestyle=':', alpha=0.5)

# Kotak Rangkuman
total_ha = gdf_suco['luas_defor_ha'].sum()
suco_terdampak = (gdf_suco['luas_defor_ha'] > 0).sum()
info_text = (f"Ringkasan Wilayah:\n"
             f"• Total Deforestasi: {total_ha:.2f} ha\n"
             f"• Suco Terdampak   : {suco_terdampak} Suco")
ax.text(0.03, 0.05, info_text, transform=ax.transAxes, fontsize=9.5,
        bbox=dict(boxstyle='square,pad=0.5', facecolor='white', alpha=0.9, edgecolor='black'))

plt.tight_layout()
peta_suco_path = os.path.join(OUTPUT_DIR, "Peta_Deforestasi_Per_Suco_Ermera.png")
plt.savefig(peta_suco_path, dpi=300)
plt.close()

print(f"\n[SUKSES] Peta analisis poligon suco berhasil disimpan di:\n{peta_suco_path}")