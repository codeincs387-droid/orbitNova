"""
Predict monthly CDD (Consecutive Dry Days: longest dry spell in the month, in days) for every
Indian state/UT, from orbitNova's regional CSVs in data/processed/regional_timeseries/.

Inputs (state x month, one row per state-month; date as YYYY-MM):
    CDD            cdd_state_monthly.csv
    temperature    t2m_state_monthly.csv
    precipitation  prectot_state_monthly.csv
    data/reference/india_states_ut.geojson      (state shapes for maps)

Model
    Two candidates are tuned with time-ordered cross-validation on the TRAINING years only:
    a Random Forest and a Gradient Boosting model. The one with the lower CV error is kept, then
    scored ONCE on the held-out test years (so the reported error is not tuned on the test set).
    The model predicts the departure from each state's monthly average (ANOMALY) and adds it back.

Setup
    LEAD = 0  -> ESTIMATE this month's CDD from this month's temperature and rainfall (plus history).
                 Much more accurate, but it is not a forecast.
    LEAD = 1  -> FORECAST month t from data up to month t-1. Honest forecast, little skill over climatology.
    ANOMALY   -> predict the departure from the training-period monthly average.
Error measures written for the dashboard (test period): MAE and RMSE (days), error rate (total absolute
error as % of total actual CDD), share of predictions within 3 days, R2, and skill vs climatology.

Run (project root):  pixi run python scripts/train_cdd_rf.py
"""
import json, warnings
from pathlib import Path

import geopandas as gpd, joblib, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

# ---------------- settings ----------------
LEAD = 1
USE_CLIMATE = True
USE_PRECIP = True
ANOMALY = True
TRAIN_END, TEST_START, TEST_END = 2015, 2016, 2025
TUNE, N_ITER, MAKE_PNG = True, 10, True

RT = Path("data/processed/regional_timeseries")
FILES = {}        # optional overrides, e.g. {"precip": RT / "prectot_state_monthly.csv"}
VALUE_COL = {}    # optional overrides, e.g. {"precip": "mean_PRECTOT_mm"}
BOUNDARY = Path("data/reference/india_states_ut.geojson")
OUT = Path("data/predictions_cdd"); MODELS = Path("data/models")
for p in (OUT, OUT / "maps", MODELS):
    p.mkdir(parents=True, exist_ok=True)

# ---------------- load state-month CSVs ----------------
def find_csv(name, keys):
    if name in FILES:
        return Path(FILES[name])
    allf = sorted(RT.glob("*.csv"))
    hits = [f for f in allf if any(k in f.name.lower() for k in keys)]
    hits = [f for f in hits if "state" in f.name.lower()] or [f for f in hits if "india" not in f.name.lower()]
    if not hits:
        raise FileNotFoundError(f"No CSV for '{name}' in {RT}; found {[f.name for f in allf]}. Set FILES['{name}'].")
    return hits[0]

def load_state_csv(name, keys):
    f = find_csv(name, keys)
    d = pd.read_csv(f)
    if "state_ut" not in d or "date" not in d:
        raise RuntimeError(f"{f.name}: needs 'date' and 'state_ut' columns; has {list(d.columns)}")
    col = VALUE_COL.get(name) or next((c for c in d.columns if c.lower().startswith("mean_")), None)
    if col is None:
        raise RuntimeError(f"{f.name}: no 'mean_*' column; has {list(d.columns)}. Set VALUE_COL['{name}'].")
    d["date"] = pd.to_datetime(d["date"]).dt.to_period("M").dt.to_timestamp()
    if d.duplicated(["state_ut", "date"]).any():
        raise RuntimeError(f"{f.name}: duplicate state-month rows")
    wide = d.pivot(index="date", columns="state_ut", values=col)
    wide = wide.reindex(pd.date_range(wide.index.min(), wide.index.max(), freq="MS"))   # explicit gaps
    print(f"{name:6s} {f.name}/{col}: {wide.shape[1]} states, {wide.index.min():%Y-%m}..{wide.index.max():%Y-%m}, "
          f"{int(wide.isna().sum().sum())} missing")
    return wide, d

cdd, cdd_long = load_state_csv("cdd", ("cdd",))
codes = cdd_long.drop_duplicates("state_ut").set_index("state_ut")["state_code"].to_dict() \
    if "state_code" in cdd_long else {}
t2m = pr = None
if USE_CLIMATE:
    t2m, _ = load_state_csv("t2m", ("t2m", "temp"))
    if float(np.nanmean(t2m.values)) > 150:
        t2m = t2m - 273.15; print("  T2M converted K -> degC")
    if USE_PRECIP:
        pr, _ = load_state_csv("precip", ("prectot", "precip", "prec", "rain"))
        if float(np.nanmean(pr.values)) < 0.01:      # a rate in kg m-2 s-1
            pr = pr * 86400; print("  precipitation converted kg m-2 s-1 -> mm/day")
        print(f"  precipitation mean {np.nanmean(pr.values):.4g} per month")

# ---------------- features ----------------
def clim_wide(w):
    """Per state and calendar month, the mean over the TRAINING years, laid out like w."""
    tr = w[w.index.year <= TRAIN_END]
    m = tr.groupby(tr.index.month).mean()
    return pd.DataFrame(m.reindex(w.index.month).values, index=w.index, columns=w.columns)

cdd_lags = sorted({max(LEAD, 1) + i for i in range(3)} | {12})
cl_lags = [LEAD + i for i in range(3)]
cdd_an = cdd - clim_wide(cdd)
feats = {"cdd": cdd}
for k in cdd_lags:
    feats[f"cdd_lag{k}"] = cdd.shift(k)
    feats[f"cdd_anom_lag{k}"] = cdd_an.shift(k)
if USE_CLIMATE:
    t2 = t2m.reindex(cdd.index)
    t2_an = t2 - clim_wide(t2)
    for k in cl_lags:
        feats[f"t2m_lag{k}"] = t2.shift(k)
        feats[f"t2m_anom_lag{k}"] = t2_an.shift(k)
    if pr is not None:
        p_ = pr.reindex(cdd.index)
        p_an = p_ - clim_wide(p_)
        for k in cl_lags:
            feats[f"precip_lag{k}"] = p_.shift(k)
            feats[f"precip_anom_lag{k}"] = p_an.shift(k)
        feats["precip_3m"] = p_.shift(LEAD).rolling(3).sum()
        feats["precip_6m"] = p_.shift(LEAD).rolling(6).sum()
        feats["precip_anom_3m"] = p_an.shift(LEAD).rolling(3).sum()

df = pd.concat({k: v.unstack() for k, v in feats.items()}, axis=1)
df.index.names = ["state_ut", "date"]
df = df.dropna().reset_index()

states = gpd.read_file(BOUNDARY).to_crs("EPSG:4326")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    cen = states.to_crs("EPSG:6933").geometry.centroid.to_crs("EPSG:4326")
states["lat"], states["lon"] = cen.y.values, cen.x.values
df = df.merge(states[["shapeName", "lat", "lon"]].rename(columns={"shapeName": "state_ut"}), on="state_ut", how="left")
if df[["lat", "lon"]].isna().any().any():
    print("WARNING: states without a boundary match:", sorted(df[df.lat.isna()].state_ut.unique()))
    df = df.dropna(subset=["lat", "lon"])

df["month"] = df.date.dt.month
df["year"] = df.date.dt.year
df["month_sin"] = np.sin(2 * np.pi * df.month / 12)
df["month_cos"] = np.cos(2 * np.pi * df.month / 12)
df["dim"] = df.date.dt.days_in_month
df = df[df.year <= TEST_END].sort_values(["date", "state_ut"]).reset_index(drop=True)

# Each state's average CDD per calendar month, from the training years only:
# the baseline to beat, and what the model adds its correction to.
clim = df[df.year <= TRAIN_END].groupby(["state_ut", "month"]).cdd.mean().rename("base").reset_index()
df = df.merge(clim, on=["state_ut", "month"], how="left").dropna(subset=["base"])
df = df.sort_values(["date", "state_ut"]).reset_index(drop=True)

PREFIX = ("cdd_lag", "cdd_anom", "t2m_lag", "t2m_anom", "precip_lag", "precip_anom", "precip_3m", "precip_6m")
FEATURES = [c for c in df.columns if c.startswith(PREFIX)]
FEATURES += ["month", "month_sin", "month_cos", "dim", "lat", "lon", "base"]
train, test = df[df.year <= TRAIN_END], df[df.year >= TEST_START]
y_tr = (train.cdd - train.base) if ANOMALY else train.cdd
y_te = (test.cdd - test.base) if ANOMALY else test.cdd
print(f"Lead {LEAD}: {'estimating this month' if LEAD == 0 else 'forecasting ' + str(LEAD) + ' month(s) ahead'}")
print(f"{len(FEATURES)} features:", FEATURES)
print(f"Target: {'anomaly vs monthly climatology' if ANOMALY else 'raw CDD'}")
print(f"Train {len(train):,} rows ({df.year.min()}-{TRAIN_END}); test {len(test):,} rows ({TEST_START}-{TEST_END})")

# ---------------- train: tune both candidates on the training years, keep the better ----------------
cands = {
    "Random Forest": (RandomForestRegressor(n_jobs=-1, random_state=42),
                      {"n_estimators": [200, 300], "min_samples_leaf": [1, 3, 5, 10],
                       "max_features": [0.3, 0.5, 0.8], "max_depth": [None, 10, 20]}),
    "Gradient Boosting": (HistGradientBoostingRegressor(random_state=42),
                          {"learning_rate": [0.03, 0.05, 0.1], "max_iter": [200, 400, 600],
                           "max_leaf_nodes": [15, 31], "min_samples_leaf": [20, 40, 80],
                           "l2_regularization": [0.0, 1.0, 5.0]}),
}
found = {}
for name, (est, grid) in cands.items():
    print(f"Tuning {name} with time-ordered CV on the training period...")
    s = RandomizedSearchCV(est, grid, n_iter=N_ITER if TUNE else 1, cv=TimeSeriesSplit(4),
                           scoring="neg_root_mean_squared_error", random_state=42)
    s.fit(train[FEATURES], y_tr)
    found[name] = s
    print(f"  CV RMSE {-s.best_score_:.3f}  params {s.best_params_}")
MODEL_NAME = min(found, key=lambda n: -found[n].best_score_)
model = found[MODEL_NAME].best_estimator_
print("Selected:", MODEL_NAME)
joblib.dump(model, MODELS / "cdd_state_rf.joblib")

# ---------------- predict + evaluate ----------------
raw = model.predict(df[FEATURES])
df["pred"] = (raw + df.base.values if ANOMALY else raw).clip(0, df.dim.values)   # CDD can't exceed the month's length
df["split"] = np.where(df.year <= TRAIN_END, "train", "test")
df["state_code"] = df.state_ut.map(codes)
df[["date", "state_code", "state_ut", "cdd", "pred", "base", "split"]].rename(
    columns={"cdd": "actual", "pred": "predicted", "base": "climatology"}).to_csv(
    OUT / "cdd_state_predictions.csv", index=False)

def score(d, col):
    e = d[col] - d.cdd
    mean = d.groupby("date")[["cdd", col]].mean()
    return {"n": int(len(d)), "MAE": float(e.abs().mean()), "RMSE": float(np.sqrt((e ** 2).mean())),
            "R2": float(r2_score(d.cdd, d[col])), "mean_R2": float(r2_score(mean.cdd, mean[col])),
            "error_pct": float(100 * e.abs().sum() / max(d.cdd.sum(), 1e-9)),
            "within3": float(100 * (e.abs() <= 3).mean())}

te = df[df.split == "test"]
def rmse(d, c): return float(np.sqrt(((d[c] - d.cdd) ** 2).mean()))
def mae(d, c): return float((d[c] - d.cdd).abs().mean())
per_state = {s: {"rf": rmse(g, "pred"), "base": rmse(g, "base"), "mae": mae(g, "pred"), "mae_base": mae(g, "base"),
                 "wape": float(100 * (g.pred - g.cdd).abs().sum() / max(g.cdd.sum(), 1e-9)),
                 "r2": float(r2_score(g.cdd, g.pred)), "n": int(len(g))} for s, g in te.groupby("state_ut")}
overall = {"rf": score(te, "pred"), "base": score(te, "base")}
overall["skill_pct"] = float(100 * (1 - overall["rf"]["RMSE"] ** 2 / max(overall["base"]["RMSE"] ** 2, 1e-12)))

# feature importance: permutation importance on the held-out test years (same method for any model)
pi = permutation_importance(model, test[FEATURES], y_te, n_repeats=3, random_state=42, n_jobs=-1,
                            scoring="neg_root_mean_squared_error")
imp = np.clip(pi.importances_mean, 0, None); imp = imp / imp.sum() if imp.sum() > 0 else imp
importance = dict(sorted(zip(FEATURES, map(float, imp)), key=lambda t: -t[1]))
metrics = {"model": MODEL_NAME, "test": overall, "per_state": per_state, "importance": importance}
def clean(o):   # NaN/inf are not valid JSON: write null so the dashboard can always load the files
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    return None if isinstance(o, float) and not np.isfinite(o) else o
(OUT / "model_metrics.json").write_text(json.dumps(clean(metrics), indent=2))

t = overall
print(f"\n=== Test {TEST_START}-{TEST_END} ({MODEL_NAME}) ===")
print(f"{'':14s}{'MAE':>8s}{'RMSE':>8s}{'Error%':>8s}{'+-3d %':>8s}{'R2':>8s}")
for lab, k in (("Model", "rf"), ("Climatology", "base")):
    r = t[k]; print(f"{lab:14s}{r['MAE']:8.3f}{r['RMSE']:8.3f}{r['error_pct']:8.1f}{r['within3']:8.1f}{r['R2']:8.3f}")
print(f"Skill vs climatology: {t['skill_pct']:+.1f}%  (0 = no better than the monthly average)")
print("Top features:", ", ".join(f"{k} {v:.3f}" for k, v in list(importance.items())[:6]))

# ---------------- maps ----------------
names = sorted(df.state_ut.unique())
dates = sorted(df.date.unique())
act = df.pivot(index="date", columns="state_ut", values="cdd").reindex(index=dates, columns=names)
prd = df.pivot(index="date", columns="state_ut", values="pred").reindex(index=dates, columns=names)
map_dates = [d for d in dates if pd.Timestamp(d).year >= TEST_START]
vmax = float(np.nanpercentile(df.cdd, 99)); dmax = float(np.nanpercentile(np.abs(te.pred - te.cdd), 99))

if MAKE_PNG:
    gdf = states.rename(columns={"shapeName": "state_ut"})
    for d in map_dates:
        g = gdf.assign(a=gdf.state_ut.map(act.loc[d]), p=gdf.state_ut.map(prd.loc[d]))
        g["e"] = g.p - g.a
        fig, ax = plt.subplots(1, 3, figsize=(15, 5))
        for axi, c, title, kw in ((ax[0], "a", "Actual", dict(cmap="YlOrRd", vmin=0, vmax=vmax)),
                                  (ax[1], "p", "Predicted", dict(cmap="YlOrRd", vmin=0, vmax=vmax)),
                                  (ax[2], "e", "Predicted - actual", dict(cmap="BrBG_r", vmin=-dmax, vmax=dmax))):
            g.plot(column=c, ax=axi, legend=True, edgecolor="#555", linewidth=0.3,
                   missing_kwds={"color": "#ddd"}, legend_kwds={"shrink": 0.7}, **kw)
            axi.set_title(title); axi.set_axis_off()
        fig.suptitle(f"CDD by state/UT, {pd.Timestamp(d):%Y-%m}")
        fig.savefig(OUT / "maps" / f"cdd_{pd.Timestamp(d):%Y-%m}.png", dpi=90, bbox_inches="tight")
        plt.close(fig)

# ---------------- export for the web UI (index.html) ----------------
def rnd(a): return [None if not np.isfinite(x) else round(float(x), 2) for x in a]
bas = df.pivot(index="date", columns="state_ut", values="base").reindex(index=dates, columns=names)
tmask = np.array([pd.Timestamp(d).year >= TEST_START for d in dates])
ma, mp, mb = act.mean(axis=1).values, prd.mean(axis=1).values, bas.mean(axis=1).values
def mean_stats(x, y):
    ok = np.isfinite(x) & np.isfinite(y) & tmask
    return float(np.sqrt(np.mean((x[ok] - y[ok]) ** 2))), float(r2_score(x[ok], y[ok])), int(ok.sum())
(r_rf, r2_rf, n_t), (r_b, _, _) = mean_stats(ma, mp), mean_stats(ma, mb)
js = {"meta": {"lead": LEAD, "model": MODEL_NAME, "unit": "days", "trainStart": int(df.year.min()), "trainEnd": TRAIN_END,
               "testStart": TEST_START, "testEnd": TEST_END, "vmax": round(vmax, 2), "dmax": round(dmax, 2)},
      "dates": [f"{pd.Timestamp(d):%Y-%m}" for d in dates],
      "states": [{"name": n, "code": codes.get(n), "act": rnd(act[n].values), "pred": rnd(prd[n].values),
                  "base": rnd(bas[n].values), "test": per_state.get(n)} for n in names],
      "mean": {"act": rnd(ma), "pred": rnd(mp), "base": rnd(mb),
               "test": {"rf": r_rf, "base": r_b, "r2": r2_rf, "n": n_t}},
      "importance": importance, "overall": overall}
(OUT / "dashboard_data.json").write_text(json.dumps(clean(js), ensure_ascii=False), encoding="utf-8")
print("\nDone. UI data:", OUT / "dashboard_data.json", "\nServe the project root: python3 -m http.server 8080")
