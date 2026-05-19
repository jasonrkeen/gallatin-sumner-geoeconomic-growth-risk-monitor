"""
Growth pressure scoring module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module estimates local growth pressure using:
- Sumner County real GDP growth
- Sumner County unemployment / labor-market tightness
- manually curated local source notes related to growth, development, infrastructure,
  construction, zoning, and economic expansion

Inputs:
- data/processed/fred_series_wide.csv
- data/raw/local_source_notes.csv

Outputs:
- data/processed/growth_pressure_scores.csv
- data/processed/growth_pressure_latest.csv
- data/processed/growth_pressure_source_summary.csv
- data/processed/growth_pressure_component_summary.csv

Methodology note:
Historical growth-pressure scores are based primarily on official economic data.
The local-source signal is applied only to the latest available year so that
current development and zoning narratives do not artificially inflate prior years.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import (
    LOCAL_SOURCE_NOTES_FILE,
    PROCESSED_DATA_DIR,
    classify_risk,
)


# ============================================================
# Input / output files
# ============================================================

FRED_WIDE_FILE = PROCESSED_DATA_DIR / "fred_series_wide.csv"

GROWTH_PRESSURE_OUTPUT = PROCESSED_DATA_DIR / "growth_pressure_scores.csv"
GROWTH_PRESSURE_LATEST_OUTPUT = PROCESSED_DATA_DIR / "growth_pressure_latest.csv"
GROWTH_PRESSURE_SOURCE_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "growth_pressure_source_summary.csv"
)
GROWTH_PRESSURE_COMPONENT_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "growth_pressure_component_summary.csv"
)


# ============================================================
# Growth pressure configuration
# ============================================================

GROWTH_RELATED_CHANNELS = {
    "growth_pressure",
    "development_friction",
    "infrastructure_strain",
    "infrastructure_resilience",
    "construction_risk",
    "geoeconomic_exposure",
    "logistics_supply_chain_exposure",
    "local_resilience",
}

LOCAL_ACTIVITY_CHANNELS = {
    "growth_pressure",
    "development_friction",
    "construction_risk",
    "infrastructure_strain",
    "geoeconomic_exposure",
    "logistics_supply_chain_exposure",
}

GROWTH_PRESSURE_WEIGHTS = {
    "real_gdp_growth_score": 0.45,
    "labor_market_tightness_score": 0.25,
    "local_growth_signal_score": 0.20,
    "development_activity_signal_score": 0.10,
}

HISTORICAL_GROWTH_PRESSURE_WEIGHTS = {
    "real_gdp_growth_score": 0.65,
    "labor_market_tightness_score": 0.35,
}


# ============================================================
# Helpers
# ============================================================

def load_fred_wide(path=FRED_WIDE_FILE) -> pd.DataFrame:
    """
    Load the wide FRED dataset.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}. Run `python -m src.fred_data` first."
        )

    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def minmax_score(series: pd.Series, invert: bool = False) -> pd.Series:
    """
    Convert a numeric series into a 0-100 min-max score.

    If invert=True, lower values receive higher risk scores.
    This is useful for unemployment because very low unemployment can indicate
    labor-market tightness during a growth cycle.
    """

    series = pd.to_numeric(series, errors="coerce")

    min_value = series.min(skipna=True)
    max_value = series.max(skipna=True)

    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        return pd.Series(np.nan, index=series.index)

    score = ((series - min_value) / (max_value - min_value)) * 100

    if invert:
        score = 100 - score

    return score


def safe_weighted_average(row: pd.Series, weights: dict[str, float]) -> float:
    """
    Calculate a weighted average while ignoring missing components.
    """

    weighted_sum = 0.0
    total_weight = 0.0

    for component, weight in weights.items():
        value = row.get(component, np.nan)

        if pd.notna(value):
            weighted_sum += float(value) * weight
            total_weight += weight

    if total_weight == 0:
        return np.nan

    return weighted_sum / total_weight


def load_local_source_notes(path=LOCAL_SOURCE_NOTES_FILE) -> pd.DataFrame:
    """
    Load manually curated local source notes.

    If the file does not exist yet, returns an empty DataFrame with the expected columns.
    """

    columns = [
        "date",
        "source_name",
        "source_type",
        "jurisdiction",
        "topic",
        "key_point",
        "risk_channel",
        "url_or_file",
    ]

    if not path.exists():
        print(f"WARNING: Could not find {path}. Local source signal will be set to zero.")
        return pd.DataFrame(columns=columns)

    df = pd.read_csv(path)

    for col in columns:
        if col not in df.columns:
            df[col] = np.nan

    df = df[columns].copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["source_name"] = df["source_name"].fillna("").astype(str)
    df["source_type"] = df["source_type"].fillna("").astype(str)
    df["jurisdiction"] = df["jurisdiction"].fillna("").astype(str)
    df["topic"] = df["topic"].fillna("").astype(str)
    df["key_point"] = df["key_point"].fillna("").astype(str)
    df["url_or_file"] = df["url_or_file"].fillna("").astype(str)
    df["risk_channel"] = df["risk_channel"].fillna("").astype(str).str.strip().str.lower()

    return df


# ============================================================
# Local source signal
# ============================================================

def summarize_local_growth_sources(notes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize local source notes by risk channel and jurisdiction.
    """

    if notes_df.empty:
        summary = pd.DataFrame(
            columns=[
                "jurisdiction",
                "risk_channel",
                "source_note_count",
                "unique_sources",
            ]
        )
    else:
        growth_notes = notes_df[
            notes_df["risk_channel"].isin(GROWTH_RELATED_CHANNELS)
        ].copy()

        if growth_notes.empty:
            summary = pd.DataFrame(
                columns=[
                    "jurisdiction",
                    "risk_channel",
                    "source_note_count",
                    "unique_sources",
                ]
            )
        else:
            summary = (
                growth_notes.groupby(["jurisdiction", "risk_channel"], dropna=False)
                .agg(
                    source_note_count=("key_point", "count"),
                    unique_sources=("source_name", "nunique"),
                )
                .reset_index()
                .sort_values(["source_note_count", "unique_sources"], ascending=False)
            )

    summary.to_csv(GROWTH_PRESSURE_SOURCE_SUMMARY_OUTPUT, index=False)
    print(f"Saved growth pressure source summary to: {GROWTH_PRESSURE_SOURCE_SUMMARY_OUTPUT}")

    return summary


def calculate_local_source_signal(notes_df: pd.DataFrame) -> dict[str, object]:
    """
    Convert manually curated local source notes into capped current-period signal scores.

    Version 2 logic:
    - Local notes support the latest/current growth pressure score only.
    - More unique sources matter more than repeated notes from one source.
    - Development-related channels increase development activity signal.
    - Scores are capped to avoid qualitative notes overwhelming official data.
    """

    if notes_df.empty:
        return {
            "local_growth_signal_score": 0.0,
            "development_activity_signal_score": 0.0,
            "growth_note_count": 0,
            "development_note_count": 0,
            "unique_growth_sources": 0,
            "unique_development_sources": 0,
            "local_source_signal_confidence": "No Evidence",
        }

    growth_notes = notes_df[
        notes_df["risk_channel"].isin(GROWTH_RELATED_CHANNELS)
    ].copy()

    if growth_notes.empty:
        return {
            "local_growth_signal_score": 0.0,
            "development_activity_signal_score": 0.0,
            "growth_note_count": 0,
            "development_note_count": 0,
            "unique_growth_sources": 0,
            "unique_development_sources": 0,
            "local_source_signal_confidence": "No Evidence",
        }

    development_notes = growth_notes[
        growth_notes["risk_channel"].isin(LOCAL_ACTIVITY_CHANNELS)
    ].copy()

    growth_note_count = len(growth_notes)
    development_note_count = len(development_notes)

    unique_growth_sources = growth_notes["source_name"].nunique()
    unique_development_sources = development_notes["source_name"].nunique()

    # Conservative, capped qualitative signals.
    local_growth_signal_score = min(
        growth_note_count * 4.0 + unique_growth_sources * 8.0,
        80.0,
    )

    development_activity_signal_score = min(
        development_note_count * 5.0 + unique_development_sources * 8.0,
        85.0,
    )

    if unique_growth_sources >= 5 and growth_note_count >= 8:
        confidence = "Strong Qualitative Signal"
    elif unique_growth_sources >= 3 and growth_note_count >= 5:
        confidence = "Moderate Qualitative Signal"
    elif growth_note_count > 0:
        confidence = "Limited Qualitative Signal"
    else:
        confidence = "No Evidence"

    return {
        "local_growth_signal_score": float(local_growth_signal_score),
        "development_activity_signal_score": float(development_activity_signal_score),
        "growth_note_count": int(growth_note_count),
        "development_note_count": int(development_note_count),
        "unique_growth_sources": int(unique_growth_sources),
        "unique_development_sources": int(unique_development_sources),
        "local_source_signal_confidence": confidence,
    }


# ============================================================
# Growth pressure model
# ============================================================

def build_growth_pressure_scores(
    fred_df: pd.DataFrame,
    notes_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build annual growth pressure scores.

    Historical scores are based on official economic data.
    Local qualitative source signals are applied only to the latest available year.
    """

    df = fred_df.set_index("date").sort_index()

    annual = df.resample("YE").last().reset_index()
    annual["year"] = annual["date"].dt.year

    if "sumner_real_gdp" in annual.columns:
        annual["sumner_real_gdp_yoy_pct"] = annual["sumner_real_gdp"].pct_change() * 100
        annual["real_gdp_growth_score"] = minmax_score(
            annual["sumner_real_gdp_yoy_pct"]
        )
    else:
        print("WARNING: sumner_real_gdp not found. GDP growth score will be blank.")
        annual["sumner_real_gdp"] = np.nan
        annual["sumner_real_gdp_yoy_pct"] = np.nan
        annual["real_gdp_growth_score"] = np.nan

    if "sumner_unemployment_rate" in annual.columns:
        annual["labor_market_tightness_score"] = minmax_score(
            annual["sumner_unemployment_rate"],
            invert=True,
        )
    else:
        print(
            "WARNING: sumner_unemployment_rate not found. "
            "Labor market tightness score will be blank."
        )
        annual["sumner_unemployment_rate"] = np.nan
        annual["labor_market_tightness_score"] = np.nan

    local_signal = calculate_local_source_signal(notes_df)

    annual["local_growth_signal_score"] = 0.0
    annual["development_activity_signal_score"] = 0.0
    annual["growth_note_count"] = 0
    annual["development_note_count"] = 0
    annual["unique_growth_sources"] = 0
    annual["unique_development_sources"] = 0
    annual["local_source_signal_confidence"] = "Historical score only"

    valid_rows = annual.dropna(
        subset=["real_gdp_growth_score", "labor_market_tightness_score"],
        how="all",
    )

    if not valid_rows.empty:
        latest_idx = valid_rows.index.max()

        annual.loc[latest_idx, "local_growth_signal_score"] = local_signal[
            "local_growth_signal_score"
        ]
        annual.loc[latest_idx, "development_activity_signal_score"] = local_signal[
            "development_activity_signal_score"
        ]
        annual.loc[latest_idx, "growth_note_count"] = local_signal["growth_note_count"]
        annual.loc[latest_idx, "development_note_count"] = local_signal[
            "development_note_count"
        ]
        annual.loc[latest_idx, "unique_growth_sources"] = local_signal[
            "unique_growth_sources"
        ]
        annual.loc[latest_idx, "unique_development_sources"] = local_signal[
            "unique_development_sources"
        ]
        annual.loc[latest_idx, "local_source_signal_confidence"] = local_signal[
            "local_source_signal_confidence"
        ]

    # Historical score excludes qualitative local signal.
    annual["historical_growth_pressure_score"] = annual.apply(
        lambda row: safe_weighted_average(row, HISTORICAL_GROWTH_PRESSURE_WEIGHTS),
        axis=1,
    )

    # Current/latest score includes qualitative local source signal.
    annual["growth_pressure_score"] = annual.apply(
        lambda row: safe_weighted_average(row, GROWTH_PRESSURE_WEIGHTS),
        axis=1,
    )

    # For non-latest years, use historical score so local-source notes do not inflate history.
    if not valid_rows.empty:
        latest_idx = valid_rows.index.max()
        non_latest_mask = annual.index != latest_idx
        annual.loc[non_latest_mask, "growth_pressure_score"] = annual.loc[
            non_latest_mask,
            "historical_growth_pressure_score",
        ]

    annual["growth_pressure_signal"] = annual["growth_pressure_score"].apply(
        lambda x: classify_risk(float(x)) if pd.notna(x) else "Insufficient Data"
    )

    annual["data_quality_flag"] = annual.apply(classify_growth_pressure_data_quality, axis=1)

    output_columns = [
        "date",
        "year",
        "sumner_real_gdp",
        "sumner_real_gdp_yoy_pct",
        "sumner_unemployment_rate",
        "real_gdp_growth_score",
        "labor_market_tightness_score",
        "historical_growth_pressure_score",
        "local_growth_signal_score",
        "development_activity_signal_score",
        "growth_pressure_score",
        "growth_pressure_signal",
        "growth_note_count",
        "development_note_count",
        "unique_growth_sources",
        "unique_development_sources",
        "local_source_signal_confidence",
        "data_quality_flag",
    ]

    output_columns = [col for col in output_columns if col in annual.columns]

    result = annual[output_columns].copy()

    return result


def classify_growth_pressure_data_quality(row: pd.Series) -> str:
    """
    Classify data quality for each annual growth pressure score.
    """

    has_gdp = pd.notna(row.get("real_gdp_growth_score", np.nan))
    has_labor = pd.notna(row.get("labor_market_tightness_score", np.nan))
    has_local_signal = row.get("growth_note_count", 0) > 0

    if has_gdp and has_labor and has_local_signal:
        return "Economic Data + Current Local Source Signal"
    if has_gdp and has_labor:
        return "Economic Data Only"
    if has_gdp or has_labor:
        return "Partial Economic Data"
    return "Insufficient Data"


def build_growth_pressure_model() -> pd.DataFrame:
    """
    Run the full growth pressure scoring module.
    """

    fred_df = load_fred_wide()
    notes_df = load_local_source_notes()

    summarize_local_growth_sources(notes_df)

    result = build_growth_pressure_scores(fred_df, notes_df)

    result.to_csv(GROWTH_PRESSURE_OUTPUT, index=False)

    latest = (
        result.dropna(subset=["growth_pressure_score"])
        .sort_values("date")
        .tail(1)
        .copy()
    )

    latest.to_csv(GROWTH_PRESSURE_LATEST_OUTPUT, index=False)

    print(f"Saved growth pressure scores to: {GROWTH_PRESSURE_OUTPUT}")
    print(f"Saved latest growth pressure score to: {GROWTH_PRESSURE_LATEST_OUTPUT}")

    if not latest.empty:
        latest_row = latest.iloc[0]
        print()
        print("Latest Growth Pressure Score")
        print("----------------------------")
        print(f"Year: {int(latest_row['year'])}")
        print(f"Score: {latest_row['growth_pressure_score']:.2f}")
        print(f"Signal: {latest_row['growth_pressure_signal']}")
        print(f"Data quality: {latest_row['data_quality_flag']}")
        print(
            "Local source confidence: "
            f"{latest_row['local_source_signal_confidence']}"
        )

        if "sumner_real_gdp_yoy_pct" in latest_row.index:
            print(f"Sumner real GDP YoY: {latest_row['sumner_real_gdp_yoy_pct']:.2f}%")

        if "sumner_unemployment_rate" in latest_row.index:
            print(f"Sumner unemployment rate: {latest_row['sumner_unemployment_rate']:.2f}%")

    return result


def summarize_growth_pressure(result: pd.DataFrame) -> pd.DataFrame:
    """
    Create a compact latest component summary table.
    """

    latest = (
        result.dropna(subset=["growth_pressure_score"])
        .sort_values("date")
        .tail(1)
    )

    if latest.empty:
        raise ValueError("No latest growth pressure score available.")

    latest_row = latest.iloc[0]

    rows = []

    for component, weight in GROWTH_PRESSURE_WEIGHTS.items():
        if component in latest_row.index:
            rows.append(
                {
                    "component": component,
                    "weight": weight,
                    "component_score": latest_row[component],
                }
            )

    summary = pd.DataFrame(rows)
    summary["weighted_contribution"] = summary["weight"] * summary["component_score"]

    summary["data_quality_flag"] = latest_row.get("data_quality_flag", "N/A")
    summary["local_source_signal_confidence"] = latest_row.get(
        "local_source_signal_confidence",
        "N/A",
    )

    summary.to_csv(GROWTH_PRESSURE_COMPONENT_SUMMARY_OUTPUT, index=False)

    print(f"Saved growth pressure component summary to: {GROWTH_PRESSURE_COMPONENT_SUMMARY_OUTPUT}")

    return summary


def main() -> None:
    """
    Run growth pressure scoring as a script.
    """

    result = build_growth_pressure_model()
    summary = summarize_growth_pressure(result)

    print()
    print("Latest growth pressure component scores:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()