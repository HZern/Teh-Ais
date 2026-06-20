from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from sustainability_calculator import SustainabilityCalculator


DEFAULT_INPUT = Path("/Users/brandonng/Downloads/resource_recommendations.json")
DEFAULT_OUTPUT = Path("/Users/brandonng/Documents/ImagineHack/person5_dashboard_output.json")


def load_ml_recommendations(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Expected resource_recommendations.json to contain a list")

    return data


def build_person5_dashboard_output(
    recommendations: list[dict[str, Any]],
    sustainability_report: dict[str, Any],
) -> dict[str, Any]:
    action_distribution = Counter(record["suggested_action"] for record in recommendations)
    risk_distribution = Counter(record["risk_level"] for record in recommendations)
    region_distribution = Counter(record.get("aws_region", "missing") for record in recommendations)

    fleet_summary = sustainability_report["fleet_summary"]

    return {
        "executive_summary": {
            "vm_count": fleet_summary["vm_count"],
            "annual_energy_saved_kwh": fleet_summary[
                "potential_scope3_cloud_energy_saved_kwh_annual"
            ],
            "annual_scope3_cloud_carbon_saved_kg": fleet_summary[
                "potential_scope3_cloud_carbon_saved_kg_annual"
            ],
            "annual_scope3_cloud_carbon_saved_tonnes": round(
                fleet_summary["potential_scope3_cloud_carbon_saved_kg_annual"] / 1000,
                2,
            ),
            "monthly_cost_saving_usd": fleet_summary["estimated_cost_saved_monthly"],
            "headline": (
                "Estimated Scope 3 cloud optimization opportunity from ML-scored "
                "AWS/EKS workload recommendations."
            ),
        },
        "carbon_widget": {
            "daily_kg_co2e_saved": fleet_summary[
                "potential_scope3_cloud_carbon_saved_kg_day"
            ],
            "monthly_kg_co2e_saved": fleet_summary[
                "potential_scope3_cloud_carbon_saved_kg_monthly"
            ],
            "annual_kg_co2e_saved": fleet_summary[
                "potential_scope3_cloud_carbon_saved_kg_annual"
            ],
            "scope_boundary": "Estimated Scope 3 cloud services impact, not Hilti Scope 2 electricity.",
        },
        "energy_widget": {
            "daily_kwh_saved": fleet_summary[
                "potential_scope3_cloud_energy_saved_kwh_day"
            ],
            "monthly_kwh_saved": fleet_summary[
                "potential_scope3_cloud_energy_saved_kwh_monthly"
            ],
            "annual_kwh_saved": fleet_summary[
                "potential_scope3_cloud_energy_saved_kwh_annual"
            ],
        },
        "cost_widget": {
            "monthly_saving_usd": fleet_summary["estimated_cost_saved_monthly"],
            "annualized_saving_usd": (
                round(fleet_summary["estimated_cost_saved_monthly"] * 12, 2)
                if fleet_summary["estimated_cost_saved_monthly"] is not None
                else None
            ),
            "cost_assumption": "Uses cost_per_core_hour from ML output when present.",
        },
        "recommendation_distribution": {
            "by_action": dict(action_distribution),
            "by_risk_level": dict(risk_distribution),
            "by_region": dict(region_distribution),
        },
        "recommendation_cards": [
            {
                "rank": index,
                "vm_id": item["vm_id"],
                "action": item["suggested_action"],
                "risk_level": item["risk_level"],
                "region": item["carbon"]["aws_region"],
                "current_cores": item["allocation"]["current_cores"],
                "recommended_cores": item["allocation"]["recommended_cores"],
                "annual_energy_saved_kwh": item["energy"]["saved_kwh_annual"],
                "annual_carbon_saved_kg": item["carbon"]["saved_kg_co2e_annual"],
                "monthly_cost_saved_usd": item["cost"]["saved_monthly"],
                "rationale": item["explainability"]["rationale"],
            }
            for index, item in enumerate(
                sustainability_report["top_recommendations"],
                start=1,
            )
        ],
        "methodology_notes": {
            "ml_input": "Azure Public Dataset V2 utilization patterns used as stand-in for missing Hilti telemetry.",
            "energy_method": "ML pipeline CCF-based estimated_wasted_energy_kwh_per_day.",
            "carbon_method": "Energy saved multiplied by AWS regional carbon intensity factor.",
            "scope3_note": "Cloud vendor data center electricity is treated as purchased cloud services impact.",
            "limitations": [
                "Not measured Hilti cloud telemetry.",
                "Not audited GHG inventory reporting.",
                "predicted_24h_demand_pct is currently a 3h-ahead forecast field.",
                "Memory utilization is not available, so memory carbon savings are not claimed.",
            ],
        },
        "raw_sustainability_report": sustainability_report,
    }


def print_demo_output(output: dict[str, Any], output_path: Path) -> None:
    print("=== ML -> Sustainability -> Person 5 Dashboard Test ===")
    print(f"Dashboard output written to: {output_path}")

    print("\n=== Executive Summary ===")
    print(json.dumps(output["executive_summary"], indent=2))

    print("\n=== Carbon Widget ===")
    print(json.dumps(output["carbon_widget"], indent=2))

    print("\n=== Energy Widget ===")
    print(json.dumps(output["energy_widget"], indent=2))

    print("\n=== Cost Widget ===")
    print(json.dumps(output["cost_widget"], indent=2))

    print("\n=== Recommendation Distribution ===")
    print(json.dumps(output["recommendation_distribution"], indent=2))

    print("\n=== Top 3 Recommendation Cards ===")
    print(json.dumps(output["recommendation_cards"][:3], indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test ML recommendation output and generate Person 5 dashboard JSON."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to resource_recommendations.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for Person 5 dashboard output JSON",
    )
    args = parser.parse_args()

    recommendations = load_ml_recommendations(args.input)
    sustainability_report = SustainabilityCalculator().aggregate_ml_recommendations(
        recommendations
    )
    dashboard_output = build_person5_dashboard_output(
        recommendations=recommendations,
        sustainability_report=sustainability_report,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(dashboard_output, file, indent=2)

    print_demo_output(dashboard_output, args.output)


if __name__ == "__main__":
    main()
