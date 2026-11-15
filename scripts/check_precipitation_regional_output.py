
from pathlib import Path
import pandas as pd

output_dir = Path("data/processed/regional_timeseries")

state_file = output_dir / "prectot_state_monthly.csv"
india_file = output_dir / "prectot_india_monthly.csv"

state_df = pd.read_csv(state_file)
india_df = pd.read_csv(india_file)

print("========== STATE/UT DATASET ==========")
print("Rows:", len(state_df))
print("Unique states/UTs:", state_df["state_code"].nunique())
print("Unique months:", state_df["date"].nunique())
print("Date range:", state_df["date"].min(), "to", state_df["date"].max())
print("Missing mean values:", state_df["mean_PRECTOT_mm"].isna().sum())
print("Negative mean values:", (state_df["mean_PRECTOT_mm"].dropna() < 0).sum())
print("Missing grid-cell records:", (state_df["valid_grid_cells"] == 0).sum())

print("\n========== INDIA DATASET ==========")
print("Rows:", len(india_df))
print("Date range:", india_df["date"].min(), "to", india_df["date"].max())
print("Missing mean values:", india_df["mean_PRECTOT_mm"].isna().sum())
print("Negative mean values:", (india_df["mean_PRECTOT_mm"].dropna() < 0).sum())

print("\n========== SAMPLE INDIA RECORDS ==========")
print(india_df.head())

print("\n========== FINAL CHECK ==========")

if (
    len(state_df) == 11556
    and state_df["state_code"].nunique() == 36
    and state_df["date"].nunique() == 321
    and len(india_df) == 321
    and india_df["mean_PRECTOT_mm"].notna().all()
    and (india_df["mean_PRECTOT_mm"] >= 0).all()
):
    print("SUCCESS: Regional PRECTOT outputs passed basic checks.")
else:
    print("WARNING: Please inspect the regional outputs.")
