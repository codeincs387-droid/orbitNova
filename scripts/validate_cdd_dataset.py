
from pathlib import Path
import calendar

import numpy as np
import pandas as pd
import xarray as xr

DATA_DIR = Path("data/processed/monthly_grid/cdd")
OUTPUT_DIR = Path("data/processed/regional_timeseries")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

files = sorted(DATA_DIR.glob("CDD_India_*.nc"))

if not files:
    raise FileNotFoundError(f"No CDD NetCDF files found in {DATA_DIR}")

records = []
reference_lat = None
reference_lon = None
errors = []

for index, file in enumerate(files, start=1):
    try:
        with xr.open_dataset(file) as ds:
            if "CDD" not in ds:
                raise ValueError("CDD variable is missing")

            if not all(name in ds.coords for name in ["time", "lat", "lon"]):
                raise ValueError("Missing time, lat or lon coordinate")

            values = ds["CDD"]

            if not all(dim in values.dims for dim in ["time", "lat", "lon"]):
                raise ValueError(f"Unexpected CDD dimensions: {values.dims}")

            if values.sizes["time"] != 1:
                raise ValueError("Expected exactly one time step")

            lat = ds["lat"].values
            lon = ds["lon"].values

            if reference_lat is None:
                reference_lat = lat.copy()
                reference_lon = lon.copy()
            else:
                if not np.array_equal(reference_lat, lat):
                    raise ValueError("Latitude grid differs")
                if not np.array_equal(reference_lon, lon):
                    raise ValueError("Longitude grid differs")

            timestamp = pd.Timestamp(ds["time"].values[0])

            expected_month = file.stem[-6:]
            actual_month = timestamp.strftime("%Y%m")

            if expected_month != actual_month:
                raise ValueError(
                    f"Filename month {expected_month} "
                    f"does not match timestamp {actual_month}"
                )

            array = values.squeeze("time").values
            valid = np.isfinite(array)

            valid_values = array[valid]

            if valid_values.size == 0:
                raise ValueError("No valid CDD grid-cell values")

            year = timestamp.year
            month = timestamp.month
            max_allowed = calendar.monthrange(year, month)[1]

            invalid_values = (
                (valid_values < 0) |
                (valid_values > max_allowed)
            )

            records.append({
                "file": file.name,
                "date": timestamp.strftime("%Y-%m-%d"),
                "year": year,
                "month": month,
                "latitude_cells": len(lat),
                "longitude_cells": len(lon),
                "total_cells": array.size,
                "valid_cells": int(valid.sum()),
                "missing_cells": int((~valid).sum()),
                "minimum_CDD": float(valid_values.min()),
                "maximum_CDD": float(valid_values.max()),
                "mean_CDD": float(valid_values.mean()),
                "invalid_value_count": int(invalid_values.sum()),
                "status": "PASS" if not invalid_values.any() else "CHECK"
            })

    except Exception as exc:
        errors.append({"file": file.name, "error": str(exc)})

    if index % 50 == 0 or index == len(files):
        print(f"Checked {index}/{len(files)} files")

report = pd.DataFrame(records)
report_path = OUTPUT_DIR / "cdd_validation_report.csv"
report.to_csv(report_path, index=False)

print("\n========== CDD VALIDATION SUMMARY ==========")
print(f"Files found: {len(files)}")
print(f"Files successfully inspected: {len(records)}")
print(f"Files with errors: {len(errors)}")

if not report.empty:
    print(f"Grid dimensions: {report['latitude_cells'].iloc[0]} x "
          f"{report['longitude_cells'].iloc[0]}")
    print(f"Files with invalid CDD values: "
          f"{(report['invalid_value_count'] > 0).sum()}")

if errors:
    print("\nERRORS:")
    for item in errors:
        print(item)

print(f"\nValidation report saved to: {report_path}")
