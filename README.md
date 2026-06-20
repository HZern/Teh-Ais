# Teh-Ais CloudOps Dashboard

## Project Description

Teh-Ais CloudOps Dashboard is a manager-friendly cloud operations prototype for cybersecurity configuration checks and AI/ML workload optimisation. It helps technical and non-technical users identify unsafe cloud configurations, review workload inefficiencies, and view clear recommendations for action.

This project has three main parts:

- `ml-pipeline/` generates workload recommendation data.
- `ai/` prepares sustainability/carbon scoring handoff output.
- `cloudConfigCheck/` runs the backend scanner and Streamlit frontend dashboards.

## Team

Team name: Teh Ais

Team members:

- Tan Hong Guan
- Brandon Ng Chee Wern
- Gavyn Teh Kye Quan
- Lim Hui Zern
- Bradley Hoh Lok Yew

## Technologies Used

- Python 3.10+
- Streamlit frontend
- Python HTTP backend
- AWS-style cloud configuration scanning
- pandas, numpy, scikit-learn, xgboost, joblib, and pyarrow for ML pipeline work
- Standard-library sustainability/carbon scoring scripts

## Challenge And Approach

### Cybersecurity Configuration Check

Cloud environments are often managed by teams with different levels of cloud security knowledge. This can lead to inconsistent configurations and risky misconfigurations such as public storage, exposed server access, excessive permissions, public databases, missing audit logging, insecure public endpoints, and over-permissive serverless roles.

Our approach is to build a cloud security monitoring module that automatically checks AWS-style cloud configuration data against professional security baselines. The dashboard separates manager-friendly explanations from technician-focused details so each user can understand what is safe, what needs review, and what requires urgent action.

### AI/ML Workload Optimisation

Cloud workloads can become idle, underutilized, or over-provisioned, creating unnecessary cost and carbon impact. The workload analytics module identifies these patterns and recommends actions such as shutdown, rightsizing, scheduling, or migration.

The ML pipeline focuses on explainable recommendations supported by usage patterns. It also produces optimized-state values such as runtime, vCPU, RAM, and storage so downstream impact calculations can estimate cost and carbon savings.

## Usage Overview

Use Python 3.10+.

## 1. Create And Activate A Python Environment

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

On Windows PowerShell:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 2. Install Dependencies

### Quick Install

From the repo root:

```bash
pip install -r ml-pipeline/requirements.txt
pip install -r cloudConfigCheck/frontend/requirements.txt
```

### Dependency Notes

ML pipeline files under `ml-pipeline/` require:

```bash
pip install pandas numpy scikit-learn xgboost joblib pyarrow
```

These are listed in:

```text
ml-pipeline/requirements.txt
```

Streamlit frontend files under `cloudConfigCheck/frontend/` require:

```bash
pip install streamlit requests pandas altair
```

These are listed in:

```text
cloudConfigCheck/frontend/requirements.txt
```

Files under `ai/` use only the Python standard library. No extra package installation is required for:

```text
ai/sustainability_calculator.py
ai/generate_dashboard_output.py
```


The backend reads:

```text
ml-pipeline/resource_recommendations.json
```

## 4. Optional: Generate Dashboard Output

After the ML pipeline has produced `resource_recommendations.json`, generate the dashboard handoff JSON with:

```bash
python3 ai/generate_dashboard_output.py \
  --input ml-pipeline/resource_recommendations.json \
  --output person5_dashboard_output.json
```


## Recommended Run Order

From the repo root, prepare the environment and optional ML output:

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Install dependencies
pip install -r ml-pipeline/requirements.txt
pip install -r cloudConfigCheck/frontend/requirements.txt


Then run the backend in Terminal 1:

```bash
source .venv/bin/activate
cd cloudConfigCheck
python3 security_backend.py
```

Run the frontend in Terminal 2:

```bash
source .venv/bin/activate
cd cloudConfigCheck/frontend
python3 -m streamlit run pages/workload_analytics.py
```
