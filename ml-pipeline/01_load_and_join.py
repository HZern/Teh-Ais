"""
Load a slice of Azure Public Dataset V2 (vmtable + a few vm_cpu_readings chunks),
join on vm id, and write a single parquet file for downstream feature engineering.

Schema confirmed against raw files + schema.csv from the dataset release:
  vmtable.csv.gz:        vm_id, subscription_id, deployment_id, ts_created, ts_deleted,
                         max_cpu, avg_cpu, p95_max_cpu, vm_category, core_bucket, memory_bucket
  vm_cpu_readings-*.csv.gz: timestamp, vm_id, min_cpu, max_cpu, avg_cpu   (per 5-min window)

Streamed in two passes to keep peak memory bounded: pass 1 counts per-VM
coverage across chunks without materializing the full 50M-row table; pass 2
re-reads and keeps only rows for a sampled set of densely-covered VMs.
"""
import glob
from collections import Counter

import numpy as np
import pandas as pd

DATA_DIR = "/Users/limhuizern/Documents/Hackathon"
READING_COLS = ["timestamp", "vm_id", "min_cpu", "max_cpu", "avg_cpu"]
VMTABLE_COLS = [
    "vm_id", "subscription_id", "deployment_id", "ts_created", "ts_deleted",
    "lifetime_max_cpu", "lifetime_avg_cpu", "lifetime_p95_max_cpu",
    "vm_category", "core_bucket", "memory_bucket",
]
VMTABLE_KEEP_COLS = [
    "vm_id", "ts_created", "ts_deleted",
    "lifetime_max_cpu", "lifetime_avg_cpu", "lifetime_p95_max_cpu",
    "vm_category", "core_bucket", "memory_bucket",
]

CHUNKSIZE = 1_000_000
N_VMS_TARGET = 8_000  # plenty for a hackathon demo; keeps memory + train time small
READING_DTYPES = {
    "timestamp": "int32", "vm_id": "string",
    "min_cpu": "float32", "max_cpu": "float32", "avg_cpu": "float32",
}


def cpu_files():
    return sorted(glob.glob(f"{DATA_DIR}/vm_cpu_readings-*.csv"))


def count_vm_coverage():
    print("Pass 1: counting per-VM reading coverage (streamed, no full materialization)...")
    counts = Counter()
    distinct_timestamps = set()
    for f in cpu_files():
        for chunk in pd.read_csv(f, header=None, names=READING_COLS, dtype=READING_DTYPES, chunksize=CHUNKSIZE):
            vc = chunk["vm_id"].value_counts()
            for vm_id, c in vc.items():
                counts[vm_id] += int(c)
            distinct_timestamps.update(chunk["timestamp"].unique().tolist())
        print(f"  scanned {f}")
    n_timestamps = len(distinct_timestamps)
    print(f"  total distinct timestamps across window: {n_timestamps}, total distinct VMs seen: {len(counts):,}")
    return counts, n_timestamps


def select_vms(counts, n_timestamps):
    dense = [vm for vm, c in counts.items() if c >= 0.95 * n_timestamps]
    print(f"  VMs with >=95% coverage: {len(dense):,}")
    rng = np.random.default_rng(42)
    if len(dense) > N_VMS_TARGET:
        dense = list(rng.choice(dense, size=N_VMS_TARGET, replace=False))
    print(f"  sampled {len(dense):,} VMs for the demo dataset")
    return set(dense)


def load_filtered_readings(selected_vms):
    print("Pass 2: re-reading chunks, keeping only sampled VMs...")
    frames = []
    for f in cpu_files():
        kept = []
        for chunk in pd.read_csv(f, header=None, names=READING_COLS, dtype=READING_DTYPES, chunksize=CHUNKSIZE):
            kept.append(chunk[chunk["vm_id"].isin(selected_vms)])
        file_df = pd.concat(kept, ignore_index=True)
        frames.append(file_df)
        print(f"  {f}: kept {len(file_df):,} rows")
    readings = pd.concat(frames, ignore_index=True)
    return readings


def load_vmtable(selected_vms):
    print("Loading vmtable.csv.gz (filtering to sampled VMs)...")
    chunks = []
    for chunk in pd.read_csv(
        f"{DATA_DIR}/vmtable.csv", header=None, names=VMTABLE_COLS,
        usecols=VMTABLE_KEEP_COLS,
        dtype={
            "vm_id": "string",
            "ts_created": "int64", "ts_deleted": "int64",
            "lifetime_max_cpu": "float32", "lifetime_avg_cpu": "float32", "lifetime_p95_max_cpu": "float32",
            "vm_category": "category", "core_bucket": "category", "memory_bucket": "category",
        },
        chunksize=CHUNKSIZE,
    ):
        chunks.append(chunk[chunk["vm_id"].isin(selected_vms)])
    vmtable = pd.concat(chunks, ignore_index=True)
    print(f"  matched {len(vmtable):,} VM metadata rows")
    return vmtable


def main():
    counts, n_timestamps = count_vm_coverage()
    selected_vms = select_vms(counts, n_timestamps)

    readings = load_filtered_readings(selected_vms)
    vmtable = load_vmtable(selected_vms)

    # Factorize the long hashed vm_id into a compact int code shared by both
    # tables before merging, then drop the original hash columns.
    ids_sorted = sorted(selected_vms)
    id_map = pd.Series(np.arange(len(ids_sorted), dtype="int32"), index=pd.Index(ids_sorted))
    readings["vm_code"] = readings["vm_id"].map(id_map).astype("int32")
    vmtable["vm_code"] = vmtable["vm_id"].map(id_map).astype("int32")

    vm_id_lookup = vmtable[["vm_code", "vm_id"]].drop_duplicates().set_index("vm_code")["vm_id"]
    vm_id_lookup.to_frame().to_parquet(f"{DATA_DIR}/vm_id_lookup.parquet")

    readings = readings.drop(columns=["vm_id"])
    vmtable = vmtable.drop(columns=["vm_id"])

    merged = readings.merge(vmtable, on="vm_code", how="inner")
    print(f"\nMerged dataset: {len(merged):,} rows, {merged.vm_code.nunique():,} unique VMs")

    out_path = f"{DATA_DIR}/joined_readings.parquet"
    merged.to_parquet(out_path, index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
