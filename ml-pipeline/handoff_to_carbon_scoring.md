# Handoff: ML Pipeline Output → Carbon/Energy Scoring Module

## Context
HILTI hackathon, "Secure & Energy-Aware Cloud Platforms" track. HILTI's real stack is AWS + Kubernetes (EKS), provisioned via Crossplane/Flux. No public HILTI cloud telemetry exists, so the ML pipeline trains on real Azure Public Dataset V2 VM workload traces as a provider-agnostic stand-in (CPU utilization behavior — idle, over-provisioned, demand spikes — is fundamentally provider-agnostic; framed to judges as "trained on real-world cloud VM utilization patterns, applied to HILTI's AWS/EKS environment since internal telemetry isn't available").

## What the ML pipeline produces
File: `resource_recommendations.json` — one record per VM, 8,000 VMs scored. Schema per record:

```json
{
  "vm_id": "string (hashed VM identifier)",
  "predicted_24h_demand_pct": 4.12,        // forecast avg CPU%, see caveat below
  "idle_status": true,                      // bool, rule-based: 6h avg CPU <= 10% (AWS Trusted Advisor's published low-utilization criterion, not an invented number)
  "anomaly_flag": false,                    // bool, IsolationForest unsupervised outlier flag
  "risk_level": "High",                     // "Low" | "Medium" | "High" -- see methodology below
  "estimated_wasted_energy_kwh_per_day": 0.0427,  // the number risk_level is bucketed from
  "current_allocation": {"cores": 2.0, "memory_gb": 2.0},
  "recommended_allocation": {"cores": 2.0, "memory_gb": 2.0},
  "suggested_action": "schedule_auto_shutdown",  // enum, see below
  "rationale": "free text explanation",
  "aws_region": "eu-central-1",             // NEW, see "added fields" section below
  "cost_per_core_hour": 0.0462              // NEW, see "added fields" section below
}
```

`suggested_action` enum (six values now, one added since the first handoff): `schedule_auto_shutdown`, `downsize_instance`, `increase_autoscaling_max`, `decrease_autoscaling_min`, `investigate_demand_spike`, `no_action_needed`.

## Changes since the first handoff (action required on your side)

1. **`idle_status` threshold changed from 5% to 10%.** Re-grounded in AWS Trusted Advisor's actual published "Low Utilization Amazon EC2 Instances" check. No schema change, just more VMs now qualify as idle than before (~762K rows → ~1.24M rows hit the rule). No action needed on your end, just don't be surprised the counts shifted if you compared against an earlier version of the file.

2. **`aws_region` and `cost_per_core_hour` are new fields**, added specifically because your calculator's `_validate_ml_recommendation` doesn't require them but `_ml_cost_saved_monthly`/`calculate_ml_recommendation_report` use them when present. Neither is a confirmed HILTI fact:
   - `aws_region: "eu-central-1"` — HILTI's real AWS region isn't publicly disclosed. The actual AWS blog post about their EKS/Crossplane/Karpenter setup only shows `us-east-1` as a generic code sample, not a real deployment detail. Defaulted to Frankfurt since HILTI is Liechtenstein-headquartered with primarily European operations. That same blog post confirms HILTI uses Spot and Graviton instances, which is real and worth keeping in the pitch.
   - `cost_per_core_hour: 0.0462` — AWS's real Graviton (m6g) on-demand price is $0.0385/vCPU-hour in us-east-1; adjusted +20% for typical EU regional pricing. Still an estimate, not a quoted eu-central-1 price.
   - Both are constant across all 8,000 records (same region/price applied fleet-wide) — they're not per-VM-varying in this dataset.

3. **New action: `decrease_autoscaling_min`.** This is the demand-forecast counterpart to `increase_autoscaling_max` — fires when predicted near-term demand drops >15 points below the current 6h baseline. **Important: your code's `calculate_ml_recommendation_report` does not currently exclude this action from the full wasted-energy claim.** I checked — right now it falls into the `else` branch alongside `schedule_auto_shutdown`/`downsize_instance` and gets `actionable_kwh_day = wasted_kwh_day`, claiming the *entire* wasted-capacity number as a guaranteed saving. That's an overclaim: this action is forecast-based (lower confidence than the sustained-idle rule) and reversible — the VM keeps running, only an autoscaling *bound* changes, and savings only materialize if the system actually scales down within that window, which isn't guaranteed the way a shutdown is. Recommend adding `"decrease_autoscaling_min"` to the same exclusion set as `increase_autoscaling_max`/`investigate_demand_spike`/`no_action_needed` (i.e. `actionable_kwh_day = 0.0`), or computing a separate, explicitly discounted estimate for it if you want to claim partial credit. Also add it to your `MlSuggestedAction` Literal type for completeness (it's just a type hint, won't crash without it, but worth keeping accurate).

## Sources/frameworks used in the ML pipeline (cite these correctly, don't blend)

| What | Source | Used for |
|---|---|---|
| VM workload data | Azure Public Dataset V2 (github.com/Azure/AzurePublicDataset) | Training data — real CPU utilization traces, stand-in for missing HILTI telemetry |
| Utilization → energy formula | Cloud Carbon Footprint methodology (cloudcarbonfootprint.org/docs/methodology) | Converts each VM's unused core capacity into estimated wasted watts/kWh. AWS coefficients used: min 0.74W/vCPU, max 3.5W/vCPU, PUE 1.135 |
| `risk_level` bucketing | Derived from the CCF-based wasted-energy estimate above, bucketed by percentile across the scored fleet (top 20% = High, next 30% = Medium, rest = Low) | Not an arbitrary ML-probability cutoff — grounded in the same CCF numbers your carbon scoring should use |
| HILTI's actual commitments | HILTI 2025 Annual Report, Sustainability Statements (pages 33-42) | Narrative/context grounding — see critical nuance below |

## Critical nuance from HILTI's actual annual report (do not skip this)
HILTI reports Scope 2 emissions as **zero** (market-based) for their own operations, achieved via purchased Renewable Energy Certificates / Guarantees of Origin + their own solar generation. **This covers HILTI's own buildings/manufacturing electricity, not their cloud vendor's data centers.** AWS buys its own electricity for AWS data centers — HILTI's RECs don't touch that. Cloud compute emissions fall under **Scope 3** (purchased services), a category HILTI's existing renewable-electricity program does not zero out.

**Why this matters for your part:** this is the actual, citable reason the carbon-scoring module's work (and the ML rightsizing/idle-detection pipeline feeding it) has real value — it targets a gap HILTI's current 100% green electricity claim does NOT cover. Frame your carbon/energy scoring output around Scope 3 cloud emissions specifically, not Scope 2, and you'll be technically accurate against their own disclosures. HILTI's report also confirms they use the GHG Protocol and have SBTi-validated targets (validated 2024, aligned to 1.5°C, 8% YoY emissions reduction in 2025) — useful for citing the standard your scoring methodology should align with.

## What's expected from the carbon-scoring module
1. Consume `resource_recommendations.json` per VM.
2. Use `current_allocation` vs `recommended_allocation` (cores) to estimate the carbon/cost delta if the `suggested_action` were applied — e.g., for `downsize_instance`, compute emissions avoided by moving from current to recommended cores.
3. `estimated_wasted_energy_kwh_per_day` is already CCF-formula-based — you can convert this directly to CO2e using a grid carbon intensity factor (CCF cites EPA eGRID2023 / EEA / provider-published regional intensity — pick the appropriate AWS region's published intensity, not a generic global average, for accuracy).
4. Aggregate across all 8,000 VMs to produce a fleet-level "potential Scope 3 cloud emissions reduction" figure — this is the headline number for the pitch.
5. Frame all output as Scope 3, not Scope 2, per the nuance above.

## Known limitations to carry forward, state plainly, don't hide
- `predicted_24h_demand_pct` is actually a 3h-ahead forecast — the hackathon data slice only covers ~18.5h of history, not enough for a true 24h-ahead model. Field name matches the agreed schema; the actual horizon is shorter. Scales to real 24h with more data, no pipeline changes needed.
- No memory *utilization* signal exists in the Azure trace (only static memory allocation bucket) — `recommended_allocation.memory_gb` is always unchanged from current; only core recommendations are utilization-driven. Don't claim memory-based carbon savings from this output.
- All VM-level numbers are from the Azure dataset, not real HILTI infrastructure — any energy/carbon totals you compute should be framed as "estimated based on real-world cloud VM utilization patterns" rather than presented as HILTI's actual measured footprint.
