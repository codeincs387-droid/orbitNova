from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
from rasterio.features import geometry_mask
from rasterio.transform import from_origin

# ==================================================
# 1. PATHS AND SETTINGS
# ==================================================

# Member 2's downloaded files
RAW_DIR = Path("data/processed/monthly_grid/temperature")

# India state and UT boundaries
BOUNDARY_FILE = Path("data/reference/india_states_ut.geojson")

# Separate output folder to protect original downloads
GRID_DIR = Path("data/processed/monthly_grid/temperature_india")

REPORT_DIR = Path("data/processed/regional_timeseries")

GRID_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = pd.Timestamp("2000-01-01")
END_DATE = pd.Timestamp("2026-09-01")

# India bounding box
WEST, EAST = 67.0, 99.0
SOUTH, NORTH = 5.0, 38.0

# ==================================================
# 2. CHECK INPUT FILES
# ==================================================

if not RAW_DIR.exists():
    raise FileNotFoundError(f"Input folder not found: {RAW_DIR}")

if not BOUNDARY_FILE.exists():
    raise FileNotFoundError(f"Boundary file not found: {BOUNDARY_FILE}")

files = sorted(
    list(RAW_DIR.glob("*.nc4")) +
    list(RAW_DIR.glob("*.nc"))
)

if not files:
    raise FileNotFoundError("No NetCDF files found.")

print("=" * 55)
print("T2M INDIA PROCESSING")
print("=" * 55)
print("Input files:", len(files))

# ==================================================
# 3. LOAD INDIA STATE BOUNDARIES
# ==================================================

gdf = gpd.read_file(BOUNDARY_FILE).to_crs("EPSG:4326")

print("State/UT features:", len(gdf))

state_masks = {}
lat = None
lon = None
weights = None
india_mask = None
transform = None

# ==================================================
# 4. PREPARE OUTPUT RECORDS
# ==================================================

state_rows = []
india_rows = []
validation_rows = []

processed_months = set()

# ==================================================
# 5. PROCESS EACH NETCDF FILE
# ==================================================

for file in files:

    print(f"\nProcessing: {file.name}")

    try:

        with xr.open_dataset(file) as source:

            if "T2M" not in source.data_vars:
                raise ValueError("T2M variable not found")

            if not all(
                coordinate in source.coords
                for coordinate in ["time", "lat", "lon"]
            ):
                raise ValueError("Missing time, lat or lon coordinates")

            for ti in range(source.sizes["time"]):

                date = pd.Timestamp(source["time"].values[ti])

                if date < START_DATE or date > END_DATE:
                    continue

                month = date.strftime("%Y%m")

                if month in processed_months:
                    raise ValueError(f"Duplicate month: {month}")

                # ----------------------------------
                # Extract T2M for this month
                # ----------------------------------

                da = source["T2M"].isel(time=ti).squeeze(drop=True)

                # Handle both 0-360 and -180 to 180
                # longitude coordinate conventions.
                longitude = da["lon"].values

                if longitude.min() >= 0 and longitude.max() > 180:
                    da = da.assign_coords(
                        lon=((da.lon + 180) % 360) - 180
                    )
                    da = da.sortby("lon")

                # Extract India bounding box
                da = da.where(
                    (da.lat >= SOUTH) &
                    (da.lat <= NORTH) &
                    (da.lon >= WEST) &
                    (da.lon <= EAST),
                    drop=True
                )

                # Standardise grid orientation
                da = da.sortby("lat", ascending=False)
                da = da.sortby("lon")

                if da.size == 0:
                    raise ValueError("India subset is empty")

                current_lat = da.lat.values
                current_lon = da.lon.values

                # ----------------------------------
                # Prepare grid and regional masks
                # ----------------------------------

                if lat is None:

                    lat = current_lat
                    lon = current_lon

                    if len(lat) < 2 or len(lon) < 2:
                        raise ValueError("Insufficient grid coordinates")

                    res_lat = abs(float(np.median(np.diff(lat))))
                    res_lon = abs(float(np.median(np.diff(lon))))

                    transform = from_origin(
                        lon.min() - res_lon / 2,
                        lat.max() + res_lat / 2,
                        res_lon,
                        res_lat
                    )

                    # Latitude-based approximate area weights
                    weights = np.broadcast_to(
                        np.cos(np.deg2rad(lat))[:, None],
                        (len(lat), len(lon))
                    )

                    # State/UT masks
                    for _, region in gdf.iterrows():

                        name = region["shapeName"]

                        state_masks[name] = geometry_mask(
                            [region.geometry],
                            out_shape=(len(lat), len(lon)),
                            transform=transform,
                            invert=True,
                            all_touched=False
                        )

                    # Combined India mask
                    india_geometry = gdf.geometry.unary_union

                    india_mask = geometry_mask(
                        [india_geometry],
                        out_shape=(len(lat), len(lon)),
                        transform=transform,
                        invert=True,
                        all_touched=False
                    )

                else:

                    if not (
                        np.array_equal(current_lat, lat) and
                        np.array_equal(current_lon, lon)
                    ):
                        raise ValueError(
                            "Grid coordinates differ between months"
                        )

                # ----------------------------------
                # Convert Kelvin to Celsius
                # ----------------------------------

                values = da.values.astype("float64") - 273.15

                valid = np.isfinite(values)

                if not valid.any():
                    raise ValueError("No valid temperature values")

                minimum = float(values[valid].min())
                maximum = float(values[valid].max())

                if minimum < -100 or maximum > 70:
                    raise ValueError(
                        f"Temperature outside expected range: "
                        f"{minimum:.2f} to {maximum:.2f} C"
                    )

                # ----------------------------------
                # Save India-only NetCDF
                # ----------------------------------

                output_ds = xr.Dataset(
                    {
                        "T2M_C": (
                            ("time", "lat", "lon"),
                            values[np.newaxis, :, :]
                        )
                    },
                    coords={
                        "time": [np.datetime64(date)],
                        "lat": lat,
                        "lon": lon
                    },
                    attrs={
                        "source": "NASA MERRA-2 M2TMNXSLV V5.12.4",
                        "variable": "T2M",
                        "unit": "degrees Celsius",
                        "region": "India bounding box",
                        "processing": "Monthly mean Kelvin converted to Celsius"
                    }
                )

                output_ds["T2M_C"].attrs["units"] = "degC"
                output_ds["T2M_C"].attrs["long_name"] = (
                    "Monthly mean 2-metre air temperature"
                )

                output_file = GRID_DIR / f"T2M_India_{month}.nc"

                output_ds.to_netcdf(output_file)
                output_ds.close()

                # ----------------------------------
                # India-wide statistics
                # ----------------------------------

                india_valid = india_mask & valid

                india_values = values[india_valid]
                india_weights = weights[india_valid]

                if len(india_values) == 0:
                    raise ValueError("No valid India grid cells")

                india_rows.append({
                    "date": date.strftime("%Y-%m"),
                    "mean_T2M_C": float(
                        np.average(
                            india_values,
                            weights=india_weights
                        )
                    ),
                    "median_T2M_C": float(
                        np.median(india_values)
                    ),
                    "minimum_T2M_C": float(
                        np.min(india_values)
                    ),
                    "maximum_T2M_C": float(
                        np.max(india_values)
                    ),
                    "valid_grid_cells": int(
                        india_valid.sum()
                    )
                })

                # ----------------------------------
                # State/UT statistics
                # ----------------------------------

                for name, mask in state_masks.items():

                    region_valid = mask & valid
                    region_values = values[region_valid]

                    if len(region_values) == 0:

                        mean_value = np.nan
                        median_value = np.nan
                        min_value = np.nan
                        max_value = np.nan

                    else:

                        region_weights = weights[region_valid]

                        mean_value = float(
                            np.average(
                                region_values,
                                weights=region_weights
                            )
                        )

                        median_value = float(
                            np.median(region_values)
                        )

                        min_value = float(
                            np.min(region_values)
                        )

                        max_value = float(
                            np.max(region_values)
                        )

                    state_rows.append({
                        "date": date.strftime("%Y-%m"),
                        "state_ut": name,
                        "mean_T2M_C": mean_value,
                        "median_T2M_C": median_value,
                        "minimum_T2M_C": min_value,
                        "maximum_T2M_C": max_value,
                        "valid_grid_cells": int(
                            region_valid.sum()
                        )
                    })

                # ----------------------------------
                # Validation record
                # ----------------------------------

                validation_rows.append({
                    "date": date.strftime("%Y-%m"),
                    "file": file.name,
                    "valid_grid_cells_india": int(
                        india_valid.sum()
                    ),
                    "minimum_T2M_C": minimum,
                    "maximum_T2M_C": maximum,
                    "status": "OK"
                })

                processed_months.add(month)

                print(f"  Completed: {month}")

    except Exception as exc:

        validation_rows.append({
            "date": "",
            "file": file.name,
            "valid_grid_cells_india": 0,
            "minimum_T2M_C": np.nan,
            "maximum_T2M_C": np.nan,
            "status": f"ERROR: {exc}"
        })

        print("  ERROR:", exc)

# ==================================================
# 6. SAVE CSV OUTPUTS
# ==================================================

state_df = pd.DataFrame(state_rows)
india_df = pd.DataFrame(india_rows)
validation_df = pd.DataFrame(validation_rows)

state_path = REPORT_DIR / "t2m_state_monthly.csv"
india_path = REPORT_DIR / "t2m_india_monthly.csv"
validation_path = REPORT_DIR / "t2m_validation_report.csv"

state_df.to_csv(state_path, index=False)
india_df.to_csv(india_path, index=False)
validation_df.to_csv(validation_path, index=False)

# ==================================================
# 7. CHECK MONTHLY COVERAGE
# ==================================================

expected_months = pd.period_range(
    START_DATE,
    END_DATE,
    freq="M"
)

actual_months = {
    pd.Period(month, freq="M")
    for month in processed_months
}

missing_months = sorted(
    expected_months.difference(actual_months)
)

coverage_path = REPORT_DIR / "t2m_missing_months.txt"

with open(coverage_path, "w") as report:

    report.write(
        f"Expected months: {len(expected_months)}\n"
    )

    report.write(
        f"Processed months: {len(processed_months)}\n"
    )

    report.write(
        f"Missing months: {len(missing_months)}\n\n"
    )

    for month in missing_months:
        report.write(str(month) + "\n")

# ==================================================
# 8. FINAL SUMMARY
# ==================================================

error_count = (
    validation_df["status"].str.startswith("ERROR").sum()
    if not validation_df.empty else 0
)

print("\n" + "=" * 55)
print("T2M PROCESSING SUMMARY")
print("=" * 55)

print("Input files:", len(files))
print("Successfully processed months:", len(processed_months))
print("Expected months:", len(expected_months))
print("Missing months:", len(missing_months))
print("Validation errors:", error_count)

if processed_months:
    print("First month:", min(processed_months))
    print("Last month:", max(processed_months))

print("\nOUTPUT FILES")
print("India NetCDF:", GRID_DIR)
print("State CSV:", state_path)
print("India CSV:", india_path)
print("Validation report:", validation_path)
print("Missing months report:", coverage_path)

print("\nPROCESSING FINISHED")
