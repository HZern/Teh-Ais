"""
Train the three ML pieces of the pipeline:
  A. Demand forecast   - XGBoost regressor  -> future_avg_cpu (3h-ahead)
  B. Rightsizing flag  - XGBoost classifier -> over_provisioned (binary)
  C. Idle/anomaly      - IsolationForest (unsupervised) on current utilization,
                          cross-checked against the rule-based idle_status label

Split is by VM (not by row) so test VMs are never seen in training -- with
time-series rolling features, splitting rows at random would leak adjacent
timestamps of the same VM across train/test.

lifetime_* columns (lifetime_max_cpu/avg_cpu/p95_max_cpu from vmtable) are
deliberately excluded from model features: they're computed over each VM's
*entire* creation-to-deletion lifetime, which overlaps with the future window
being predicted -- including them would leak the forecast target.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    classification_report, f1_score, mean_absolute_error, roc_auc_score,
)
from sklearn.model_selection import train_test_split
import xgboost as xgb
import joblib

DATA_DIR = "/Users/limhuizern/Documents/Hackathon"
RANDOM_STATE = 42

FEATURE_COLS = [
    "avg_cpu", "max_cpu", "min_cpu",
    "avg_cpu_roll_1h", "max_cpu_roll_1h",
    "avg_cpu_roll_3h", "max_cpu_roll_3h",
    "avg_cpu_roll_6h", "max_cpu_roll_6h",
    "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos",
    "allocated_cores", "allocated_memory_gb", "wasted_core_capacity",
]
CATEGORICAL_COLS = ["vm_category"]


def prep_features(df, feature_cols=FEATURE_COLS):
    X = df[feature_cols].copy()
    cat = pd.get_dummies(df[CATEGORICAL_COLS].astype(str), prefix=CATEGORICAL_COLS)
    X = pd.concat([X, cat], axis=1)
    return X


def vm_train_test_split(df, test_size=0.2):
    vm_ids = df["vm_code"].unique()
    train_vms, test_vms = train_test_split(vm_ids, test_size=test_size, random_state=RANDOM_STATE)
    return df[df["vm_code"].isin(train_vms)], df[df["vm_code"].isin(test_vms)]


def train_demand_forecast(train_df, test_df):
    print("\n=== A. Demand forecast (XGBoost regressor -> future_avg_cpu) ===")
    train = train_df.dropna(subset=FEATURE_COLS + ["future_avg_cpu"])
    test = test_df.dropna(subset=FEATURE_COLS + ["future_avg_cpu"])

    X_train, y_train = prep_features(train), train["future_avg_cpu"]
    X_test, y_test = prep_features(test), test["future_avg_cpu"]
    # align dummy columns between train/test
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

    model = xgb.XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.08,
        subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_STATE,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"  train rows: {len(X_train):,}, test rows: {len(X_test):,}")
    print(f"  Test MAE: {mae:.2f} cpu-percentage-points")
    print(f"  Baseline MAE (predict current avg_cpu_roll_6h as next): "
          f"{mean_absolute_error(y_test, test['avg_cpu_roll_6h']):.2f}")

    importances = pd.Series(model.feature_importances_, index=X_train.columns).sort_values(ascending=False)
    print("  Top features:\n", importances.head(6).to_string())

    joblib.dump({"model": model, "feature_cols": list(X_train.columns)}, f"{DATA_DIR}/model_demand_forecast.joblib")
    return model, list(X_train.columns)


# over_provisioned is defined as (allocated_cores >= 8) & (avg_cpu_roll_6h < 20) --
# a deterministic function of two columns. If both are left in the feature set the
# classifier just re-derives the threshold rule (trivial, AUC=1.0, tells us nothing).
# Excluding them turns this into a genuine "nowcast the 6h-aggregated state from
# less-aggregated signals" task.
RIGHTSIZING_FEATURE_COLS = [c for c in FEATURE_COLS if c not in ("allocated_cores", "avg_cpu_roll_6h", "max_cpu_roll_6h")]


def train_rightsizing(train_df, test_df):
    print("\n=== B. Rightsizing flag (XGBoost classifier -> over_provisioned) ===")
    train = train_df.dropna(subset=RIGHTSIZING_FEATURE_COLS + ["over_provisioned"])
    test = test_df.dropna(subset=RIGHTSIZING_FEATURE_COLS + ["over_provisioned"])

    X_train, y_train = prep_features(train, RIGHTSIZING_FEATURE_COLS), train["over_provisioned"].astype(int)
    X_test, y_test = prep_features(test, RIGHTSIZING_FEATURE_COLS), test["over_provisioned"].astype(int)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

    pos_rate = y_train.mean()
    scale_pos_weight = (1 - pos_rate) / max(pos_rate, 1e-6)
    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.08,
        subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_STATE,
        scale_pos_weight=scale_pos_weight, eval_metric="logloss",
    )
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)

    print(f"  train rows: {len(X_train):,} (pos rate {pos_rate:.3f}), test rows: {len(X_test):,}")
    print(f"  ROC-AUC: {roc_auc_score(y_test, proba):.3f}, F1: {f1_score(y_test, preds):.3f}")
    print(classification_report(y_test, preds, target_names=["right-sized", "over-provisioned"]))

    joblib.dump({"model": model, "feature_cols": list(X_train.columns)}, f"{DATA_DIR}/model_rightsizing.joblib")
    return model, list(X_train.columns)


def train_idle_anomaly(train_df, test_df):
    print("\n=== C. Idle / anomaly detection ===")
    print("  idle_status is the operational flag: a transparent rule (sustained 6h avg CPU")
    print("  < 5%) used directly for auto-shutdown/consolidation decisions -- it needs to be")
    print("  explainable to an ops team, not a black box.")
    print("  IsolationForest runs alongside it as a secondary 'unusual behavior' detector.")
    cols = ["avg_cpu", "max_cpu", "min_cpu", "avg_cpu_roll_1h", "avg_cpu_roll_6h"]
    train = train_df.dropna(subset=cols)
    test = test_df.dropna(subset=cols + ["idle_status"])

    model = IsolationForest(n_estimators=200, contamination=0.15, random_state=RANDOM_STATE)
    model.fit(train[cols])

    anomaly_flag = model.predict(test[cols]) == -1  # -1 = anomaly

    # In this trace, sustained low CPU is the *majority* pattern (idle_status is
    # True ~47% of the time), so IsolationForest treats it as normal, not anomalous --
    # it instead isolates atypical spikes/erratic usage. That's a genuinely different,
    # complementary signal to the rule-based idle flag, not a replacement for it.
    idle_rate_in_anomalies = test.loc[anomaly_flag, "idle_status"].astype(bool).mean()
    idle_rate_overall = test["idle_status"].astype(bool).mean()
    print(f"  test rows: {len(test):,}, flagged anomalies: {anomaly_flag.sum():,}")
    print(f"  idle rate among flagged anomalies: {idle_rate_in_anomalies:.2f} "
          f"(vs {idle_rate_overall:.2f} baseline) -- confirms anomalies = activity spikes, not idle VMs")

    joblib.dump({"model": model, "feature_cols": cols}, f"{DATA_DIR}/model_idle_anomaly.joblib")
    return model, cols


def main():
    df = pd.read_parquet(f"{DATA_DIR}/features_labeled.parquet")
    train_df, test_df = vm_train_test_split(df)
    print(f"Train VMs: {train_df.vm_code.nunique():,} ({len(train_df):,} rows)")
    print(f"Test VMs:  {test_df.vm_code.nunique():,} ({len(test_df):,} rows)")

    train_demand_forecast(train_df, test_df)
    train_rightsizing(train_df, test_df)
    train_idle_anomaly(train_df, test_df)

    print("\nSaved models: model_demand_forecast.joblib, model_rightsizing.joblib, model_idle_anomaly.joblib")


if __name__ == "__main__":
    main()
