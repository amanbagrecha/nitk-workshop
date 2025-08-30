#!/usr/bin/env python3
import os
from pathlib import Path
from datetime import datetime, date

import xarray as xr
import rioxarray  # noqa: F401  # needed to enable .rio
import geopandas as gpd
from shapely.geometry import mapping
from tqdm import tqdm
import pandas as pd

import imdlib as imd  # IMD downloader

# --------------------
# User params (edit this block)
# --------------------
VARIABLE = "rain"                                # 'rain' | 'tmin' | 'tmax'  (rain=mm)  # noqa
START_YEAR, END_YEAR = 2016, 2017                # inclusive year range (used when USE_REALTIME_API=False)
TIME_START, TIME_END = "2016-06-01", "2017-09-30"  # ISO dates for real-time API or final time slicing
AOI_PATH = "data/aoi/aoi.geojson"                # or a shapefile: data/aoi/aoi.shp
OUT_DIR = Path("outputs")
EXPORT_DAILY_GEOTIFFS = False                    # set True if you want daily tiffs
EXPORT_MONTHLY_GEOTIFFS = True                   # monthly sums
CHUNK_TIME = 60                                  # dask chunking for memory, tweak as needed
USE_REALTIME_API = False                         # True: use get_real_data() with TIME_START/TIME_END dates
                                                # False: use get_data() with START_YEAR/END_YEAR

# --------------------
# Paths
# --------------------
DATA_DIR = Path("data")
DOWNLOAD_DIR = DATA_DIR / "raw" / "imd_data"     # changed to handle GRD format


def download_data_by_daterange(variable, start_date, end_date):
    """Download data using real-time API with date range."""
    print(f"Downloading {variable} data from {start_date} to {end_date} using real-time API...")
    
    try:
        # Use get_real_data for date-based downloads
        imd_obj = imd.get_real_data(variable, start_date, end_date, file_dir=".")
        print("Date-range data download successful!")
        return imd_obj
    except Exception as e:
        print(f"Error: Date-range data download failed: {e}")
        raise


def download_data_by_years(variable, start_year, end_year):
    """Download data using yearly API."""
    print(f"Downloading {variable} data for years {start_year}-{end_year}...")
    
    # Create subdirectory structure for imdlib
    variable_dir = Path(variable)
    variable_dir.mkdir(exist_ok=True)
    
    # Check if GRD files already exist, if not download them
    existing_files = list(variable_dir.glob("*.grd"))
    years_present = {int(f.stem) for f in existing_files}
    years_needed = set(range(start_year, end_year + 1))
    
    if not years_needed.issubset(years_present):
        print("Downloading missing years...")
        imd_obj = imd.get_data(variable, start_year, end_year, 
                             fn_format="yearwise", file_dir=".", sub_dir=True)
    
    # Load the data
    print("Loading yearly data...")
    imd_obj = imd.open_data(variable, start_year, end_year, 
                           fn_format="yearwise", file_dir=".")
    return imd_obj


def main():
    """Main function to run the IMD AOI pipeline."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------
    # 1) Download/Load IMD data based on processing mode
    # --------------------
    if USE_REALTIME_API:
        # Use real-time API with TIME_START/TIME_END dates
        imd_obj = download_data_by_daterange(VARIABLE, TIME_START, TIME_END)
    else:
        # Use yearly API with START_YEAR/END_YEAR
        imd_obj = download_data_by_years(VARIABLE, START_YEAR, END_YEAR)
    
    # --------------------
    # 2) Convert to xarray Dataset
    # --------------------
    print("Converting to xarray...")
    ds = imd_obj.get_xarray()
    
    # Add chunking for better memory management
    ds = ds.chunk({"time": CHUNK_TIME})
    
    # Sanity check: ensure spatial dims are named `lat` / `lon` for rioxarray
    if "lat" not in ds.dims or "lon" not in ds.dims:
        raise SystemExit(f"Unexpected dims: {ds.dims}. Expected 'lat' and 'lon'.")

    da = ds[VARIABLE]  # DataArray: time, lat, lon

    # Assign CRS & spatial dims for rioxarray
    da = (da
          .rio.write_crs("EPSG:4326", inplace=False)
          .rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=False))

    # --------------------
    # 3) Clip to AOI
    #     rioxarray clip expects geometries+CRS; handles masks neatly.
    #     Docs: https://corteva.github.io/rioxarray/stable/examples/clip_geom.html
    # --------------------
    print(f"Reading AOI: {AOI_PATH}")
    aoi = gpd.read_file(AOI_PATH)
    aoi = aoi.to_crs(epsg=4326)

    shapes = [mapping(geom) for geom in aoi.geometry]
    da_aoi = da.rio.clip(shapes, aoi.crs, drop=True)

    # # --------------------
    # # 4) Time subset
    # # --------------------
    # print(f"Time slice: {TIME_START} -> {TIME_END}")
    # da_sub = da_aoi.sel(time=slice(TIME_START, TIME_END))

    # --------------------
    # Handle nodata values (-999) before processing
    # --------------------
    print("Handling nodata values (-999)...")
    da_aoi = da_aoi.where(da_aoi != -999, other=float('nan'))
    
    # --------------------
    # 5a) (Optional) Export daily GeoTIFFs
    # --------------------
    if EXPORT_DAILY_GEOTIFFS:
        daily_dir = OUT_DIR / "daily_geotiff"
        daily_dir.mkdir(parents=True, exist_ok=True)
        print("Exporting daily GeoTIFFs...")
        for t in tqdm(da_aoi.time.values, desc="Daily TIF"):
            day = str(pd.to_datetime(t).date())
            daily_slice = da_aoi.sel(time=t)
            daily_slice.rio.write_nodata(float('nan'), inplace=True)
            daily_slice.rio.to_raster(daily_dir / f"imd_rain_{day}.tif")

    # --------------------
    # 5b) Monthly sum & export
    # --------------------
    if EXPORT_MONTHLY_GEOTIFFS:
        print("Computing monthly sums...")
        # .resample keeps calendar correct; rainfall is additive
        # Use skipna=True to ignore NaN values in the sum
        monthly = da_aoi.resample(time="MS").sum(keep_attrs=True, skipna=True)
        mon_dir = OUT_DIR / "monthly_sum_geotiff"
        mon_dir.mkdir(parents=True, exist_ok=True)
        for t in tqdm(monthly.time.values, desc="Monthly TIF"):
            stamp = pd.to_datetime(t).strftime("%Y_%m")
            monthly_slice = monthly.sel(time=t)
            monthly_slice.rio.write_nodata(float('nan'), inplace=True)
            monthly_slice.rio.to_raster(mon_dir / f"imd_rain_monthsum_{stamp}.tif")

    print("Done. Outputs in:", OUT_DIR)


if __name__ == "__main__":
    main()
