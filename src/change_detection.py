"""
Change detection module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module compares the latest model output against the prior run snapshot.

Purpose:
- Track whether the local risk monitor is improving, worsening, or stable.
- Identify changes in composite risk, adjusted risk, growth pressure, construction shock,
  infrastructure strain, development friction, industry exposure, household vulnerability,
  local resilience, and highest-risk scenario.
- Save a latest run snapshot for future comparisons.

Inputs:
- data/processed/composite_risk_score_latest.csv
- data/processed/growth_pressure_latest.csv
- data/processed/construction_shock_latest.csv
- data/processed/local_resilience_latest.csv
- data/processed/scenario_forecast_summary.csv
- data/processed/construction_shock_category_summary.csv
- data/processed/housing_affordability_latest.csv
- data/processed/infrastructure_strain_latest.csv
- data/processed/development_friction_latest.csv
- data/processed/geoeconomic_industry_exposure_latest.csv
- data/processed/household_vulnerability_latest.csv

Outputs:
- outputs/snapshots/latest_run_snapshot.json
- outputs/snapshots/previous_run_snapshot.json
- data/processed/change_detection_summary.csv
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import OUTPUTS_DIR, PROCESSED_DATA_DIR


# ============================================================
# Input files
# ============================================================

COMPOSITE_LATEST_FILE = PROCESSED_DATA_DIR / "composite_risk_score_latest.csv"
GROWTH_LATEST_FILE = PROCESSED_DATA_DIR / "growth_pressure_latest.csv"
CONSTRUCTION_LATEST_FILE = PROCESSED_DATA_DIR / "construction_shock_latest.csv"
RESILIENCE_LATEST_FILE = PROCESSED_DATA_DIR / "local_resilience_latest.csv"
SCENARIO_SUMMARY_FILE = PROCESSED_DATA_DIR / "scenario_forecast_summary.csv"
CONSTRUCTION_CATEGORY_FILE = PROCESSED_DATA_DIR / "construction_shock_category_summary.csv"

HOUSING_LATEST_FILE = PROCESSED_DATA_DIR / "housing_affordability_latest.csv"
INFRASTRUCTURE_LATEST_FILE = PROCESSED_DATA_DIR / "infrastructure_strain_latest.csv"
DEVELOPMENT_FRICTION_LATEST_FILE = PROCESSED_DATA_DIR / "development_friction_latest.csv"
GEOECONOMIC_INDUSTRY_LATEST_FILE = (
    PROCESSED_DATA_DIR / "geoeconomic_industry_exposure_latest.csv"
)
HOUSEHOLD_VULNERABILITY_LATEST_FILE = (
    PROCESSED_DATA_DIR / "household_vulnerability_latest.csv"
)


# ============================================================
# Output files
# ============================================================

SNAPSHOTS_DIR = OUTPUTS_DIR / "snapshots"
LATEST_SNAPSHOT_FILE = SNAPSHOTS_DIR / "latest_run_snapshot.json"
PREVIOUS_SNAPSHOT_FILE = SNAPSHOTS_DIR / "previous_run_snapshot.json"
CHANGE_DETECTION_OUTPUT = PROCESSED_DATA_DIR / "change_detection_summary.csv"


# ============================================================
# Helpers
# ============================================================

def read_csv_if_exists(path: Path) -> pd.DataFrame:
    """
    Read a CSV file if it exists.
    """

    if not path.exists():
        print(f"WARNING: Missing change detection input file: {path}")
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

    if isinstance(value, np.generic):
        return value.item()

    return value


def safe_float(value, default=None):
    """
    Safely convert a value to float.
    """

    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def classify_change(delta: float | None, threshold: float = 2.5) -> str:
    """
    Classify score change direction.

    Positive score changes generally indicate higher risk pressure.
    Negative score changes generally indicate easing risk pressure.
    """

    if delta is None or pd.isna(delta):
        return "No Prior Snapshot"

    if delta >= threshold:
        return "Worsening"
    if delta <= -threshold:
        return "Improving"
    return "Stable"


def classify_materiality(delta: float | None) -> str:
    """
    Classify how meaningful a score change is.
    """

    if delta is None or pd.isna(delta):
        return "No Prior Snapshot"

    abs_delta = abs(delta)

    if abs_delta >= 10:
        return "High"
    if abs_delta >= 5:
        return "Moderate"
    if abs_delta >= 2.5:
        return "Low"
    return "Minimal"


def signal_for_metric(metric: str, snapshot: dict) -> str:
    """
    Return the best matching signal field for a tracked metric.
    """

    signal_map = {
        "composite_risk_score": "composite_risk_signal",
        "adjusted_geoeconomic_growth_risk_score": "adjusted_geoeconomic_growth_risk_signal",
        "growth_pressure_score": "growth_pressure_signal",
        "housing_affordability_pressure_score": "housing_affordability_pressure_signal",
        "construction_shock_score": "construction_shock_signal",
        "infrastructure_strain_score": "infrastructure_strain_signal",
        "development_friction_score": "development_friction_signal",
        "geoeconomic_industry_exposure_score": "geoeconomic_industry_exposure_signal",
        "household_vulnerability_score": "household_vulnerability_signal",
        "local_resilience_offset": "local_resilience_signal",
        "highest_risk_scenario_score": "highest_risk_scenario_signal",
    }

    signal_key = signal_map.get(metric)

    if signal_key:
        return snapshot.get(signal_key, "N/A")

    return snapshot.get(metric.replace("_score", "_signal"), "N/A")


def load_snapshot(path: Path) -> dict:
    """
    Load a JSON snapshot.
    """

    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_snapshot(snapshot: dict, path: Path) -> None:
    """
    Save snapshot to JSON.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(snapshot, file, indent=4, default=str)


# ============================================================
# Snapshot construction
# ============================================================

def build_current_snapshot() -> dict:
    """
    Build a snapshot of the latest model state.
    """

    composite_df = read_csv_if_exists(COMPOSITE_LATEST_FILE)
    growth_df = read_csv_if_exists(GROWTH_LATEST_FILE)
    construction_df = read_csv_if_exists(CONSTRUCTION_LATEST_FILE)
    resilience_df = read_csv_if_exists(RESILIENCE_LATEST_FILE)
    scenario_df = read_csv_if_exists(SCENARIO_SUMMARY_FILE)
    construction_category_df = read_csv_if_exists(CONSTRUCTION_CATEGORY_FILE)

    housing_df = read_csv_if_exists(HOUSING_LATEST_FILE)
    infrastructure_df = read_csv_if_exists(INFRASTRUCTURE_LATEST_FILE)
    development_df = read_csv_if_exists(DEVELOPMENT_FRICTION_LATEST_FILE)
    industry_df = read_csv_if_exists(GEOECONOMIC_INDUSTRY_LATEST_FILE)
    household_df = read_csv_if_exists(HOUSEHOLD_VULNERABILITY_LATEST_FILE)

    highest_scenario_name = None
    highest_scenario_score = None
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
        highest_scenario_signal = top_scenario.get("scenario_signal")

    fuel_energy_score = None
    materials_score = None
    financing_score = None

    if not construction_category_df.empty:
        for _, row in construction_category_df.iterrows():
            category = str(row.get("category", "")).lower()
            score = safe_float(row.get("category_score"))

            if category == "fuel_energy":
                fuel_energy_score = score
            elif category == "materials":
                materials_score = score
            elif category == "financing":
                financing_score = score

    snapshot = {
        "run_timestamp": pd.Timestamp.today().isoformat(),

        # Composite model
        "composite_risk_score": safe_float(
            safe_value(composite_df, "composite_risk_score")
        ),
        "composite_risk_signal": safe_value(
            composite_df,
            "composite_risk_signal",
            default="N/A",
        ),
        "adjusted_geoeconomic_growth_risk_score": safe_float(
            safe_value(composite_df, "adjusted_geoeconomic_growth_risk_score")
        ),
        "adjusted_geoeconomic_growth_risk_signal": safe_value(
            composite_df,
            "adjusted_geoeconomic_growth_risk_signal",
            default="N/A",
        ),

        # Resilience
        "local_resilience_offset": safe_float(
            safe_value(composite_df, "local_resilience_offset")
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
        "resilience_credit_applied": safe_float(
            safe_value(composite_df, "resilience_credit_applied")
        ),

        # Live risk modules
        "growth_pressure_score": safe_float(
            safe_value(growth_df, "growth_pressure_score")
        ),
        "growth_pressure_signal": safe_value(
            growth_df,
            "growth_pressure_signal",
            default="N/A",
        ),
        "housing_affordability_pressure_score": safe_float(
            safe_value(housing_df, "housing_affordability_pressure_score")
        ),
        "housing_affordability_pressure_signal": safe_value(
            housing_df,
            "housing_affordability_pressure_signal",
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
        "construction_shock_momentum_3m": safe_float(
            safe_value(construction_df, "construction_shock_momentum_3m")
        ),
        "construction_shock_momentum_signal": safe_value(
            construction_df,
            "construction_shock_momentum_signal",
            default="N/A",
        ),
        "infrastructure_strain_score": safe_float(
            safe_value(infrastructure_df, "infrastructure_strain_score")
        ),
        "infrastructure_strain_signal": safe_value(
            infrastructure_df,
            "infrastructure_strain_signal",
            default="N/A",
        ),
        "development_friction_score": safe_float(
            safe_value(development_df, "development_friction_score")
        ),
        "development_friction_signal": safe_value(
            development_df,
            "development_friction_signal",
            default="N/A",
        ),
        "geoeconomic_industry_exposure_score": safe_float(
            safe_value(industry_df, "geoeconomic_industry_exposure_score")
        ),
        "geoeconomic_industry_exposure_signal": safe_value(
            industry_df,
            "geoeconomic_industry_exposure_signal",
            default="N/A",
        ),
        "household_vulnerability_score": safe_float(
            safe_value(household_df, "household_vulnerability_score")
        ),
        "household_vulnerability_signal": safe_value(
            household_df,
            "household_vulnerability_signal",
            default="N/A",
        ),

        # Construction category sub-signals
        "fuel_energy_shock_score": fuel_energy_score,
        "materials_shock_score": materials_score,
        "financing_shock_score": financing_score,

        # Scenario
        "highest_risk_scenario": highest_scenario_name,
        "highest_risk_scenario_score": highest_scenario_score,
        "highest_risk_scenario_signal": highest_scenario_signal,

        # Model maturity
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
        "placeholder_components_used": safe_float(
            safe_value(composite_df, "placeholder_components_used")
        ),
        "live_components_used": safe_float(
            safe_value(composite_df, "live_components_used")
        ),
        "placeholder_share": safe_float(
            safe_value(composite_df, "placeholder_share")
        ),
    }

    return snapshot


# ============================================================
# Change detection
# ============================================================

def compare_snapshots(current: dict, previous: dict) -> pd.DataFrame:
    """
    Compare current and previous run snapshots.
    """

    tracked_metrics = [
        "composite_risk_score",
        "adjusted_geoeconomic_growth_risk_score",
        "growth_pressure_score",
        "housing_affordability_pressure_score",
        "construction_shock_score",
        "fuel_energy_shock_score",
        "materials_shock_score",
        "financing_shock_score",
        "infrastructure_strain_score",
        "development_friction_score",
        "geoeconomic_industry_exposure_score",
        "household_vulnerability_score",
        "local_resilience_offset",
        "resilience_credit_applied",
        "highest_risk_scenario_score",
        "placeholder_share",
        "live_components_used",
        "placeholder_components_used",
    ]

    rows = []

    for metric in tracked_metrics:
        current_value = safe_float(current.get(metric))
        previous_value = safe_float(previous.get(metric))

        if current_value is not None and previous_value is not None:
            delta = current_value - previous_value
        else:
            delta = None

        rows.append(
            {
                "metric": metric,
                "current_value": current_value,
                "previous_value": previous_value,
                "delta": delta,
                "change_direction": classify_change(delta),
                "change_materiality": classify_materiality(delta),
                "current_signal": signal_for_metric(metric, current),
            }
        )

    # Add qualitative scenario name change.
    current_scenario = current.get("highest_risk_scenario")
    previous_scenario = previous.get("highest_risk_scenario")

    rows.append(
        {
            "metric": "highest_risk_scenario",
            "current_value": current_scenario,
            "previous_value": previous_scenario,
            "delta": None,
            "change_direction": (
                "Changed"
                if previous_scenario and current_scenario != previous_scenario
                else "Stable"
                if previous_scenario
                else "No Prior Snapshot"
            ),
            "change_materiality": (
                "Moderate"
                if previous_scenario and current_scenario != previous_scenario
                else "Minimal"
                if previous_scenario
                else "No Prior Snapshot"
            ),
            "current_signal": current.get("highest_risk_scenario_signal", "N/A"),
        }
    )

    # Add qualitative model maturity change.
    current_maturity = current.get("model_maturity_level")
    previous_maturity = previous.get("model_maturity_level")

    rows.append(
        {
            "metric": "model_maturity_level",
            "current_value": current_maturity,
            "previous_value": previous_maturity,
            "delta": None,
            "change_direction": (
                "Changed"
                if previous_maturity and current_maturity != previous_maturity
                else "Stable"
                if previous_maturity
                else "No Prior Snapshot"
            ),
            "change_materiality": (
                "Moderate"
                if previous_maturity and current_maturity != previous_maturity
                else "Minimal"
                if previous_maturity
                else "No Prior Snapshot"
            ),
            "current_signal": current.get("data_quality_flag", "N/A"),
        }
    )

    return pd.DataFrame(rows)


def create_change_summary_text(change_df: pd.DataFrame) -> str:
    """
    Create a simple narrative summary.
    """

    if change_df.empty:
        return "No change detection summary available."

    no_prior = (change_df["change_direction"] == "No Prior Snapshot").all()

    if no_prior:
        return (
            "No prior snapshot was available. This run has been saved as the "
            "baseline for future change detection."
        )

    worsening = change_df[change_df["change_direction"] == "Worsening"]
    improving = change_df[change_df["change_direction"] == "Improving"]
    changed = change_df[change_df["change_direction"] == "Changed"]

    messages = []

    if not worsening.empty:
        metrics = ", ".join(worsening["metric"].head(5).tolist())
        messages.append(f"Risk pressure increased in: {metrics}.")

    if not improving.empty:
        metrics = ", ".join(improving["metric"].head(5).tolist())
        messages.append(f"Risk pressure eased in: {metrics}.")

    if not changed.empty:
        changed_metrics = ", ".join(changed["metric"].head(3).tolist())
        messages.append(f"Qualitative model fields changed in: {changed_metrics}.")

    if not messages:
        messages.append("No material changes were detected versus the prior run.")

    return " ".join(messages)


def run_change_detection() -> pd.DataFrame:
    """
    Run full change detection workflow.
    """

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    current_snapshot = build_current_snapshot()
    previous_snapshot = load_snapshot(LATEST_SNAPSHOT_FILE)

    change_df = compare_snapshots(current_snapshot, previous_snapshot)

    summary_text = create_change_summary_text(change_df)
    change_df["summary_text"] = summary_text
    change_df["run_timestamp"] = current_snapshot["run_timestamp"]

    change_df.to_csv(CHANGE_DETECTION_OUTPUT, index=False)

    # Preserve the prior latest snapshot before overwriting.
    if LATEST_SNAPSHOT_FILE.exists():
        shutil.copy2(LATEST_SNAPSHOT_FILE, PREVIOUS_SNAPSHOT_FILE)

    save_snapshot(current_snapshot, LATEST_SNAPSHOT_FILE)

    print(f"Saved change detection summary to: {CHANGE_DETECTION_OUTPUT}")
    print(f"Saved latest run snapshot to: {LATEST_SNAPSHOT_FILE}")

    print()
    print("Change Detection Summary")
    print("------------------------")
    print(summary_text)
    print()
    print(change_df.to_string(index=False))

    return change_df


def summarize_change_detection() -> pd.DataFrame:
    """
    Load and print the latest change detection summary.
    """

    if not CHANGE_DETECTION_OUTPUT.exists():
        raise FileNotFoundError(
            "No change detection summary found. Run run_change_detection() first."
        )

    change_df = pd.read_csv(CHANGE_DETECTION_OUTPUT)

    print()
    print("Latest change detection summary:")
    print(change_df.to_string(index=False))

    return change_df


def main() -> None:
    """
    Run change detection as a script.
    """

    run_change_detection()


if __name__ == "__main__":
    main()
