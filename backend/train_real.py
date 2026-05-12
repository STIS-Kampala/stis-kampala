"""
train_real.py — Three-Experiment ML Training
Experiment A: Synthetic only
Experiment B: Synthetic + Real
Experiment C: Real only
"""

from __future__ import annotations
import os, logging
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, f1_score, classification_report
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("train_real")

os.makedirs("results", exist_ok=True)
os.makedirs("models",  exist_ok=True)

FEATURES = [
    "is_rush_morning", "is_rush_evening", "is_rush_midday",
    "is_night", "is_weekend", "is_friday_pm",
    "has_boda_boda", "rain_mm", "hour",
]
TARGET_REG = "delay_ratio"
TARGET_CLF = "label_encoded"

LABEL_MAP = {"low": 0, "medium": 1, "high": 2}
LABEL_INV = {0: "low", 1: "medium", 2: "high"}


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
                feats["delay_ratio"] = round(max(0.5, min(3.5, mult)), 4)
                label = "high" if feats["delay_ratio"] >= 1.60 else ("medium" if feats["delay_ratio"] >= 1.25 else "low")
                feats["label"] = label
                feats["label_encoded"] = LABEL_MAP[label]
                rows.append(feats)
    df = pd.DataFrame(rows)
    return df.sort_values("day").reset_index(drop=True)


def load_real():
    try:
        from app.core.database import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT road_id, road_name, label, delay_ratio, hour, rain_mm
            FROM predictions
            WHERE source != 'api'
            ORDER BY timestamp
        """)
        cols = ["road_id", "road_name", "label", "delay_ratio", "hour", "rain_mm"]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.close()
        conn.close()

        if not rows:
            log.warning("No real data in DB")
            return None

        df = pd.DataFrame(rows)
        log.info(f"Loaded {len(df)} real records from DB")

        # Engineer features
        df["is_rush_morning"] = df["hour"].apply(lambda h: int(h in (7, 8, 9)))
        df["is_rush_evening"] = df["hour"].apply(lambda h: int(h in (17, 18, 19, 20)))
        df["is_rush_midday"]  = df["hour"].apply(lambda h: int(h in (12, 13, 14)))
        df["is_night"]        = df["hour"].apply(lambda h: int(h < 5 or h >= 23))
        df["is_weekend"]      = 0
        df["is_friday_pm"]    = 0
        df["has_boda_boda"]   = df["road_id"].apply(
            lambda r: int(r in ("kampala_rd","jinja_rd","bombo_rd","masaka_rd","gaba_rd","portbell_rd"))
        )
        df["label_encoded"] = df["label"].map(LABEL_MAP).fillna(0).astype(int)

        return df

    except Exception as e:
        log.error(f"DB error: {e}")
        return None


def evaluate_reg(model, X_test, y_test):
    preds = model.predict(X_test)
    mae  = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2   = r2_score(y_test, preds)
    def label(x): return "high" if x >= 1.60 else ("medium" if x >= 1.25 else "low")
    acc = sum(label(t) == label(p) for t, p in zip(y_test, preds)) / len(y_test)
    return {
        "MAE":      round(mae, 4),
        "RMSE":     round(rmse, 4),
        "R2":       round(r2, 4),
        "Accuracy": round(acc, 4),
    }


def evaluate_clf(model, X_test, y_test):
    preds = model.predict(X_test)
    acc  = accuracy_score(y_test, preds)
    f1   = f1_score(y_test, preds, average="weighted", zero_division=0)
    return {
        "Accuracy": round(acc, 4),
        "F1":       round(f1, 4),
    }


def train_reg(X, y):
    m = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
    m.fit(X, y)
    return m


def train_clf(X, y):
    m = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
    m.fit(X, y)
    return m


def run_experiments():
    results = []
    synth = load_synthetic()
    n = len(synth)

    X_s = synth[FEATURES]
    y_reg_s = synth[TARGET_REG]
    y_clf_s = synth[TARGET_CLF]

    train_end = int(n * 0.70)
    test_start = int(n * 0.85)

    X_train_s = X_s.iloc[:train_end]
    y_reg_train_s = y_reg_s.iloc[:train_end]
    y_clf_train_s = y_clf_s.iloc[:train_end]

    X_test_s  = X_s.iloc[test_start:]
    y_reg_test_s = y_reg_s.iloc[test_start:]
    y_clf_test_s = y_clf_s.iloc[test_start:]

    # ====== Experiment A: Synthetic Only ======
    log.info("=== Experiment A: Synthetic Only ===")
    ma_reg = train_reg(X_train_s, y_reg_train_s)
    ma_clf = train_clf(X_train_s, y_clf_train_s)
    ra = {**evaluate_reg(ma_reg, X_test_s, y_reg_test_s), **evaluate_clf(ma_clf, X_test_s, y_clf_test_s)}
    ra["Train_size"] = len(X_train_s)
    log.info(f"  {ra}")
    results.append({"Experiment": "A: Synthetic Only", **ra})

    # ====== Load Real Data ======
    real = load_real()

    if real is not None:
        X_r = real[FEATURES]
        y_reg_r = real[TARGET_REG]
        y_clf_r = real[TARGET_CLF]

        # ====== Experiment B: Synthetic + Real ======
        log.info("=== Experiment B: Synthetic + Real ===")
        X_b = pd.concat([X_train_s, X_r], ignore_index=True)
        y_reg_b = pd.concat([y_reg_train_s, y_reg_r], ignore_index=True)
        y_clf_b = pd.concat([y_clf_train_s, y_clf_r], ignore_index=True)

        mb_reg = train_reg(X_b, y_reg_b)
        mb_clf = train_clf(X_b, y_clf_b)
        rb = {**evaluate_reg(mb_reg, X_test_s, y_reg_test_s), **evaluate_clf(mb_clf, X_test_s, y_clf_test_s)}
        rb["Train_size"] = len(X_b)
        log.info(f"  {rb}")
        results.append({"Experiment": "B: Synth + Real", **rb})

        # ====== Experiment C: Real Only ======
        if len(real) >= 100:
            log.info("=== Experiment C: Real Only ===")
            split = int(len(real) * 0.8)
            X_r_train = X_r.iloc[:split]
            X_r_test  = X_r.iloc[split:]
            y_reg_r_train = y_reg_r.iloc[:split]
            y_reg_r_test  = y_reg_r.iloc[split:]
            y_clf_r_train = y_clf_r.iloc[:split]
            y_clf_r_test  = y_clf_r.iloc[split:]

            mc_reg = train_reg(X_r_train, y_reg_r_train)
            mc_clf = train_clf(X_r_train, y_clf_r_train)
            rc = {**evaluate_reg(mc_reg, X_r_test, y_reg_r_test), **evaluate_clf(mc_clf, X_r_test, y_clf_r_test)}
            rc["Train_size"] = split
            log.info(f"  {rc}")
            results.append({"Experiment": "C: Real Only", **rc})

    df_r = pd.DataFrame(results)
    df_r.to_csv("results/experiment_results.csv", index=False)

    print("\n" + "="*60)
    print("EXPERIMENT RESULTS")
    print("="*60)
    print(df_r.to_string(index=False))
    print("="*60)

    return df_r


if __name__ == "__main__":
    run_experiments()
