
"""
train_real.py — Full Research Pipeline
Experiments A, B, C + SHAP + Stats + Drift
"""

from __future__ import annotations
import os, logging
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, f1_score, confusion_matrix,
    classification_report
)
from sklearn.model_selection import cross_val_score
import shap

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("train_real")

os.makedirs("results", exist_ok=True)
os.makedirs("results/charts", exist_ok=True)

FEATURES = [
    "is_rush_morning", "is_rush_evening", "is_rush_midday",
    "is_night", "is_weekend", "is_friday_pm",
    "has_boda_boda", "rain_mm", "hour",
]
TARGET_REG = "delay_ratio"
TARGET_CLF = "label_encoded"
LABEL_MAP  = {"low": 0, "medium": 1, "high": 2}
LABEL_INV  = {0: "low", 1: "medium", 2: "high"}
LABEL_NAMES = ["low", "medium", "high"]


# ─────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────

def load_synthetic() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    roads = [
        ("kampala_rd", True), ("jinja_rd", True),
        ("bombo_rd",   True), ("masaka_rd", True),
        ("gaba_rd",    True), ("portbell_rd", True),
        ("entebbe_rd", False),("n_bypass", False),
    ]
    rows = []
    for day in range(90):
        for hour in range(24):
            for road_id, has_boda in roads:
                rain_mm = max(0, float(rng.normal(2, 5)) if rng.random() < 0.3 else 0)
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
                mult += float(rng.normal(0, 0.05))
                feats["delay_ratio"]   = round(max(0.5, min(3.5, mult)), 4)
                feats["label_encoded"] = 2 if feats["delay_ratio"] >= 1.60 else (
                                         1 if feats["delay_ratio"] >= 1.25 else 0)
                rows.append(feats)
    return pd.DataFrame(rows).sort_values("day").reset_index(drop=True)


def load_real() -> pd.DataFrame | None:
    try:
        from app.core.database import get_conn
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT road_id, label, delay_ratio, hour, rain_mm
            FROM predictions
            WHERE source != 'api'
            ORDER BY timestamp
        """)
        rows = [dict(zip(["road_id","label","delay_ratio","hour","rain_mm"], r))
                for r in cur.fetchall()]
        cur.close(); conn.close()
        if not rows:
            log.warning("No real data in DB")
            return None
        df = pd.DataFrame(rows)
        log.info(f"Loaded {len(df)} real records from DB")
        df["is_rush_morning"] = df["hour"].apply(lambda h: int(h in (7,8,9)))
        df["is_rush_evening"] = df["hour"].apply(lambda h: int(h in (17,18,19,20)))
        df["is_rush_midday"]  = df["hour"].apply(lambda h: int(h in (12,13,14)))
        df["is_night"]        = df["hour"].apply(lambda h: int(h < 5 or h >= 23))
        df["is_weekend"]      = 0
        df["is_friday_pm"]    = 0
        df["has_boda_boda"]   = df["road_id"].apply(
            lambda r: int(r in ("kampala_rd","jinja_rd","bombo_rd",
                                "masaka_rd","gaba_rd","portbell_rd")))
        df["label_encoded"] = df["label"].map(LABEL_MAP).fillna(0).astype(int)
        return df
    except Exception as e:
        log.error(f"DB error: {e}")
        return None


# ─────────────────────────────────────────
# TRAINING & EVALUATION
# ─────────────────────────────────────────

def train_models(X, y_reg, y_clf):
    reg = GradientBoostingRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
    clf = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
    reg.fit(X, y_reg)
    clf.fit(X, y_clf)
    return reg, clf


def evaluate(reg, clf, X_test, y_reg_test, y_clf_test, name, train_size):
    preds_reg = reg.predict(X_test)
    preds_clf = clf.predict(X_test)

    def lbl(x): return 2 if x >= 1.60 else (1 if x >= 1.25 else 0)
    acc_reg = sum(lbl(t) == lbl(p) for t, p in zip(y_reg_test, preds_reg)) / len(y_reg_test)

    result = {
        "Experiment": name,
        "Train_size": train_size,
        "MAE":        round(float(mean_absolute_error(y_reg_test, preds_reg)), 4),
        "RMSE":       round(float(np.sqrt(mean_squared_error(y_reg_test, preds_reg))), 4),
        "R2":         round(float(r2_score(y_reg_test, preds_reg)), 4),
        "Accuracy":   round(float(accuracy_score(y_clf_test, preds_clf)), 4),
        "F1":         round(float(f1_score(y_clf_test, preds_clf,
                                           average="weighted", zero_division=0)), 4),
        "Acc_from_reg": round(acc_reg, 4),
    }

    # Confusion Matrix
    cm = confusion_matrix(y_clf_test, preds_clf)
    plot_confusion_matrix(cm, name)

    # Classification report
    report = classification_report(y_clf_test, preds_clf,
                                   target_names=LABEL_NAMES, zero_division=0)
    with open(f"results/{name.split(':')[0].strip()}_report.txt", "w") as f:
        f.write(f"=== {name} ===\n{report}\n")
    log.info(f"\n{report}")

    return result, preds_reg, preds_clf


# ─────────────────────────────────────────
# CROSS VALIDATION
# ─────────────────────────────────────────

def cross_validate(X, y_reg, y_clf, name):
    reg = GradientBoostingRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
    clf = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)

    cv_mae = cross_val_score(reg, X, y_reg, cv=5,
                             scoring="neg_mean_absolute_error")
    cv_acc = cross_val_score(clf, X, y_clf, cv=5, scoring="accuracy")

    log.info(f"[{name}] CV MAE: {-cv_mae.mean():.4f} ± {cv_mae.std():.4f}")
    log.info(f"[{name}] CV Acc: {cv_acc.mean():.4f} ± {cv_acc.std():.4f}")

    return {
        "cv_mae_mean": round(float(-cv_mae.mean()), 4),
        "cv_mae_std":  round(float(cv_mae.std()), 4),
        "cv_acc_mean": round(float(cv_acc.mean()), 4),
        "cv_acc_std":  round(float(cv_acc.std()), 4),
    }


# ─────────────────────────────────────────
# SHAP — REAL
# ─────────────────────────────────────────

def compute_shap(reg, X_test, name):
    log.info(f"Computing SHAP for {name}...")
    explainer   = shap.TreeExplainer(reg)
    shap_values = explainer.shap_values(X_test)

    # Summary plot
    plt.figure(figsize=(8, 5))
    shap.summary_plot(shap_values, X_test, feature_names=FEATURES,
                      show=False, plot_type="bar")
    plt.title(f"SHAP Feature Importance — {name}")
    plt.tight_layout()
    safe = name.replace(":", "").replace(" ", "_")
    plt.savefig(f"results/charts/shap_{safe}.png", dpi=150)
    plt.close()

    # Mean absolute SHAP per feature
    mean_shap = np.abs(shap_values).mean(axis=0)
    shap_df   = pd.DataFrame({
        "feature":    FEATURES,
        "mean_shap":  mean_shap,
    }).sort_values("mean_shap", ascending=False)
    shap_df.to_csv(f"results/shap_{safe}.csv", index=False)
    log.info(f"Top SHAP feature: {shap_df.iloc[0]['feature']} = {shap_df.iloc[0]['mean_shap']:.4f}")
    return shap_df


# ─────────────────────────────────────────
# STATISTICAL SIGNIFICANCE
# ─────────────────────────────────────────

def statistical_tests(preds: dict[str, np.ndarray], y_true):
    log.info("\n=== Statistical Significance Tests ===")
    names = list(preds.keys())
    results = []
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            n1, n2 = names[i], names[j]
            e1 = np.abs(y_true - preds[n1])
            e2 = np.abs(y_true - preds[n2])
            stat, p = stats.wilcoxon(e1, e2)
            sig = "✅ Significant" if p < 0.05 else "❌ Not significant"
            log.info(f"  {n1} vs {n2}: p={p:.4f} {sig}")
            results.append({
                "comparison": f"{n1} vs {n2}",
                "statistic":  round(float(stat), 4),
                "p_value":    round(float(p), 6),
                "significant": p < 0.05,
            })
    pd.DataFrame(results).to_csv("results/statistical_tests.csv", index=False)
    return results


# ─────────────────────────────────────────
# DATA DRIFT ANALYSIS
# ─────────────────────────────────────────

def data_drift_analysis(synth: pd.DataFrame, real: pd.DataFrame):
    log.info("\n=== Data Drift Analysis ===")
    results = []
    for feat in FEATURES:
        if feat not in real.columns:
            continue
        s_vals = synth[feat].values
        r_vals = real[feat].values
        stat, p = stats.ks_2samp(s_vals, r_vals)
        drift = "⚠️ Drift" if p < 0.05 else "✅ Similar"
        log.info(f"  {feat}: KS={stat:.4f}, p={p:.4f} {drift}")
        results.append({
            "feature":   feat,
            "ks_stat":   round(float(stat), 4),
            "p_value":   round(float(p), 6),
            "drift":     p < 0.05,
        })

    pd.DataFrame(results).to_csv("results/data_drift.csv", index=False)

    # Label distribution comparison
    plot_label_distribution(synth, real)

    # Delay ratio distribution
    plot_delay_distribution(synth, real)

    return results


# ─────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────

def plot_confusion_matrix(cm, name):
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=LABEL_NAMES, yticklabels=LABEL_NAMES, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix — {name}")
    plt.tight_layout()
    safe = name.replace(":", "").replace(" ", "_")
    plt.savefig(f"results/charts/cm_{safe}.png", dpi=150)
    plt.close()


def plot_label_distribution(synth, real):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, df, title in zip(axes, [synth, real], ["Synthetic", "Real"]):
        counts = df["label_encoded"].value_counts().sort_index()
        ax.bar(LABEL_NAMES, [counts.get(i, 0) for i in range(3)],
               color=["#22c55e", "#f59e0b", "#ef4444"])
        ax.set_title(f"Label Distribution — {title}")
        ax.set_ylabel("Count")
    plt.tight_layout()
    plt.savefig("results/charts/label_distribution.png", dpi=150)
    plt.close()


def plot_delay_distribution(synth, real):
    plt.figure(figsize=(8, 4))
    plt.hist(synth["delay_ratio"], bins=40, alpha=0.6, label="Synthetic", color="#6366f1")
    plt.hist(real["delay_ratio"],  bins=40, alpha=0.6, label="Real",      color="#00ffe0")
    plt.xlabel("Delay Ratio")
    plt.ylabel("Count")
    plt.title("Delay Ratio Distribution: Synthetic vs Real")
    plt.legend()
    plt.tight_layout()
    plt.savefig("results/charts/delay_distribution.png", dpi=150)
    plt.close()


def plot_experiment_comparison(results_df):
    metrics = ["MAE", "RMSE", "R2", "Accuracy", "F1"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(16, 4))
    colors = ["#6366f1", "#00ffe0", "#f59e0b"]
    for ax, metric in zip(axes, metrics):
        bars = ax.bar(results_df["Experiment"], results_df[metric], color=colors)
        ax.set_title(metric)
        ax.set_ylim(0, max(results_df[metric].max() * 1.15, 0.1))
        for bar, val in zip(bars, results_df[metric]):
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 0.005,
                    f"{val:.4f}", ha="center", va="bottom", fontsize=7)
        ax.tick_params(axis="x", labelrotation=15, labelsize=7)
    plt.suptitle("Experiment Comparison", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig("results/charts/experiment_comparison.png", dpi=150)
    plt.close()


def plot_feature_importance(reg, name):
    imp = reg.feature_importances_
    df  = pd.DataFrame({"feature": FEATURES, "importance": imp})
    df  = df.sort_values("importance", ascending=True)
    plt.figure(figsize=(7, 5))
    plt.barh(df["feature"], df["importance"], color="#6366f1")
    plt.xlabel("Importance")
    plt.title(f"Feature Importance — {name}")
    plt.tight_layout()
    safe = name.replace(":", "").replace(" ", "_")
    plt.savefig(f"results/charts/feat_imp_{safe}.png", dpi=150)
    plt.close()


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def run_experiments():
    results    = []
    cv_results = []
    reg_preds  = {}

    # ── Load data ──
    synth = load_synthetic()
    real  = load_real()
    n     = len(synth)

    X_s      = synth[FEATURES]
    y_reg_s  = synth[TARGET_REG]
    y_clf_s  = synth[TARGET_CLF]

    train_end  = int(n * 0.70)
    test_start = int(n * 0.85)

    X_train_s    = X_s.iloc[:train_end]
    X_test_s     = X_s.iloc[test_start:]
    y_reg_train  = y_reg_s.iloc[:train_end]
    y_reg_test   = y_reg_s.iloc[test_start:]
    y_clf_train  = y_clf_s.iloc[:train_end]
    y_clf_test   = y_clf_s.iloc[test_start:]

    # ── Experiment A ──
    log.info("\n=== Experiment A: Synthetic Only ===")
    reg_a, clf_a = train_models(X_train_s, y_reg_train, y_clf_train)
    res_a, preds_reg_a, _ = evaluate(reg_a, clf_a, X_test_s,
                                      y_reg_test, y_clf_test,
                                      "A: Synthetic Only", len(X_train_s))
    results.append(res_a)
    reg_preds["A"] = preds_reg_a
    compute_shap(reg_a, X_test_s, "A")
    plot_feature_importance(reg_a, "A")
    cv_a = cross_validate(X_train_s, y_reg_train, y_clf_train, "A")
    cv_results.append({"Experiment": "A", **cv_a})

    if real is not None:
        log.info(f"\nReal data: {len(real)} records")

        X_r     = real[FEATURES]
        y_reg_r = real[TARGET_REG]
        y_clf_r = real[TARGET_CLF]

        # ── Data Drift ──
        data_drift_analysis(synth, real)

        # ── Experiment B ──
        log.info("\n=== Experiment B: Synthetic + Real ===")
        X_b     = pd.concat([X_train_s, X_r], ignore_index=True)
        y_reg_b = pd.concat([y_reg_train, y_reg_r], ignore_index=True)
        y_clf_b = pd.concat([y_clf_train, y_clf_r], ignore_index=True)

        reg_b, clf_b = train_models(X_b, y_reg_b, y_clf_b)
        res_b, preds_reg_b, _ = evaluate(reg_b, clf_b, X_test_s,
                                          y_reg_test, y_clf_test,
                                          "B: Synth + Real", len(X_b))
        results.append(res_b)
        reg_preds["B"] = preds_reg_b
        compute_shap(reg_b, X_test_s, "B")
        plot_feature_importance(reg_b, "B")
        cv_b = cross_validate(X_b, y_reg_b, y_clf_b, "B")
        cv_results.append({"Experiment": "B", **cv_b})

        # ── Experiment C ──
        if len(real) >= 100:
            log.info("\n=== Experiment C: Real Only ===")
            split       = int(len(real) * 0.8)
            X_r_train   = X_r.iloc[:split]
            X_r_test    = X_r.iloc[split:]
            y_reg_r_tr  = y_reg_r.iloc[:split]
            y_reg_r_te  = y_reg_r.iloc[split:]
            y_clf_r_tr  = y_clf_r.iloc[:split]
            y_clf_r_te  = y_clf_r.iloc[split:]

            reg_c, clf_c = train_models(X_r_train, y_reg_r_tr, y_clf_r_tr)
            res_c, preds_reg_c, _ = evaluate(reg_c, clf_c, X_r_test,
                                              y_reg_r_te, y_clf_r_te,
                                              "C: Real Only", split)
            results.append(res_c)
            compute_shap(reg_c, X_r_test, "C")
            plot_feature_importance(reg_c, "C")
            cv_c = cross_validate(X_r_train, y_reg_r_tr, y_clf_r_tr, "C")
            cv_results.append({"Experiment": "C", **cv_c})

        # ── Statistical Tests (A vs B) ──
        statistical_tests(reg_preds, y_reg_test.values)

    # ── Save Results ──
    df_res = pd.DataFrame(results)
    df_cv  = pd.DataFrame(cv_results)
    df_res.to_csv("results/experiment_results.csv", index=False)
    df_cv.to_csv("results/cv_results.csv", index=False)

    plot_experiment_comparison(df_res)

    print("\n" + "="*65)
    print("EXPERIMENT RESULTS")
    print("="*65)
    print(df_res.to_string(index=False))
    print("\nCROSS-VALIDATION")
    print(df_cv.to_string(index=False))
    print("="*65)
    print("\n✅ All charts saved to results/charts/")

    return df_res


if __name__ == "__main__":
    run_experiments()
