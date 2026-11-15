
from pathlib import Path
import xarray as xr
import numpy as np
import pandas as pd

data_dir = Path("data/processed/monthly_grid/prectot")

start = pd.Period("2000-01", freq="M")
end = pd.Period("2026-09", freq="M")
expected_months = pd.period_range(start, end, freq="M")

print("Validating PRECTOT monthly dataset...")
print("Folder:", data_dir)

if not data_dir.exists():
    raise FileNotFoundError(f"Folder not found: {data_dir}")

files = sorted(data_dir.glob("PRECTOT_India_*.nc"))

print("\nFiles found:", len(files))
print("Expected months:", len(expected_months))

# Extract month labels from filenames
file_months = {}

for file in files:
    label = file.stem.replace("PRECTOT_India_", "")

    try:
        month = pd.Period(label, freq="M")
        file_months.setdefault(month, []).append(file)
    except Exception:
        print("Invalid filename:", file.name)

missing = [
    month for month in expected_months
    if month not in file_months
]

unexpected = [
    month for month in file_months
    if month not in expected_months
]

duplicates = [
    month for month, matches in file_months.items()
    if len(matches) > 1
]

print("\n--- MONTH COVERAGE ---")
print("Missing months:", len(missing))
print("Unexpected months:", len(unexpected))
print("Duplicate months:", len(duplicates))

if missing:
    print("Missing:", [str(m) for m in missing])

if unexpected:
    print("Unexpected:", [str(m) for m in unexpected])

if duplicates:
    print("Duplicates:", [str(m) for m in duplicates])

# Validate every expected monthly file
valid_files = 0
invalid_files = 0
report = []

for month in expected_months:
    matches = file_months.get(month, [])

    if len(matches) != 1:
        continue

    file = matches[0]

    try:
        with xr.open_dataset(file) as ds:

            if "PRECTOT" not in ds:
                raise ValueError("PRECTOT variable missing")

            data = ds["PRECTOT"]

            if data.dims != ("time", "lat", "lon"):
                raise ValueError(f"Unexpected dimensions: {data.dims}")

            values = data.values.astype(float)
            finite = np.isfinite(values)

            valid_count = int(finite.sum())
            invalid_count = int((~finite).sum())

            if valid_count == 0:
                raise ValueError("No valid data values")

            if np.any(values[finite] < 0):
                raise ValueError("Negative precipitation values found")

            units = data.attrs.get("units", "Not specified")

            if units != "mm":
                raise ValueError(f"Unexpected units: {units}")

            valid_files += 1

            report.append({
                "month": str(month),
                "status": "VALID",
                "valid_cells": valid_count,
                "missing_cells": invalid_count,
                "minimum_mm": float(np.nanmin(values)),
                "maximum_mm": float(np.nanmax(values)),
                "mean_mm": float(np.nanmean(values)),
                "units": units
            })

    except Exception as error:
        invalid_files += 1
        report.append({
            "month": str(month),
            "status": f"INVALID: {error}"
        })

report_path = Path("data/processed/prectot_validation_report.csv")
report_path.parent.mkdir(parents=True, exist_ok=True)

pd.DataFrame(report).to_csv(report_path, index=False)

print("\n--- FILE VALIDATION ---")
print("Valid files:", valid_files)
print("Invalid files:", invalid_files)
print("Validation report:", report_path)

print("\n========== FINAL SUMMARY ==========")
print("Expected months:", len(expected_months))
print("Files found:", len(files))
print("Missing months:", len(missing))
print("Valid files:", valid_files)
print("Invalid files:", invalid_files)

if (
    len(missing) == 0
    and len(unexpected) == 0
    and len(duplicates) == 0
    and valid_files == len(expected_months)
    and invalid_files == 0
):
    print("\nSUCCESS: PRECTOT dataset validation passed.")
else:
    print("\nWARNING: Dataset needs further inspection.")
