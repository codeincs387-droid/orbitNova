
import earthaccess
import xarray as xr
from pathlib import Path

# Folders
raw_dir = Path("data/raw/merra2/cdd_downloads")
output_dir = Path("data/processed/monthly_grid/cdd")

raw_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)

# India bounding box: west, south, east, north
india_bbox = (67, 5, 99, 38)

print("Connecting to NASA Earthdata...")
earthaccess.login()

print("Searching all available CDD V2 granules...")

granules = earthaccess.search_data(
    short_name="M2SMNXEDI",
    version="2",
    temporal=("1980-01-01", "2026-11-30")
)

print(f"Total granules found: {len(granules)}")

if not granules:
    raise RuntimeError("No CDD V2 granules found.")

print("\nStarting bulk download...")

for index, granule in enumerate(granules, start=1):

    print(f"\nProcessing granule {index}/{len(granules)}")

    downloaded = earthaccess.download(
        [granule],
        local_path=str(raw_dir)
    )

    if not downloaded:
        print("Download failed. Skipping.")
        continue

    source_file = Path(downloaded[0])

    # Preserve original filename for reliable date extraction
    filename = source_file.name
    parts = filename.split(".")

    # Expected filename: ...v2_1.YYYYMM.nc4
    year_month = parts[-2]

    output_file = output_dir / f"CDD_India_{year_month}.nc"

    if output_file.exists():
        print("Already extracted:", output_file.name)
        continue

    try:
        with xr.open_dataset(source_file) as ds:

            india = ds[["CDD"]].sel(
                lat=slice(5, 38),
                lon=slice(67, 99)
            )

            india.to_netcdf(output_file)

        print("India subset saved:", output_file.name)

    except Exception as error:
        print("Extraction error:", error)

print("\nCDD historical download and extraction finished!")
