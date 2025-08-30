# Geospatial Data Download Toolkit

This repository provides tools for downloading and processing geospatial datasets:

1. **IMD Rainfall Pipeline** - Downloads, subsets, and exports daily rainfall data from India Meteorological Department's 0.25° gridded dataset
2. **Copernicus Data Access** - Demonstrates searching and downloading Sentinel satellite data via CDSE STAC API

---

## Installation

> Works on macOS/Linux/WSL. Windows PowerShell users can adapt the activate step.

```bash
# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up virtual environment
uv venv .venv
source .venv/bin/activate  # Linux/macOS/WSL
# or
.venv\Scripts\activate     # Windows PowerShell

# Install dependencies
uv pip install imdlib xarray rioxarray geopandas pyogrio shapely tqdm dask pystac-client boto3
```

---

## 1. IMD Rainfall Data Pipeline

### Overview

**Bulk-download IMD 0.25° daily rainfall (NetCDF)**, subset to an **AOI** and **time window**, and export **GeoTIFFs/netCDFs**.

Uses **uv** (Astral's fast Python tool), **imdlib** (purpose-built for IMD downloads), **xarray/rioxarray** for raster work, and **geopandas** for AOIs.

### What you get

* **Bulk downloader** for IMD daily rainfall (1901–present) using `imdlib`
* **AOI clip** (any shapefile/GeoJSON; assumes WGS84/EPSG:4326)
* **Time slice** (e.g., 2015-06-01 → 2017-09-30)
* **Exports**: daily stack or monthly sums in any xarray supported format

### Setup your AOI

Drop **one** of these into `data/aoi/`:

* `aoi.geojson` (preferred)
* or `aoi.shp` + sidecars

AOI must be **EPSG:4326** (lat/lon). If not, we'll reproject in code.

### Configuration

All parameters are at the top of `imd_aoi_pipeline.py`:

* `VARIABLE`: 'rain', 'tmin', or 'tmax'
* `USE_REALTIME_API`: True=use date-based API, False=use year-based API
* `START_YEAR`, `END_YEAR`: Year range
* `TIME_START`, `TIME_END`: ISO date range for time slicing
* `AOI_PATH`: Path to AOI geometry file
* Export flags for daily/monthly outputs

### Run it

```bash
uv run python imd_aoi_pipeline.py
```

Outputs appear in:
* `outputs/monthly_sum_geotiff/*.tif` (monthly sums)
* `outputs/daily_geotiff/*.tif` (if enabled)

Open in QGIS—GeoTIFFs are georeferenced.

### Notes

* IMD NetCDF uses **lat/lon in EPSG:4326** over **66.5E–100E, 6.5N–38.5N**, daily **mm**
* `imdlib.get_data()` is the battle-tested bulk route (yearwise)
* Coordinate system: EPSG:4326, extent 66.5E–100E, 6.5N–38.5N

---

## 2. Copernicus Data Space Ecosystem (CDSE)

### Overview

**CDSE STAC Notebook** (`cdse.ipynb`) demonstrates accessing Sentinel satellite data via CDSE's STAC API.

### What it does

* Uses `pystac-client` to search Sentinel-1/2/3/5P collections
* Queries by bbox, datetime, and cloud cover filters
* Accesses JP2 band files via S3 using CDSE credentials
* API endpoint: `https://stac.dataspace.copernicus.eu/v1/`
* S3 endpoint: `https://eodata.dataspace.copernicus.eu`

### Setup

1. **Register at Copernicus Data Space**: https://documentation.dataspace.copernicus.eu/APIs/S3.html#registration
2. **Generate S3 credentials** from your CDSE account
3. **Set environment variables**:
   ```bash
   export CDSE_S3_ACCESS_KEY="your_access_key"
   export CDSE_S3_SECRET_KEY="your_secret_key"
   ```

### Usage

Open and run `cdse.ipynb` to:
1. Connect to CDSE STAC catalog
2. Search for Sentinel-2 data with filters
3. Inspect metadata and available assets
4. Download JP2 band files using S3

---

## References

### IMD Data
* [IMDLIB documentation](https://imdlib.readthedocs.io/en/latest/Usage.html)
* [IMD Pune Gridded Data](https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html)
* [rioxarray examples](https://corteva.github.io/rioxarray/stable/examples/clip_geom.html)

### Copernicus Data
* [CDSE Documentation](https://documentation.dataspace.copernicus.eu/)
* [STAC API Guide](https://documentation.dataspace.copernicus.eu/APIs/STAC.html)
* [S3 Access Guide](https://documentation.dataspace.copernicus.eu/APIs/S3.html)