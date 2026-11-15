
import earthaccess
import xarray as xr
import numpy as np
import calendar
from pathlib import Path

# Directories
raw_dir = Path("data/raw/merra2/precipitation_downloads")
output_dir = Path("data/processed/monthly_grid/prectot")

raw_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)

# India bounding box: west, south, east, north
india_bbox = (67, 5, 99, 38)

print("Connecting to NASA Earthdata...")
earthaccess.login()

print("\nSearching MERRA-2 PRECTOT monthly granules...")

granules = earthaccess.search_data(
    short_name="M2TMNXFLX",
    version="5.12.4",
    temporal=("2000-01-01", "2026-09-30")
)

print("Total granules found:", len(granules))

if not granules:
    raise RuntimeError("No precipitation granules found.")

print("\nStarting precipitation download and extraction...")

successful = 0
skipped = 0
failed = 0

for index, granule in enumerate(granules, start=1):

    print(f"\nProcessing {index}/{len(granules)}")

    try:
        downloaded = earthaccess.download(
            [granule],
            local_path=str(raw_dir)
        )

        if not downloaded:
            print("Download failed. Skipping.")
            failed += 1
            continue

        source_file = Path(downloaded[0])

        # Extract YYYYMM from NASA filename
        parts = source_file.name.split(".")
        year_month = parts[-2]

        year = int(year_month[:4])
        month = int(year_month[4:6])

        output_file = output_dir / f"PRECTOT_India_{year_month}.nc"

        if output_file.exists():
            print("Already processed:", output_file.name)
            source_file.unlink(missing_ok=True)
            skipped += 1
            continue

        days = calendar.monthrange(year, month)[1]

        with xr.open_dataset(source_file) as ds:

            if "PRECTOT" not in ds.variables:
                raise ValueError("PRECTOT variable not found.")

            # Select India region
            india = ds["PRECTOT"].sel(
                lat=slice(india_bbox[1], india_bbox[3]),
                lon=slice(india_bbox[0], india_bbox[2])
            ).astype("float64")

            # Remove missing and invalid values
            missing_value = india.attrs.get("fmissing_value", 1e15)

            india = india.where(
                np.isfinite(india)
                & (india < 1e15)
                & (india > -1e15)
                & (india != missing_value)
            )

            # Convert kg m-2 s-1 to monthly accumulated mm
            monthly_rainfall = india * 86400 * days

            monthly_rainfall.attrs = {
                "long_name": "monthly_total_precipitation",
                "units": "mm",
                "source_variable": "PRECTOT",
                "source_units": "kg m-2 s-1",
                "conversion": "PRECTOT * 86400 * days_in_month"
            }

            output_ds = monthly_rainfall.to_dataset(
                name="PRECTOT"
            )

            output_ds.attrs = {
                "source": "NASA MERRA-2",
                "collection": "M2TMNXFLX",
                "version": "5.12.4",
                "region": "India",
                "period": year_month
            }

            output_ds.to_netcdf(output_file)

        # Remove global source file after successful extraction
        source_file.unlink(missing_ok=True)

        print("Saved:", output_file.name)
        successful += 1

    except Exception as error:
        print("Processing error:", error)
        failed += 1

print("\n========== DOWNLOAD SUMMARY ==========")
print("Total granules:", len(granules))
print("Successfully processed:", successful)
print("Already processed:", skipped)
print("Failed:", failed)
print("Output directory:", output_dir)
print("\nPrecipitation download and extraction finished.")
