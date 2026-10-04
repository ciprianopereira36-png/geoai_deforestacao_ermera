import os
import rasterio
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# 1. Menentukan path data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")
VECTOR_DIR = os.path.join(BASE_DIR, "vector")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

defor_path = os.path.join(RAW_DIR, "deforestation_alert_ermera.tif")
s2_path = os.path.join(RAW_DIR, "sentinel2_ermera_2026.tif")
shp_path = os.path.join(VECTOR_DIR, "Ermera_munisipality_boundary.shp")

print("--- MEMBUAT VISUALISASI TITIK ALERT API / DEFORESTASI ERMERA ---")

# 2. Baca data vektor batas wilayah
gdf_boundary = gpd.read_file(shp_path)

# 3. Baca raster deforestasi & ekstrak koordinat (X, Y) dari piksel yang bernilai 1
with rasterio.open(defor_path) as src_defor:
    defor_data = src_defor.read(1)
    crs = src_defor.crs
    extent = [src_defor.bounds.left, src_defor.bounds.right, 
              src_defor.bounds.bottom, src_defor.bounds.top]
    
    # Hitung ukuran piksel dalam meter
    if crs.is_geographic:
        lat_tengah = (src_defor.bounds.bottom + src_defor.bounds.top) / 2.0
        deg_to_m_y = 111320.0
        deg_to_m_x = 111320.0 * np.cos(np.radians(lat_tengah))
        res_x_m = abs(src_defor.res[0]) * deg_to_m_x
        res_y_m = abs(src_defor.res[1]) * deg_to_m_y
    else:
        res_x_m, res_y_m = abs(src_defor.res[0]), abs(src_defor.res[1])

    pixel_area_m2 = res_x_m * res_y_m
    
    # Ekstraksi koordinat spasial baris & kolom piksel deforestasi
    rows, cols = np.where(defor_data == 1)
    xs, ys = rasterio.transform.xy(src_defor.transform, rows, cols)

defor_pixels = len(xs)
luas_ha = (defor_pixels * pixel_area_m2) / 10000.0
luas_km2 = (defor_pixels * pixel_area_m2) / 1000000.0

print(f"Piksel Terdeteksi : {defor_pixels:,} titik koordinat")
print(f"Total Deforestasi : {luas_ha:.2f} Hektare ({luas_km2:.3f} km²)")

# 4. Baca citra True Color Sentinel-2 (RGB: B4, B3, B2)
with rasterio.open(s2_path) as src_s2:
    r = src_s2.read(1).astype(float)
    g = src_s2.read(2).astype(float)
    b = src_s2.read(3).astype(float)

def stretch(band):
    valid = band[band > 0]
    if len(valid) == 0:
        return band
    p2, p98 = np.percentile(valid, (2, 98))
    return np.clip((band - p2) / (p98 - p2 + 1e-6), 0, 1)

rgb_image = np.dstack([stretch(r), stretch(g), stretch(b)])

# 5. Visualisasi Peta Publikasi dengan Titik Peringatan Api
fig, ax = plt.subplots(figsize=(10, 11), dpi=300)

# A. Base Image RGB
ax.imshow(rgb_image, extent=extent)

# B. Lapisan Glow Luar (Aura Merah Terang agar terlihat mencolok dari jauh)
ax.scatter(xs, ys, c='#FF1E00', s=35, alpha=0.35, edgecolors='none', zorder=4)

# C. Lapisan Titik Inti Api (Kuning Terang dengan tepi merah tua)
ax.scatter(xs, ys, c='#FFEA00', s=10, alpha=0.95, edgecolors='#B30000', linewidths=0.5, zorder=5)

# D. Batas Administrasi Munisípiu Ermera
if gdf_boundary.crs != src_defor.crs:
    gdf_boundary = gdf_boundary.to_crs(src_defor.crs)
gdf_boundary.boundary.plot(ax=ax, color='#00FFFF', linewidth=1.4, linestyle='--', zorder=6)

# E. Format Judul & Grid
ax.set_title("Peta Titik Alert Deforestasi & Kebakaran (NRT) di Munisípiu Ermera (2025–2026)\n"
             "Integrasi GeoAI Random Forest & Sentinel-2 MSI", 
             fontsize=12, fontweight='bold', pad=12)
ax.set_xlabel("Bujur / Longitude (°E)", fontsize=9)
ax.set_ylabel("Lintang / Latitude (°S)", fontsize=9)
ax.grid(True, linestyle=':', alpha=0.4, color='gray')

# F. Kotak Statistik
stats_text = (f"Statistik Deforestasi:\n"
              f"• Jumlah Titik: {defor_pixels:,} titik\n"
              f"• Luas Area   : {luas_ha:.2f} ha\n"
              f"• Estimasi    : {luas_km2:.3f} km²")
ax.text(0.03, 0.08, stats_text, transform=ax.transAxes, fontsize=9.5, fontweight='medium',
        bbox=dict(boxstyle='square,pad=0.5', facecolor='white', alpha=0.9, edgecolor='black'), zorder=7)

# G. Legenda Simbol Titik (zorder dihapus dari argumen legend)
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Titik Alert Deforestasi / Api',
           markerfacecolor='#FFEA00', markeredgecolor='#B30000', markersize=8),
    Patch(facecolor='none', edgecolor='#00FFFF', linestyle='--', label='Batas Munisípiu Ermera')
]
leg = ax.legend(handles=legend_elements, loc='lower right', framealpha=0.9, fontsize=9)
leg.set_zorder(7)

# Simpan Peta Output
out_map = os.path.join(OUTPUT_DIR, "Peta_Deforestasi_Ermera_2026.png")
plt.tight_layout()
plt.savefig(out_map, dpi=300)
plt.close()

print(f"\n[SUKSES] Peta titik deforestasi baru berhasil disimpan di:\n{out_map}")