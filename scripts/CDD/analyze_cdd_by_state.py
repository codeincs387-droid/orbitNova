
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from rasterio.features import geometry_mask
from rasterio.transform import from_origin

DATA_DIR = Path("data/processed/monthly_grid/cdd")
BOUNDARY_FILE = Path("data/reference/india_states_ut.geojson")
OUTPUT_DIR = Path("data/processed/regional_timeseries")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load state and UT boundaries
states = gpd.read_file(BOUNDARY_FILE).to_crs("EPSG:4326")

# Find monthly CDD files
files = sorted(DATA_DIR.glob("CDD_India_*.nc"))

if not files:
    raise FileNotFoundError("No CDD NetCDF files found.")

state_records = []
india_records = []

reference_lat = None
reference_lon = None
state_masks = None
india_mask = None
weights = None

for file_number, file in enumerate(files, start=1):

    with xr.open_dataset(file) as ds:

        if "CDD" not in ds:
            raise ValueError(f"CDD variable missing: {file.name}")

        da = ds["CDD"].squeeze("time")

        lat = ds["lat"].values
        lon = ds["lon"].values

        # Prepare grid and masks once
        if state_masks is None:

            # Standardize latitude to descending order
            if lat[0] < lat[-1]:
                lat = lat[::-1]
                reverse_lat = True
            else:
                reverse_lat = False

            lon = np.asarray(lon)

            lat_step = abs(float(np.median(np.diff(lat))))
            lon_step = abs(float(np.median(np.diff(lon))))

            transform = from_origin(
                float(lon.min() - lon_step / 2),
                float(lat.max() + lat_step / 2),
                lon_step,
                lat_step
            )

            shape = (len(lat), len(lon))

            state_masks = {}

            for _, state in states.iterrows():
                mask = geometry_mask(
                    [state.geometry],
                    out_shape=shape,
                    transform=transform,
                    invert=True,
                    all_touched=False
                )

                state_masks[state["shapeISO"]] = (
                    state["shapeName"],
                    mask
                )

            india_mask = np.zeros(shape, dtype=bool)

            for _, mask in state_masks.values():
                india_mask |= mask

            # Approximate grid-cell area weighting
            weights = np.cos(np.deg2rad(lat))[:, None]
            weights = np.broadcast_to(weights, shape)

            reference_lat = lat.copy()
            reference_lon = lon.copy()

        else:
            if not np.array_equal(
                np.sort(ds["lat"].values), np.sort(reference_lat)
            ):
                raise ValueError(f"Latitude grid mismatch: {file.name}")

            if not np.array_equal(ds["lon"].values, reference_lon):
                raise ValueError(f"Longitude grid mismatch: {file.name}")

            reverse_lat = ds["lat"].values[0] < ds["lat"].values[-1]

        values = da.values

        if reverse_lat:
            values = values[::-1, :]

        timestamp = pd.Timestamp(ds["time"].values[0])
        month = timestamp.strftime("%Y-%m")

        # State-wise statistics
        for state_code, (state_name, mask) in state_masks.items():

            valid_mask = mask & np.isfinite(values)
            selected = values[valid_mask]

            if selected.size == 0:
                mean_value = np.nan
                median_value = np.nan
                max_value = np.nan
                valid_cells = 0
            else:
                selected_weights = weights[valid_mask]

                mean_value = float(
                    np.average(selected, weights=selected_weights)
                )
                median_value = float(np.median(selected))
                max_value = float(np.max(selected))
                valid_cells = int(selected.size)

            state_records.append({
                "date": month,
                "state_code": state_code,
                "state_ut": state_name,
                "mean_CDD": mean_value,
                "median_CDD": median_value,
                "maximum_CDD": max_value,
                "valid_grid_cells": valid_cells
            })

        # India-wide statistics
        valid_india = india_mask & np.isfinite(values)
        india_values = values[valid_india]

        if india_values.size:
            india_weights = weights[valid_india]

            india_records.append({
                "date": month,
                "mean_CDD": float(
                    np.average(india_values, weights=india_weights)
                ),
                "median_CDD": float(np.median(india_values)),
                "maximum_CDD": float(np.max(india_values)),
                "valid_grid_cells": int(india_values.size)
            })

    if file_number % 50 == 0 or file_number == len(files):
        print(f"Processed {file_number}/{len(files)} months")

# Save results
state_df = pd.DataFrame(state_records)
india_df = pd.DataFrame(india_records)

state_path = OUTPUT_DIR / "cdd_state_monthly.csv"
india_path = OUTPUT_DIR / "cdd_india_monthly.csv"

state_df.to_csv(state_path, index=False)
india_df.to_csv(india_path, index=False)

print("\n========== ANALYSIS COMPLETE ==========")
print("Monthly files processed:", len(files))
print("State/UT features:", len(states))
print("State monthly records:", len(state_df))
print("India monthly records:", len(india_df))
print("State output:", state_path)
print("India output:", india_path)
