"""
Construction shock scoring module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module transforms FRED construction, fuel, energy, and financing indicators
into a 0-100 Construction Shock Exposure Score.

Inputs:
- data/processed/fred_series_wide.csv

Outputs:
- data/processed/construction_shock_scores.csv
- data/processed/construction_shock_latest.csv
- data/processed/construction_shock_component_summary.csv
- data/processed/construction_shock_category_summary.csv

Methodology:
- Most commodity / input-cost indicators are scored using 12-month percent change.
- Interest-rate indicators are scored using level-based normalization.
- The model also calculates category scores for materials, fuel/energy, and financing.
- Momentum and trailing-average fields are included to make the shock signal more interpretable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import PROCESSED_DATA_DIR, classify_risk


# ============================================================
# Input / output files
# ============================================================

FRED_WIDE_FILE = PROCESSED_DATA_DIR / "fred_series_wide.csv"

CONSTRUCTION_SHOCK_OUTPUT = PROCESSED_DATA_DIR / "construction_shock_scores.csv"
CONSTRUCTION_SHOCK_LATEST_OUTPUT = PROCESSED_DATA_DIR / "construction_shock_latest.csv"
CONSTRUCTION_SHOCK_COMPONENT_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "construction_shock_component_summary.csv"
)
CONSTRUCTION_SHOCK_CATEGORY_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "construction_shock_category_summary.csv"
)


# ============================================================
# Construction shock components and weights
# ============================================================

CONSTRUCTION_SHOCK_COMPONENTS = {
    "construction_materials_ppi": {
        "weight": 0.20,
        "category": "materials",
        "score_method": "yoy_change",
        "label": "Construction Materials PPI",
    },
    "lumber_ppi": {
        "weight": 0.10,
        "category": "materials",
        "score_method": "yoy_change",
        "label": "Lumber PPI",
    },
    "cement_ppi": {
        "weight": 0.10,
        "category": "materials",
        "score_method": "yoy_change",
        "label": "Cement PPI",
    },
    "steel_mill_products_ppi": {
        "weight": 0.10,
        "category": "materials",
        "score_method": "yoy_change",
        "label": "Steel Mill Products PPI",
    },
    "diesel_price": {
        "weight": 0.15,
        "category": "fuel_energy",
        "score_method": "yoy_change",
        "label": "Diesel Price",
    },
    "retail_gasoline": {
        "weight": 0.10,
        "category": "fuel_energy",
        "score_method": "yoy_change",
        "label": "Retail Gasoline Price",
    },
    "wti_crude_oil": {
        "weight": 0.10,
        "category": "fuel_energy",
        "score_method": "yoy_change",
        "label": "WTI Crude Oil",
    },
    "thirty_year_mortgage_rate": {
        "weight": 0.15,
        "category": "financing",
        "score_method": "level",
        "label": "30-Year Mortgage Rate",
    },
    "federal_funds_rate": {
        "weight": 0.10,
        "category": "financing",
        "score_method": "level",
        "label": "Federal Funds Rate",
    },
}


CATEGORY_LABELS = {
    "materials": "Construction Materials",
    "fuel_energy": "Fuel and Energy",
    "financing": "Financing Conditions",
}


# ============================================================
# Helpers
# ============================================================

def load_fred_wide(path=FRED_WIDE_FILE) -> pd.DataFrame:
    """
    Load the wide FRED dataset produced by src.fred_data.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}. Run `python -m src.fred_data` first."
        )

    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def minmax_score(series: pd.Series) -> pd.Series:
    """
    Convert a numeric series into a 0-100 score using min-max normalization.

    Higher values receive higher risk scores.
    """

    series = pd.to_numeric(series, errors="coerce")

    min_value = series.min(skipna=True)
    max_value = series.max(skipna=True)

    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        return pd.Series(np.nan, index=series.index)

    return ((series - min_value) / (max_value - min_value)) * 100


def safe_weighted_average(
    df: pd.DataFrame,
    score_cols: list[str],
    weights: dict[str, float],
) -> pd.Series:
    """
    Calculate row-wise weighted average while ignoring missing values.
    """

    numerator = pd.Series(0.0, index=df.index)
    denominator = pd.Series(0.0, index=df.index)

    for col in score_cols:
        if col not in df.columns:
            continue

        weight = weights.get(col, 0.0)
        valid = df[col].notna()

        numerator.loc[valid] += df.loc[valid, col] * weight
        denominator.loc[valid] += weight

    result = numerator / denominator.replace(0, np.nan)

    return result


def classify_data_quality(
    available_component_count: int,
    expected_component_count: int,
) -> str:
    """
    Classify component coverage for the construction shock model.
    """

    if expected_component_count == 0:
        return "No Model Components Defined"

    coverage = available_component_count / expected_component_count

    if coverage >= 0.90:
        return "Strong Component Coverage"
    if coverage >= 0.70:
        return "Moderate Component Coverage"
    if coverage > 0:
        return "Limited Component Coverage"
    return "No Component Coverage"


def calculate_yoy_change(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Calculate year-over-year percentage change for selected columns.

    Because FRED series have mixed frequencies, this function forward-fills values
    and calculates a 12-period percent change on monthly-resampled data.
    """

    monthly = df.set_index("date").sort_index()

    monthly = monthly.resample("ME").last().ffill()

    for col in columns:
        if col in monthly.columns:
            monthly[f"{col}_yoy_pct"] = monthly[col].pct_change(12) * 100

    monthly = monthly.reset_index()

    return monthly


# ============================================================
# Scoring logic
# ============================================================

def build_component_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build normalized construction shock component scores.
    """

    expected_components = list(CONSTRUCTION_SHOCK_COMPONENTS.keys())

    available_components = [
        col for col in expected_components if col in df.columns
    ]

    missing_components = [
        col for col in expected_components if col not in df.columns
    ]

    if missing_components:
        print("WARNING: Missing construction shock components:")
        for col in missing_components:
            print(f" - {col}")

    if not available_components:
        raise ValueError("No construction shock components found in FRED dataset.")

    monthly = calculate_yoy_change(df, available_components)

    score_df = monthly[["date"]].copy()

    for component in available_components:
        component_config = CONSTRUCTION_SHOCK_COMPONENTS[component]
        score_method = component_config["score_method"]

        raw_col = component
        yoy_col = f"{component}_yoy_pct"

        if raw_col in monthly.columns:
            score_df[f"{component}_raw_value"] = monthly[raw_col]

        if yoy_col in monthly.columns:
            score_df[f"{component}_yoy_pct"] = monthly[yoy_col]

        if score_method == "level":
            score_df[f"{component}_score"] = minmax_score(monthly[raw_col])
        elif score_method == "yoy_change" and yoy_col in monthly.columns:
            score_df[f"{component}_score"] = minmax_score(monthly[yoy_col])
        else:
            score_df[f"{component}_score"] = minmax_score(monthly[raw_col])

    score_df["available_component_count"] = len(available_components)
    score_df["expected_component_count"] = len(expected_components)
    score_df["missing_component_count"] = len(missing_components)
    score_df["component_coverage_ratio"] = len(available_components) / len(expected_components)
    score_df["data_quality_flag"] = classify_data_quality(
        available_component_count=len(available_components),
        expected_component_count=len(expected_components),
    )

    return score_df


def calculate_category_scores(score_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate materials, fuel/energy, and financing category scores.
    """

    result = score_df.copy()

    for category in sorted({info["category"] for info in CONSTRUCTION_SHOCK_COMPONENTS.values()}):
        category_components = [
            component
            for component, info in CONSTRUCTION_SHOCK_COMPONENTS.items()
            if info["category"] == category
        ]

        score_cols = [
            f"{component}_score"
            for component in category_components
            if f"{component}_score" in result.columns
        ]

        category_weights = {
            f"{component}_score": CONSTRUCTION_SHOCK_COMPONENTS[component]["weight"]
            for component in category_components
            if f"{component}_score" in result.columns
        }

        if score_cols:
            result[f"{category}_shock_score"] = safe_weighted_average(
                result,
                score_cols=score_cols,
                weights=category_weights,
            )
        else:
            result[f"{category}_shock_score"] = np.nan

    return result


def calculate_construction_shock_score(score_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the weighted Construction Shock Exposure Score.
    """

    result = calculate_category_scores(score_df)

    score_cols = []
    weights = {}

    for component, info in CONSTRUCTION_SHOCK_COMPONENTS.items():
        score_col = f"{component}_score"

        if score_col in result.columns:
            score_cols.append(score_col)
            weights[score_col] = info["weight"]

    if not score_cols:
        raise ValueError("No component score columns available for construction shock scoring.")

    result["construction_shock_score"] = safe_weighted_average(
        result,
        score_cols=score_cols,
        weights=weights,
    )

    result["construction_shock_score_3m_ma"] = (
        result["construction_shock_score"].rolling(window=3, min_periods=1).mean()
    )

    result["construction_shock_score_12m_ma"] = (
        result["construction_shock_score"].rolling(window=12, min_periods=3).mean()
    )

    result["construction_shock_momentum_3m"] = (
        result["construction_shock_score"]
        - result["construction_shock_score"].shift(3)
    )

    result["construction_shock_momentum_12m"] = (
        result["construction_shock_score"]
        - result["construction_shock_score"].shift(12)
    )

    result["construction_shock_trailing_5y_avg"] = (
        result["construction_shock_score"].rolling(window=60, min_periods=12).mean()
    )

    result["construction_shock_vs_5y_avg"] = (
        result["construction_shock_score"]
        - result["construction_shock_trailing_5y_avg"]
    )

    result["construction_shock_signal"] = result["construction_shock_score"].apply(
        lambda x: classify_risk(float(x)) if pd.notna(x) else "Insufficient Data"
    )

    result["construction_shock_momentum_signal"] = result[
        "construction_shock_momentum_3m"
    ].apply(classify_momentum)

    return result


def classify_momentum(momentum: float) -> str:
    """
    Classify short-term shock momentum.
    """

    if pd.isna(momentum):
        return "Insufficient History"
    if momentum >= 10:
        return "Rapidly Rising"
    if momentum >= 3:
        return "Rising"
    if momentum <= -10:
        return "Rapidly Easing"
    if momentum <= -3:
        return "Easing"
    return "Stable"


# ============================================================
# Summaries
# ============================================================

def summarize_construction_categories(result: pd.DataFrame) -> pd.DataFrame:
    """
    Create a latest category-level summary table.
    """

    latest = (
        result.dropna(subset=["construction_shock_score"])
        .sort_values("date")
        .tail(1)
    )

    if latest.empty:
        raise ValueError("No latest construction shock score available.")

    latest_row = latest.iloc[0]

    rows = []

    for category, label in CATEGORY_LABELS.items():
        col = f"{category}_shock_score"

        if col in latest_row.index:
            rows.append(
                {
                    "category": category,
                    "category_label": label,
                    "category_score": latest_row[col],
                    "category_signal": classify_risk(float(latest_row[col]))
                    if pd.notna(latest_row[col])
                    else "Insufficient Data",
                }
            )

    summary = pd.DataFrame(rows)
    summary.to_csv(CONSTRUCTION_SHOCK_CATEGORY_SUMMARY_OUTPUT, index=False)

    print(f"Saved construction shock category summary to: {CONSTRUCTION_SHOCK_CATEGORY_SUMMARY_OUTPUT}")

    return summary


def summarize_construction_shock(result: pd.DataFrame) -> pd.DataFrame:
    """
    Create a compact summary table for the latest available component scores.
    """

    latest = (
        result.dropna(subset=["construction_shock_score"])
        .sort_values("date")
        .tail(1)
    )

    if latest.empty:
        raise ValueError("No latest construction shock score available.")

    latest_row = latest.iloc[0]

    rows = []

    for component, info in CONSTRUCTION_SHOCK_COMPONENTS.items():
        score_col = f"{component}_score"
        raw_col = f"{component}_raw_value"
        yoy_col = f"{component}_yoy_pct"

        if score_col in latest_row.index:
            rows.append(
                {
                    "component": component,
                    "label": info["label"],
                    "category": info["category"],
                    "weight": info["weight"],
                    "score_method": info["score_method"],
                    "raw_latest_value": latest_row[raw_col]
                    if raw_col in latest_row.index
                    else np.nan,
                    "latest_yoy_pct": latest_row[yoy_col]
                    if yoy_col in latest_row.index
                    else np.nan,
                    "component_score": latest_row[score_col],
                    "weighted_contribution": info["weight"] * latest_row[score_col],
                }
            )

    summary = pd.DataFrame(rows)
    summary.to_csv(CONSTRUCTION_SHOCK_COMPONENT_SUMMARY_OUTPUT, index=False)

    print(f"Saved construction shock component summary to: {CONSTRUCTION_SHOCK_COMPONENT_SUMMARY_OUTPUT}")

    return summary


# ============================================================
# Main model
# ============================================================

def build_construction_shock_model() -> pd.DataFrame:
    """
    Run the full construction shock scoring model.
    """

    fred_df = load_fred_wide()

    score_df = build_component_scores(fred_df)
    result = calculate_construction_shock_score(score_df)

    result.to_csv(CONSTRUCTION_SHOCK_OUTPUT, index=False)

    latest = (
        result.dropna(subset=["construction_shock_score"])
        .sort_values("date")
        .tail(1)
        .copy()
    )

    latest.to_csv(CONSTRUCTION_SHOCK_LATEST_OUTPUT, index=False)

    summarize_construction_categories(result)

    print(f"Saved construction shock scores to: {CONSTRUCTION_SHOCK_OUTPUT}")
    print(f"Saved latest construction shock score to: {CONSTRUCTION_SHOCK_LATEST_OUTPUT}")

    if not latest.empty:
        latest_row = latest.iloc[0]
        print()
        print("Latest Construction Shock Exposure Score")
        print("----------------------------------------")
        print(f"Date: {latest_row['date'].date()}")
        print(f"Score: {latest_row['construction_shock_score']:.2f}")
        print(f"Signal: {latest_row['construction_shock_signal']}")
        print(f"3-month momentum: {latest_row['construction_shock_momentum_3m']:.2f}")
        print(f"Momentum signal: {latest_row['construction_shock_momentum_signal']}")
        print(f"Score vs. 5-year average: {latest_row['construction_shock_vs_5y_avg']:.2f}")
        print(f"Data quality: {latest_row['data_quality_flag']}")

    return result


def main() -> None:
    """
    Run construction shock scoring as a script.
    """

    result = build_construction_shock_model()
    component_summary = summarize_construction_shock(result)
    category_summary = summarize_construction_categories(result)

    print()
    print("Latest construction shock component scores:")
    print(component_summary.to_string(index=False))

    print()
    print("Latest construction shock category scores:")
    print(category_summary.to_string(index=False))


if __name__ == "__main__":
    main()