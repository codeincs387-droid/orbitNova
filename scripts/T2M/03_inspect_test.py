from pathlib import Path
import xarray as xr

RAW_DIR = Path("data/raw/merra2/temperature")
files = sorted(RAW_DIR.glob("*.nc4"))

if not files:
    raise FileNotFoundError("No .nc4 file found. Run Script 2 first.")

source = files[0]

print("Inspecting:", source.name)

with xr.open_dataset(source) as ds:
    print("\nDataset information:")
    print(ds)


print("\nVariables:")
for name in ds.data_vars:
    print(name, ds[name].attrs)

if "T2M" not in ds:
    raise ValueError("T2M variable not found in this file.")

print("\nT2M dimensions:", ds["T2M"].dims)
print("T2M shape:", ds["T2M"].shape)
print("T2M units:", ds["T2M"].attrs.get("units"))
print("Latitude range:", float(ds.lat.min()), float(ds.lat.max()))
print("Longitude range:", float(ds.lon.min()), float(ds.lon.max()))
print("Time:", ds.time.values)
