import os
import glob
import re
import warnings
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd

from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from shapely.geometry import mapping

warnings.filterwarnings("ignore")

# --------------------------------------------------
# PATHS
# --------------------------------------------------

INPUT_DIR = "data/processed/monthly_grid/temperature_india"
GEOJSON = "data/reference/india_states_ut.geojson"

OUTPUT_DIR = "data/processed/regional_timeseries"

os.makedirs(OUTPUT_DIR, exist_ok=True)

STATE_OUTPUT = os.path.join(
    OUTPUT_DIR, "t2m_state_monthly.csv"
)

INDIA_OUTPUT = os.path.join(
    OUTPUT_DIR, "t2m_india_monthly.csv"
)

VALIDATION_OUTPUT = os.path.join(
    OUTPUT_DIR, "t2m_validation_report.csv"
)

MISSING_OUTPUT = os.path.join(
    OUTPUT_DIR, "t2m_missing_months.txt"
)

# Expected study period
EXPECTED_MONTHS = pd.period_range(
    "2000-01", "2026-09", freq="M"
)

# --------------------------------------------------
# LOAD BOUNDARIES
# --------------------------------------------------

print("\nLoading India state boundaries...")

states = gpd.read_file(GEOJSON)

if "shapeName" not in states.columns:
    raise ValueError(
        f"shapeName not found. Available columns: {states.columns.tolist()}"
    )

states = states.to_crs("EPSG:4326")

print("State/UT features:", len(states))
print("State name column: shapeName")

# --------------------------------------------------
# FIND INPUT FILES
# --------------------------------------------------

files = sorted(
    glob.glob(os.path.join(INPUT_DIR, "T2M_India_*.nc"))
)

print("\nInput files found:", len(files))

# --------------------------------------------------
# GRID INFORMATION
# --------------------------------------------------

if not files:
    raise FileNotFoundError("No India T2M NetCDF files found.")

with xr.open_dataset(files[0]) as sample:
    lat = sample["lat"].values
    lon = sample["lon"].values

    dx = float(np.abs(np.diff(lon)).mean())
    dy = float(np.abs(np.diff(lat)).mean())

    transform = from_origin(
        lon.min() - dx / 2,
        lat.max() + dy / 2,
        dx,
        dy
    )

    print("Grid:", len(lat), "x", len(lon))
    print("Latitude:", lat.min(), "to", lat.max())
    print("Longitude:", lon.min(), "to", lon.max())

# --------------------------------------------------
# BUILD STATE MASKS
# --------------------------------------------------

print("\nBuilding state masks...")

state_masks = {}

for _, row in states.iterrows():

    name = str(row["shapeName"])

    mask = geometry_mask(
        [mapping(row.geometry)],
        out_shape=(len(lat), len(lon)),
        transform=transform,
        invert=True,
        all_touched=False
    )

    state_masks[name] = mask

    print(name, ":", int(mask.sum()), "grid cells")

# India mask: union of state masks
india_mask = np.zeros(
    (len(lat), len(lon)),
    dtype=bool
)

for mask in state_masks.values():
    india_mask |= mask

# Latitude area weights
weights = np.cos(np.deg2rad(lat))[:, None]

# --------------------------------------------------
# HELPER FUNCTION
# --------------------------------------------------

def weighted_mean(values, mask):

    valid = mask & np.isfinite(values)

    count = int(valid.sum())

    if count == 0:
        return np.nan, 0

    selected_weights = np.broadcast_to(
        weights, values.shape
    )[valid]

    selected_values = values[valid]

    mean = np.sum(
        selected_values * selected_weights
    ) / np.sum(selected_weights)

    return float(mean), count


# --------------------------------------------------
# PROCESS MONTHLY FILES
# --------------------------------------------------

state_records = []
india_records = []
validation_records = []

processed_months = set()

print("\nStarting regional processing...\n")

for index, file in enumerate(files, start=1):

    filename = os.path.basename(file)

    match = re.search(r"T2M_India_(\d{6})\.nc$", filename)

    if not match:
        continue

    month = match.group(1)

    try:

        with xr.open_dataset(file) as ds:

            if "T2M_C" not in ds.data_vars:
                raise ValueError(
                    f"T2M_C variable missing. Found: {list(ds.data_vars)}"
                )

            values = ds["T2M_C"].squeeze().values

            if values.shape != (len(lat), len(lon)):
                raise ValueError(
                    f"Unexpected grid shape: {values.shape}"
                )

            if not np.issubdtype(values.dtype, np.number):
                raise ValueError("Temperature data is not numeric")

            if np.isinf(values).any():
                raise ValueError("Infinite temperature values found")

            if np.isfinite(values).sum() == 0:
                raise ValueError("No valid temperature values")

            # Basic plausibility check, not a substitute for metadata validation
            valid_values = values[np.isfinite(values)]

            if valid_values.min() < -100 or valid_values.max() > 70:
                raise ValueError(
                    "Temperature outside broad plausibility range"
                )

            processed_months.add(month)

            # INDIA-WIDE STATISTICS
            india_mean, india_count = weighted_mean(
                values, india_mask
            )

            india_records.append({
                "date": month,
                "mean_T2M_C": india_mean,
                "valid_grid_cells": india_count
            })

            # STATE / UT STATISTICS
            for state_name, mask in state_masks.items():

                mean_temp, count = weighted_mean(
                    values, mask
                )

                state_records.append({
                    "date": month,
                    "state": state_name,
                    "mean_T2M_C": mean_temp,
                    "valid_grid_cells": count
                })

            validation_records.append({
                "file": filename,
                "status": "SUCCESS",
                "valid_grid_cells": int(
                    np.isfinite(values).sum()
                ),
                "minimum_T2M_C": float(valid_values.min()),
                "maximum_T2M_C": float(valid_values.max())
            })

    except Exception as error:

        validation_records.append({
            "file": filename,
            "status": f"ERROR: {error}",
            "valid_grid_cells": 0,
            "minimum_T2M_C": np.nan,
            "maximum_T2M_C": np.nan
        })

    if index % 25 == 0:
        print(f"Processed {index}/{len(files)} files")

# --------------------------------------------------
# SAVE OUTPUTS
# --------------------------------------------------

state_df = pd.DataFrame(state_records)
india_df = pd.DataFrame(india_records)
validation_df = pd.DataFrame(validation_records)

state_df.to_csv(STATE_OUTPUT, index=False)
india_df.to_csv(INDIA_OUTPUT, index=False)
validation_df.to_csv(VALIDATION_OUTPUT, index=False)

# --------------------------------------------------
# CHECK MISSING MONTHS
# --------------------------------------------------

actual_months = {
    pd.Period(month, freq="M")
    for month in processed_months
}

missing_months = sorted(
    set(EXPECTED_MONTHS) - actual_months
)

with open(MISSING_OUTPUT, "w") as report:
    report.write("MISSING T2M MONTHS\n")
    report.write("=================\n\n")

    if missing_months:
        for month in missing_months:
            report.write(str(month) + "\n")
    else:
        report.write("No missing months.\n")

# --------------------------------------------------
# FINAL SUMMARY
# --------------------------------------------------

success_count = (
    validation_df["status"] == "SUCCESS"
).sum()

error_count = len(validation_df) - success_count

print("\n" + "=" * 45)
print("T2M REGIONAL PROCESSING SUMMARY")
print("=" * 45)

print("Input files:", len(files))
print("Successfully processed:", success_count)
print("Processing errors:", error_count)

print("Expected months:", len(EXPECTED_MONTHS))
print("Successfully processed unique months:", len(actual_months))
print("Missing months:", len(missing_months))

print("\nSTATE OUTPUT")
print(STATE_OUTPUT)

print("\nINDIA OUTPUT")
print(INDIA_OUTPUT)

print("\nVALIDATION REPORT")
print(VALIDATION_OUTPUT)

print("\nMISSING MONTH REPORT")
print(MISSING_OUTPUT)

print("\nPROCESSING FINISHED")
