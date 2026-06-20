"""
Feature engineering + label derivation on top of joined_readings.parquet.

Data notes:
- Readings are every 5 minutes (300s). Our sample window covers ~18.5h
  (223 timestamps), not a full 24h+48h. The brief's pipeline plan calls for
  1h/6h/24h rolling windows and a 24h-ahead demand label — with only ~18.5h
  of history per VM that's not achievable as literally specified, so windows
  are scaled to what the sampled slice actually supports (1h/3h/6h rolling,
  3h-ahead demand forecast) while keeping the same modeling approach. This
  scales unchanged to 1h/6h/24h if more chunks are downloaded.
- timestamp is seconds-from-trace-start, not a real epoch, so day-of-week is
  mostly constant within this slice; hour-of-day is still meaningful since
  the trace starts at t=0 and progresses forward in real time.
- core_bucket / memory_bucket are the VM's allocated size (vCPUs / GB RAM),
  given as strings with open-ended top buckets ('>24' cores, '>64' GB) which
  we map to representative numeric values for the over-provisioning signal.
"""
import numpy as np
import pandas as pd

DATA_DIR = "/Users/limhuizern/Documents/Hackathon"
SAMPLE_INTERVAL_SEC = 300

CORE_BUCKET_MAP = {"2": 2, "4": 4, "8": 8, "24": 24, ">24": 32}
MEMORY_BUCKET_MAP = {"2": 2, "4": 4, "8": 8, "32": 32, "64": 64, ">64": 128}

ROLL_WINDOWS = {"1h": 12, "3h": 36, "6h": 72}
FORECAST_HORIZON = 36  # 3h ahead, in 5-min steps

# AWS Trusted Advisor's "Low Utilization Amazon EC2 Instances" check flags an
# instance as low-utilization at <=10% average daily CPU (sustained on >=4 of
# the previous 14 days; it also checks network I/O, which isn't available in
# this dataset). We use the same 10% CPU figure rather than an invented number,
# applied to our 6h rolling window instead of their 14-day one since that's
# the longest sustained window our ~18.5h data slice supports.
IDLE_CPU_THRESHOLD = 10.0

# No equivalent published single-number threshold exists for "over-provisioned"
# the way it does for idle -- AWS Compute Optimizer's rightsizing logic isn't a
# disclosed fixed cutoff. These remain engineering judgment calls, not a cited
# standard; flagged here rather than implied to be authoritative.
OVERPROV_CPU_THRESHOLD = 20.0  # avg cpu% below this on a large VM => over-provisioned
OVERPROV_MIN_CORES = 8         # only flag over-provisioning on VMs this size or larger


def add_rolling_features(df):
    df = df.sort_values(["vm_code", "timestamp"]).reset_index(drop=True)
    g = df.groupby("vm_code", group_keys=False)
    for label, window in ROLL_WINDOWS.items():
        df[f"avg_cpu_roll_{label}"] = g["avg_cpu"].transform(
            lambda s: s.rolling(window, min_periods=max(1, window // 4)).mean()
        )
        df[f"max_cpu_roll_{label}"] = g["max_cpu"].transform(
            lambda s: s.rolling(window, min_periods=max(1, window // 4)).max()
        )
    return df


def add_time_features(df):
    seconds_of_day = df["timestamp"] % 86400
    hour_of_day = seconds_of_day / 3600.0
    df["hour_sin"] = np.sin(2 * np.pi * hour_of_day / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour_of_day / 24)
    day_of_trace = (df["timestamp"] // 86400).astype("int32")
    df["day_of_week_sin"] = np.sin(2 * np.pi * (day_of_trace % 7) / 7)
    df["day_of_week_cos"] = np.cos(2 * np.pi * (day_of_trace % 7) / 7)
    return df


def add_allocation_features(df):
    df["allocated_cores"] = df["core_bucket"].astype(str).map(CORE_BUCKET_MAP).astype("float32")
    df["allocated_memory_gb"] = df["memory_bucket"].astype(str).map(MEMORY_BUCKET_MAP).astype("float32")
    # avg_cpu is already a % of this VM's own allocation; wasted_core_capacity
    # turns that into an absolute proxy for over-provisioning impact: a big
    # VM sitting at 5% utilization wastes far more than a small VM at 5%.
    df["wasted_core_capacity"] = df["allocated_cores"] * (1 - df["avg_cpu"] / 100.0).clip(lower=0)
    return df


def add_labels(df):
    df = df.sort_values(["vm_code", "timestamp"]).reset_index(drop=True)
    g = df.groupby("vm_code", group_keys=False)

    # Idle: 6h rolling avg CPU sustained below threshold.
    df["idle_status"] = (df["avg_cpu_roll_6h"] < IDLE_CPU_THRESHOLD).astype("boolean")
    df.loc[df["avg_cpu_roll_6h"].isna(), "idle_status"] = pd.NA

    # Over-provisioned: big VM (>= OVERPROV_MIN_CORES) with sustained low utilization.
    df["over_provisioned"] = (
        (df["allocated_cores"] >= OVERPROV_MIN_CORES) & (df["avg_cpu_roll_6h"] < OVERPROV_CPU_THRESHOLD)
    ).astype("boolean")
    df.loc[df["avg_cpu_roll_6h"].isna(), "over_provisioned"] = pd.NA

    # Future demand label: avg CPU over the next FORECAST_HORIZON samples (regression target).
    df["future_avg_cpu"] = g["avg_cpu"].transform(
        lambda s: s.shift(-1).rolling(FORECAST_HORIZON, min_periods=FORECAST_HORIZON).mean().shift(-(FORECAST_HORIZON - 1))
    )

    def demand_class(x):
        if pd.isna(x):
            return pd.NA
        if x < 20:
            return "low"
        if x < 60:
            return "medium"
        return "high"

    df["future_demand_class"] = df["future_avg_cpu"].map(demand_class)
    return df


def main():
    df = pd.read_parquet(f"{DATA_DIR}/joined_readings.parquet")
    print(f"Loaded {len(df):,} rows, {df.vm_code.nunique():,} VMs")

    df = add_rolling_features(df)
    df = add_time_features(df)
    df = add_allocation_features(df)
    df = add_labels(df)

    print("\nLabel distribution:")
    print("idle_status:\n", df["idle_status"].value_counts(dropna=False))
    print("over_provisioned:\n", df["over_provisioned"].value_counts(dropna=False))
    print("future_demand_class:\n", df["future_demand_class"].value_counts(dropna=False))

    out_path = f"{DATA_DIR}/features_labeled.parquet"
    df.to_parquet(out_path, index=False)
    print(f"\nWrote {out_path} ({len(df):,} rows, {df.shape[1]} columns)")


if __name__ == "__main__":
    main()
