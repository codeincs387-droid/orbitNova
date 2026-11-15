
import earthaccess
import xarray as xr
import pandas as pd

from pathlib import Path
from datetime import date
import time
import traceback

# ---------------- CONFIGURATION ----------------

SHORT_NAME = "M2TMNXSLV"
VERSION = "5.12.4"

START_DATE = "2000-01-01"
END_DATE = date.today().isoformat()

RAW_DIR = Path("data/raw/merra2/temperature")
OUTPUT_DIR = Path("data/processed/monthly_grid/temperature")
REPORT_DIR = Path("reports")

LOG_FILE = REPORT_DIR / "download_log.csv"

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# India bounding box
WEST, EAST = 67, 99
SOUTH, NORTH = 5, 38

# ------------------------------------------------


def log_result(month, status, filename="", message=""):
    row = pd.DataFrame([{
        "month": month,
        "status": status,
        "filename": filename,
        "message": message
    }])

    row.to_csv(
        LOG_FILE,
        mode="a",
        header=not LOG_FILE.exists(),
        index=False
    )


def extract_india(source_file):
    """Extract T2M from one global monthly NetCDF file."""

    with xr.open_dataset(source_file) as ds:

        if "T2M" not in ds:
            raise ValueError(
                f"T2M variable missing in {source_file.name}"
            )

        if "lat" not in ds.coords or "lon" not in ds.coords:
            raise ValueError("Latitude or longitude coordinates missing.")

        lat_slice = (
            slice(SOUTH, NORTH)
            if ds.lat.values[0] < ds.lat.values[-1]
            else slice(NORTH, SOUTH)
        )

        india = ds[["T2M"]].sel(
            lat=lat_slice,
            lon=slice(WEST, EAST)
        ).load()

        if india.sizes.get("lat", 0) == 0:
            raise ValueError("No India latitude cells extracted.")

        if india.sizes.get("lon", 0) == 0:
            raise ValueError("No India longitude cells extracted.")

        if "time" not in india.coords or india.sizes["time"] == 0:
            raise ValueError("No valid time coordinate.")

        month = pd.Timestamp(india.time.values[0]).strftime("%Y%m")

        output_file = OUTPUT_DIR / f"T2M_India_{month}.nc"

        temporary_output = output_file.with_suffix(".tmp.nc")

        india.to_netcdf(
            temporary_output,
            encoding={
                "T2M": {
                    "zlib": True,
                    "complevel": 4
                }
            }
        )

        # Validate the newly written output before replacing final file.
        with xr.open_dataset(temporary_output) as check:
            if "T2M" not in check:
                raise ValueError("Output validation failed.")

            if check.sizes.get("lat", 0) == 0:
                raise ValueError("Output has no latitude cells.")

            if check.sizes.get("lon", 0) == 0:
                raise ValueError("Output has no longitude cells.")

            if check.sizes.get("time", 0) == 0:
                raise ValueError("Output has no time values.")

        temporary_output.replace(output_file)

        return month, output_file


def main():

    print("NASA Earthdata login...")
    earthaccess.login()

    print("\nSearching MERRA-2 temperature granules...")

    granules = earthaccess.search_data(
        short_name=SHORT_NAME,
        version=VERSION,
        temporal=(START_DATE, END_DATE),
        count=10000
    )

    if not granules:
        raise RuntimeError(
            "No granules found. Check collection version and date range."
        )

    print("Granules found:", len(granules))
    print("Date range:", START_DATE, "to", END_DATE)

    completed = 0
    failed = 0

    for index, granule in enumerate(granules, start=1):

        print(f"\n[{index}/{len(granules)}] Processing granule")

        downloaded_files = []

        try:
            # Retry individual downloads.
            for attempt in range(1, 4):

                try:
                    downloaded_files = earthaccess.download(
                        [granule],
                        local_path=str(RAW_DIR)
                    )

                    if downloaded_files:
                        break

                    raise RuntimeError("Download returned no files.")

                except Exception:
                    if attempt == 3:
                        raise

                    print(f"Download attempt {attempt} failed. Retrying...")
                    time.sleep(5 * attempt)

            if not downloaded_files:
                raise RuntimeError("Could not download granule.")

            for downloaded_file in downloaded_files:

                source = Path(downloaded_file)

                try:
                    month, output_file = extract_india(source)

                    print("Extracted:", output_file.name)

                    log_result(
                        month,
                        "SUCCESS",
                        output_file.name,
                        "India extraction and validation successful"
                    )

                    completed += 1

                    # Delete only after successful extraction and validation.
                    source.unlink(missing_ok=True)

                except Exception:
                    raise

        except Exception as error:

            print("ERROR:", error)
            traceback.print_exc()

            failed += 1

            log_result(
                "",
                "FAILED",
                "",
                str(error)
            )

            # Keep downloaded raw files if extraction failed.
            continue

    print("\n========== DOWNLOAD SUMMARY ==========")
    print("Granules found:", len(granules))
    print("Successful:", completed)
    print("Failed:", failed)
    print("Output folder:", OUTPUT_DIR)
    print("Log file:", LOG_FILE)

    print("\nRun Script 6 to validate all processed months.")


if __name__ == "__main__":
    main()
