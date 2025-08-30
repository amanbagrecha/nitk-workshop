### bulk-download **IMD 0.25° daily rainfall (NetCDF)**, subset to an **AOI** and **time window**, and export **GeoTIFFs/netCDFs**.

I’m using **uv** (Astral’s fast Python tool), **imdlib** (purpose-built for IMD downloads), **xarray/rioxarray** for raster work, and **geopandas** for AOIs. Key references are linked inline. ([imdlib.readthedocs.io][1], [imdpune.gov.in][2], [corteva.github.io][3])

---

# IMD Rainfall (0.25°) — Workshop Setup

## 0) What you get

* **Bulk downloader** for IMD daily rainfall (1901–present) using `imdlib`. ([imdlib.readthedocs.io][1])
* **AOI clip** (any shapefile/GeoJSON; assumes WGS84/EPSG:4326). ([corteva.github.io][3])
* **Time slice** (e.g., 2015-06-01 → 2017-09-30).
* **Exports**: daily stack or monthly sums in any xarray supported format.

IMD dataset details (grid, extent, units) are documented by IMD Pune; we use the **NetCDF** variant. ([imdpune.gov.in][2])

---

## 1) Install prerequisites

> Works on macOS/Linux/WSL. Windows PowerShell users can adapt the activate step.

```bash
# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone/download this project and navigate to it
cd imd-aoi-pipeline

# Install the project in development mode with all dependencies
uv sync --dev

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS/WSL
# or
.venv\Scripts\activate     # Windows PowerShell
```

---

## 2) Put your AOI in the project

Drop **one** of these into `data/aoi/`:

* `aoi.geojson` (preferred)
* or `aoi.shp` + sidecars

AOI must be **EPSG:4326** (lat/lon). If not, we’ll reproject in code.

---

## 3) Script: download, subset, and export


**Notes & gotchas (based on docs & field use):**

* IMD NetCDF uses **lat/lon in EPSG:4326** over **66.5E–100E, 6.5N–38.5N**, daily **mm**. If your AOI crosses longitude conventions, ensure it’s in **66.5…100E** range (not 0–360 or −180…180 issues). ([imdpune.gov.in][2], [GIS Stack Exchange][4])
* `imdlib.get_data()` is the simplest, battle-tested bulk route (yearwise). ([imdlib.readthedocs.io][1])
* rioxarray clip & examples: see **clip by geometry/box** pages. ([corteva.github.io][3])

---

## 4) Run it

```bash
# From the project folder:
uv run python imd_aoi_pipeline.py
```

Then look in:

* `outputs/monthly_sum_geotiff/*.tif` (monthly sums), and/or
* `outputs/daily_geotiff/*.tif` (if enabled).

Open in QGIS—GeoTIFFs are georeferenced.

---

## 5) Variations you  might want

* **Different variable**: set `VARIABLE = "tmin"` or `"tmax"`; `imdlib` can fetch those too.
* **Speed / memory**: turn on dask (installed above), increase `CHUNK_TIME`, or export by year to keep arrays small.
* **Direct manual URLs**: if you must avoid `imdlib`, curate the **NetCDF year links** from IMD Pune (same product) and download with `aria2c/wget`, then open via `xarray.open_mfdataset`. ([imdpune.gov.in][2])
* **Background reading on dataset**: official IMD 0.25° dataset papers/notes. ([mausamjournal.imd.gov.in][5], [AGU Publications][6], [Nature][7])

---


[1]: https://imdlib.readthedocs.io/en/latest/Usage.html "Downloading — IMDLIB documentation"
[2]: https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html "Yearly Gridded Rainfall (0.25 x 0.25) data NetCDF File"
[3]: https://corteva.github.io/rioxarray/stable/examples/clip_geom.html "Example - Clip — rioxarray 0.19.0 documentation"
[4]: https://gis.stackexchange.com/questions/382037/python-rioxarray-clip-masking-netcdf-data-with-a-polygon-returns-all-nan "python rioxarray.clip masking netcdf data with a polygon ..."
[5]: https://mausamjournal.imd.gov.in/index.php/MAUSAM/article/view/851 "Development of a new high spatial resolution (0.25° × 0.25 ..."
[6]: https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022EA002595 "Long‐Term High‐Resolution Gauge Adjusted Satellite ..."
[7]: https://www.nature.com/articles/s41597-025-04474-2 "A station-based 0.1-degree daily gridded ensemble ..."
[8]: https://www.sciencedirect.com/science/article/abs/pii/S1364815223002554 "IMDLIB: An open-source library for retrieval, processing ..."
[9]: https://pypi.org/project/imdlib/ "imdlib"
[10]: https://corteva.github.io/rioxarray/stable/examples/examples.html "Usage Examples — rioxarray 0.19.0 documentation"
[11]: https://geog-312.gishub.org/book/geospatial/rioxarray.html "13. Rioxarray - Introduction to GIS Programming"
