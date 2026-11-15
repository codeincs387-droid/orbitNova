# Phase 3 — CDD Regional Processing & Data Quality Report

## 1. Dataset Overview

**Dataset:** NASA MERRA-2 — Consecutive Dry Days (CDD)  
**Collection:** M2SMNXEDI  
**Version:** V2  
**Variable:** CDD  
**Unit:** Count (days)  
**Spatial resolution:** 0.5° latitude × 0.625° longitude  
**Study area:** India  
**Historical coverage:** January 1980 – September 2026  
**Total monthly records:** 561

CDD represents the maximum number of consecutive days in a month with daily precipitation below 1 mm.

## 2. Data Processing

The following steps were completed:

1. Downloaded monthly CDD NetCDF files from NASA Earthdata.
2. Selected the India geographical bounding box.
3. Extracted the India-region grid while retaining monthly time and spatial coordinates.
4. Validated all extracted monthly NetCDF files.
5. Loaded the India state and union territory boundary dataset.
6. Generated state/UT-level monthly CDD statistics.
7. Generated India-wide monthly CDD statistics.
8. Checked regional record coverage and missing values.

## 3. Data Quality Results

| Validation | Result |
|---|---|
| Monthly files extracted | 561 |
| Expected monthly coverage | 561 |
| Missing months | 0 |
| NetCDF validation errors | 0 |
| Invalid CDD values | 0 |
| Regional records | 20,196 |
| India-wide monthly records | 561 |
| Missing India-wide CSV values | 0 |

The extracted India grid contains 67 latitude points and 51 longitude points.

## 4. Regional Coverage

The administrative boundary dataset contains 36 state and union territory features.

Six regions had zero valid grid-cell centres at the native MERRA-2 resolution:

- Chandigarh
- Delhi
- Dadra and Nagar Haveli and Daman and Diu
- Goa
- Lakshadweep
- Puducherry

These regions will be excluded from state-level statistical analysis because the available grid resolution does not provide sufficient spatial coverage.

Andaman and Nicobar Islands has only one valid grid cell and will be flagged as having very limited spatial representation.

Missing regional values are not replaced with zero.

## 5. Statistical Processing Method

For each region, the following monthly statistics were generated:

- Mean CDD
- Median CDD
- Maximum CDD
- Number of valid grid cells

The regional mean uses cosine-of-latitude weighting to account approximately for differences in grid-cell area.

India-wide statistics were generated from the union of state/UT grid-centre masks.

## 6. Output Files

**Processed monthly grid:**
`data/processed/monthly_grid/cdd/`

**State/UT monthly statistics:**
`data/processed/regional_timeseries/cdd_state_monthly.csv`

**India-wide monthly statistics:**
`data/processed/regional_timeseries/cdd_india_monthly.csv`

**NetCDF validation report:**
`data/processed/regional_timeseries/cdd_validation_report.csv`

**Administrative boundaries:**
`data/reference/india_states_ut.geojson`

## 7. Limitations

1. MERRA-2 has a relatively coarse spatial resolution. Small states and union territories may not contain a valid grid-cell centre.
2. Andaman and Nicobar Islands has only one valid grid cell, limiting the reliability of its regional average.
3. State-level averages represent gridded estimates, not direct weather-station observations.
4. The administrative boundary dataset is based on a 2011 boundary vintage.
5. Grid-cell-centre masking is an approximation; fractional polygon-cell overlap was not calculated.
6. The India bounding box includes areas outside India's land boundary. Regional analysis uses administrative polygon masks to limit the calculation to the represented land regions.

## 8. Phase 3 Status

**Status: Completed with documented spatial coverage limitations.**

The historical CDD dataset has been downloaded, extracted, validated and processed into India-wide and state/UT-level monthly datasets.

The resulting datasets are prepared for the next stage: historical trend analysis.

---

*Project: Be An Earth System Trend Detective! — NASA Space Apps Challenge 2026*
