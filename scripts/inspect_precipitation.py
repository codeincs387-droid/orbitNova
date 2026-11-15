
import xarray as xr
import numpy as np
import calendar
from pathlib import Path

file_path = Path(
    "data/raw/merra2/precipitation_test/"
    "MERRA2_400.tavgM_2d_flx_Nx.202001.nc4"
)

print("Opening precipitation sample...")

with xr.open_dataset(file_path) as ds:

    # Select India bounding box
    india = ds["PRECTOT"].sel(
        lat=slice(5, 38),
        lon=slice(67, 99)
    )

    values = india.values.astype(float)

    # Replace missing/invalid values
    values[~np.isfinite(values)] = np.nan
    values[values >= 1e15] = np.nan
    values[values <= -1e15] = np.nan

    valid = values[np.isfinite(values)]

    print("\n--- INDIA PRECIPITATION SAMPLE ---")
    print("Shape:", values.shape)
    print("Valid grid cells:", len(valid))
    print("Missing grid cells:", np.isnan(values).sum())

    if len(valid) == 0:
        print("No valid precipitation values found.")
        raise SystemExit(1)

    print("\n--- ORIGINAL PRECTOT RATE ---")
    print("Minimum:", np.min(valid))
    print("Maximum:", np.max(valid))
    print("Mean:", np.mean(valid))
    print("Units: kg m-2 s-1")

    # Convert January 2020 mean rate to monthly rainfall
    days = calendar.monthrange(2020, 1)[1]
    monthly_rainfall = valid * 86400 * days

    print("\n--- CONVERTED JANUARY RAINFALL ---")
    print("Days in month:", days)
    print("Minimum:", np.min(monthly_rainfall), "mm")
    print("Maximum:", np.max(monthly_rainfall), "mm")
    print("Mean:", np.mean(monthly_rainfall), "mm")

print("\nInspection completed.")
