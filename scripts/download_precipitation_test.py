
import earthaccess
import xarray as xr
from pathlib import Path

output_dir = Path("data/raw/merra2/precipitation_test")
output_dir.mkdir(parents=True, exist_ok=True)

india_bbox = (67, 5, 99, 38)

print("Logging in to NASA Earthdata...")
earthaccess.login()

print("Searching MERRA-2 precipitation data...")

results = earthaccess.search_data(
    short_name="M2TMNXFLX",
    version="5.12.4",
    bounding_box=india_bbox,
    temporal=("2020-01-01", "2020-01-31"),
    count=1
)

if not results:
    print("No precipitation granules found.")
    raise SystemExit(1)

print(f"Found {len(results)} granule(s).")

downloaded = earthaccess.download(
    results,
    local_path=str(output_dir)
)

if not downloaded:
    print("Download failed or returned no files.")
    raise SystemExit(1)

print("\nDownloaded file(s):")

for file in downloaded:
    print(file)

    print("\nInspecting NetCDF metadata...")

    with xr.open_dataset(file) as ds:
        print("\nDataset information:")
        print(ds)

        print("\nPRECTOT variable:")

        if "PRECTOT" in ds.variables:
            variable = ds["PRECTOT"]

            print("Dimensions:", variable.dims)
            print("Shape:", variable.shape)
            print("Data type:", variable.dtype)
            print("Attributes:", variable.attrs)
            print("Units:", variable.attrs.get("units", "Not specified"))
            print("Long name:", variable.attrs.get("long_name", "Not specified"))
        else:
            print("PRECTOT was not found.")
            print("Available variables:", list(ds.data_vars))
