"""
Sensitivity analysis module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module tests whether the composite risk conclusion changes under alternative
weighting assumptions.

Purpose:
- Evaluate robustness of the adjusted risk score.
- Show whether the model conclusion depends heavily on the baseline weights.
- Support transparent reporting while placeholder components remain in the model.

Inputs:
- data/processed/composite_risk_component_summary.csv
- data/processed/local_resilience_latest.csv
- data/processed/composite_risk_score_latest.csv

Outputs:
- data/processed/sensitivity_analysis_results.csv
- data/processed/sensitivity_analysis_summary.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import (
    MAX_RESILIENCE_CREDIT,
    PROCESSED_DATA_DIR,
    RESILIENCE_CREDIT_RATE,
    RISK_SCORE_WEIGHTS,
    classify_risk,
)


# ============================================================
# Input / output files
# ============================================================

COMPOSITE_COMPONENT_FILE = PROCESSED_DATA_DIR / "composite_risk_component_summary.csv"
LOCAL_RESILIENCE_LATEST_FILE = PROCESSED_DATA_DIR / "local_resilience_latest.csv"
COMPOSITE_LATEST_FILE = PROCESSED_DATA_DIR / "composite_risk_score_latest.csv"

SENSITIVITY_RESULTS_OUTPUT = PROCESSED_DATA_DIR / "sensitivity_analysis_results.csv"
SENSITIVITY_SUMMARY_OUTPUT = PROCESSED_DATA_DIR / "sensitivity_analysis_summary.csv"


# ============================================================
# Sensitivity weighting cases
# ============================================================

SENSITIVITY_WEIGHT_CASES = {
    "baseline": {
        "name": "Baseline Weights",
        "description": "Uses the core project weighting framework.",
        "weights": RISK_SCORE_WEIGHTS,
    },
    "growth_heavy": {
        "name": "Growth-Heavy Case",
        "description": "Places more emphasis on local growth pressure and infrastructure strain.",
        "weights": {
            "growth_pressure": 0.30,
            "housing_affordability_pressure": 0.15,
            "construction_shock_exposure": 0.10,
            "infrastructure_strain": 0.20,
            "development_friction": 0.10,
            "geoeconomic_industry_exposure": 0.075,
            "household_vulnerability": 0.075,
        },
    },
    "construction_shock_heavy": {
        "name": "Construction-Shock-Heavy Case",
        "description": "Places more emphasis on materials, fuel, energy, and financing exposure.",
        "weights": {
            "growth_pressure": 0.15,
            "housing_affordability_pressure": 0.15,
            "construction_shock_exposure": 0.30,
            "infrastructure_strain": 0.125,
            "development_friction": 0.10,
            "geoeconomic_industry_exposure": 0.10,
            "household_vulnerability": 0.075,
        },
    },
    "infrastructure_friction_heavy": {
        "name": "Infrastructure / Friction Heavy Case",
        "description": "Places more emphasis on infrastructure strain and development friction.",
        "weights": {
            "growth_pressure": 0.15,
            "housing_affordability_pressure": 0.125,
            "construction_shock_exposure": 0.10,
            "infrastructure_strain": 0.25,
            "development_friction": 0.25,
            "geoeconomic_industry_exposure": 0.075,
            "household_vulnerability": 0.05,
        },
    },
    "household_vulnerability_heavy": {
        "name": "Household-Vulnerability-Heavy Case",
        "description": "Places more emphasis on housing affordability and household vulnerability.",
        "weights": {
            "growth_pressure": 0.15,
            "housing_affordability_pressure": 0.25,
            "construction_shock_exposure": 0.10,
            "infrastructure_strain": 0.125,
            "development_friction": 0.10,
            "geoeconomic_industry_exposure": 0.075,
            "household_vulnerability": 0.20,
        },
    },
    "equal_weight": {
        "name": "Equal-Weight Case",
        "description": "Assigns equal weight to every composite risk component.",
        "weights": {
            "growth_pressure": 1 / 7,
            "housing_affordability_pressure": 1 / 7,
            "construction_shock_exposure": 1 / 7,
            "infrastructure_strain": 1 / 7,
            "development_friction": 1 / 7,
            "geoeconomic_industry_exposure": 1 / 7,
            "household_vulnerability": 1 / 7,
        },
    },
}


# ============================================================
# Helpers
# ============================================================

def read_csv_if_exists(path) -> pd.DataFrame:
    """
    Read a CSV if it exists.
    """

    if not path.exists():
        print(f"WARNING: Missing sensitivity input file: {path}")
        return pd.DataFrame()

    return pd.read_csv(path)


def clamp_score(score: float, lower: float = 0.0, upper: float = 100.0) -> float:
    """
    Keep a score within a 0-100 range.
    """

    if pd.isna(score):
        return np.nan

    return float(max(min(score, upper), lower))


def calculate_resilience_credit(
    local_resilience_offset: float,
    credit_rate: float = RESILIENCE_CREDIT_RATE,
    max_credit: float = MAX_RESILIENCE_CREDIT,
) -> float:
    """
    Convert resilience offset into a capped risk reduction.
    """

    if pd.isna(local_resilience_offset):
        return 0.0

    raw_credit = float(local_resilience_offset) * credit_rate
    return float(max(min(raw_credit, max_credit), 0.0))


def load_resilience_offset() -> float:
    """
    Load latest local resilience offset.
    """

    df = read_csv_if_exists(LOCAL_RESILIENCE_LATEST_FILE)

    if df.empty or "local_resilience_offset" not in df.columns:
        return 0.0

    value = df.tail(1).iloc[0]["local_resilience_offset"]

    if pd.isna(value):
        return 0.0

    return clamp_score(float(value))


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """
    Normalize weights so they sum to 1.0.
    """

    total = sum(weights.values())

    if total <= 0:
        raise ValueError("Sensitivity weights must sum to a positive value.")

    return {component: weight / total for component, weight in weights.items()}


def calculate_weighted_score(
    component_df: pd.DataFrame,
    weights: dict[str, float],
) -> tuple[float, pd.DataFrame]:
    """
    Calculate composite score under a specific weighting case.
    """

    weights = normalize_weights(weights)

    rows = []

    for component, weight in weights.items():
        match = component_df[component_df["component"] == component]

        if match.empty:
            score = np.nan
            signal = "Missing Data"
            is_placeholder = np.nan
        else:
            score = match.iloc[0].get("score", np.nan)
            signal = match.iloc[0].get("signal", "N/A")
            is_placeholder = match.iloc[0].get("is_placeholder", np.nan)

        weighted_contribution = (
            float(score) * weight if pd.notna(score) else np.nan
        )

        rows.append(
            {
                "component": component,
                "sensitivity_weight": weight,
                "score": score,
                "signal": signal,
                "weighted_contribution": weighted_contribution,
                "is_placeholder": is_placeholder,
            }
        )

    result = pd.DataFrame(rows)
    valid = result.dropna(subset=["score"])

    if valid.empty:
        return np.nan, result

    total_valid_weight = valid["sensitivity_weight"].sum()

    if total_valid_weight <= 0:
        return np.nan, result

    score = valid["weighted_contribution"].sum() / total_valid_weight

    return clamp_score(score), result


def classify_sensitivity_stability(
    min_adjusted_score: float,
    max_adjusted_score: float,
    signal_count: int,
) -> str:
    """
    Classify how stable the model conclusion is across sensitivity cases.
    """

    score_range = max_adjusted_score - min_adjusted_score

    if signal_count == 1 and score_range < 5:
        return "Highly Stable"
    if signal_count <= 2 and score_range < 10:
        return "Stable"
    if signal_count <= 2 and score_range < 15:
        return "Moderately Sensitive"
    return "Highly Sensitive"


# ============================================================
# Main model
# ============================================================

def run_sensitivity_analysis() -> pd.DataFrame:
    """
    Run full sensitivity analysis.
    """

    component_df = read_csv_if_exists(COMPOSITE_COMPONENT_FILE)

    if component_df.empty:
        raise FileNotFoundError(
            "Composite component summary is required. "
            "Run `python -m src.composite_score` first."
        )

    local_resilience_offset = load_resilience_offset()
    resilience_credit = calculate_resilience_credit(local_resilience_offset)

    rows = []
    detail_rows = []

    for case_key, case in SENSITIVITY_WEIGHT_CASES.items():
        composite_score, component_detail = calculate_weighted_score(
            component_df=component_df,
            weights=case["weights"],
        )

        adjusted_score = clamp_score(composite_score - resilience_credit)

        rows.append(
            {
                "case_key": case_key,
                "case_name": case["name"],
                "case_description": case["description"],
                "sensitivity_composite_risk_score": composite_score,
                "local_resilience_offset": local_resilience_offset,
                "resilience_credit_applied": resilience_credit,
                "sensitivity_adjusted_risk_score": adjusted_score,
                "sensitivity_adjusted_signal": classify_risk(adjusted_score)
                if pd.notna(adjusted_score)
                else "Insufficient Data",
            }
        )

        component_detail["case_key"] = case_key
        component_detail["case_name"] = case["name"]
        detail_rows.append(component_detail)

    result = pd.DataFrame(rows)

    min_score = result["sensitivity_adjusted_risk_score"].min()
    max_score = result["sensitivity_adjusted_risk_score"].max()
    mean_score = result["sensitivity_adjusted_risk_score"].mean()
    score_range = max_score - min_score
    signal_count = result["sensitivity_adjusted_signal"].nunique()

    stability = classify_sensitivity_stability(
        min_adjusted_score=min_score,
        max_adjusted_score=max_score,
        signal_count=signal_count,
    )

    summary = pd.DataFrame(
        [
            {
                "sensitivity_case_count": len(result),
                "min_adjusted_risk_score": min_score,
                "max_adjusted_risk_score": max_score,
                "mean_adjusted_risk_score": mean_score,
                "adjusted_risk_score_range": score_range,
                "unique_signal_count": signal_count,
                "sensitivity_stability": stability,
                "lowest_risk_case": result.sort_values(
                    "sensitivity_adjusted_risk_score",
                    ascending=True,
                ).iloc[0]["case_name"],
                "highest_risk_case": result.sort_values(
                    "sensitivity_adjusted_risk_score",
                    ascending=False,
                ).iloc[0]["case_name"],
            }
        ]
    )

    result.to_csv(SENSITIVITY_RESULTS_OUTPUT, index=False)
    summary.to_csv(SENSITIVITY_SUMMARY_OUTPUT, index=False)

    if detail_rows:
        detail = pd.concat(detail_rows, ignore_index=True)
        detail_output = PROCESSED_DATA_DIR / "sensitivity_component_detail.csv"
        detail.to_csv(detail_output, index=False)
        print(f"Saved sensitivity component detail to: {detail_output}")

    print(f"Saved sensitivity results to: {SENSITIVITY_RESULTS_OUTPUT}")
    print(f"Saved sensitivity summary to: {SENSITIVITY_SUMMARY_OUTPUT}")

    print()
    print("Sensitivity Analysis Summary")
    print("----------------------------")
    print(summary.to_string(index=False))

    print()
    print("Sensitivity cases:")
    print(result.to_string(index=False))

    return result


def summarize_sensitivity_analysis() -> pd.DataFrame:
    """
    Load and print sensitivity summary.
    """

    if not SENSITIVITY_SUMMARY_OUTPUT.exists():
        raise FileNotFoundError(
            "No sensitivity summary found. Run run_sensitivity_analysis() first."
        )

    summary = pd.read_csv(SENSITIVITY_SUMMARY_OUTPUT)

    print()
    print("Latest sensitivity analysis summary:")
    print(summary.to_string(index=False))

    return summary


def main() -> None:
    """
    Run sensitivity analysis as a script.
    """

    run_sensitivity_analysis()


if __name__ == "__main__":
    main()