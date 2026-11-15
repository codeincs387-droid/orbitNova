
import xarray as xr
from pathlib import Path

folder = Path("data/raw/merra2/cdd_v2_test")
files = list(folder.glob("*.nc4"))

if not files:
    raise FileNotFoundError("No V2 NetCDF file found.")

ds = xr.open_dataset(files[0])

print("FILE:", files[0])
print("COLLECTION:", ds.attrs.get("ShortName"))
print("DATE:", ds.attrs.get("RangeBeginningDate"))
print("CDD:", ds["CDD"])
print("CDD UNITS:", ds["CDD"].attrs.get("units"))

ds.close()
