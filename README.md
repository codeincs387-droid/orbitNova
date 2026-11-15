orbitNova
India Climate Data Processing and Visualization

orbitNova is a Python-based project for processing NASA MERRA-2 climate datasets, extracting India-specific gridded data, generating monthly regional statistics for Indian states and union territories (UTs), and visualizing the results through an interactive web dashboard.

The project currently supports two climate variables:

CDD (Cooling Degree Days): Used to analyze cooling demand and temperature-related climate patterns.
T2M (2-Metre Air Temperature): Monthly average near-surface air temperature from NASA MERRA-2.

The processed datasets are extracted for India and used to generate monthly statistics at both state/UT and national levels.

1. Project Structure

The project follows this directory structure:

text
orbitNova/
├── data/
│   ├── processed/
│   │   └── regional_timeseries/
│   │       ├── cdd_india_monthly.csv
│   │       ├── cdd_state_monthly.csv
│   │       ├── cdd_validation_report.csv
│   │       ├── t2m_india_monthly.csv
│   │       ├── t2m_missing_months.txt
│   │       ├── t2m_state_monthly.csv
│   │       └── t2m_validation_report.csv
│   └── reference/
│       └── india_states_ut.geojson
├── docs/
│   └── PHASE_3_CDD_REPORT.md
├── pixi.lock
├── pixi.toml
├── README.md
├── scripts/
│   ├── CDD/
│   │   ├── analyze_cdd_by_state.py
│   │   ├── check_cdd_regional_output.py
│   │   ├── check_cdd_versions.py
│   │   ├── download_all_cdd.py
│   │   ├── download_cdd_test.py
│   │   ├── extract_india_cdd.py
│   │   ├── extract_india_cdd_v2.py
│   │   ├── inspect_cdd.py
│   │   ├── inspect_india_boundaries.py
│   │   └── validate_cdd_dataset.py
│   └── T2M/
│       ├── 01_check_collection.py
│       ├── 02_download_test.py
│       ├── 03_inspect_test.py
│       ├── 04_extract_test.py
│       ├── 05_download_all.py
│       ├── 06_validate_output.py
│       ├── process_t2m_india.py
│       └── process_t2m_regions.py
└── UI/
    ├── dashboard.js
    ├── index.html
    ├── leaflet.css
    ├── leaflet.js
    └── map.js

2. Requirements and Environment Setup
Prerequisites
Python 3
Pixi for Python environment and dependency management
NASA Earthdata account
Internet connection for downloading NASA datasets and loading online map tiles
Clone or open the project

Open the project directory in your terminal:

bash
cd orbitNova


Install the project environment and dependencies:

bash
pixi install


All Python scripts should be executed from the project root directory using pixi run.

NASA Earthdata Authentication

The CDD and T2M download scripts retrieve data from NASA Earthdata.

You must have a valid NASA Earthdata account and complete authentication when prompted by the download scripts.

3. CDD Data Processing Workflow

The CDD workflow downloads NASA MERRA-2 Cooling Degree Days datasets, extracts the India geographical region, validates the processed data, and generates monthly statistics for India and individual states/UTs.

Execution Order

All scripts in this workflow are located inside scripts/CDD/.

Step 1. Check NASA dataset version
bash
pixi run python scripts/CDD/check_cdd_versions.py


Checks the available MERRA-2 CDD collection and its version.

Step 2. Download a sample CDD file
bash
pixi run python scripts/CDD/download_cdd_test.py


Downloads a sample CDD dataset from NASA Earthdata.

Log in using your NASA Earthdata account when prompted.

Step 3. Inspect the sample dataset
bash
pixi run python scripts/CDD/inspect_cdd.py


Inspects the downloaded NetCDF file, including:

Collection information
Dataset date
CDD variable
Variable dimensions
Units and metadata

Run Step 2 before this step.

Step 4. Test India-region extraction
bash
pixi run python scripts/CDD/extract_india_cdd_v2.py


Extracts the India geographical region from the sample NetCDF file and saves the extracted result.

Step 5. Download and extract all CDD datasets
bash
pixi run python scripts/CDD/download_all_cdd.py


Downloads the available historical monthly CDD datasets from NASA Earthdata and extracts the India region into individual NetCDF files.

Step 6. Validate the extracted datasets
bash
pixi run python scripts/CDD/validate_cdd_dataset.py


Checks the downloaded and extracted files for:

Missing data
Invalid values
Coordinate consistency
Monthly data coverage

Complete validation before proceeding with regional analysis.

Step 7. Inspect India state and UT boundaries
bash
pixi run python scripts/CDD/inspect_india_boundaries.py


Inspects the India state/UT GeoJSON boundary file, including:

Feature count
Coordinate reference system
Geometry validity
Boundary information

The boundary file is:

text
data/reference/india_states_ut.geojson

Step 8. Generate state/UT and India-level statistics
bash
pixi run python scripts/CDD/analyze_cdd_by_state.py


Processes the monthly CDD grids and generates regional statistics for:

Individual Indian states
Union territories
India as a whole

The results are saved in:

text
data/processed/regional_timeseries/

Step 9. Check the final regional outputs
bash
pixi run python scripts/CDD/check_cdd_regional_output.py


Checks the generated regional CSV files for:

Regional coverage
Duplicate records
Missing values
Valid grid-cell counts
4. T2M Data Processing Workflow

The T2M workflow processes NASA MERRA-2 2-metre air temperature data from the M2TMNXSLV collection, version 5.12.4.

The workflow downloads monthly temperature datasets, extracts the India region, converts temperature from Kelvin to Celsius, and calculates area-weighted temperature statistics for India and its states/UTs.

All scripts in this workflow are located inside scripts/T2M/.

Execution Order
Step 1. Check NASA dataset collection
bash
pixi run python scripts/T2M/01_check_collection.py


Searches NASA Earthdata for the MERRA-2 temperature collection (M2TMNXSLV).

Prints the matching collection's:

Short name
Version
Concept ID
Title
Abstract
Summary

Stops with an error if the collection is not found.

Step 2. Download a sample T2M file
bash
pixi run python scripts/T2M/02_download_test.py


Logs in to NASA Earthdata and downloads up to 10 monthly granules for January 2020.

The downloaded files are saved in:

text
data/raw/merra2/temperature/


Enter your NASA Earthdata account details when prompted.

Step 3. Inspect the sample dataset
bash
pixi run python scripts/T2M/03_inspect_test.py


Opens the first .nc4 file in the raw data folder and prints:

Dataset structure
Available variables
T2M dimensions and shape
Units
Latitude and longitude ranges
Time information

Run Step 2 before this step.

Step 4. Test India-region extraction
bash
pixi run python scripts/T2M/04_extract_test.py


Extracts the India geographical bounding box:

Parameter	Range
Latitude	5°–38° N
Longitude	67°–99° E

Handles both ascending and descending latitude coordinates.

Saves the extracted compressed NetCDF file in:

text
data/processed/monthly_grid/temperature/


The output filename follows this format:

text
T2M_India_YYYYMM.nc

Step 5. Download and extract all T2M datasets
bash
pixi run python scripts/T2M/05_download_all.py


Downloads monthly T2M granules from 2000-01-01 up to the current date.

The script:

Downloads one monthly granule at a time.
Retries failed downloads up to three times.
Extracts the India geographical region.
Validates the extracted output.
Deletes the large raw file after successful extraction.
Retains raw files if extraction fails.

Download activity is logged in:

text
reports/download_log.csv


Processed monthly NetCDF files are saved in:

text
data/processed/monthly_grid/temperature/

Step 6. Validate the extracted datasets
bash
pixi run python scripts/T2M/06_validate_output.py


This script is intended to validate all processed monthly files for:

Missing months
Invalid values
Coordinate consistency
Monthly coverage

Note: The validation script is currently empty. Validation will not be performed until its logic is implemented.

Step 7. Convert to Celsius and generate state/UT and India-level statistics
bash
pixi run python scripts/T2M/process_t2m_india.py


Reads the monthly NetCDF files generated in Step 5.

The script:

Converts temperature from Kelvin to Celsius.
Saves India-only monthly NetCDF files using the variable T2M_C.
Builds state/UT geographical masks using the GeoJSON boundary file.
Calculates area-weighted mean, median, minimum, and maximum temperatures.
Generates monthly statistics for India and every state/UT.

The India-only Celsius NetCDF files are saved in:

text
data/processed/monthly_grid/temperature_india/


The expected processing period is:

text
2000-01 to 2026-09


Months outside this period are skipped.

Months with duplicate records or implausible temperatures (below -100 °C or above 70 °C) are reported as errors.

The regional CSV and validation outputs are saved in:

text
data/processed/regional_timeseries/

Step 8. Re-generate regional statistics from the Celsius grids (optional)
bash
pixi run python scripts/T2M/process_t2m_regions.py


Reads the T2M_India_YYYYMM.nc files generated in Step 7.

The script:

Rebuilds the state/UT geographical masks.
Recalculates area-weighted mean temperatures.
Calculates valid grid-cell counts for India and each state/UT.
Generates a validation report.
Generates a missing-months report.

Important: Step 8 overwrites the regional reports generated by Step 7.

The Step 8 CSV files contain fewer statistical columns (mean temperature and valid grid cells), use state instead of state_ut, and use the YYYYMM date format instead of YYYY-MM.

Skip Step 8 if you need the median, minimum, and maximum temperature statistics generated by Step 7.

5. Regional Output Files

Both CDD and T2M workflows generate regional outputs inside:

text
data/processed/regional_timeseries/

CDD Outputs
File	Description
cdd_india_monthly.csv	Monthly CDD statistics for India as a whole
cdd_state_monthly.csv	Monthly CDD statistics for individual states and UTs
cdd_validation_report.csv	Validation information for processed CDD datasets
T2M Outputs
File	Description
t2m_india_monthly.csv	Monthly temperature statistics for India
t2m_state_monthly.csv	Monthly temperature statistics for each state/UT
t2m_validation_report.csv	Per-file status, valid grid cells, and temperature range
t2m_missing_months.txt	Months missing from the expected January 2000 to September 2026 range

The T2M processing scripts also generate intermediate monthly NetCDF datasets in:

text
data/processed/monthly_grid/temperature/
data/processed/monthly_grid/temperature_india/


These intermediate files are required for regional analysis.

6. India State and UT Boundary Data

Both workflows use the same geographical reference file:

text
data/reference/india_states_ut.geojson


This file contains the geographical boundaries of Indian states and union territories.

The GeoJSON file must contain a property/column named:

text
shapeName


The shapeName values are used to identify individual states and union territories during regional analysis.

Make sure the boundary file is available before running the CDD or T2M regional processing scripts.

7. Running the Dashboard Locally

The project includes an interactive web dashboard inside the UI/ directory.

The dashboard visualizes the processed climate data using an interactive map.

Step 1. Navigate to the UI directory

From the project root:

bash
cd UI

Step 2. Start a local web server

Run:

bash
python3 -m http.server 8080

Step 3. Open the dashboard

Open the following URL in your browser:

text
http://localhost:8080


Important: Always run the dashboard through a local web server. Do not open index.html by double-clicking it.

Why use a local web server?

Opening index.html directly from disk results in a file:// URL.

When opened this way, map tiles may display an API key required or access blocked warning, or fail to load entirely.

The map tile providers (OpenStreetMap and CARTO) may check the HTTP Referer header to validate requests.

A page opened through file:// does not send the expected HTTP Referer information.

Serving the dashboard through:

bash
python3 -m http.server 8080


allows the browser to access it through http://localhost, enabling the required HTTP requests.

Dashboard Troubleshooting

Map looks incorrect after editing map.js:

Perform a hard refresh:

macOS: Cmd + Shift + R
Windows/Linux: Ctrl + Shift + R

Blank map:

Open the browser developer console:

macOS: Cmd + Option + J
Windows/Linux: F12

Check for JavaScript errors.

Map tiles do not load:

Check your internet connection.
Make sure the local web server is running.
Check the browser console for network or tile-loading errors.
Leaflet and the online map tiles require internet access unless bundled locally.
8. Important Notes and Recommendations
Always execute Python scripts from the orbitNova project root.
Use pixi run python to execute scripts within the project environment.
Complete NASA Earthdata authentication before running download scripts.
The sample download and extraction steps can be skipped if sample datasets have already been downloaded and inspected.
Complete the relevant validation steps before performing regional analysis.
Ensure data/reference/india_states_ut.geojson is available before running state/UT analysis.
The full historical download can take considerable time depending on network speed and NASA Earthdata availability.
Do not delete intermediate monthly NetCDF files before completing regional analysis.
The T2M processing period is currently configured for January 2000 to September 2026. Update END_DATE and EXPECTED_MONTHS in the relevant scripts if the study period changes.
Running process_t2m_regions.py after process_t2m_india.py overwrites the T2M regional CSV and report files with a reduced set of statistics.
Run the dashboard using a local HTTP server rather than opening the HTML file directly.
9. Recommended Execution Sequence

The following summarizes the recommended execution order for both climate variables.

CDD Workflow
Check NASA CDD collection and version.
Download a sample CDD dataset.
Inspect the sample dataset.
Test India-region extraction.
Download and extract all monthly CDD datasets.
Validate the extracted CDD datasets.
Inspect India state/UT boundaries.
Generate state/UT and India-level CDD statistics.
Check the final regional outputs.
T2M Workflow
Check the NASA MERRA-2 T2M collection.
Download a sample T2M dataset.
Inspect the sample dataset.
Test India-region extraction.
Download and extract all monthly T2M datasets.
Validate the extracted T2M datasets (after implementing the validation script).
Convert temperature to Celsius and generate regional statistics.
Optionally regenerate regional statistics from the Celsius grids.
Dashboard

After the regional CSV files have been generated:

bash
cd UI
python3 -m http.server 8080


Open:

text
http://localhost:8080

10. Project Documentation

Additional project documentation is available in:

text
docs/PHASE_3_CDD_REPORT.md


This document contains supplementary information about the CDD analysis.

Project Summary

The orbitNova project provides an integrated workflow for processing and visualizing NASA MERRA-2 climate data over India.

It combines:

NASA Earthdata integration for retrieving historical climate datasets.
NetCDF processing for extracting and managing monthly gridded climate data.
Geospatial analysis for identifying Indian states and union territories.
Statistical analysis for calculating regional and national climate indicators.
Data validation for checking monthly coverage and dataset consistency.
Interactive visualization through a locally hosted web dashboard.

The final outputs support the analysis of monthly Cooling Degree Days and 2-metre air temperature patterns across India at both national and state/UT levels.
