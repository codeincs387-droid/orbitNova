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
