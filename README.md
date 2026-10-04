# GeoAI Deforestation Monitoring Pipeline - Munisípiu Ermera

Pipeline automatizasaun bazeia ba GeoAI no dadus remote sensing hodi deteta no monitoriza dinámika desflorestasaun iha nivel munisípiu no suku iha Munisípiu Ermera, Timor-Leste.

---

## 📌 Vizaun Jerál Projetu
Repozitóriu ida-ne'e integra dadus imajen satélite (Sentinel-2), algoritmu detesaun kobertura rai bazeia ba intelijénsia spasiál (GeoAI), no baliza administrativa vetór hodi prodús monitorizasaun desflorestasaun ne'ebé periódiku (*near real-time*). Sistema ne'e dezenvolve hodi apoia análize ordenamentu do teritóriu ambientál, konservasaun floresta, no mitigasaun risku degradasaun rai.

---

## 📂 Strutura Repozitóriu
* `.github/workflows/nrt_monitor.yml`: Skrip automatizasaun GitHub Actions hodi ezekuta prosesamentu no atualizasaun dadus periódiku.
* `analisis_ermera.py`: Skrip prinsipál ba prosesamentu imajen satélite, estrasaun índise spektrál, no kalkulasaun desflorestasaun agregadu iha nivel munisípiu.
* `analisis_suco.py`: Skrip análize spasiál bazeia ba zonamentu administrativu iha nivel suku iha Ermera.
* `vector/`: Dadus spasiál baliza administrativa Munisípiu Ermera no suku sira (`.shp`, `.dbf`, `.prj`, `.shx`).
* `outputs/`: Rezultadu vizualizasaun kartográfika no rekapitulasaun numérika:
  * `Peta_Deforestasi_Ermera_2026.png`
  * `Peta_Deforestasi_Per_Suco_Ermera.png`
  * `rekapitulasi_deforestasi_per_suco.csv`
* `raw/`: Diretóriu temporáriu hodi rai dadus raster (la inklui iha rastreamentu repozitóriu liuhusi `.gitignore`).

---

## 🛠️ Rekizitus Sistema & Instalasaun
Atu ezekuta pipeline ida-ne'e iha ambiente lokál:

1. **Kloning Repozitóriu:**
   ```bash
   git clone [https://github.com/ciprianopereira36-png/geoai_deforestacao_ermera.git](https://github.com/ciprianopereira36-png/geoai_deforestacao_ermera.git)
   cd geoai_deforestacao_ermera
