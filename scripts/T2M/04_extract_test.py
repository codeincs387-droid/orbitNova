from pathlib import Path
import xarray as xr

RAW_DIR = Path("data/raw/merra2/temperature")
OUTPUT_DIR = Path("data/processed/monthly_grid/temperature")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

files = sorted(RAW_DIR.glob("*.nc4"))

if not files:
    raise FileNotFoundError("No test .nc4 file found.")

source = files[0]

with xr.open_dataset(source) as ds:
    if "T2M" not in ds:
        raise ValueError("T2M variable not found.")

    #Handle ascending or descending latitude coordinates.
    lat_slice = (
        slice(5, 38)
        if ds.lat.values[0] < ds.lat.values[-1]
        else slice(38, 5)
)

india = ds[["T2M"]].sel(
    lat=lat_slice,
    lon=slice(67, 99)
).load()

if india.sizes.get("lat", 0) == 0 or india.sizes.get("lon", 0) == 0:
    raise ValueError("India extraction returned an empty grid.")

month = str(india.time.values[0])[:7].replace("-", "")
output_file = OUTPUT_DIR / f"T2M_India_{month}.nc"

india.to_netcdf(
    output_file,
    encoding={
        "T2M": {
            "zlib": True,
            "complevel": 4
        }
    }
)

print("\nExtraction successful!")
print("Output:", output_file)
print("Dimensions:", dict(india.sizes))
print("T2M units:", india["T2M"].attrs.get("units"))