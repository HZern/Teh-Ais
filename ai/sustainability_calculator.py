from __future__ import annotations

import copy
import json
import math
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence, TypedDict


TaxonomyRating = Literal["Green", "Amber", "Red"]
RecommendationType = Literal[
    "shutdown",
    "rightsizing",
    "scheduling",
    "region_migration",
    "storage_tier_optimization",
]

MlSuggestedAction = Literal[
    "schedule_auto_shutdown",
    "downsize_instance",
    "increase_autoscaling_max",
    "decrease_autoscaling_min",
    "investigate_demand_spike",
    "no_action_needed",
]


class WorkloadInput(TypedDict, total=False):
    asset_id: str
    asset_type: str
    cpu_utilization: float
    memory_utilization: float
    allocated_vcpu: int
    allocated_ram_gb: float
    runtime_hours_month: float
    monthly_cost: float
    region: str
    ai_status: str
    confidence: float
    recommended_action: str
    recommendation_type: RecommendationType
    target_runtime_hours_month: float
    recommended_vcpu: int
    recommended_ram_gb: float
    target_region: str
    target_region_cost_multiplier: float
    storage_gb: float
    storage_tier: str
    target_storage_tier: str
    business_criticality: str
    implementation_effort: str
    annual_baseline_carbon_kg: float
    current_annual_carbon_kg: float
    target_reduction_percent: float
    baseline_year: int
    target_year: int
    current_year: int


class LegacySustainabilityReport(TypedDict):
    asset_id: str
    energy_kwh: float
    carbon_kg_co2e: float
    energy_waste_score: float
    taxonomy_rating: TaxonomyRating
    estimated_monthly_cost_saving: float


class MlPipelineRecommendation(TypedDict, total=False):
    vm_id: str
    predicted_24h_demand_pct: float
    idle_status: bool
    anomaly_flag: bool
    risk_level: str
    estimated_wasted_energy_kwh_per_day: float
    current_allocation: dict[str, float]
    recommended_allocation: dict[str, float]
    suggested_action: MlSuggestedAction
    rationale: str
    aws_region: str
    cost_per_core_hour: float


@dataclass(frozen=True)
class SustainabilityConstants:
    # Cloud Carbon Footprint-inspired energy coefficients for simulated VM data.
    idle_watts_per_vcpu: float = 5.0
    dynamic_watts_per_vcpu: float = 15.0
    ram_watts_per_gb: float = 0.4
    pue: float = 1.2

    # Target utilization assumptions used for rightsizing estimates.
    target_cpu_utilization: float = 0.60
    target_memory_utilization: float = 0.70
    minimum_capacity_ratio: float = 0.25

    # Month and scheduling assumptions.
    full_month_hours: float = 720.0
    office_hours_per_month: float = 220.0
    default_scheduling_reduction_ratio: float = 0.30

    # Energy waste score weights. These are surfaced in output metadata so the
    # score remains explainable and configurable rather than a black box.
    cpu_utilization_weight: float = 0.70
    memory_utilization_weight: float = 0.30
    waste_underutilization_weight: float = 0.40
    waste_runtime_weight: float = 0.30
    waste_oversize_weight: float = 0.30

    # Default recommendation assumptions.
    default_confidence: float = 1.0
    default_target_region_cost_multiplier: float = 1.0

    # Coefficients handed off by the ML pipeline. They are Cloud Carbon
    # Footprint methodology coefficients used by that pipeline for wasted-energy
    # scoring, not measured Hilti telemetry.
    ccf_min_watts_per_vcpu: float = 0.74
    ccf_max_watts_per_vcpu: float = 3.5
    ccf_pue: float = 1.135
    days_per_month: float = 30.0
    days_per_year: float = 365.0
    default_hilti_aws_region: str = "aws:eu-central-1"


@dataclass
class SustainabilityCalculator:
    constants: SustainabilityConstants = field(default_factory=SustainabilityConstants)

    # Simulated location-based carbon intensity factors in kg CO2e/kWh.
    # In production, this should be replaced by provider or electricityMap-style
    # regional factors with a source timestamp.
    region_carbon_intensity: Mapping[str, float] = field(
        default_factory=lambda: {
            "us-east-1": 0.38,
            "us-west-2": 0.20,
            "eu-west-1": 0.25,
            "eu-central-1": 0.36,
            "ap-southeast-1": 0.42,
            "ap-south-1": 0.71,
            "ap-northeast-1": 0.46,
            "sa-east-1": 0.09,
            "aws:us-east-1": 0.38,
            "aws:us-west-2": 0.20,
            "aws:eu-west-1": 0.25,
            "aws:eu-central-1": 0.36,
            "aws:ap-southeast-1": 0.42,
            "aws:ap-south-1": 0.71,
            "aws:ap-northeast-1": 0.46,
            "aws:sa-east-1": 0.09,
            "default": 0.40,
        }
    )

    # Simulated storage tier coefficients for storage optimization impact.
    storage_tier_kwh_per_gb_month: Mapping[str, float] = field(
        default_factory=lambda: {
            "hot": 0.012,
            "cool": 0.007,
            "archive": 0.002,
            "default": 0.010,
        }
    )

    storage_tier_cost_per_gb_month: Mapping[str, float] = field(
        default_factory=lambda: {
            "hot": 0.020,
            "cool": 0.010,
            "archive": 0.002,
            "default": 0.015,
        }
    )

    def calculate_ml_recommendation_report(
        self,
        recommendation: Mapping[str, Any],
        aws_region: str | None = None,
    ) -> dict[str, Any]:
        """Convert one ML recommendation record into Scope 3 cloud impact.

        The ML pipeline already calculated estimated wasted energy with a Cloud
        Carbon Footprint-based method. This function does not recalculate that
        number unless it is missing; it converts the wasted kWh into CO2e and
        dashboard-ready before/after impact.
        """
        self._validate_ml_recommendation(recommendation)

        region_source = "record"
        if "aws_region" in recommendation:
            region = str(recommendation["aws_region"])
        else:
            region = aws_region or self.constants.default_hilti_aws_region
            region_source = "module_default"
        carbon_intensity = self._carbon_intensity(region)
        action = str(recommendation["suggested_action"])
        wasted_kwh_day = self._ml_wasted_energy_kwh_per_day(recommendation)

        if action in {
            "increase_autoscaling_max",
            "decrease_autoscaling_min",
            "investigate_demand_spike",
            "no_action_needed",
        }:
            actionable_kwh_day = 0.0
        else:
            actionable_kwh_day = wasted_kwh_day

        carbon_saved_kg_day = actionable_kwh_day * carbon_intensity
        cost_saved_monthly = self._ml_cost_saved_monthly(recommendation, action)

        return {
            "vm_id": str(recommendation["vm_id"]),
            "cloud_provider": "AWS/EKS target environment",
            "training_data_context": "Azure Public Dataset V2 VM traces used as provider-agnostic stand-in",
            "scope_category": "Scope 3 cloud services estimate",
            "suggested_action": action,
            "risk_level": str(recommendation["risk_level"]),
            "idle_status": bool(recommendation["idle_status"]),
            "anomaly_flag": bool(recommendation["anomaly_flag"]),
            "predicted_demand_pct": float(recommendation["predicted_24h_demand_pct"]),
            "forecast_horizon_note": (
                "Field name says 24h, but current ML pipeline forecast is 3h-ahead "
                "because the hackathon slice has limited history."
            ),
            "allocation": {
                "current_cores": float(recommendation["current_allocation"]["cores"]),
                "recommended_cores": float(recommendation["recommended_allocation"]["cores"]),
                "current_memory_gb": float(recommendation["current_allocation"]["memory_gb"]),
                "recommended_memory_gb": float(
                    recommendation["recommended_allocation"]["memory_gb"]
                ),
                "memory_savings_claimed": False,
            },
            "energy": {
                "wasted_kwh_day": round(wasted_kwh_day, 6),
                "saved_kwh_day": round(actionable_kwh_day, 6),
                "saved_kwh_monthly": round(
                    actionable_kwh_day * self.constants.days_per_month,
                    4,
                ),
                "saved_kwh_annual": round(
                    actionable_kwh_day * self.constants.days_per_year,
                    4,
                ),
            },
            "carbon": {
                "saved_kg_co2e_day": round(carbon_saved_kg_day, 6),
                "saved_kg_co2e_monthly": round(
                    carbon_saved_kg_day * self.constants.days_per_month,
                    4,
                ),
                "saved_kg_co2e_annual": round(
                    carbon_saved_kg_day * self.constants.days_per_year,
                    4,
                ),
                "aws_region": region,
                "aws_region_source": region_source,
                "carbon_intensity_kg_per_kwh": carbon_intensity,
                "accounting_boundary": "Estimated Scope 3 purchased cloud services, not Hilti Scope 2 electricity",
                "carbon_intensity_source": "simulated AWS regional factor; replace with sourced AWS/provider or grid factor",
            },
            "cost": {
                "saved_monthly": cost_saved_monthly,
                "cost_method": (
                    "cost_per_core_hour estimate"
                    if cost_saved_monthly is not None
                    else "not_calculated_missing_unit_cost"
                ),
            },
            "explainability": {
                "energy_method": "Uses ML pipeline's CCF-based estimated_wasted_energy_kwh_per_day",
                "shutdown_energy_caveat": (
                    "For schedule_auto_shutdown, estimated_wasted_energy_kwh_per_day is "
                    "used as a conservative proxy for avoidable idle VM energy. It is "
                    "wasted unused-capacity energy, not a metered total VM draw; this is "
                    "reasonable for idle_status records at or below the ML pipeline's 10% CPU "
                    "idle threshold, but should be replaced with total VM energy if the "
                    "idle definition changes."
                    if action == "schedule_auto_shutdown"
                    else None
                ),
                "ccf_coefficients": {
                    "min_watts_per_vcpu": self.constants.ccf_min_watts_per_vcpu,
                    "max_watts_per_vcpu": self.constants.ccf_max_watts_per_vcpu,
                    "pue": self.constants.ccf_pue,
                },
                "rationale": str(recommendation.get("rationale", "")),
                "limitations": [
                    "Azure Public Dataset V2 traces are a stand-in, not measured Hilti telemetry.",
                    "Cloud impact is framed as Scope 3 cloud services, not Hilti market-based Scope 2.",
                    "Memory utilization is unavailable in the ML output, so memory carbon savings are not claimed.",
                ],
            },
        }

    def aggregate_ml_recommendations(
        self,
        recommendations: Sequence[Mapping[str, Any]],
        aws_region: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate per-VM ML recommendations into fleet-level headline impact."""
        reports = [
            self.calculate_ml_recommendation_report(record, aws_region)
            for record in recommendations
        ]

        total_energy_day = sum(report["energy"]["saved_kwh_day"] for report in reports)
        total_carbon_day = sum(report["carbon"]["saved_kg_co2e_day"] for report in reports)
        calculated_costs = [
            report["cost"]["saved_monthly"]
            for report in reports
            if report["cost"]["saved_monthly"] is not None
        ]

        by_action: dict[str, int] = {}
        by_risk: dict[str, int] = {}
        for report in reports:
            by_action[report["suggested_action"]] = by_action.get(report["suggested_action"], 0) + 1
            by_risk[report["risk_level"]] = by_risk.get(report["risk_level"], 0) + 1

        top_recommendations = sorted(
            reports,
            key=lambda report: report["carbon"]["saved_kg_co2e_annual"],
            reverse=True,
        )[:10]

        return {
            "fleet_summary": {
                "vm_count": len(reports),
                "potential_scope3_cloud_energy_saved_kwh_day": round(total_energy_day, 4),
                "potential_scope3_cloud_energy_saved_kwh_monthly": round(
                    total_energy_day * self.constants.days_per_month,
                    2,
                ),
                "potential_scope3_cloud_energy_saved_kwh_annual": round(
                    total_energy_day * self.constants.days_per_year,
                    2,
                ),
                "potential_scope3_cloud_carbon_saved_kg_day": round(total_carbon_day, 4),
                "potential_scope3_cloud_carbon_saved_kg_monthly": round(
                    total_carbon_day * self.constants.days_per_month,
                    2,
                ),
                "potential_scope3_cloud_carbon_saved_kg_annual": round(
                    total_carbon_day * self.constants.days_per_year,
                    2,
                ),
                "estimated_cost_saved_monthly": (
                    round(sum(calculated_costs), 2) if calculated_costs else None
                ),
            },
            "distribution": {
                "by_suggested_action": by_action,
                "by_risk_level": by_risk,
            },
            "top_recommendations": top_recommendations,
            "reporting_context": {
                "scope_category": "Scope 3 cloud services estimate",
                "hilti_scope2_note": (
                    "Hilti reports market-based Scope 2 as zero for its own operations; "
                    "cloud vendor data center electricity is outside that claim and should "
                    "be treated here as purchased cloud services impact."
                ),
                "data_source": "Azure Public Dataset V2 VM traces via ML pipeline",
                "method_basis": "ML pipeline CCF-based wasted energy converted with AWS regional carbon intensity",
            },
        }

    def load_resource_recommendations_report(
        self,
        path: str | Path,
        aws_region: str | None = None,
    ) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8") as file:
            recommendations = json.load(file)

        if not isinstance(recommendations, list):
            raise ValueError("resource_recommendations.json must contain a list of records")

        return self.aggregate_ml_recommendations(recommendations, aws_region)

    def calculate_energy_kwh(self, workload: Mapping[str, Any]) -> float:
        """Estimate monthly workload energy in kWh."""
        return round(self._calculate_energy_kwh_raw(workload), 2)

    def calculate_carbon_kg(self, energy_kwh: float, region: str) -> float:
        """Estimate emissions with Energy x regional carbon intensity."""
        if energy_kwh < 0:
            raise ValueError("energy_kwh must be non-negative")

        # Carbon formula:
        # kg CO2e = energy kWh * regional carbon intensity kg CO2e/kWh.
        # This aligns with GHG Protocol-style electricity emissions factor logic.
        return round(energy_kwh * self._carbon_intensity(region), 2)

    def calculate_energy_waste_score(self, workload: Mapping[str, Any]) -> float:
        """Return a normalized 0-100 operational energy waste score."""
        self._validate_workload(workload)

        underutilization_factor = self._calculate_underutilization_factor(workload)

        # Runtime factor formula:
        # runtime hours / full month hours. Always-on workloads receive a higher
        # penalty only when combined with underutilization and oversizing.
        runtime_factor = min(
            float(workload["runtime_hours_month"]) / self.constants.full_month_hours,
            1.0,
        )

        oversize_factor = self._calculate_oversize_factor(workload)

        # Energy Waste Score formula:
        # weighted normalized blend of underutilization, runtime, and oversizing.
        # The score supports prioritization; it is not a carbon accounting metric.
        score = 100.0 * (
            self.constants.waste_underutilization_weight * underutilization_factor
            + self.constants.waste_runtime_weight * runtime_factor
            + self.constants.waste_oversize_weight * oversize_factor
        )

        return round(self._clamp(score, 0.0, 100.0), 0)

    def calculate_cost_saving(
        self,
        workload: Mapping[str, Any],
        recommendation_type: RecommendationType | None = None,
    ) -> float:
        """Estimate monthly cost saving for the selected recommendation type."""
        impact = self.calculate_recommendation_impact(workload, recommendation_type)
        return float(impact["cost"]["saved_monthly"])

    def calculate_taxonomy_rating(
        self,
        workload: Mapping[str, Any],
        carbon_kg_co2e: float,
        energy_waste_score: float,
    ) -> TaxonomyRating:
        """Return a taxonomy-inspired Green/Amber/Red governance rating."""
        rating, _ = self.calculate_taxonomy_assessment(
            workload=workload,
            carbon_kg_co2e=carbon_kg_co2e,
            energy_waste_score=energy_waste_score,
        )
        return rating

    def calculate_taxonomy_assessment(
        self,
        workload: Mapping[str, Any],
        carbon_kg_co2e: float,
        energy_waste_score: float,
    ) -> tuple[TaxonomyRating, list[str]]:
        self._validate_workload(workload)

        effective_utilization = self._calculate_effective_utilization(workload)
        carbon_intensity = self._carbon_intensity(str(workload["region"]))
        reasons: list[str] = []

        # Red criteria: operationally wasteful or avoidably high-carbon.
        if effective_utilization < 0.25:
            reasons.append("Effective utilization below 25%.")
        if energy_waste_score >= 70:
            reasons.append("Energy waste score is 70 or higher.")
        if carbon_intensity > 0.55:
            reasons.append("Regional carbon intensity is above 0.55 kg CO2e/kWh.")

        if reasons:
            return "Red", reasons

        # Green criteria: efficient workload in a relatively lower-carbon region.
        if (
            effective_utilization >= 0.45
            and energy_waste_score < 35
            and carbon_intensity <= 0.35
        ):
            return "Green", [
                "Utilization, waste score, and regional carbon intensity meet Green criteria."
            ]

        return "Amber", [
            "Workload is acceptable but has optimization potential."
        ]

    def calculate_sbti_progress(
        self,
        baseline_carbon_kg: float,
        current_carbon_kg: float,
        target_reduction_percent: float,
    ) -> float:
        """Track progress against a reduction target; do not calculate carbon."""
        return self.calculate_sbti_metrics(
            baseline_carbon_kg=baseline_carbon_kg,
            current_carbon_kg=current_carbon_kg,
            target_reduction_percent=target_reduction_percent,
        )["sbti_progress_percent"]

    def calculate_sbti_metrics(
        self,
        baseline_carbon_kg: float,
        current_carbon_kg: float,
        target_reduction_percent: float,
        projected_annual_carbon_saved_kg: float = 0.0,
        baseline_year: int | None = None,
        target_year: int | None = 2050,
        current_year: int | None = None,
    ) -> dict[str, Any]:
        if baseline_carbon_kg <= 0:
            raise ValueError("baseline_carbon_kg must be greater than zero")
        if current_carbon_kg < 0:
            raise ValueError("current_carbon_kg must be non-negative")

        target_reduction_ratio = self._normalize_utilization(target_reduction_percent)
        if target_reduction_ratio <= 0:
            raise ValueError("target_reduction_percent must be greater than zero")

        # SBTi progress formula:
        # actual reduction / required target reduction * 100.
        # This uses SBTi correctly as target tracking, not as a carbon formula.
        required_reduction = baseline_carbon_kg * target_reduction_ratio
        actual_reduction = baseline_carbon_kg - current_carbon_kg
        sbti_progress = (actual_reduction / required_reduction) * 100.0

        emission_reduction_percent = (
            actual_reduction / baseline_carbon_kg
        ) * 100.0
        projected_annual_reduction_percent = (
            projected_annual_carbon_saved_kg / current_carbon_kg * 100.0
            if current_carbon_kg > 0
            else 0.0
        )

        target_gap_kg = max(required_reduction - actual_reduction, 0.0)
        on_track_status = "not_evaluated"

        if baseline_year is not None and current_year is not None and target_year:
            elapsed_years = max(current_year - baseline_year, 0)
            total_years = max(target_year - baseline_year, 1)
            expected_progress = min(elapsed_years / total_years * 100.0, 100.0)
            on_track_status = "on_track" if sbti_progress >= expected_progress else "behind"

        return {
            "sbti_progress_percent": round(self._clamp(sbti_progress, 0.0, 100.0), 2),
            "emission_reduction_percent": round(
                self._clamp(emission_reduction_percent, 0.0, 100.0), 2
            ),
            "target_achievement_percent": round(
                self._clamp(sbti_progress, 0.0, 100.0), 2
            ),
            "projected_annual_reduction_percent": round(
                max(projected_annual_reduction_percent, 0.0), 2
            ),
            "required_reduction_kg": round(required_reduction, 2),
            "actual_reduction_kg": round(max(actual_reduction, 0.0), 2),
            "target_gap_kg": round(target_gap_kg, 2),
            "net_zero_target_year": target_year,
            "on_track_status": on_track_status,
        }

    def calculate_recommendation_impact(
        self,
        workload: Mapping[str, Any],
        recommendation_type: RecommendationType | None = None,
    ) -> dict[str, Any]:
        """Calculate before/after energy, carbon, cost, and classification impact."""
        self._validate_workload(workload)

        recommendation_type = recommendation_type or self._infer_recommendation_type(workload)
        before_workload = dict(workload)
        after_workload = self._apply_recommendation_projection(
            workload=before_workload,
            recommendation_type=recommendation_type,
        )

        before_state = self._calculate_state(before_workload)
        after_state = self._calculate_state(after_workload)

        cost_before = float(before_workload["monthly_cost"])
        cost_after = float(after_workload["monthly_cost"])
        cost_saved = max(cost_before - cost_after, 0.0)

        energy_saved = max(before_state["energy_kwh"] - after_state["energy_kwh"], 0.0)
        carbon_saved = max(before_state["carbon_kg"] - after_state["carbon_kg"], 0.0)

        recommendation = self._build_recommendation_metadata(
            workload=before_workload,
            recommendation_type=recommendation_type,
            carbon_saved_kg=carbon_saved,
            cost_saved=cost_saved,
        )

        return {
            "asset_id": str(workload["asset_id"]),
            "asset_type": str(workload.get("asset_type", "Unknown")),
            "recommendation": recommendation,
            "energy": {
                "before_kwh_monthly": before_state["energy_kwh"],
                "after_kwh_monthly": after_state["energy_kwh"],
                "saved_kwh_monthly": round(energy_saved, 2),
                "saved_kwh_annual": round(energy_saved * 12.0, 2),
            },
            "carbon": {
                "before_kg_monthly": before_state["carbon_kg"],
                "after_kg_monthly": after_state["carbon_kg"],
                "saved_kg_monthly": round(carbon_saved, 2),
                "saved_kg_annual": round(carbon_saved * 12.0, 2),
                "carbon_intensity_before_kg_per_kwh": self._carbon_intensity(
                    str(before_workload["region"])
                ),
                "carbon_intensity_after_kg_per_kwh": self._carbon_intensity(
                    str(after_workload["region"])
                ),
                "accounting_method": "estimated_scope3_cloud_services_location_based_factor",
                "carbon_intensity_source": "simulated_region_factor; replace with sourced cloud/grid factor",
                "scope_boundary_note": (
                    "Cloud vendor data center electricity is treated as purchased "
                    "cloud services impact, not Hilti market-based Scope 2 electricity."
                ),
            },
            "cost": {
                "before_monthly": round(cost_before, 2),
                "after_monthly": round(cost_after, 2),
                "saved_monthly": round(cost_saved, 2),
                "saved_annual": round(cost_saved * 12.0, 2),
            },
            "sustainability": {
                "energy_waste_score_before": before_state["energy_waste_score"],
                "energy_waste_score_after": after_state["energy_waste_score"],
                "taxonomy_before": before_state["taxonomy_rating"],
                "taxonomy_after": after_state["taxonomy_rating"],
                "taxonomy_reasons_before": before_state["taxonomy_reasons"],
                "taxonomy_reasons_after": after_state["taxonomy_reasons"],
                "effective_utilization_before": round(
                    self._calculate_effective_utilization(before_workload), 4
                ),
                "effective_utilization_after": round(
                    self._calculate_effective_utilization(after_workload), 4
                ),
            },
            "explainability": {
                "primary_driver": self._primary_driver(before_workload),
                "formula_basis": "Power x Time x PUE x regional carbon intensity",
                "framework_alignment": [
                    "Cloud Carbon Footprint-inspired energy estimation",
                    "GHG Protocol-style electricity emissions factor logic",
                    "FinOps optimization principles",
                    "SBTi target tracking only",
                    "Taxonomy-inspired internal classification only",
                ],
                "judge_summary": self._judge_summary(recommendation_type),
            },
            "projected_workload": {
                "region": after_workload["region"],
                "runtime_hours_month": after_workload["runtime_hours_month"],
                "allocated_vcpu": after_workload["allocated_vcpu"],
                "allocated_ram_gb": after_workload["allocated_ram_gb"],
                "monthly_cost": round(float(after_workload["monthly_cost"]), 2),
            },
        }

    def generate_sustainability_report(self, workload: Mapping[str, Any]) -> dict[str, Any]:
        """Return a dashboard-ready sustainability report.

        The top-level legacy fields are retained for backwards compatibility.
        The nested sections are the preferred contract for Hilti-aligned
        before/after decision support.
        """
        impact = self.calculate_recommendation_impact(workload)

        sbti = None
        if {
            "annual_baseline_carbon_kg",
            "current_annual_carbon_kg",
            "target_reduction_percent",
        }.issubset(workload.keys()):
            sbti = self.calculate_sbti_metrics(
                baseline_carbon_kg=float(workload["annual_baseline_carbon_kg"]),
                current_carbon_kg=float(workload["current_annual_carbon_kg"]),
                target_reduction_percent=float(workload["target_reduction_percent"]),
                projected_annual_carbon_saved_kg=impact["carbon"]["saved_kg_annual"],
                baseline_year=workload.get("baseline_year"),
                current_year=workload.get("current_year"),
                target_year=workload.get("target_year", 2050),
            )

        report = {
            # Legacy headline fields.
            "asset_id": impact["asset_id"],
            "energy_kwh": impact["energy"]["before_kwh_monthly"],
            "carbon_kg_co2e": impact["carbon"]["before_kg_monthly"],
            "energy_waste_score": impact["sustainability"]["energy_waste_score_before"],
            "taxonomy_rating": impact["sustainability"]["taxonomy_before"],
            "estimated_monthly_cost_saving": impact["cost"]["saved_monthly"],
            # Preferred dashboard contract.
            **impact,
        }

        if sbti is not None:
            report["sbti"] = sbti

        return report

    def _calculate_energy_kwh_raw(self, workload: Mapping[str, Any]) -> float:
        self._validate_workload(workload)

        cpu_utilization = self._normalize_utilization(workload["cpu_utilization"])
        memory_utilization = self._normalize_utilization(workload["memory_utilization"])
        allocated_vcpu = float(workload["allocated_vcpu"])
        allocated_ram_gb = float(workload["allocated_ram_gb"])
        runtime_hours = float(workload["runtime_hours_month"])

        # vCPU power formula:
        # allocated vCPU * (idle watts + dynamic watts * CPU utilization).
        # This estimates compute power from provisioned capacity and utilization.
        vcpu_power_watts = allocated_vcpu * (
            self.constants.idle_watts_per_vcpu
            + self.constants.dynamic_watts_per_vcpu * cpu_utilization
        )

        # Memory power formula:
        # allocated RAM * watts per GB * memory activity factor.
        # A baseline activity factor is kept because allocated RAM consumes power
        # even when memory utilization is low.
        memory_activity_factor = 0.5 + 0.5 * memory_utilization
        memory_power_watts = (
            allocated_ram_gb
            * self.constants.ram_watts_per_gb
            * memory_activity_factor
        )

        # Optional storage energy formula:
        # storage GB * tier kWh/GB-month. This supports storage tier optimization.
        storage_energy_kwh = self._storage_energy_kwh(workload)

        # Energy formula:
        # ((compute watts + memory watts) * runtime hours * PUE) / 1000
        # plus storage tier energy. This is the module's Power x Time basis.
        compute_memory_energy_kwh = (
            (vcpu_power_watts + memory_power_watts)
            * runtime_hours
            * self.constants.pue
        ) / 1000.0

        return compute_memory_energy_kwh + storage_energy_kwh

    def _calculate_state(self, workload: Mapping[str, Any]) -> dict[str, Any]:
        energy_kwh = self.calculate_energy_kwh(workload)
        carbon_kg = self.calculate_carbon_kg(energy_kwh, str(workload["region"]))
        waste_score = self.calculate_energy_waste_score(workload)
        taxonomy_rating, taxonomy_reasons = self.calculate_taxonomy_assessment(
            workload=workload,
            carbon_kg_co2e=carbon_kg,
            energy_waste_score=waste_score,
        )

        return {
            "energy_kwh": energy_kwh,
            "carbon_kg": carbon_kg,
            "energy_waste_score": waste_score,
            "taxonomy_rating": taxonomy_rating,
            "taxonomy_reasons": taxonomy_reasons,
        }

    def _apply_recommendation_projection(
        self,
        workload: Mapping[str, Any],
        recommendation_type: RecommendationType,
    ) -> dict[str, Any]:
        projected = copy.deepcopy(dict(workload))
        confidence = self._clamp(
            float(projected.get("confidence", self.constants.default_confidence)),
            0.0,
            1.0,
        )
        monthly_cost = float(projected["monthly_cost"])
        runtime_hours = float(projected["runtime_hours_month"])

        if recommendation_type == "shutdown":
            target_runtime = float(
                projected.get(
                    "target_runtime_hours_month",
                    self.constants.office_hours_per_month,
                )
            )
            target_runtime = self._clamp(target_runtime, 0.0, runtime_hours)
            runtime_ratio = target_runtime / runtime_hours
            projected["runtime_hours_month"] = target_runtime
            projected["monthly_cost"] = monthly_cost * (
                1.0 - ((1.0 - runtime_ratio) * confidence)
            )

        elif recommendation_type == "rightsizing":
            current_vcpu = float(projected["allocated_vcpu"])
            current_ram_gb = float(projected["allocated_ram_gb"])
            recommended_size_ratio = self._calculate_recommended_size_ratio(projected)
            projected["allocated_vcpu"] = int(
                projected.get(
                    "recommended_vcpu",
                    max(1, math.ceil(float(projected["allocated_vcpu"]) * recommended_size_ratio)),
                )
            )
            projected["allocated_ram_gb"] = float(
                projected.get(
                    "recommended_ram_gb",
                    max(1.0, math.ceil(float(projected["allocated_ram_gb"]) * recommended_size_ratio)),
                )
            )
            projected["cpu_utilization"] = min(
                self._normalize_utilization(projected["cpu_utilization"])
                * current_vcpu
                / float(projected["allocated_vcpu"]),
                1.0,
            )
            projected["memory_utilization"] = min(
                self._normalize_utilization(projected["memory_utilization"])
                * current_ram_gb
                / float(projected["allocated_ram_gb"]),
                1.0,
            )
            projected["monthly_cost"] = monthly_cost * (
                1.0 - ((1.0 - recommended_size_ratio) * confidence)
            )

        elif recommendation_type == "scheduling":
            reduction_ratio = float(
                projected.get(
                    "runtime_reduction_ratio",
                    self.constants.default_scheduling_reduction_ratio,
                )
            )
            reduction_ratio = self._clamp(reduction_ratio, 0.0, 1.0)
            projected["runtime_hours_month"] = runtime_hours * (1.0 - reduction_ratio)
            projected["monthly_cost"] = monthly_cost * (1.0 - reduction_ratio * confidence)

        elif recommendation_type == "region_migration":
            projected["region"] = str(projected.get("target_region", projected["region"]))
            cost_multiplier = float(
                projected.get(
                    "target_region_cost_multiplier",
                    self.constants.default_target_region_cost_multiplier,
                )
            )
            projected["monthly_cost"] = monthly_cost * cost_multiplier

        elif recommendation_type == "storage_tier_optimization":
            projected["storage_tier"] = str(
                projected.get("target_storage_tier", projected.get("storage_tier", "cool"))
            )
            storage_gb = float(projected.get("storage_gb", 0.0))
            current_tier = str(workload.get("storage_tier", "default"))
            target_tier = str(projected["storage_tier"])
            current_storage_cost = storage_gb * self._storage_cost_per_gb(current_tier)
            target_storage_cost = storage_gb * self._storage_cost_per_gb(target_tier)
            projected["monthly_cost"] = max(
                monthly_cost - current_storage_cost + target_storage_cost,
                0.0,
            )

        else:
            raise ValueError(f"Unsupported recommendation_type: {recommendation_type}")

        return projected

    def _build_recommendation_metadata(
        self,
        workload: Mapping[str, Any],
        recommendation_type: RecommendationType,
        carbon_saved_kg: float,
        cost_saved: float,
    ) -> dict[str, Any]:
        confidence = self._clamp(
            float(workload.get("confidence", self.constants.default_confidence)),
            0.0,
            1.0,
        )
        priority = "High" if carbon_saved_kg >= 10 or cost_saved >= 500 else "Medium"
        if carbon_saved_kg < 2 and cost_saved < 50:
            priority = "Low"

        return {
            "type": recommendation_type,
            "action": str(workload.get("recommended_action", recommendation_type)),
            "confidence": round(confidence, 2),
            "priority": priority,
            "implementation_effort": str(workload.get("implementation_effort", "Medium")),
            "business_criticality": str(workload.get("business_criticality", "Unknown")),
        }

    def _calculate_effective_utilization(self, workload: Mapping[str, Any]) -> float:
        cpu_utilization = self._normalize_utilization(workload["cpu_utilization"])
        memory_utilization = self._normalize_utilization(workload["memory_utilization"])

        # Effective utilization formula:
        # weighted CPU and memory utilization. CPU carries more weight because it
        # often drives VM sizing decisions.
        return (
            self.constants.cpu_utilization_weight * cpu_utilization
            + self.constants.memory_utilization_weight * memory_utilization
        )

    def _calculate_underutilization_factor(self, workload: Mapping[str, Any]) -> float:
        # Underutilization formula:
        # 1 - effective utilization. Lower utilization means higher waste risk.
        return 1.0 - self._calculate_effective_utilization(workload)

    def _calculate_recommended_size_ratio(self, workload: Mapping[str, Any]) -> float:
        cpu_utilization = self._normalize_utilization(workload["cpu_utilization"])
        memory_utilization = self._normalize_utilization(workload["memory_utilization"])
        allocated_vcpu = int(workload["allocated_vcpu"])
        allocated_ram_gb = float(workload["allocated_ram_gb"])

        # Required vCPU formula:
        # allocated vCPU * max(actual utilization / target utilization, minimum
        # capacity). This estimates the capacity needed to reach healthy target
        # utilization while retaining a safety floor.
        required_vcpu = math.ceil(
            allocated_vcpu
            * max(
                cpu_utilization / self.constants.target_cpu_utilization,
                self.constants.minimum_capacity_ratio,
            )
        )

        # Required RAM formula:
        # allocated RAM * max(actual utilization / target utilization, minimum
        # capacity). This mirrors the CPU rightsizing method for memory.
        required_ram_gb = math.ceil(
            allocated_ram_gb
            * max(
                memory_utilization / self.constants.target_memory_utilization,
                self.constants.minimum_capacity_ratio,
            )
        )

        vcpu_ratio = required_vcpu / allocated_vcpu
        ram_ratio = required_ram_gb / allocated_ram_gb

        return self._clamp((vcpu_ratio + ram_ratio) / 2.0, 0.0, 1.0)

    def _calculate_oversize_factor(self, workload: Mapping[str, Any]) -> float:
        # Oversize factor formula:
        # 1 - recommended size ratio. A larger capacity gap means more waste.
        return 1.0 - self._calculate_recommended_size_ratio(workload)

    def _infer_recommendation_type(
        self,
        workload: Mapping[str, Any],
    ) -> RecommendationType:
        if "recommendation_type" in workload:
            return workload["recommendation_type"]  # type: ignore[return-value]

        action_text = str(workload.get("recommended_action", "")).lower()
        ai_status = str(workload.get("ai_status", "")).lower()

        if "region" in action_text or "migrat" in action_text:
            return "region_migration"
        if "storage" in action_text or "tier" in action_text:
            return "storage_tier_optimization"
        if "shutdown" in action_text or "shut" in action_text or "idle" in ai_status:
            return "shutdown"
        if "right" in action_text or "over" in ai_status:
            return "rightsizing"
        if "sched" in action_text or "schedule" in ai_status:
            return "scheduling"

        effective_utilization = self._calculate_effective_utilization(workload)
        oversize_factor = self._calculate_oversize_factor(workload)
        runtime_hours = float(workload["runtime_hours_month"])

        if effective_utilization < 0.20 and runtime_hours > self.constants.office_hours_per_month:
            return "shutdown"
        if oversize_factor >= 0.20:
            return "rightsizing"
        return "scheduling"

    def _primary_driver(self, workload: Mapping[str, Any]) -> str:
        if self._calculate_effective_utilization(workload) < 0.25:
            return "Low utilization"
        if float(workload["runtime_hours_month"]) >= self.constants.full_month_hours:
            return "Full-month runtime"
        if self._calculate_oversize_factor(workload) >= 0.30:
            return "Over-provisioned capacity"
        return "Optimization opportunity"

    @staticmethod
    def _judge_summary(recommendation_type: RecommendationType) -> str:
        summaries = {
            "shutdown": "Reducing idle runtime lowers energy, CO2, and cloud spend.",
            "rightsizing": "Reducing over-provisioned capacity lowers power demand and cost.",
            "scheduling": "Running workloads only when needed reduces runtime-driven impact.",
            "region_migration": "Moving to a lower-carbon region reduces CO2 per kWh.",
            "storage_tier_optimization": "Moving cold data to lower-energy storage reduces storage impact and cost.",
        }
        return summaries[recommendation_type]

    def _storage_energy_kwh(self, workload: Mapping[str, Any]) -> float:
        storage_gb = float(workload.get("storage_gb", 0.0))
        if storage_gb <= 0:
            return 0.0
        tier = str(workload.get("storage_tier", "default"))
        return storage_gb * self._storage_kwh_per_gb(tier)

    def _storage_kwh_per_gb(self, tier: str) -> float:
        return self.storage_tier_kwh_per_gb_month.get(
            tier,
            self.storage_tier_kwh_per_gb_month["default"],
        )

    def _storage_cost_per_gb(self, tier: str) -> float:
        return self.storage_tier_cost_per_gb_month.get(
            tier,
            self.storage_tier_cost_per_gb_month["default"],
        )

    def _ml_wasted_energy_kwh_per_day(self, recommendation: Mapping[str, Any]) -> float:
        if "estimated_wasted_energy_kwh_per_day" in recommendation:
            wasted_energy = float(recommendation["estimated_wasted_energy_kwh_per_day"])
            if wasted_energy < 0:
                raise ValueError("estimated_wasted_energy_kwh_per_day must be non-negative")
            return wasted_energy

        current_cores = float(recommendation["current_allocation"]["cores"])
        recommended_cores = float(recommendation["recommended_allocation"]["cores"])
        reducible_cores = max(current_cores - recommended_cores, 0.0)

        # Fallback only. The handoff says the ML pipeline already provides a
        # CCF-based wasted-energy estimate, so this branch should rarely run.
        watts_per_reducible_core = (
            self.constants.ccf_max_watts_per_vcpu
            - self.constants.ccf_min_watts_per_vcpu
        )
        return (
            reducible_cores
            * watts_per_reducible_core
            * 24.0
            * self.constants.ccf_pue
            / 1000.0
        )

    def _ml_cost_saved_monthly(
        self,
        recommendation: Mapping[str, Any],
        action: str,
    ) -> float | None:
        if "cost_per_core_hour" not in recommendation:
            return None

        if action not in {"schedule_auto_shutdown", "downsize_instance"}:
            return 0.0

        current_cores = float(recommendation["current_allocation"]["cores"])
        recommended_cores = float(recommendation["recommended_allocation"]["cores"])
        cost_per_core_hour = float(recommendation["cost_per_core_hour"])

        if cost_per_core_hour < 0:
            raise ValueError("cost_per_core_hour must be non-negative")

        if action == "downsize_instance":
            reducible_cores = max(current_cores - recommended_cores, 0.0)
            return round(
                reducible_cores
                * cost_per_core_hour
                * 24.0
                * self.constants.days_per_month,
                2,
            )

        if action == "schedule_auto_shutdown":
            # The ML handoff does not provide the exact shutdown window. Use the
            # wasted-energy field for carbon, and estimate cost only from the
            # same office-hours policy used elsewhere in this module.
            removable_runtime_ratio = (
                self.constants.full_month_hours - self.constants.office_hours_per_month
            ) / self.constants.full_month_hours
            return round(
                current_cores
                * cost_per_core_hour
                * self.constants.full_month_hours
                * removable_runtime_ratio,
                2,
            )

        return None

    def _carbon_intensity(self, region: str) -> float:
        return self.region_carbon_intensity.get(region, self.region_carbon_intensity["default"])

    @staticmethod
    def _normalize_utilization(value: float | int) -> float:
        utilization = float(value)

        if utilization < 0:
            raise ValueError("utilization must be non-negative")

        if utilization > 1.0:
            utilization = utilization / 100.0

        if utilization > 1.0:
            raise ValueError("utilization cannot exceed 100%")

        return utilization

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(value, maximum))

    @staticmethod
    def _validate_workload(workload: Mapping[str, Any]) -> None:
        required_fields = {
            "asset_id",
            "cpu_utilization",
            "memory_utilization",
            "allocated_vcpu",
            "allocated_ram_gb",
            "runtime_hours_month",
            "monthly_cost",
            "region",
        }

        missing_fields = required_fields - workload.keys()
        if missing_fields:
            raise ValueError(f"Missing required workload fields: {sorted(missing_fields)}")

        if int(workload["allocated_vcpu"]) <= 0:
            raise ValueError("allocated_vcpu must be greater than zero")

        if float(workload["allocated_ram_gb"]) <= 0:
            raise ValueError("allocated_ram_gb must be greater than zero")

        if float(workload["runtime_hours_month"]) <= 0:
            raise ValueError("runtime_hours_month must be greater than zero")

        if float(workload["monthly_cost"]) < 0:
            raise ValueError("monthly_cost must be non-negative")

    @staticmethod
    def _validate_ml_recommendation(recommendation: Mapping[str, Any]) -> None:
        required_fields = {
            "vm_id",
            "predicted_24h_demand_pct",
            "idle_status",
            "anomaly_flag",
            "risk_level",
            "current_allocation",
            "recommended_allocation",
            "suggested_action",
        }
        missing_fields = required_fields - recommendation.keys()
        if missing_fields:
            raise ValueError(f"Missing required ML recommendation fields: {sorted(missing_fields)}")

        for allocation_field in ("current_allocation", "recommended_allocation"):
            allocation = recommendation[allocation_field]
            if not isinstance(allocation, Mapping):
                raise ValueError(f"{allocation_field} must be an object")
            if "cores" not in allocation or "memory_gb" not in allocation:
                raise ValueError(f"{allocation_field} must include cores and memory_gb")
            if float(allocation["cores"]) <= 0:
                raise ValueError(f"{allocation_field}.cores must be greater than zero")
            if float(allocation["memory_gb"]) <= 0:
                raise ValueError(f"{allocation_field}.memory_gb must be greater than zero")


def generate_sustainability_report(workload: Mapping[str, Any]) -> dict[str, Any]:
    calculator = SustainabilityCalculator()
    return calculator.generate_sustainability_report(workload)


class TestSustainabilityCalculator(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = SustainabilityCalculator()
        self.sample_workload: WorkloadInput = {
            "asset_id": "vm-001",
            "asset_type": "VirtualMachine",
            "cpu_utilization": 12,
            "memory_utilization": 18,
            "allocated_vcpu": 8,
            "allocated_ram_gb": 32,
            "runtime_hours_month": 720,
            "region": "ap-southeast-1",
            "monthly_cost": 1200,
            "ai_status": "Idle",
            "confidence": 0.91,
            "recommended_action": "Auto-shutdown after office hours",
            "target_runtime_hours_month": 220,
            "annual_baseline_carbon_kg": 10_000,
            "current_annual_carbon_kg": 7_500,
            "target_reduction_percent": 40,
            "baseline_year": 2020,
            "current_year": 2026,
            "target_year": 2050,
        }
        self.sample_ml_recommendation: MlPipelineRecommendation = {
            "vm_id": "hashed-vm-001",
            "predicted_24h_demand_pct": 4.12,
            "idle_status": True,
            "anomaly_flag": False,
            "risk_level": "High",
            "estimated_wasted_energy_kwh_per_day": 0.0427,
            "current_allocation": {"cores": 2.0, "memory_gb": 2.0},
            "recommended_allocation": {"cores": 2.0, "memory_gb": 2.0},
            "suggested_action": "schedule_auto_shutdown",
            "rationale": "6h average CPU below idle threshold.",
            "aws_region": "aws:us-east-1",
            "cost_per_core_hour": 0.05,
        }

    def test_calculate_energy_kwh(self) -> None:
        self.assertEqual(
            self.calculator.calculate_energy_kwh(self.sample_workload),
            53.53,
        )

    def test_calculate_carbon_kg(self) -> None:
        self.assertEqual(
            self.calculator.calculate_carbon_kg(53.53, "ap-southeast-1"),
            22.48,
        )

    def test_calculate_energy_waste_score(self) -> None:
        self.assertEqual(
            self.calculator.calculate_energy_waste_score(self.sample_workload),
            87,
        )

    def test_calculate_cost_saving_shutdown(self) -> None:
        self.assertEqual(
            self.calculator.calculate_cost_saving(self.sample_workload, "shutdown"),
            758.33,
        )

    def test_calculate_taxonomy_rating(self) -> None:
        self.assertEqual(
            self.calculator.calculate_taxonomy_rating(
                workload=self.sample_workload,
                carbon_kg_co2e=22.48,
                energy_waste_score=87,
            ),
            "Red",
        )

    def test_calculate_sbti_progress(self) -> None:
        self.assertEqual(
            self.calculator.calculate_sbti_progress(
                baseline_carbon_kg=10_000,
                current_carbon_kg=7_500,
                target_reduction_percent=40,
            ),
            62.5,
        )

    def test_generate_sustainability_report_includes_dashboard_contract(self) -> None:
        report = self.calculator.generate_sustainability_report(self.sample_workload)

        self.assertEqual(report["asset_id"], "vm-001")
        self.assertEqual(report["energy_kwh"], 53.53)
        self.assertEqual(report["taxonomy_rating"], "Red")
        self.assertEqual(report["energy"]["before_kwh_monthly"], 53.53)
        self.assertEqual(report["energy"]["after_kwh_monthly"], 16.36)
        self.assertEqual(report["carbon"]["saved_kg_annual"], 187.32)
        self.assertEqual(report["cost"]["saved_monthly"], 758.33)
        self.assertEqual(report["sbti"]["sbti_progress_percent"], 62.5)

    def test_region_migration_reduces_carbon_not_energy(self) -> None:
        workload: WorkloadInput = {
            **self.sample_workload,
            "recommendation_type": "region_migration",
            "target_region": "us-west-2",
            "recommended_action": "Move workload to lower-carbon region",
        }
        impact = self.calculator.calculate_recommendation_impact(workload)

        self.assertEqual(
            impact["energy"]["before_kwh_monthly"],
            impact["energy"]["after_kwh_monthly"],
        )
        self.assertGreater(impact["carbon"]["saved_kg_monthly"], 0)

    def test_storage_tier_optimization(self) -> None:
        workload: WorkloadInput = {
            **self.sample_workload,
            "recommendation_type": "storage_tier_optimization",
            "storage_gb": 1000,
            "storage_tier": "hot",
            "target_storage_tier": "archive",
            "recommended_action": "Move cold storage to archive tier",
        }
        impact = self.calculator.calculate_recommendation_impact(workload)

        self.assertGreater(impact["energy"]["saved_kwh_monthly"], 0)
        self.assertGreater(impact["cost"]["saved_monthly"], 0)

    def test_ml_recommendation_report_uses_pipeline_wasted_energy(self) -> None:
        report = self.calculator.calculate_ml_recommendation_report(
            self.sample_ml_recommendation
        )

        self.assertEqual(report["vm_id"], "hashed-vm-001")
        self.assertEqual(report["scope_category"], "Scope 3 cloud services estimate")
        self.assertEqual(report["energy"]["saved_kwh_day"], 0.0427)
        self.assertEqual(report["carbon"]["saved_kg_co2e_day"], 0.016226)
        self.assertFalse(report["allocation"]["memory_savings_claimed"])
        self.assertEqual(report["carbon"]["aws_region_source"], "record")
        self.assertIsNotNone(report["explainability"]["shutdown_energy_caveat"])

    def test_ml_recommendation_defaults_region_and_marks_missing_cost(self) -> None:
        recommendation_without_optional_fields: MlPipelineRecommendation = {
            key: value
            for key, value in self.sample_ml_recommendation.items()
            if key not in {"aws_region", "cost_per_core_hour"}
        }

        report = self.calculator.calculate_ml_recommendation_report(
            recommendation_without_optional_fields
        )

        self.assertEqual(report["carbon"]["aws_region"], "aws:eu-central-1")
        self.assertEqual(report["carbon"]["aws_region_source"], "module_default")
        self.assertEqual(report["carbon"]["carbon_intensity_kg_per_kwh"], 0.36)
        self.assertIsNone(report["cost"]["saved_monthly"])
        self.assertEqual(report["cost"]["cost_method"], "not_calculated_missing_unit_cost")

    def test_aggregate_ml_recommendations(self) -> None:
        no_action: MlPipelineRecommendation = {
            **self.sample_ml_recommendation,
            "vm_id": "hashed-vm-002",
            "suggested_action": "no_action_needed",
            "risk_level": "Low",
        }

        aggregate = self.calculator.aggregate_ml_recommendations(
            [self.sample_ml_recommendation, no_action]
        )

        self.assertEqual(aggregate["fleet_summary"]["vm_count"], 2)
        self.assertEqual(
            aggregate["fleet_summary"]["potential_scope3_cloud_energy_saved_kwh_day"],
            0.0427,
        )
        self.assertEqual(
            aggregate["distribution"]["by_suggested_action"]["schedule_auto_shutdown"],
            1,
        )

    def test_decrease_autoscaling_min_does_not_claim_guaranteed_energy_saving(self) -> None:
        recommendation: MlPipelineRecommendation = {
            **self.sample_ml_recommendation,
            "suggested_action": "decrease_autoscaling_min",
        }

        report = self.calculator.calculate_ml_recommendation_report(recommendation)

        self.assertEqual(report["energy"]["wasted_kwh_day"], 0.0427)
        self.assertEqual(report["energy"]["saved_kwh_day"], 0.0)
        self.assertEqual(report["carbon"]["saved_kg_co2e_day"], 0.0)


if __name__ == "__main__":
    sample_workloads: list[WorkloadInput] = [
        {
            "asset_id": "vm-001",
            "asset_type": "VirtualMachine",
            "cpu_utilization": 12,
            "memory_utilization": 18,
            "allocated_vcpu": 8,
            "allocated_ram_gb": 32,
            "runtime_hours_month": 720,
            "region": "ap-southeast-1",
            "monthly_cost": 1200,
            "ai_status": "Idle",
            "confidence": 0.91,
            "recommended_action": "Auto-shutdown after office hours",
            "target_runtime_hours_month": 220,
            "annual_baseline_carbon_kg": 10_000,
            "current_annual_carbon_kg": 7_500,
            "target_reduction_percent": 40,
            "baseline_year": 2020,
            "current_year": 2026,
            "target_year": 2050,
        },
        {
            "asset_id": "vm-002",
            "asset_type": "VirtualMachine",
            "cpu_utilization": 45,
            "memory_utilization": 52,
            "allocated_vcpu": 4,
            "allocated_ram_gb": 16,
            "runtime_hours_month": 500,
            "region": "us-west-2",
            "monthly_cost": 430,
            "ai_status": "Moderate",
            "confidence": 0.85,
            "recommended_action": "Rightsize instance",
        },
        {
            "asset_id": "storage-001",
            "asset_type": "StorageAccount",
            "cpu_utilization": 0.01,
            "memory_utilization": 0.01,
            "allocated_vcpu": 1,
            "allocated_ram_gb": 1,
            "runtime_hours_month": 720,
            "region": "eu-west-1",
            "monthly_cost": 250,
            "recommendation_type": "storage_tier_optimization",
            "storage_gb": 5000,
            "storage_tier": "hot",
            "target_storage_tier": "archive",
            "recommended_action": "Move cold storage to archive tier",
            "confidence": 0.95,
        },
    ]

    calculator = SustainabilityCalculator()

    for workload_item in sample_workloads:
        print(calculator.generate_sustainability_report(workload_item))

    unittest.main(argv=["first-arg-is-ignored"], exit=False)
