# Earth Trend Detective

### Discovering Regional Climate Patterns Across India

**Earth Trend Detective** is a climate data analysis and visualization project designed to identify, analyze and understand long-term environmental trends across India.

National climate averages often hide significant regional variations. While temperature, precipitation and dry-day conditions may increase in one region and decrease in another, a single national average cannot adequately represent these differences.

Earth Trend Detective addresses this challenge by transforming large-scale satellite-derived climate datasets into meaningful regional insights through geospatial analysis, statistical trend detection, interactive visualization and predictive modelling.

---

## The Problem We Address

Climate change does not affect every geographical region equally.

- **Regional variations:** Climate indicators can behave differently across states and geographical regions.
- **Hidden climate patterns:** National averages can conceal important local and regional changes.
- **Difficult data interpretation:** Large scientific datasets, particularly NetCDF files, are difficult to interpret without specialized tools.
- **Limited accessibility:** Raw climate datasets do not directly communicate trends in a way that is easy for researchers and decision-makers to understand.
- **Understanding future conditions:** Historical patterns can help identify potential future climate risks, but require careful statistical analysis and predictive modelling.

**Our objective:** Make climate trends easier to discover, understand and interpret at both national and state/UT levels.

---

## Our Solution

We are developing an integrated climate trend detection platform that processes historical climate data, identifies regional patterns and presents the findings through an interactive dashboard.

The platform focuses on three important climate indicators:

| Climate variable | Description             | Unit |
| ---------------- | ----------------------- | ---- |
| T2M              | 2-metre air temperature | °C   |
| PRECTOT          | Total precipitation     | mm   |
| CDD              | Consecutive dry days    | Days |

Using historical climate observations, the system enables users to explore how these indicators change over time and how their trends differ across Indian states and union territories.

---

## Key Features

### 1. Climate Data Processing

- Integration with NASA MERRA-2 climate datasets.
- Downloading and processing scientific NetCDF/NC4 files.
- Extraction of India-specific geographical regions.
- Processing monthly climate observations.
- Conversion and preparation of climate variables for regional analysis.

### 2. Geospatial Analysis

- State-wise and Union Territory-wise climate analysis.
- Integration of Indian geographical boundaries using GeoJSON.
- Regional climate statistics and comparisons.
- Identification of differences between national and regional trends.

### 3. Statistical Trend Detection

The dashboard calculates and displays:

- Long-term climate change.
- Trend slope and rate of change.
- Statistical significance (p-value).
- Coefficient of determination (R²).
- Slope standard error.
- 95% confidence interval.
- Mean, maximum, minimum and standard deviation.

These statistics help distinguish observed trends from ordinary climate variability.

### 4. Interactive Climate Dashboard

Users can:

- Explore climate patterns through an interactive map of India.
- Select temperature, precipitation or dry-day indicators.
- Select different time periods.
- Explore individual states and union territories.
- Visualize historical climate trends through graphs.
- Examine statistical summaries and trend interpretations.

### 5. Predictive Modelling

The project also includes a CDD model-results section.

It provides:

- Actual versus predicted CDD values.
- Model performance evaluation.
- Mean Absolute Error (MAE).
- Root Mean Squared Error (RMSE).
- R² score.
- State-wise model performance.
- Feature importance.
- Actual, predicted and error maps.

The interpretation of the model output depends on its configured prediction lead time.

## &#x20;Data Sources

The project uses NASA's Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2).

**Primary data source:**

- NASA GES DISC: [https://disc.gsfc.nasa.gov/](https://disc.gsfc.nasa.gov/)
- NASA Earthdata: [https://www.earthdata.nasa.gov/](https://www.earthdata.nasa.gov/)

MERRA-2 provides historical atmospheric and climate-related observations that can be used to investigate changes over time.

**Data format:** NetCDF / NC4

**Geographical focus:** India, including individual states and union territories.

**Temporal resolution:** Monthly climate data.

## &#x20;Technology Stack

| Component              | Technologies                    |
| ---------------------- | ------------------------------- |
| Programming language   | Python 3.12                     |
| Data processing        | NumPy, Pandas, SciPy            |
| Climate data handling  | Xarray, NetCDF4, h5netcdf       |
| Geospatial processing  | GeoPandas, GDAL, Rasterio, PROJ |
| Statistical analysis   | SciPy, PyMannKendall            |
| Backend environment    | FastAPI, Uvicorn                |
| Frontend               | HTML, CSS, JavaScript           |
| Interactive maps       | Leaflet.js                      |
| Data visualization     | JavaScript, SVG, HTML Canvas    |
| Environment management | Pixi                            |

## &#x20;Project Architecture

The project follows a data-processing and visualization workflow.

```text
        NASA MERRA-2 DATA
                |
                v
       NetCDF / NC4 FILES
                |
                v
       DATA EXTRACTION
        (India Region)
                |
                v
      CLIMATE DATA PROCESSING
       /        |         \
      /         |          \
 Temperature Precipitation  CDD
      \         |          /
       \        |         /
                v
       GEOSPATIAL ANALYSIS
      (States & Union Territories)
                |
                v
        STATISTICAL ANALYSIS
                |
          +-----+------+
          |            |
          v            v
     TREND ANALYSIS  PREDICTIVE
                     MODELLING
          |            |
          +-----+------+
                |
                v
       INTERACTIVE DASHBOARD
                |
                v
       REGIONAL CLIMATE INSIGHTS
```

## &#x20;Repository Structure

```text
orbitNova/
│
├── UI/
│   ├── dashboard.js
│   ├── map.js
│   ├── leaflet.js
│   └── leaflet.css
│
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── monthly_grid/
│   │   └── regional_timeseries/
│   ├── predictions_cdd/
│   └── reference/
│       └── india_states_ut.geojson
│
├── docs/
│   └── PHASE_3_CDD_REPORT.md
│
├── scripts/
│   ├── CDD/
│   └── T2M/
│
├── index.html
├── pixi.toml
├── pixi.lock
├── LICENSE
└── README.md
```

*Note: Some generated data directories and files are created during processing and may not be present in a fresh clone.*

## &#x20;Installation and Setup

### Prerequisites

Before running the project, install:

- Python 3.12
- Pixi package manager
- Git
- NASA Earthdata account
- A modern web browser

### 1. Clone the repository

```bash
git clone https://github.com/codeincs387-droid/orbitNova.git
```

Navigate into the project:

```bash
cd orbitNova
```

### 2. Install dependencies

```bash
pixi install
```

Pixi automatically creates the project environment using the dependencies specified in `pixi.toml`.

### 3. NASA Earthdata authentication

A valid NASA Earthdata account is required for downloading protected climate datasets.

Visit:

[https://urs.earthdata.nasa.gov/](https://urs.earthdata.nasa.gov/)

Configure your authentication as required by the download scripts.

### 4. Process climate datasets

Execute the relevant processing scripts from the project root.

For example, the CDD workflow:

```bash
pixi run python scripts/CDD/check_cdd_versions.py

pixi run python scripts/CDD/download_cdd_test.py

pixi run python scripts/CDD/inspect_cdd.py

pixi run python scripts/CDD/download_all_cdd.py

pixi run python scripts/CDD/validate_cdd_dataset.py

pixi run python scripts/CDD/analyze_cdd_by_state.py
```

For temperature processing:

```bash
pixi run python scripts/T2M/01_check_collection.py

pixi run python scripts/T2M/02_download_test.py

pixi run python scripts/T2M/03_inspect_test.py

pixi run python scripts/T2M/05_download_all.py

pixi run python scripts/T2M/process_t2m_india.py
```

Run the sample extraction and inspection steps as appropriate before processing the complete datasets.

## &#x20;Running the Dashboard

Once the required processed data files are available, run the application from the project root.

```bash
python -m http.server 8080
```

Open your browser and visit:

```text
http://localhost:8080
```

**Important:** Run the dashboard through a local HTTP server rather than opening `index.html` directly. The application loads its data files using browser fetch requests.

## &#x20;Expected Outputs

The processing workflows generate regional datasets and supporting reports.

Examples include:

| File                        | Purpose                              |
| --------------------------- | ------------------------------------ |
| `t2m_india_monthly.csv`     | Monthly India temperature statistics |
| `t2m_state_monthly.csv`     | State/UT temperature statistics      |
| `cdd_india_monthly.csv`     | Monthly India CDD statistics         |
| `cdd_state_monthly.csv`     | State/UT CDD statistics              |
| `t2m_validation_report.csv` | Temperature data validation          |
| `cdd_validation_report.csv` | CDD data validation                  |

The dashboard also expects precipitation CSV files and CDD prediction results where the corresponding features are used.

---

## Project Impact

Earth Trend Detective aims to make climate information more understandable and accessible.

Potential applications include:

- Identifying regions experiencing significant temperature changes.
- Understanding regional precipitation variations.
- Investigating changing dry-day patterns.
- Supporting climate research and environmental studies.
- Providing useful regional information for climate adaptation and planning.
- Helping users explore climate patterns beyond national averages.

---

## Future Scope

Our planned directions for further development include:

- Expanding climate indicators beyond the current variables.
- Improving predictive modelling and validation.
- Incorporating additional satellite and climate datasets.
- Developing finer geographical analysis, including district-level trends.
- Improving historical and future climate comparisons.
- Enhancing regional climate risk interpretation.
- Making the platform more accessible to researchers and policymakers.

---

## &#x20;Team

**Project:** Earth Trend Detective
**Repository:** [orbitNova](https://github.com/codeincs387-droid/orbitNova)
This repository is maintained through a dedicated team GitHub account created exclusively for this project.

All team members have actively contributed to the development of Earth Trend Detective, collaborating on different aspects of the project, including:

Developed as a team project to investigate regional climate trends and make climate data more meaningful through data science, geospatial technology and interactive visualization.

---

## &#x20;License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

**Earth Trend Detective — Because climate change is not the same everywhere.** 
