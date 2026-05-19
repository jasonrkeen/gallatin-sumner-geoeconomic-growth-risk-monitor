"""
Scenario forecast module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module creates scenario-based risk forecasts using:
- latest growth pressure score
- latest construction shock score
- latest composite risk score
- latest adjusted risk score
- capped resilience credit from composite_score.py
- centralized scenario multipliers and scenario risk weights from config.py

Scenarios:
- Managed Growth
- Overheated Growth
- Geopolitical Construction Cost Shock
- Growth Pause / Rezoning Constraint

Inputs:
- data/processed/growth_pressure_latest.csv
- data/processed/construction_shock_latest.csv
- data/processed/composite_risk_score_latest.csv
- data/processed/local_resilience_latest.csv

Outputs:
- data/processed/scenario_forecasts.csv
- data/processed/scenario_forecast_summary.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import (
    MAX_RESILIENCE_CREDIT,
    PROCESSED_DATA_DIR,
    RESILIENCE_CREDIT_RATE,
    SCENARIOS,
    SCENARIO_RISK_WEIGHTS,
    classify_risk,
)


# ============================================================
# Input / output files
# ============================================================

GROWTH_PRESSURE_LATEST_FILE = PROCESSED_DATA_DIR / "growth_pressure_latest.csv"
CONSTRUCTION_SHOCK_LATEST_FILE = PROCESSED_DATA_DIR / "construction_shock_latest.csv"
COMPOSITE_RISK_LATEST_FILE = PROCESSED_DATA_DIR / "composite_risk_score_latest.csv"
LOCAL_RESILIENCE_LATEST_FILE = PROCESSED_DATA_DIR / "local_resilience_latest.csv"

SCENARIO_FORECAST_OUTPUT = PROCESSED_DATA_DIR / "scenario_forecasts.csv"
SCENARIO_FORECAST_SUMMARY_OUTPUT = PROCESSED_DATA_DIR / "scenario_forecast_summary.csv"


# ============================================================
# Helper functions
# ============================================================

def clamp_score(score: float, lower: float = 0.0, upper: float = 100.0) -> float:
    """
    Keep risk scores within a 0-100 range.
    """

    if pd.isna(score):
        return np.nan

    return float(max(min(score, upper), lower))


def load_scalar_from_csv(
    path,
    column: str,
    default: float = np.nan,
) -> float:
    """
    Load a single scalar value from the last row of a CSV.
    """

    if not path.exists():
        print(
            f"WARNING: Could not find {path}. "
            f"Using default value for {column}: {default}"
        )
        return default

    df = pd.read_csv(path)

    if df.empty or column not in df.columns:
        print(f"WARNING: Could not load {column} from {path}. Using default: {default}")
        return default

    value = df.tail(1).iloc[0][column]

    if pd.isna(value):
        return default

    return float(value)


def load_text_from_csv(
    path,
    column: str,
    default: str = "N/A",
) -> str:
    """
    Load a single text value from the last row of a CSV.
    """

    if not path.exists():
        return default

    df = pd.read_csv(path)

    if df.empty or column not in df.columns:
        return default

    value = df.tail(1).iloc[0][column]

    if pd.isna(value):
        return default

    return str(value)


def calculate_resilience_credit(
    local_resilience_offset: float,
    credit_rate: float = RESILIENCE_CREDIT_RATE,
    max_credit: float = MAX_RESILIENCE_CREDIT,
) -> float:
    """
    Calculate capped resilience credit using centralized config assumptions.

    This mirrors the composite_score.py logic so scenario forecasts do not become
    overly optimistic when qualitative resilience scores are high.
    """

    if pd.isna(local_resilience_offset):
        return 0.0

    raw_credit = float(local_resilience_offset) * credit_rate
    capped_credit = min(raw_credit, max_credit)

    return float(max(capped_credit, 0.0))


def load_latest_model_state() -> dict[str, float | str]:
    """
    Load the latest available model state from processed outputs.
    """

    local_resilience_offset = load_scalar_from_csv(
        LOCAL_RESILIENCE_LATEST_FILE,
        "local_resilience_offset",
        default=0.0,
    )

    fallback_resilience_credit = calculate_resilience_credit(local_resilience_offset)

    resilience_credit_applied = load_scalar_from_csv(
        COMPOSITE_RISK_LATEST_FILE,
        "resilience_credit_applied",
        default=fallback_resilience_credit,
    )

    state = {
        "growth_pressure_score": load_scalar_from_csv(
            GROWTH_PRESSURE_LATEST_FILE,
            "growth_pressure_score",
            default=50.0,
        ),
        "growth_pressure_signal": load_text_from_csv(
            GROWTH_PRESSURE_LATEST_FILE,
            "growth_pressure_signal",
            default="N/A",
        ),
        "construction_shock_score": load_scalar_from_csv(
            CONSTRUCTION_SHOCK_LATEST_FILE,
            "construction_shock_score",
            default=50.0,
        ),
        "construction_shock_signal": load_text_from_csv(
            CONSTRUCTION_SHOCK_LATEST_FILE,
            "construction_shock_signal",
            default="N/A",
        ),
        "construction_shock_momentum_signal": load_text_from_csv(
            CONSTRUCTION_SHOCK_LATEST_FILE,
            "construction_shock_momentum_signal",
            default="N/A",
        ),
        "composite_risk_score": load_scalar_from_csv(
            COMPOSITE_RISK_LATEST_FILE,
            "composite_risk_score",
            default=55.0,
        ),
        "composite_risk_signal": load_text_from_csv(
            COMPOSITE_RISK_LATEST_FILE,
            "composite_risk_signal",
            default="N/A",
        ),
        "adjusted_geoeconomic_growth_risk_score": load_scalar_from_csv(
            COMPOSITE_RISK_LATEST_FILE,
            "adjusted_geoeconomic_growth_risk_score",
            default=55.0,
        ),
        "adjusted_geoeconomic_growth_risk_signal": load_text_from_csv(
            COMPOSITE_RISK_LATEST_FILE,
            "adjusted_geoeconomic_growth_risk_signal",
            default="N/A",
        ),
        "local_resilience_offset": local_resilience_offset,
        "local_resilience_signal": load_text_from_csv(
            LOCAL_RESILIENCE_LATEST_FILE,
            "local_resilience_signal",
            default="N/A",
        ),
        "local_resilience_confidence": load_text_from_csv(
            LOCAL_RESILIENCE_LATEST_FILE,
            "local_resilience_confidence",
            default=load_text_from_csv(
                COMPOSITE_RISK_LATEST_FILE,
                "local_resilience_confidence",
                default="N/A",
            ),
        ),
        "resilience_credit_applied": resilience_credit_applied,
        "model_maturity_level": load_text_from_csv(
            COMPOSITE_RISK_LATEST_FILE,
            "model_maturity_level",
            default="N/A",
        ),
        "data_quality_flag": load_text_from_csv(
            COMPOSITE_RISK_LATEST_FILE,
            "data_quality_flag",
            default="N/A",
        ),
        "placeholder_components_used": load_scalar_from_csv(
            COMPOSITE_RISK_LATEST_FILE,
            "placeholder_components_used",
            default=np.nan,
        ),
        "live_components_used": load_scalar_from_csv(
            COMPOSITE_RISK_LATEST_FILE,
            "live_components_used",
            default=np.nan,
        ),
        "placeholder_share": load_scalar_from_csv(
            COMPOSITE_RISK_LATEST_FILE,
            "placeholder_share",
            default=np.nan,
        ),
    }

    return state


def calculate_local_stress_proxy(
    housing_multiplier: float,
    infrastructure_multiplier: float,
    development_friction_multiplier: float,
) -> float:
    """
    Estimate local stress using scenario-specific housing, infrastructure,
    and development friction multipliers.

    This is a temporary proxy until dedicated modules are built for:
    - housing affordability
    - infrastructure strain
    - development friction
    """

    proxy_score = 55.0 * (
        housing_multiplier * 0.35
        + infrastructure_multiplier * 0.35
        + development_friction_multiplier * 0.30
    )

    return clamp_score(proxy_score)


def scenario_resilience_credit_multiplier(scenario_key: str) -> float:
    """
    Determine how much of the base resilience credit applies under each scenario.

    Stress scenarios receive less resilience credit because local capacity can be
    strained when growth, construction costs, or policy friction intensify.
    """

    multipliers = {
        "managed_growth": 1.00,
        "overheated_growth": 0.75,
        "construction_cost_shock": 0.65,
        "growth_pause_rezoning_constraint": 0.85,
    }

    return multipliers.get(scenario_key, 1.00)


def calculate_scenario_scores(
    state: dict[str, float | str],
) -> pd.DataFrame:
    """
    Calculate scenario forecast scores.

    Scenario Raw Risk =
        config weight: composite baseline risk
      + config weight: scenario-adjusted growth pressure
      + config weight: scenario-adjusted construction shock
      + config weight: scenario local stress proxy

    Scenario Adjusted Risk =
        Scenario Raw Risk - capped scenario resilience credit

    The scenario model uses the unadjusted composite risk score as the baseline
    because stress scenarios should not begin from an already heavily reduced
    risk state.
    """

    rows = []

    composite_baseline = float(state["composite_risk_score"])
    baseline_adjusted = float(state["adjusted_geoeconomic_growth_risk_score"])
    growth_score = float(state["growth_pressure_score"])
    construction_score = float(state["construction_shock_score"])
    local_resilience_offset = float(state["local_resilience_offset"])
    base_resilience_credit = float(state["resilience_credit_applied"])

    for scenario_key, scenario in SCENARIOS.items():
        growth_multiplier = scenario.get("growth_multiplier", 1.0)
        housing_multiplier = scenario.get("housing_multiplier", 1.0)
        construction_multiplier = scenario.get("construction_cost_multiplier", 1.0)
        infrastructure_multiplier = scenario.get("infrastructure_multiplier", 1.0)
        development_friction_multiplier = scenario.get(
            "development_friction_multiplier",
            1.0,
        )

        scenario_growth_score = clamp_score(growth_score * growth_multiplier)

        scenario_construction_score = clamp_score(
            construction_score * construction_multiplier
        )

        scenario_local_stress_proxy_score = calculate_local_stress_proxy(
            housing_multiplier=housing_multiplier,
            infrastructure_multiplier=infrastructure_multiplier,
            development_friction_multiplier=development_friction_multiplier,
        )

        raw_scenario_score = (
            composite_baseline * SCENARIO_RISK_WEIGHTS["composite_baseline"]
            + scenario_growth_score * SCENARIO_RISK_WEIGHTS["scenario_growth_pressure"]
            + scenario_construction_score
            * SCENARIO_RISK_WEIGHTS["scenario_construction_shock"]
            + scenario_local_stress_proxy_score
            * SCENARIO_RISK_WEIGHTS["scenario_local_stress_proxy"]
        )

        scenario_credit_multiplier = scenario_resilience_credit_multiplier(
            scenario_key
        )

        scenario_resilience_credit = min(
            base_resilience_credit * scenario_credit_multiplier,
            MAX_RESILIENCE_CREDIT,
        )

        scenario_adjusted_score = clamp_score(
            raw_scenario_score - scenario_resilience_credit
        )

        scenario_delta_vs_adjusted_baseline = (
            scenario_adjusted_score - baseline_adjusted
        )

        scenario_delta_vs_composite_baseline = (
            scenario_adjusted_score - composite_baseline
        )

        rows.append(
            {
                "scenario_key": scenario_key,
                "scenario_name": scenario["name"],
                "scenario_description": scenario["description"],
                "composite_baseline_risk_score": composite_baseline,
                "baseline_adjusted_risk_score": baseline_adjusted,
                "base_growth_pressure_score": growth_score,
                "base_growth_pressure_signal": state["growth_pressure_signal"],
                "base_construction_shock_score": construction_score,
                "base_construction_shock_signal": state["construction_shock_signal"],
                "base_construction_shock_momentum_signal": state[
                    "construction_shock_momentum_signal"
                ],
                "local_resilience_offset": local_resilience_offset,
                "local_resilience_signal": state["local_resilience_signal"],
                "local_resilience_confidence": state["local_resilience_confidence"],
                "base_resilience_credit_applied": base_resilience_credit,
                "scenario_resilience_credit_multiplier": scenario_credit_multiplier,
                "scenario_resilience_credit": scenario_resilience_credit,
                "growth_multiplier": growth_multiplier,
                "housing_multiplier": housing_multiplier,
                "construction_cost_multiplier": construction_multiplier,
                "infrastructure_multiplier": infrastructure_multiplier,
                "development_friction_multiplier": development_friction_multiplier,
                "scenario_growth_pressure_score": scenario_growth_score,
                "scenario_construction_shock_score": scenario_construction_score,
                "scenario_local_stress_proxy_score": scenario_local_stress_proxy_score,
                "raw_scenario_risk_score": clamp_score(raw_scenario_score),
                "scenario_adjusted_risk_score": scenario_adjusted_score,
                "scenario_delta_vs_adjusted_baseline": scenario_delta_vs_adjusted_baseline,
                "scenario_delta_vs_composite_baseline": scenario_delta_vs_composite_baseline,
                "scenario_signal": classify_risk(scenario_adjusted_score),
                "model_maturity_level": state["model_maturity_level"],
                "data_quality_flag": state["data_quality_flag"],
                "placeholder_components_used": state["placeholder_components_used"],
                "live_components_used": state["live_components_used"],
                "placeholder_share": state["placeholder_share"],
            }
        )

    return pd.DataFrame(rows)


def add_scenario_interpretation(result: pd.DataFrame) -> pd.DataFrame:
    """
    Add short interpretation fields for reporting.
    """

    interpretation_map = {
        "managed_growth": (
            "Baseline case: local growth remains positive and mostly absorbable "
            "if planning, infrastructure, and utility capacity keep pace."
        ),
        "overheated_growth": (
            "Stress case: development and population growth outpace infrastructure, "
            "housing affordability, road capacity, utilities, and planning capacity."
        ),
        "construction_cost_shock": (
            "Geopolitical cost-shock case: materials, fuel, rates, and logistics costs "
            "increase pressure on housing, public infrastructure, and private development."
        ),
        "growth_pause_rezoning_constraint": (
            "Policy-friction case: slower approvals may reduce near-term infrastructure "
            "pressure but can worsen housing supply constraints and developer uncertainty."
        ),
    }

    primary_risk_driver_map = {
        "managed_growth": "Baseline growth absorption",
        "overheated_growth": "Infrastructure, housing, and development pressure",
        "construction_cost_shock": "Materials, fuel, financing, and supply-chain costs",
        "growth_pause_rezoning_constraint": "Rezoning uncertainty and housing supply constraints",
    }

    severity_note_map = {
        "managed_growth": (
            "This scenario should be interpreted as a controlled baseline rather than "
            "a downside shock."
        ),
        "overheated_growth": (
            "This is the main local stress case because it tests rapid growth against "
            "housing, road, utility, and planning capacity."
        ),
        "construction_cost_shock": (
            "This scenario tests external geoeconomic shock exposure through materials, "
            "fuel, financing, and logistics costs."
        ),
        "growth_pause_rezoning_constraint": (
            "This scenario tests policy and planning friction, where lower growth may "
            "reduce some infrastructure pressure but increase housing supply risk."
        ),
    }

    result = result.copy()
    result["primary_risk_driver"] = result["scenario_key"].map(primary_risk_driver_map)
    result["interpretation"] = result["scenario_key"].map(interpretation_map)
    result["severity_note"] = result["scenario_key"].map(severity_note_map)

    return result


def build_scenario_forecast_model() -> pd.DataFrame:
    """
    Run the full scenario forecast model.
    """

    state = load_latest_model_state()

    result = calculate_scenario_scores(state)
    result = add_scenario_interpretation(result)

    result = result.sort_values(
        "scenario_adjusted_risk_score",
        ascending=False,
    ).reset_index(drop=True)

    result.to_csv(SCENARIO_FORECAST_OUTPUT, index=False)

    summary_columns = [
        "scenario_name",
        "scenario_adjusted_risk_score",
        "scenario_signal",
        "scenario_delta_vs_adjusted_baseline",
        "primary_risk_driver",
        "interpretation",
        "severity_note",
        "model_maturity_level",
        "data_quality_flag",
    ]

    summary = result[summary_columns].copy()
    summary.to_csv(SCENARIO_FORECAST_SUMMARY_OUTPUT, index=False)

    print(f"Saved scenario forecasts to: {SCENARIO_FORECAST_OUTPUT}")
    print(f"Saved scenario forecast summary to: {SCENARIO_FORECAST_SUMMARY_OUTPUT}")

    print()
    print("Scenario Forecast Summary")
    print("-------------------------")
    print(summary.to_string(index=False))

    return result


def summarize_scenario_forecasts() -> pd.DataFrame:
    """
    Load and print scenario forecast summary.
    """

    if not SCENARIO_FORECAST_SUMMARY_OUTPUT.exists():
        raise FileNotFoundError(
            "No scenario forecast summary found. "
            "Run build_scenario_forecast_model() first."
        )

    summary = pd.read_csv(SCENARIO_FORECAST_SUMMARY_OUTPUT)

    print()
    print("Scenario forecast summary:")
    print(summary.to_string(index=False))

    return summary


def main() -> None:
    """
    Run scenario forecasting as a script.
    """

    build_scenario_forecast_model()


if __name__ == "__main__":
    main()