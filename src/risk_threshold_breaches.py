"""
Risk threshold breach monitor for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module tracks whether key model outputs cross material warning thresholds.

Purpose:
- Convert model outputs into an alert-style monitoring layer.
- Identify whether growth pressure, construction shock, fuel/energy exposure,
  scenario stress, resilience, or model-quality risks have crossed warning levels.
- Support repeatable local intelligence monitoring.

Inputs:
- data/processed/composite_risk_score_latest.csv
- data/processed/growth_pressure_latest.csv
- data/processed/construction_shock_latest.csv
- data/processed/construction_shock_category_summary.csv
- data/processed/scenario_forecast_summary.csv
- data/processed/local_resilience_latest.csv
- data/processed/sensitivity_analysis_summary.csv

Outputs:
- data/processed/risk_threshold_breaches.csv
- data/processed/risk_threshold_breach_summary.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import PROCESSED_DATA_DIR


# ============================================================
# Input files
# ============================================================

COMPOSITE_LATEST_FILE = PROCESSED_DATA_DIR / "composite_risk_score_latest.csv"
GROWTH_LATEST_FILE = PROCESSED_DATA_DIR / "growth_pressure_latest.csv"
CONSTRUCTION_LATEST_FILE = PROCESSED_DATA_DIR / "construction_shock_latest.csv"
CONSTRUCTION_CATEGORY_FILE = PROCESSED_DATA_DIR / "construction_shock_category_summary.csv"
SCENARIO_SUMMARY_FILE = PROCESSED_DATA_DIR / "scenario_forecast_summary.csv"
RESILIENCE_LATEST_FILE = PROCESSED_DATA_DIR / "local_resilience_latest.csv"
SENSITIVITY_SUMMARY_FILE = PROCESSED_DATA_DIR / "sensitivity_analysis_summary.csv"


# ============================================================
# Output files
# ============================================================

RISK_THRESHOLD_BREACH_OUTPUT = PROCESSED_DATA_DIR / "risk_threshold_breaches.csv"
RISK_THRESHOLD_BREACH_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "risk_threshold_breach_summary.csv"
)


# ============================================================
# Threshold framework
# ============================================================

THRESHOLDS = {
    "adjusted_risk_elevated": {
        "metric": "adjusted_geoeconomic_growth_risk_score",
        "threshold": 50.0,
        "direction": "above",
        "severity": "Medium",
        "category": "Composite Risk",
        "description": "Adjusted risk score is in elevated-risk territory.",
    },
    "adjusted_risk_high": {
        "metric": "adjusted_geoeconomic_growth_risk_score",
        "threshold": 75.0,
        "direction": "above",
        "severity": "High",
        "category": "Composite Risk",
        "description": "Adjusted risk score is in high-risk territory.",
    },
    "composite_risk_elevated": {
        "metric": "composite_risk_score",
        "threshold": 50.0,
        "direction": "above",
        "severity": "Medium",
        "category": "Composite Risk",
        "description": "Unadjusted composite risk score is elevated.",
    },
    "growth_pressure_high": {
        "metric": "growth_pressure_score",
        "threshold": 75.0,
        "direction": "above",
        "severity": "High",
        "category": "Growth Pressure",
        "description": "Growth pressure is high, suggesting local absorption risk.",
    },
    "construction_shock_elevated": {
        "metric": "construction_shock_score",
        "threshold": 50.0,
        "direction": "above",
        "severity": "Medium",
        "category": "Construction Shock",
        "description": "Construction shock exposure is elevated.",
    },
    "construction_shock_high": {
        "metric": "construction_shock_score",
        "threshold": 75.0,
        "direction": "above",
        "severity": "High",
        "category": "Construction Shock",
        "description": "Construction shock exposure is high.",
    },
    "fuel_energy_shock_high": {
        "metric": "fuel_energy_shock_score",
        "threshold": 75.0,
        "direction": "above",
        "severity": "High",
        "category": "Fuel / Energy",
        "description": "Fuel and energy shock category is near or above high-risk territory.",
    },
    "materials_shock_elevated": {
        "metric": "materials_shock_score",
        "threshold": 50.0,
        "direction": "above",
        "severity": "Medium",
        "category": "Materials",
        "description": "Construction materials shock category is elevated.",
    },
    "financing_shock_elevated": {
        "metric": "financing_shock_score",
        "threshold": 50.0,
        "direction": "above",
        "severity": "Medium",
        "category": "Financing",
        "description": "Financing shock category is elevated.",
    },
    "scenario_delta_material": {
        "metric": "highest_scenario_delta",
        "threshold": 7.5,
        "direction": "above",
        "severity": "Medium",
        "category": "Scenario Stress",
        "description": "Highest-risk scenario is materially above the adjusted baseline.",
    },
    "scenario_score_elevated": {
        "metric": "highest_scenario_score",
        "threshold": 50.0,
        "direction": "above",
        "severity": "Medium",
        "category": "Scenario Stress",
        "description": "Highest-risk scenario is elevated.",
    },
    "scenario_score_high": {
        "metric": "highest_scenario_score",
        "threshold": 75.0,
        "direction": "above",
        "severity": "High",
        "category": "Scenario Stress",
        "description": "Highest-risk scenario is high risk.",
    },
    "local_resilience_limited": {
        "metric": "local_resilience_offset",
        "threshold": 40.0,
        "direction": "below",
        "severity": "Medium",
        "category": "Local Resilience",
        "description": "Local resilience offset is limited or weak.",
    },
    "placeholder_share_high": {
        "metric": "placeholder_share",
        "threshold": 0.50,
        "direction": "above",
        "severity": "Model Quality",
        "category": "Model Quality",
        "description": "More than half of composite components are still placeholders.",
    },
    "sensitivity_range_wide": {
        "metric": "sensitivity_score_range",
        "threshold": 10.0,
        "direction": "above",
        "severity": "Model Quality",
        "category": "Model Quality",
        "description": "Sensitivity analysis shows a wide range across weighting cases.",
    },
}


SEVERITY_SCORES = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Model Quality": 1,
}


# ============================================================
# Helpers
# ============================================================

def read_csv_if_exists(path) -> pd.DataFrame:
    """
    Read a CSV if it exists.
    """

    if not path.exists():
        print(f"WARNING: Missing threshold input file: {path}")
        return pd.DataFrame()

    return pd.read_csv(path)


def safe_value(df: pd.DataFrame, column: str, default=None):
    """
    Safely read a value from the first row of a DataFrame.
    """

    if df.empty or column not in df.columns:
        return default

    value = df.iloc[0][column]

    if pd.isna(value):
        return default

    return value


def safe_float(value, default=None):
    """
    Safely convert value to float.
    """

    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def get_category_score(category_df: pd.DataFrame, category_name: str) -> float | None:
    """
    Get construction shock category score from category summary.
    """

    if category_df.empty:
        return None

    if "category" not in category_df.columns or "category_score" not in category_df.columns:
        return None

    match = category_df[
        category_df["category"].astype(str).str.lower() == category_name.lower()
    ]

    if match.empty:
        return None

    return safe_float(match.iloc[0]["category_score"])


def evaluate_threshold(
    current_value: float | None,
    threshold: float,
    direction: str,
) -> bool:
    """
    Evaluate whether a metric breaches its threshold.
    """

    if current_value is None or pd.isna(current_value):
        return False

    if direction == "above":
        return current_value >= threshold

    if direction == "below":
        return current_value <= threshold

    raise ValueError(f"Unsupported threshold direction: {direction}")


def calculate_distance_to_threshold(
    current_value: float | None,
    threshold: float,
    direction: str,
) -> float | None:
    """
    Calculate distance from the threshold.

    Positive value means the metric has breached the threshold.
    Negative value means the metric remains below the breach threshold.
    """

    if current_value is None or pd.isna(current_value):
        return None

    if direction == "above":
        return current_value - threshold

    if direction == "below":
        return threshold - current_value

    return None


def classify_alert_level(total_breaches: int, high_breaches: int, model_quality_breaches: int) -> str:
    """
    Classify overall alert level.
    """

    if high_breaches >= 2:
        return "High Alert"

    if high_breaches == 1 and total_breaches >= 3:
        return "Elevated Alert"

    if total_breaches >= 4:
        return "Elevated Alert"

    if total_breaches >= 1:
        return "Watch"

    if model_quality_breaches >= 1:
        return "Model Quality Watch"

    return "No Active Alert"


# ============================================================
# State construction
# ============================================================

def load_current_threshold_state() -> dict:
    """
    Load latest model values used by the breach monitor.
    """

    composite_df = read_csv_if_exists(COMPOSITE_LATEST_FILE)
    growth_df = read_csv_if_exists(GROWTH_LATEST_FILE)
    construction_df = read_csv_if_exists(CONSTRUCTION_LATEST_FILE)
    construction_category_df = read_csv_if_exists(CONSTRUCTION_CATEGORY_FILE)
    scenario_df = read_csv_if_exists(SCENARIO_SUMMARY_FILE)
    resilience_df = read_csv_if_exists(RESILIENCE_LATEST_FILE)
    sensitivity_df = read_csv_if_exists(SENSITIVITY_SUMMARY_FILE)

    highest_scenario_name = None
    highest_scenario_score = None
    highest_scenario_delta = None
    highest_scenario_signal = None

    if not scenario_df.empty and "scenario_adjusted_risk_score" in scenario_df.columns:
        top_scenario = scenario_df.sort_values(
            "scenario_adjusted_risk_score",
            ascending=False,
        ).iloc[0]

        highest_scenario_name = top_scenario.get("scenario_name")
        highest_scenario_score = safe_float(
            top_scenario.get("scenario_adjusted_risk_score")
        )
        highest_scenario_delta = safe_float(
            top_scenario.get("scenario_delta_vs_adjusted_baseline")
        )
        highest_scenario_signal = top_scenario.get("scenario_signal")

    state = {
        "composite_risk_score": safe_float(
            safe_value(composite_df, "composite_risk_score")
        ),
        "adjusted_geoeconomic_growth_risk_score": safe_float(
            safe_value(composite_df, "adjusted_geoeconomic_growth_risk_score")
        ),
        "adjusted_geoeconomic_growth_risk_signal": safe_value(
            composite_df,
            "adjusted_geoeconomic_growth_risk_signal",
            default="N/A",
        ),
        "growth_pressure_score": safe_float(
            safe_value(growth_df, "growth_pressure_score")
        ),
        "growth_pressure_signal": safe_value(
            growth_df,
            "growth_pressure_signal",
            default="N/A",
        ),
        "construction_shock_score": safe_float(
            safe_value(construction_df, "construction_shock_score")
        ),
        "construction_shock_signal": safe_value(
            construction_df,
            "construction_shock_signal",
            default="N/A",
        ),
        "construction_shock_momentum_signal": safe_value(
            construction_df,
            "construction_shock_momentum_signal",
            default="N/A",
        ),
        "fuel_energy_shock_score": get_category_score(
            construction_category_df,
            "fuel_energy",
        ),
        "materials_shock_score": get_category_score(
            construction_category_df,
            "materials",
        ),
        "financing_shock_score": get_category_score(
            construction_category_df,
            "financing",
        ),
        "local_resilience_offset": safe_float(
            safe_value(
                composite_df,
                "local_resilience_offset",
                default=safe_value(resilience_df, "local_resilience_offset"),
            )
        ),
        "local_resilience_signal": safe_value(
            composite_df,
            "local_resilience_signal",
            default=safe_value(resilience_df, "local_resilience_signal", default="N/A"),
        ),
        "local_resilience_confidence": safe_value(
            composite_df,
            "local_resilience_confidence",
            default=safe_value(
                resilience_df,
                "local_resilience_confidence",
                default="N/A",
            ),
        ),
        "placeholder_share": safe_float(
            safe_value(composite_df, "placeholder_share")
        ),
        "model_maturity_level": safe_value(
            composite_df,
            "model_maturity_level",
            default="N/A",
        ),
        "data_quality_flag": safe_value(
            composite_df,
            "data_quality_flag",
            default="N/A",
        ),
        "highest_scenario_name": highest_scenario_name,
        "highest_scenario_score": highest_scenario_score,
        "highest_scenario_delta": highest_scenario_delta,
        "highest_scenario_signal": highest_scenario_signal,
        "sensitivity_score_range": safe_float(
            safe_value(sensitivity_df, "adjusted_risk_score_range")
        ),
        "sensitivity_stability": safe_value(
            sensitivity_df,
            "sensitivity_stability",
            default="N/A",
        ),
    }

    return state


# ============================================================
# Breach detection
# ============================================================

def evaluate_threshold_breaches(state: dict) -> pd.DataFrame:
    """
    Evaluate all configured threshold breaches.
    """

    rows = []

    for threshold_key, config in THRESHOLDS.items():
        metric = config["metric"]
        threshold = config["threshold"]
        direction = config["direction"]
        current_value = safe_float(state.get(metric))

        is_breached = evaluate_threshold(
            current_value=current_value,
            threshold=threshold,
            direction=direction,
        )

        distance = calculate_distance_to_threshold(
            current_value=current_value,
            threshold=threshold,
            direction=direction,
        )

        rows.append(
            {
                "threshold_key": threshold_key,
                "category": config["category"],
                "metric": metric,
                "current_value": current_value,
                "threshold": threshold,
                "direction": direction,
                "is_breached": is_breached,
                "distance_to_threshold": distance,
                "severity": config["severity"],
                "severity_score": SEVERITY_SCORES.get(config["severity"], 1),
                "description": config["description"],
                "model_maturity_level": state.get("model_maturity_level", "N/A"),
                "data_quality_flag": state.get("data_quality_flag", "N/A"),
                "highest_scenario_name": state.get("highest_scenario_name", "N/A"),
                "highest_scenario_signal": state.get("highest_scenario_signal", "N/A"),
                "construction_shock_momentum_signal": state.get(
                    "construction_shock_momentum_signal",
                    "N/A",
                ),
                "sensitivity_stability": state.get("sensitivity_stability", "N/A"),
            }
        )

    result = pd.DataFrame(rows)

    return result


def build_breach_summary(breach_df: pd.DataFrame, state: dict) -> pd.DataFrame:
    """
    Build one-row summary of breach monitor status.
    """

    active = breach_df[breach_df["is_breached"] == True].copy()

    active_non_model_quality = active[active["severity"] != "Model Quality"]
    high_active = active[active["severity"] == "High"]
    model_quality_active = active[active["severity"] == "Model Quality"]

    total_breaches = len(active_non_model_quality)
    high_breaches = len(high_active)
    model_quality_breaches = len(model_quality_active)

    alert_level = classify_alert_level(
        total_breaches=total_breaches,
        high_breaches=high_breaches,
        model_quality_breaches=model_quality_breaches,
    )

    if active.empty:
        top_breach_category = "None"
        top_breach_description = "No active threshold breaches."
    else:
        active_sorted = active.sort_values(
            ["severity_score", "distance_to_threshold"],
            ascending=[False, False],
        )
        top = active_sorted.iloc[0]
        top_breach_category = top["category"]
        top_breach_description = top["description"]

    breached_categories = (
        ", ".join(sorted(active["category"].dropna().unique()))
        if not active.empty
        else "None"
    )

    summary_text = create_breach_summary_text(
        alert_level=alert_level,
        active=active,
        state=state,
    )

    summary = pd.DataFrame(
        [
            {
                "run_timestamp": pd.Timestamp.today().isoformat(),
                "alert_level": alert_level,
                "total_active_breaches": int(total_breaches),
                "high_severity_breaches": int(high_breaches),
                "model_quality_breaches": int(model_quality_breaches),
                "top_breach_category": top_breach_category,
                "top_breach_description": top_breach_description,
                "breached_categories": breached_categories,
                "adjusted_risk_score": state.get(
                    "adjusted_geoeconomic_growth_risk_score"
                ),
                "adjusted_risk_signal": state.get(
                    "adjusted_geoeconomic_growth_risk_signal"
                ),
                "growth_pressure_score": state.get("growth_pressure_score"),
                "construction_shock_score": state.get("construction_shock_score"),
                "fuel_energy_shock_score": state.get("fuel_energy_shock_score"),
                "highest_scenario_name": state.get("highest_scenario_name"),
                "highest_scenario_score": state.get("highest_scenario_score"),
                "highest_scenario_delta": state.get("highest_scenario_delta"),
                "sensitivity_stability": state.get("sensitivity_stability"),
                "summary_text": summary_text,
            }
        ]
    )

    return summary


def create_breach_summary_text(alert_level: str, active: pd.DataFrame, state: dict) -> str:
    """
    Create narrative summary for the breach monitor.
    """

    if active.empty:
        return "No active risk threshold breaches were detected."

    active_non_model_quality = active[active["severity"] != "Model Quality"]
    high_active = active[active["severity"] == "High"]
    model_quality_active = active[active["severity"] == "Model Quality"]

    messages = []

    if not high_active.empty:
        high_categories = ", ".join(sorted(high_active["category"].unique()))
        messages.append(f"High-severity thresholds are active in: {high_categories}.")

    if not active_non_model_quality.empty:
        categories = ", ".join(sorted(active_non_model_quality["category"].unique()))
        messages.append(f"Active risk thresholds are present in: {categories}.")

    if not model_quality_active.empty:
        messages.append(
            "Model-quality thresholds are active, reflecting prototype limitations "
            "such as placeholder component coverage or sensitivity uncertainty."
        )

    highest_scenario = state.get("highest_scenario_name")
    highest_delta = state.get("highest_scenario_delta")

    if highest_scenario and highest_delta is not None:
        messages.append(
            f"The highest-risk scenario is {highest_scenario}, with a delta of "
            f"{highest_delta:+.1f} versus the adjusted baseline."
        )

    messages.append(f"Overall breach monitor status: {alert_level}.")

    return " ".join(messages)


# ============================================================
# Main workflow
# ============================================================

def run_risk_threshold_breach_monitor() -> pd.DataFrame:
    """
    Run full threshold breach monitor.
    """

    state = load_current_threshold_state()

    breach_df = evaluate_threshold_breaches(state)
    summary_df = build_breach_summary(breach_df, state)

    breach_df.to_csv(RISK_THRESHOLD_BREACH_OUTPUT, index=False)
    summary_df.to_csv(RISK_THRESHOLD_BREACH_SUMMARY_OUTPUT, index=False)

    print(f"Saved risk threshold breaches to: {RISK_THRESHOLD_BREACH_OUTPUT}")
    print(f"Saved risk threshold breach summary to: {RISK_THRESHOLD_BREACH_SUMMARY_OUTPUT}")

    print()
    print("Risk Threshold Breach Summary")
    print("-----------------------------")
    print(summary_df.to_string(index=False))

    active = breach_df[breach_df["is_breached"] == True].copy()

    print()
    print("Active threshold breaches:")
    if active.empty:
        print("No active threshold breaches.")
    else:
        display_cols = [
            "category",
            "metric",
            "current_value",
            "threshold",
            "direction",
            "severity",
            "description",
        ]
        print(active[display_cols].to_string(index=False))

    return breach_df


def summarize_risk_threshold_breaches() -> pd.DataFrame:
    """
    Load and print risk threshold breach summary.
    """

    if not RISK_THRESHOLD_BREACH_SUMMARY_OUTPUT.exists():
        raise FileNotFoundError(
            "No risk threshold breach summary found. "
            "Run run_risk_threshold_breach_monitor() first."
        )

    summary = pd.read_csv(RISK_THRESHOLD_BREACH_SUMMARY_OUTPUT)

    print()
    print("Latest risk threshold breach summary:")
    print(summary.to_string(index=False))

    return summary


def main() -> None:
    """
    Run risk threshold breach monitor as a script.
    """

    run_risk_threshold_breach_monitor()


if __name__ == "__main__":
    main()