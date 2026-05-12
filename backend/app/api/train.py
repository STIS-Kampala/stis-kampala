from fastapi import APIRouter
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score
from app.core.database import get_conn

router = APIRouter()

FEATURES = [
    "is_rush_morning", "is_rush_evening", "is_rush_midday",
    "is_night", "is_weekend", "is_friday_pm",
    "has_boda_boda", "rain_mm", "hour",
]
LABEL_MAP = {"low": 0, "medium": 1, "high": 2}

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
                rain_mm = max(0, float(rng.normal(2, 5)) if rng.random() < 0.3 else 0)
                feats = {
                    "is_rush_morning": int(hour in (7,8,9)),
                    "is_rush_evening": int(hour in (17,18,19,20)),
                    "is_rush_midday":  int(hour in (12,13,14)),
                    "is_night":        int(hour < 5 or hour >= 23),
                    "is_weekend":      int(day % 7 in (5,6)),
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
                mult += float(rng.normal(0, 0.05))
                feats["delay_ratio"] = round(max(0.5, min(3.5, mult)), 4)
                feats["label_encoded"] = 2 if feats["delay_ratio"] >= 1.60 else (1 if feats["delay_ratio"] >= 1.25 else 0)
                rows.append(feats)
    return pd.DataFrame(rows).sort_values("day").reset_index(drop=True)

def load_real():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT road_id, label, delay_ratio, hour, rain_mm
            FROM predictions WHERE source != 'api' ORDER BY timestamp
        """)
        rows = [dict(zip(["road_id","label","delay_ratio","hour","rain_mm"], r)) for r in cur.fetchall()]
        cur.close(); conn.close()
        if not rows: return None
        df = pd.DataFrame(rows)
        df["is_rush_morning"] = df["hour"].apply(lambda h: int(h in (7,8,9)))
        df["is_rush_evening"] = df["hour"].apply(lambda h: int(h in (17,18,19,20)))
        df["is_rush_midday"]  = df["hour"].apply(lambda h: int(h in (12,13,14)))
        df["is_night"]        = df["hour"].apply(lambda h: int(h < 5 or h >= 23))
        df["is_weekend"]      = 0
        df["is_friday_pm"]    = 0
        df["has_boda_boda"]   = df["road_id"].apply(lambda r: int(r in ("kampala_rd","jinja_rd","bombo_rd","masaka_rd","gaba_rd","portbell_rd")))
        df["label_encoded"]   = df["label"].map(LABEL_MAP).fillna(0).astype(int)
        return df
    except Exception as e:
        return None

def run_exp(X_train, y_reg_train, y_clf_train, X_test, y_reg_test, y_clf_test, name, train_size):
    reg = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
    clf = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
    reg.fit(X_train, y_reg_train)
    clf.fit(X_train, y_clf_train)
    preds_reg = reg.predict(X_test)
    preds_clf = clf.predict(X_test)
    def lbl(x): return 2 if x >= 1.60 else (1 if x >= 1.25 else 0)
    return {
        "experiment": name,
        "train_size": train_size,
        "MAE":        round(float(mean_absolute_error(y_reg_test, preds_reg)), 4),
        "RMSE":       round(float(np.sqrt(mean_squared_error(y_reg_test, preds_reg))), 4),
        "R2":         round(float(r2_score(y_reg_test, preds_reg)), 4),
        "Accuracy":   round(float(accuracy_score(y_clf_test, preds_clf)), 4),
        "F1":         round(float(f1_score(y_clf_test, preds_clf, average="weighted", zero_division=0)), 4),
    }

@router.get("")
def train():
    synth = load_synthetic()
    n = len(synth)
    X_s = synth[FEATURES]
    y_reg_s = synth["delay_ratio"]
    y_clf_s = synth["label_encoded"]
    train_end  = int(n * 0.70)
    test_start = int(n * 0.85)
    X_train_s = X_s.iloc[:train_end]
    X_test_s  = X_s.iloc[test_start:]
    y_reg_train_s = y_reg_s.iloc[:train_end]
    y_reg_test_s  = y_reg_s.iloc[test_start:]
    y_clf_train_s = y_clf_s.iloc[:train_end]
    y_clf_test_s  = y_clf_s.iloc[test_start:]

    results = []

    # Experiment A
    results.append(run_exp(X_train_s, y_reg_train_s, y_clf_train_s, X_test_s, y_reg_test_s, y_clf_test_s, "A: Synthetic Only", len(X_train_s)))

    real = load_real()
    if real is not None:
        X_r = real[FEATURES]
        y_reg_r = real["delay_ratio"]
        y_clf_r = real["label_encoded"]

        # Experiment B
        X_b = pd.concat([X_train_s, X_r], ignore_index=True)
        y_reg_b = pd.concat([y_reg_train_s, y_reg_r], ignore_index=True)
        y_clf_b = pd.concat([y_clf_train_s, y_clf_r], ignore_index=True)
        results.append(run_exp(X_b, y_reg_b, y_clf_b, X_test_s, y_reg_test_s, y_clf_test_s, "B: Synth + Real", len(X_b)))

        # Experiment C
        if len(real) >= 100:
            split = int(len(real) * 0.8)
            results.append(run_exp(
                X_r.iloc[:split], y_reg_r.iloc[:split], y_clf_r.iloc[:split],
                X_r.iloc[split:], y_reg_r.iloc[split:], y_clf_r.iloc[split:],
                "C: Real Only", split
            ))

    return {"status": "ok", "results": results}
