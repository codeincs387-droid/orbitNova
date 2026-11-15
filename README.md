# orbitNova
# Running the Python Scripts

Follow these steps in order to execute the CDD data-processing workflow.

First, open the project directory in your terminal:

```bash
cd orbitNova
```

Activate the project environment:

```bash
pixi install
```

## Execution Order

### 1. Check NASA dataset version

```bash
pixi run python scripts/check_cdd_versions.py
```

Checks the available MERRA-2 CDD collection and its version.

### 2. Download a sample CDD file

```bash
pixi run python scripts/download_cdd_test.py
```

Downloads one sample dataset from NASA Earthdata. Log in using your NASA Earthdata account when prompted.

### 3. Inspect the sample dataset

```bash
pixi run python scripts/inspect_cdd.py
```

Checks the downloaded file, collection information, date, CDD variable, and units.

### 4. Test India-region extraction

```bash
pixi run python scripts/extract_india_cdd_v2.py
```

Extracts the India geographical region from the sample NetCDF file and saves the result.

### 5. Download and extract all CDD datasets

```bash
pixi run python scripts/download_all_cdd.py
```

Downloads the available historical CDD monthly datasets and extracts the India region into individual NetCDF files.

### 6. Validate the extracted datasets

```bash
pixi run python scripts/validate_cdd_dataset.py
```

Checks the downloaded files for missing data, invalid values, coordinate consistency, and monthly coverage.

### 7. Inspect India state and UT boundaries

```bash
pixi run python scripts/inspect_india_boundaries.py
```

Checks the GeoJSON boundary file, feature count, coordinate reference system, and geometry validity.

### 8. Generate state/UT and India-level statistics

```bash
pixi run python scripts/analyze_cdd_by_state.py
```

Processes the monthly CDD grids and generates regional statistics for each state/UT and India as a whole.

### 9. Check the final regional outputs

```bash
pixi run python scripts/check_cdd_regional_output.py
```

Checks regional coverage, duplicate records, missing values, and valid grid-cell counts.

---

## Important Notes

- Run the scripts from the project root directory (`orbitNova`).
- Complete the NASA Earthdata login before downloading datasets.
- Steps 2–4 are sample-testing steps. They can be skipped if the sample data has already been downloaded and inspected.
- Run the validation script before regional analysis.
- Make sure `data/reference/india_states_ut.geojson` is available before Step 8.
- The bulk download can take time depending on network speed and data availability.
- Do not delete the generated monthly NetCDF files before completing regional analysis.

**Final output:** The regional CSV files are generated inside:

```text
data/processed/regional_timeseries/
```