"""
Score the latest snapshot of every VM with the three trained models and emit
per-asset recommendations in the schema the carbon-scoring module consumes:

  vm_id, predicted_24h_demand, idle_status, current_allocation,
  recommended_allocation, suggested_action, rationale

Notes on scope, stated plainly rather than hidden in the numbers:
- "predicted_24h_demand" is computed by the 3h-ahead model (see
  02_features_and_labels.py for why the horizon is scaled down) -- the field
  name matches the spec the rest of the team is integrating against, but the
  actual forecast horizon is 3h given how much history this hackathon slice
  contains. Swapping in more vm_cpu_readings chunks and retraining gets a true
  24h horizon with no pipeline changes.
- The Azure trace has no memory *utilization* signal, only the VM's memory
  *allocation* bucket -- so recommended_memory_gb is left at the current
  allocation; only the core recommendation is utilization-driven.
- idle_status (and therefore the schedule_auto_shutdown action) uses AWS Trusted
  Advisor's published low-utilization criterion: <=10% average CPU, applied to
  our 6h rolling window (their check uses 14 days, sustained on >=4 days; we
  scale to 6h since that's the longest window our ~18.5h slice supports).
  over_provisioned's thresholds have no equivalent published standard to cite
  and remain engineering judgment calls -- noted as such, not implied to be
  authoritative.
- risk_level is grounded in the Cloud Carbon Footprint methodology
  (cloudcarbonfootprint.org/docs/methodology), the same framework the
  energy/carbon teammate's scoring cites. It converts each VM's unused core
  capacity into an estimated wasted-energy figure (kWh/day) using CCF's
  published AWS watt-per-vCPU coefficients and PUE, then buckets VMs into
  Low/Medium/High by percentile of wasted energy within the scored fleet --
  not an arbitrary ML-probability cutoff.
- decrease_autoscaling_min is the demand-forecast counterpart to
  increase_autoscaling_max: predicted demand notably below the 6h baseline
  triggers a recommendation to lower the autoscaling min bound. It's placed
  after idle_status/over_provisioned in suggest_action's priority order
  (sustained, already-observed signals win over a forecast), and it's framed
  as a reversible, elastic adjustment -- not a shutdown candidate -- since the
  workload is expected to recover, unlike a sustained-idle VM.
- aws_region and cost_per_core_hour were added because the carbon-scoring
  module's calculator needs them but the dataset has neither. HILTI's actual
  AWS region is not publicly disclosed -- the real AWS blog post about their
  EKS/Crossplane setup (aws.amazon.com/blogs/alps, "Modernizing Platform
  Management: Hilti Group's...") only shows "us-east-1" as a generic code
  sample, not a confirmed deployment region, and separately confirms HILTI
  uses Spot and Graviton instances. Given HILTI is headquartered in
  Liechtenstein with primarily European operations, eu-central-1 is used as a
  documented assumption, not a confirmed fact. cost_per_core_hour is AWS's
  real m6g (Graviton) on-demand price, $0.0385/vCPU-hour in us-east-1
  (consistent across instance sizes), adjusted +20% for typical EU regional
  pricing -- also an estimate, not an exact quoted price for eu-central-1.
"""
import json

import joblib
import numpy as np
import pandas as pd

DATA_DIR = "/Users/limhuizern/Documents/Hackathon"

CORE_BUCKETS = [2, 4, 8, 24, 32]   # 32 stands in for the open-ended '>24' bucket
TARGET_UTILIZATION = 0.6           # recommended size aims for ~60% avg utilization under predicted demand
DEMAND_DROP_THRESHOLD = 15.0       # predicted demand this many points below the 6h baseline triggers decrease_autoscaling_min

# Not in the Azure dataset; added only because the carbon-scoring calculator
# needs them. See module docstring for sourcing -- both are estimates, not
# confirmed HILTI figures.
AWS_REGION = "eu-central-1"
COST_PER_VCPU_HOUR_USD_US_EAST_1 = 0.0385  # AWS m6g (Graviton) on-demand, us-east-1
EU_REGION_PRICE_MARKUP = 1.20
COST_PER_CORE_HOUR = round(COST_PER_VCPU_HOUR_USD_US_EAST_1 * EU_REGION_PRICE_MARKUP, 4)

# Cloud Carbon Footprint methodology (cloudcarbonfootprint.org/docs/methodology),
# AWS coefficients -- HILTI's stack is AWS/EKS. Same formula + same published
# numbers the energy/carbon teammate's scoring is grounded in, so risk_level
# below is comparable to their work rather than an arbitrary ML cutoff.
AWS_MIN_WATTS_PER_VCPU = 0.74
AWS_MAX_WATTS_PER_VCPU = 3.5
AWS_PUE = 1.135

# risk_level buckets are percentiles of estimated wasted energy across the
# scored fleet, not fixed numbers -- "High" means "in the worst 20% for wasted
# energy among VMs we looked at," which adapts to whatever fleet is scored.
RISK_HIGH_PERCENTILE = 0.80
RISK_MEDIUM_PERCENTILE = 0.50


def estimate_wasted_energy_kwh_per_day(row):
    """CCF formula: Average Watts = Min + utilization * (Max - Min).
    Applied here to the *unused* core capacity (allocated - actually used)
    rather than the whole VM, so the result estimates the energy cost of
    over-provisioning/idling specifically, not the VM's total energy draw."""
    avg_watts_per_vcpu = AWS_MIN_WATTS_PER_VCPU + (row["avg_cpu_roll_6h"] / 100.0) * (
        AWS_MAX_WATTS_PER_VCPU - AWS_MIN_WATTS_PER_VCPU
    )
    wasted_watts = row["wasted_core_capacity"] * avg_watts_per_vcpu * AWS_PUE
    return wasted_watts * 24 / 1000.0


def next_bucket_at_or_above(value, buckets=CORE_BUCKETS):
    for b in buckets:
        if b >= value:
            return b
    return buckets[-1]


def latest_snapshot_per_vm(df):
    idx = df.groupby("vm_code")["timestamp"].idxmax()
    return df.loc[idx].reset_index(drop=True)


def score(df):
    demand_bundle = joblib.load(f"{DATA_DIR}/model_demand_forecast.joblib")
    rightsizing_bundle = joblib.load(f"{DATA_DIR}/model_rightsizing.joblib")
    idle_bundle = joblib.load(f"{DATA_DIR}/model_idle_anomaly.joblib")

    def build_X(cols):
        X = df[[c for c in cols if c in df.columns]].copy()
        cat = pd.get_dummies(df[["vm_category"]].astype(str), prefix=["vm_category"])
        X = pd.concat([X, cat], axis=1)
        return X.reindex(columns=cols, fill_value=0)

    demand_feature_cols = [c for c in demand_bundle["feature_cols"]]
    X_demand = build_X(demand_feature_cols)
    df["predicted_24h_demand"] = demand_bundle["model"].predict(X_demand)

    rightsizing_feature_cols = [c for c in rightsizing_bundle["feature_cols"]]
    X_right = build_X(rightsizing_feature_cols)
    df["over_provisioned_proba"] = rightsizing_bundle["model"].predict_proba(X_right)[:, 1]

    idle_cols = idle_bundle["feature_cols"]
    idle_input = df[idle_cols].fillna(df[idle_cols].median())
    df["anomaly_flag"] = idle_bundle["model"].predict(idle_input) == -1

    return df


def risk_level(wasted_kwh_per_day, high_cutoff, medium_cutoff):
    if wasted_kwh_per_day >= high_cutoff:
        return "High"
    if wasted_kwh_per_day >= medium_cutoff:
        return "Medium"
    return "Low"


def suggest_action(row):
    if bool(row["idle_status"]):
        return "schedule_auto_shutdown", (
            f"Sustained avg CPU {row['avg_cpu_roll_6h']:.1f}% over the last 6h on a "
            f"{row['allocated_cores']:.0f}-core VM -- at or below the 10% threshold AWS "
            f"Trusted Advisor uses to flag low-utilization EC2 instances. "
            f"Candidate for auto-shutdown scheduling or consolidation onto another node."
        )
    if row["over_provisioned_proba"] >= 0.5:
        return "downsize_instance", (
            f"Avg CPU {row['avg_cpu_roll_6h']:.1f}% over the last 6h on a "
            f"{row['allocated_cores']:.0f}-core VM (over-provisioning probability "
            f"{row['over_provisioned_proba']:.2f}). Recommend reducing the instance size."
        )
    if row["anomaly_flag"] and row["predicted_24h_demand"] > row["avg_cpu_roll_6h"] + 15:
        return "investigate_demand_spike", (
            f"Unusual utilization pattern flagged (anomaly score) with predicted near-term "
            f"demand {row['predicted_24h_demand']:.1f}% rising from a {row['avg_cpu_roll_6h']:.1f}% "
            f"6h baseline. Review before autoscaling reacts on its own."
        )
    if row["predicted_24h_demand"] > 75:
        return "increase_autoscaling_max", (
            f"Predicted near-term demand {row['predicted_24h_demand']:.1f}% is approaching "
            f"capacity on a {row['allocated_cores']:.0f}-core VM. Recommend raising the "
            f"autoscaling max bound to avoid throttling."
        )
    if row["predicted_24h_demand"] < row["avg_cpu_roll_6h"] - DEMAND_DROP_THRESHOLD:
        return "decrease_autoscaling_min", (
            f"Predicted near-term demand {row['predicted_24h_demand']:.1f}% is well below the "
            f"{row['avg_cpu_roll_6h']:.1f}% 6h baseline on a {row['allocated_cores']:.0f}-core VM. "
            f"Forecast-based, not a sustained-idle finding -- recommend lowering the "
            f"autoscaling min bound rather than a permanent resize, since demand is expected "
            f"to recover."
        )
    return "no_action_needed", (
        f"Avg CPU {row['avg_cpu_roll_6h']:.1f}% over the last 6h on a "
        f"{row['allocated_cores']:.0f}-core VM is within a healthy operating range; "
        f"predicted near-term demand {row['predicted_24h_demand']:.1f}%."
    )


def build_records(df, vm_id_lookup):
    wasted_kwh = df.apply(estimate_wasted_energy_kwh_per_day, axis=1)
    high_cutoff = wasted_kwh.quantile(RISK_HIGH_PERCENTILE)
    medium_cutoff = wasted_kwh.quantile(RISK_MEDIUM_PERCENTILE)
    print(f"  risk_level cutoffs (wasted kWh/day): High >= {high_cutoff:.3f}, Medium >= {medium_cutoff:.3f}")

    records = []
    for (_, row), wasted in zip(df.iterrows(), wasted_kwh):
        action, rationale = suggest_action(row)
        recommended_cores = row["allocated_cores"]
        if action == "downsize_instance":
            implied_cores = (row["allocated_cores"] * row["avg_cpu_roll_6h"] / 100.0) / TARGET_UTILIZATION
            # Clamp to current allocation -- a "downsize" must never recommend
            # *more* cores than the VM already has, but bucket rounding can
            # overshoot when the implied need lands just above the current bucket.
            recommended_cores = min(
                next_bucket_at_or_above(max(implied_cores, CORE_BUCKETS[0])),
                row["allocated_cores"],
            )
        elif action == "increase_autoscaling_max":
            implied_cores = (row["allocated_cores"] * row["predicted_24h_demand"] / 100.0) / TARGET_UTILIZATION
            recommended_cores = next_bucket_at_or_above(max(implied_cores, row["allocated_cores"]))
        elif action == "decrease_autoscaling_min":
            implied_cores = (row["allocated_cores"] * row["predicted_24h_demand"] / 100.0) / TARGET_UTILIZATION
            recommended_cores = min(
                next_bucket_at_or_above(max(implied_cores, CORE_BUCKETS[0])),
                row["allocated_cores"],
            )

        records.append({
            "vm_id": vm_id_lookup.get(row["vm_code"], str(row["vm_code"])),
            "predicted_24h_demand_pct": round(float(row["predicted_24h_demand"]), 2),
            "idle_status": bool(row["idle_status"]),
            "anomaly_flag": bool(row["anomaly_flag"]),
            "risk_level": risk_level(wasted, high_cutoff, medium_cutoff),
            "estimated_wasted_energy_kwh_per_day": round(float(wasted), 4),
            "current_allocation": {
                "cores": float(row["allocated_cores"]),
                "memory_gb": float(row["allocated_memory_gb"]),
            },
            "recommended_allocation": {
                "cores": float(recommended_cores),
                "memory_gb": float(row["allocated_memory_gb"]),  # no memory utilization signal in this trace
            },
            "suggested_action": action,
            "rationale": rationale,
            "aws_region": AWS_REGION,
            "cost_per_core_hour": COST_PER_CORE_HOUR,
        })
    return records


def main():
    df = pd.read_parquet(f"{DATA_DIR}/features_labeled.parquet")
    latest = latest_snapshot_per_vm(df)
    print(f"Scoring latest snapshot for {len(latest):,} VMs")

    required = ["avg_cpu_roll_1h", "avg_cpu_roll_3h", "avg_cpu_roll_6h", "idle_status"]
    latest = latest.dropna(subset=required).reset_index(drop=True)
    print(f"  {len(latest):,} VMs have enough history for scoring")

    latest = score(latest)

    vm_id_lookup_df = pd.read_parquet(f"{DATA_DIR}/vm_id_lookup.parquet")
    vm_id_lookup = vm_id_lookup_df["vm_id"].to_dict()

    records = build_records(latest, vm_id_lookup)

    action_counts = pd.Series([r["suggested_action"] for r in records]).value_counts()
    print("\nSuggested action breakdown:")
    print(action_counts.to_string())

    out_path = f"{DATA_DIR}/resource_recommendations.json"
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"\nWrote {len(records):,} records to {out_path}")
    print("\nSample record:")
    print(json.dumps(records[0], indent=2))


if __name__ == "__main__":
    main()
