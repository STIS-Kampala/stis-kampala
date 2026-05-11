"""
train_real.py — Three-Experiment ML Training
Experiment A: Synthetic only
Experiment B: Synthetic + Real fine-tune
Experiment C: Real only
"""

from __future__ import annotations
import os, logging
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("train_real")

os.makedirs("results", exist_ok=True)
os.makedirs("models",  exist_ok=True)

FEATURES = [
    "is_rush_morning", "is_rush_evening", "is_rush_midday",
    "is_night", "is_weekend", "is_friday_pm",
    "has_boda_boda", "rain_mm", "hour",
]
TARGET = "congestion_ratio"

def load_synthetic():
    rng = np.random.default_rng(42)
    roads = [
        ("kampala_rd", True), ("jinja_rd", True),
        ("bombo_rd", True),   ("masaka_rd", True),
        ("gaba_rd", True),    ("portbell_rd", True),
        ("entebbe_rd", False),("n_bypass", False),
    ]
    rows = []
    for day in range(90):
        for hour in range(24):
            for road_id, has_boda in roads:
                rain_mm = max(0, rng.normal(2, 5) if rng.random() < 0.3 else 0)
                feats = {
                    "is_rush_morning": int(hour in (7, 8, 9)),
                    "is_rush_evening": int(hour in (17, 18, 19, 20)),
                    "is_rush_midday":  int(hour in (12, 13, 14)),
                    "is_night":        int(hour < 5 or hour >= 23),
                    "is_weekend":      int(day % 7 in (5, 6)),
                    "is_friday_pm":    int(day % 7 == 4 and hour >= 16),
                    "has_boda_boda":   int(has_boda),
                    "rain_mm":         round(rain_mm, 2),
                    "hour":            hour,
                    "day":             day,
                }
                mult = 1.0
                if feats["is_rush_morning"]: mult += 0.85
                if feats["is_rush_evening"]: mult += 1.10
                if feats["is_rush_midday"]:  mult += 0.38
                if feats["is_night"]:        mult -= 0.55
                mult += rain_mm * 0.025
                if has_boda and feats["is_rush_morning"]: mult += 0.12
                mult += rng.normal(0, 0.05)
                feats["congestion_ratio"] = round(max(0.5, min(3.5, mult)), 4)
                rows.append(feats)
    df = pd.DataFrame(rows)
    return df.sort_values("day").reset_index(drop=True)

def load_real():
    path = "data/real_kampala_traffic.csv"
    if not os.path.exists(path):
        log.warning("No real data found — run collector.py first")
        return None
    df = pd.read_csv(path)
    if len(df) < 10:
        return None
    log.info(f"Loaded {len(df)} real records")
    return df

def evaluate(model, X_test, y_test):
    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    rmse  = np.sqrt(mean_squared_error(y_test, preds))
    r2    = r2_score(y_test, preds)
    def label(x): return "high" if x >= 1.60 else ("medium" if x >= 1.25 else "low")
    acc = sum(label(t)==label(p) for t,p in zip(y_test, preds)) / len(y_test)
    return {"MAE": round(mae,4), "RMSE": round(rmse,4), "R2": round(r2,4), "Accuracy": round(acc,4)}

def train_model(X, y):
    m = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
    m.fit(X, y)
    return m

def run_experiments():
    results = []
    synth = load_synthetic()
    n = len(synth)
    X = synth[FEATURES]
    y = synth[TARGET]
    X_train = X.iloc[:int(n*0.70)]
    y_train = y.iloc[:int(n*0.70)]
    X_test  = X.iloc[int(n*0.85):]
    y_test  = y.iloc[int(n*0.85):]

    log.info("=== Experiment A: Synthetic only ===")
    ma = train_model(X_train, y_train)
    ra = evaluate(ma, X_test, y_test)
    log.info(f"  {ra}")
    results.append({"Experiment": "A: Synthetic Only", **ra, "Train_size": len(X_train)})

    real = load_real()
    if real is not None:
        Xr = real[FEATURES]
        yr = real[TARGET]

        log.info("=== Experiment B: Synthetic + Real ===")
        Xc = pd.concat([X_train, Xr], ignore_index=True)
        yc = pd.concat([y_train, yr], ignore_index=True)
        mb = train_model(Xc, yc)
        rb = evaluate(mb, X_test, y_test)
        log.info(f"  {rb}")
        results.append({"Experiment": "B: Synth + Real", **rb, "Train_size": len(Xc)})

        if len(real) >= 50:
            log.info("=== Experiment C: Real only ===")
            split = int(len(real)*0.8)
            mc = train_model(Xr.iloc[:split], yr.iloc[:split])
            rc = evaluate(mc, Xr.iloc[split:], yr.iloc[split:])
            log.info(f"  {rc}")
            results.append({"Experiment": "C: Real Only", **rc, "Train_size": split})

    df_r = pd.DataFrame(results)
    df_r.to_csv("results/experiment_results.csv", index=False)
    print("\n=== RESULTS ===")
    print(df_r.to_string(index=False))
    return df_r

if __name__ == "__main__":
    run_experiments()
