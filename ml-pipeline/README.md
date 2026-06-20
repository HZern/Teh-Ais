# ML Pipeline — Predictive Scaling & Resource Allocation

Trains on real Azure Public Dataset V2 VM workload traces (provider-agnostic stand-in for HILTI's AWS/EKS telemetry, which isn't publicly available) and produces per-VM recommendations: demand forecast, idle detection, rightsizing, anomaly flagging, and a risk level grounded in the Cloud Carbon Footprint methodology.

## Run order
1. `01_load_and_join.py` — downloads/loads vmtable + CPU reading chunks, joins on VM id (expects raw Azure files in the same directory; not committed here due to size)
2. `02_features_and_labels.py` — rolling CPU features, time features, idle/over-provisioned/demand labels
3. `03_train_models.py` — trains the demand forecast regressor, rightsizing classifier, and anomaly detector
4. `04_generate_output.py` — scores the latest snapshot per VM, writes `resource_recommendations.json`

Install dependencies first: `pip install -r requirements.txt`

## Output
`resource_recommendations.json` — the file other parts of this project (carbon-scoring, UI) should consume. See `handoff_to_carbon_scoring.md` for the full schema, methodology sources, and known limitations.

Note: trained model files (`.joblib`) and intermediate data (`.parquet`) are gitignored — regenerate by running the scripts in order.
