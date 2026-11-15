
import pandas as pd

state_file = "data/processed/regional_timeseries/cdd_state_monthly.csv"
india_file = "data/processed/regional_timeseries/cdd_india_monthly.csv"

states = pd.read_csv(state_file)
india = pd.read_csv(india_file)

print("========== STATE/UT COVERAGE ==========")

summary = states.groupby("state_ut").agg(
    months=("date", "nunique"),
    records=("date", "size"),
    min_grid_cells=("valid_grid_cells", "min"),
    max_grid_cells=("valid_grid_cells", "max"),
    missing_means=("mean_CDD", lambda x: x.isna().sum())
).reset_index()

print(summary.to_string(index=False))

print("\n========== OVERALL CHECKS ==========")
print("Unique states/UTs:", states["state_ut"].nunique())
print("Expected monthly records:", 36 * 561)
print("Actual monthly records:", len(states))
print("Duplicate state-month rows:",
      states.duplicated(["state_ut", "date"]).sum())
print("India monthly records:", len(india))
print("Duplicate India months:", india["date"].duplicated().sum())
print("States with fewer than 561 months:",
      (summary["months"] < 561).sum())
print("States with zero grid cells:",
      (summary["max_grid_cells"] == 0).sum())
