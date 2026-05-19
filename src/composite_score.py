"""
Composite geoeconomic growth risk scoring module.

This module combines available component scores into the Gallatin-Sumner County
Geoeconomic Growth Risk Score.

Current live components:
- Growth Pressure Score
- Housing Affordability Pressure Score
- Construction Shock Exposure Score
- Infrastructure Strain Score
- Development Friction Score
- Geoeconomic Industry Exposure Score
- Household Vulnerability Score
- Local Resilience Offset

Placeholder components for future modules:
- None

Inputs:
- data/processed/growth_pressure_latest.csv
- data/processed/housing_affordability_latest.csv
- data/processed/construction_shock_latest.csv
- data/processed/infrastructure_strain_latest.csv
- data/processed/development_friction_latest.csv
- data/processed/geoeconomic_industry_exposure_latest.csv
- data/processed/household_vulnerability_latest.csv
- data/processed/local_resilience_latest.csv

Outputs:
- data/processed/composite_risk_score.csv
- data/processed/composite_risk_score_latest.csv
- data/processed/composite_risk_component_summary.csv

Methodology note:
The Local Resilience Offset is treated as a capped risk credit rather than a
large direct subtraction. This prevents qualitative resilience evidence from
overpowering high growth pressure or construction shock risk.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import (
    MAX_RESILIENCE_CREDIT,
    MODEL_MATURITY_THRESHOLDS,
    PROCESSED_DATA_DIR,
    RESILIENCE_CREDIT_RATE,
    RISK_SCORE_WEIGHTS,
    classify_risk,
)


# ============================================================
# Input / output files
# ============================================================

GROWTH_PRESSURE_LATEST_FILE = PROCESSED_DATA_DIR / "growth_pressure_latest.csv"

HOUSING_AFFORDABILITY_LATEST_FILE = (
    PROCESSED_DATA_DIR / "housing_affordability_latest.csv"
)

CONSTRUCTION_SHOCK_LATEST_FILE = PROCESSED_DATA_DIR / "construction_shock_latest.csv"

INFRASTRUCTURE_STRAIN_LATEST_FILE = (
    PROCESSED_DATA_DIR / "infrastructure_strain_latest.csv"
)

DEVELOPMENT_FRICTION_LATEST_FILE = (
    PROCESSED_DATA_DIR / "development_friction_latest.csv"
)

GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_FILE = (
    PROCESSED_DATA_DIR / "geoeconomic_industry_exposure_latest.csv"
)

HOUSEHOLD_VULNERABILITY_LATEST_FILE = (
    PROCESSED_DATA_DIR / "household_vulnerability_latest.csv"
)

LOCAL_RESILIENCE_LATEST_FILE = PROCESSED_DATA_DIR / "local_resilience_latest.csv"

COMPOSITE_RISK_OUTPUT = PROCESSED_DATA_DIR / "composite_risk_score.csv"
COMPOSITE_RISK_LATEST_OUTPUT = PROCESSED_DATA_DIR / "composite_risk_score_latest.csv"
COMPOSITE_COMPONENT_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "composite_risk_component_summary.csv"
)


# ============================================================
# Placeholder scores
# ============================================================

# No placeholder scores remain after household_vulnerability.py is added.
# Keep this dictionary in place so model maturity and reporting logic remain
# stable if future optional modules are added.
PLACEHOLDER_COMPONENT_SCORES = {}


# ============================================================
# Helper functions
# ============================================================

def clamp_score(score: float, lower: float = 0.0, upper: float = 100.0) -> float:
    """
    Keep a score within a defined range.
    """

    if pd.isna(score):
        return np.nan

    return float(max(min(score, upper), lower))


def safe_classify_risk(score: float) -> str:
    """
    Classify risk safely.
    """

    if score is None or pd.isna(score):
        return "Missing Data"

    return classify_risk(float(score))


def classify_model_maturity(placeholder_count: int, total_components: int) -> str:
    """
    Classify model maturity based on placeholder share.
    """

    if total_components == 0:
        return "Insufficient Model Structure"

    placeholder_share = placeholder_count / total_components

    mostly_threshold = MODEL_MATURITY_THRESHOLDS[
        "mostly_data_driven_max_placeholder_share"
    ]
    partial_threshold = MODEL_MATURITY_THRESHOLDS[
        "partially_data_driven_max_placeholder_share"
    ]

    if placeholder_count == 0:
        return "Fully Data-Driven"
    if placeholder_share <= mostly_threshold:
        return "Mostly Data-Driven"
    if placeholder_share <= partial_threshold:
        return "Partially Data-Driven"
    return "Prototype Model"


def classify_data_quality(placeholder_count: int, missing_count: int) -> str:
    """
    Create a simple data quality flag for reporting.
    """

    if missing_count > 0 and placeholder_count > 0:
        return "Prototype - Placeholder and Missing Components"
    if missing_count > 0:
        return "Incomplete - Missing Components"
    if placeholder_count > 0:
        return "Prototype - Placeholder Components Used"
    return "Data-Driven Components Available"


def load_latest_score(
    path,
    score_column: str,
    signal_column: str | None = None,
) -> dict[str, object]:
    """
    Load the latest score from a processed module output.
    """

    if not path.exists():
        print(f"WARNING: Could not find {path}. Score will be set to NaN.")
        return {
            "score": np.nan,
            "signal": "Missing Data",
            "date": pd.NaT,
            "source_status": "missing_file",
        }

    df = pd.read_csv(path)

    if df.empty:
        print(f"WARNING: {path} is empty. Score will be set to NaN.")
        return {
            "score": np.nan,
            "signal": "Missing Data",
            "date": pd.NaT,
            "source_status": "empty_file",
        }

    latest = df.tail(1).iloc[0]

    score = latest[score_column] if score_column in latest.index else np.nan

    if signal_column is not None and signal_column in latest.index:
        signal = latest[signal_column]
    elif pd.notna(score):
        signal = safe_classify_risk(float(score))
    else:
        signal = "Missing Data"

    date = latest["date"] if "date" in latest.index else pd.NaT

    return {
        "score": float(score) if pd.notna(score) else np.nan,
        "signal": signal,
        "date": date,
        "source_status": "available" if pd.notna(score) else "missing_score",
    }


def collect_component_scores() -> dict[str, dict[str, object]]:
    """
    Collect all current risk component scores.
    """

    growth = load_latest_score(
        GROWTH_PRESSURE_LATEST_FILE,
        score_column="growth_pressure_score",
        signal_column="growth_pressure_signal",
    )

    housing = load_latest_score(
        HOUSING_AFFORDABILITY_LATEST_FILE,
        score_column="housing_affordability_pressure_score",
        signal_column="housing_affordability_pressure_signal",
    )

    construction = load_latest_score(
        CONSTRUCTION_SHOCK_LATEST_FILE,
        score_column="construction_shock_score",
        signal_column="construction_shock_signal",
    )

    infrastructure = load_latest_score(
        INFRASTRUCTURE_STRAIN_LATEST_FILE,
        score_column="infrastructure_strain_score",
        signal_column="infrastructure_strain_signal",
    )

    development_friction = load_latest_score(
        DEVELOPMENT_FRICTION_LATEST_FILE,
        score_column="development_friction_score",
        signal_column="development_friction_signal",
    )

    geoeconomic_industry_exposure = load_latest_score(
        GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_FILE,
        score_column="geoeconomic_industry_exposure_score",
        signal_column="geoeconomic_industry_exposure_signal",
    )

    household_vulnerability = load_latest_score(
        HOUSEHOLD_VULNERABILITY_LATEST_FILE,
        score_column="household_vulnerability_score",
        signal_column="household_vulnerability_signal",
    )

    components = {
        "growth_pressure": growth,
        "housing_affordability_pressure": housing,
        "construction_shock_exposure": construction,
        "infrastructure_strain": infrastructure,
        "development_friction": development_friction,
        "geoeconomic_industry_exposure": geoeconomic_industry_exposure,
        "household_vulnerability": household_vulnerability,
    }

    for component, placeholder_score in PLACEHOLDER_COMPONENT_SCORES.items():
        components[component] = {
            "score": float(placeholder_score),
            "signal": safe_classify_risk(float(placeholder_score)),
            "date": pd.Timestamp.today().date().isoformat(),
            "source_status": "placeholder",
        }

    return components


def load_local_resilience_offset() -> dict[str, object]:
    """
    Load the Local Resilience Offset from the local resilience module.
    """

    if not LOCAL_RESILIENCE_LATEST_FILE.exists():
        print(
            f"WARNING: Could not find {LOCAL_RESILIENCE_LATEST_FILE}. "
            "Resilience offset will be set to zero."
        )
        return {
            "offset": 0.0,
            "signal": "Missing Data",
            "confidence": "Missing Data",
            "date": pd.Timestamp.today().date().isoformat(),
            "source_status": "missing_file",
        }

    df = pd.read_csv(LOCAL_RESILIENCE_LATEST_FILE)

    if df.empty:
        return {
            "offset": 0.0,
            "signal": "Missing Data",
            "confidence": "Missing Data",
            "date": pd.Timestamp.today().date().isoformat(),
            "source_status": "empty_file",
        }

    latest = df.tail(1).iloc[0]

    offset = (
        float(latest["local_resilience_offset"])
        if "local_resilience_offset" in latest.index
        and pd.notna(latest["local_resilience_offset"])
        else 0.0
    )

    signal = (
        latest["local_resilience_signal"]
        if "local_resilience_signal" in latest.index
        else "Missing Data"
    )

    confidence = (
        latest["local_resilience_confidence"]
        if "local_resilience_confidence" in latest.index
        else "N/A"
    )

    date = (
        latest["date"]
        if "date" in latest.index
        else pd.Timestamp.today().date().isoformat()
    )

    return {
        "offset": clamp_score(offset),
        "signal": signal,
        "confidence": confidence,
        "date": date,
        "source_status": "available",
    }


def calculate_composite_risk(
    component_scores: dict[str, dict[str, object]],
) -> tuple[float, pd.DataFrame]:
    """
    Calculate weighted composite risk score before resilience credit.
    """

    rows = []

    for component, weight in RISK_SCORE_WEIGHTS.items():
        component_info = component_scores.get(component, {})
        score = component_info.get("score", np.nan)

        if pd.isna(score):
            weighted_contribution = np.nan
        else:
            weighted_contribution = float(score) * weight

        rows.append(
            {
                "component": component,
                "weight": weight,
                "score": score,
                "signal": component_info.get("signal", "Missing Data"),
                "source_date": component_info.get("date", pd.NaT),
                "source_status": component_info.get("source_status", "unknown"),
                "weighted_contribution": weighted_contribution,
                "is_placeholder": component in PLACEHOLDER_COMPONENT_SCORES,
                "is_live_component": (
                    component not in PLACEHOLDER_COMPONENT_SCORES
                    and component_info.get("source_status") == "available"
                ),
                "is_missing": pd.isna(score),
            }
        )

    component_summary = pd.DataFrame(rows)

    valid_components = component_summary.dropna(subset=["score"]).copy()

    if valid_components.empty:
        return np.nan, component_summary

    total_weight = valid_components["weight"].sum()

    if total_weight <= 0:
        return np.nan, component_summary

    composite_score = valid_components["weighted_contribution"].sum() / total_weight

    return clamp_score(composite_score), component_summary


def calculate_resilience_credit(
    resilience_offset: float,
    credit_rate: float = RESILIENCE_CREDIT_RATE,
    max_credit: float = MAX_RESILIENCE_CREDIT,
) -> float:
    """
    Convert the Local Resilience Offset into a capped risk reduction credit.
    """

    if pd.isna(resilience_offset):
        return 0.0

    raw_credit = float(resilience_offset) * credit_rate
    capped_credit = min(raw_credit, max_credit)

    return float(max(capped_credit, 0.0))


def calculate_adjusted_risk(
    composite_score: float,
    resilience_credit: float,
) -> float:
    """
    Apply the capped resilience credit to the composite score.
    """

    if pd.isna(composite_score):
        return np.nan

    adjusted_score = composite_score - resilience_credit

    return clamp_score(adjusted_score)


def build_composite_score_model() -> pd.DataFrame:
    """
    Run the full composite risk scoring model.
    """

    component_scores = collect_component_scores()
    resilience = load_local_resilience_offset()

    composite_score, component_summary = calculate_composite_risk(component_scores)

    resilience_offset = float(resilience["offset"])

    resilience_credit = calculate_resilience_credit(
        resilience_offset=resilience_offset,
        credit_rate=RESILIENCE_CREDIT_RATE,
        max_credit=MAX_RESILIENCE_CREDIT,
    )

    adjusted_score = calculate_adjusted_risk(
        composite_score=composite_score,
        resilience_credit=resilience_credit,
    )

    total_components = len(component_summary)
    placeholder_count = int(component_summary["is_placeholder"].sum())
    live_component_count = int(component_summary["is_live_component"].sum())
    missing_component_count = int(component_summary["is_missing"].sum())

    placeholder_share = (
        placeholder_count / total_components if total_components > 0 else np.nan
    )

    model_maturity = classify_model_maturity(
        placeholder_count=placeholder_count,
        total_components=total_components,
    )

    data_quality_flag = classify_data_quality(
        placeholder_count=placeholder_count,
        missing_count=missing_component_count,
    )

    result = pd.DataFrame(
        [
            {
                "date": pd.Timestamp.today().normalize(),
                "composite_risk_score": composite_score,
                "composite_risk_signal": safe_classify_risk(composite_score)
                if pd.notna(composite_score)
                else "Insufficient Data",
                "local_resilience_offset": resilience_offset,
                "local_resilience_signal": resilience["signal"],
                "local_resilience_confidence": resilience["confidence"],
                "resilience_credit_rate": RESILIENCE_CREDIT_RATE,
                "max_resilience_credit": MAX_RESILIENCE_CREDIT,
                "resilience_credit_applied": resilience_credit,
                "adjusted_geoeconomic_growth_risk_score": adjusted_score,
                "adjusted_geoeconomic_growth_risk_signal": safe_classify_risk(adjusted_score)
                if pd.notna(adjusted_score)
                else "Insufficient Data",
                "placeholder_components_used": placeholder_count,
                "live_components_used": live_component_count,
                "missing_components": missing_component_count,
                "total_components": total_components,
                "placeholder_share": placeholder_share,
                "model_maturity_level": model_maturity,
                "data_quality_flag": data_quality_flag,
            }
        ]
    )

    result.to_csv(COMPOSITE_RISK_OUTPUT, index=False)
    result.to_csv(COMPOSITE_RISK_LATEST_OUTPUT, index=False)
    component_summary.to_csv(COMPOSITE_COMPONENT_SUMMARY_OUTPUT, index=False)

    print(f"Saved composite risk score to: {COMPOSITE_RISK_OUTPUT}")
    print(f"Saved latest composite risk score to: {COMPOSITE_RISK_LATEST_OUTPUT}")
    print(f"Saved composite component summary to: {COMPOSITE_COMPONENT_SUMMARY_OUTPUT}")

    latest = result.iloc[0]

    print()
    print("Composite Geoeconomic Growth Risk Score")
    print("---------------------------------------")

    composite_display = (
        f"{latest['composite_risk_score']:.2f}"
        if pd.notna(latest["composite_risk_score"])
        else "N/A"
    )
    adjusted_display = (
        f"{latest['adjusted_geoeconomic_growth_risk_score']:.2f}"
        if pd.notna(latest["adjusted_geoeconomic_growth_risk_score"])
        else "N/A"
    )

    print(f"Composite risk score: {composite_display}")
    print(f"Composite signal: {latest['composite_risk_signal']}")
    print(f"Local resilience offset: {latest['local_resilience_offset']:.2f}")
    print(f"Local resilience signal: {latest['local_resilience_signal']}")
    print(f"Local resilience confidence: {latest['local_resilience_confidence']}")
    print(f"Resilience credit applied: {latest['resilience_credit_applied']:.2f}")
    print(f"Adjusted geoeconomic growth risk score: {adjusted_display}")
    print(
        "Adjusted signal: "
        f"{latest['adjusted_geoeconomic_growth_risk_signal']}"
    )
    print(f"Placeholder components used: {latest['placeholder_components_used']}")
    print(f"Live components used: {latest['live_components_used']}")
    print(f"Placeholder share: {latest['placeholder_share']:.1%}")
    print(f"Model maturity level: {latest['model_maturity_level']}")
    print(f"Data quality flag: {latest['data_quality_flag']}")

    return result


def summarize_composite_components() -> pd.DataFrame:
    """
    Load and print the composite component summary.
    """

    if not COMPOSITE_COMPONENT_SUMMARY_OUTPUT.exists():
        raise FileNotFoundError(
            "No composite component summary found. "
            "Run build_composite_score_model() first."
        )

    summary = pd.read_csv(COMPOSITE_COMPONENT_SUMMARY_OUTPUT)

    print()
    print("Composite component summary:")
    print(summary.to_string(index=False))

    return summary


def main() -> None:
    """
    Run composite scoring as a script.
    """

    build_composite_score_model()
    summarize_composite_components()


if __name__ == "__main__":
    main()
