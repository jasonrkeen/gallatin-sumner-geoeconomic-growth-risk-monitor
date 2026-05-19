"""
Housing affordability pressure module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module estimates local housing affordability pressure using Census ACS data and
the existing mortgage-rate series collected through the FRED pipeline.

Purpose:
- Replace the housing_affordability_pressure placeholder in the composite model.
- Measure affordability pressure from income, rent, home value, cost burden, and mortgage-rate conditions.
- Create a repeatable county/city-level housing stress signal for Sumner County and Gallatin.

Inputs:
- Census ACS 5-Year API
- data/processed/fred_series_wide.csv
- .env file containing CENSUS_API_KEY

Outputs:
- data/processed/housing_affordability_scores.csv
- data/processed/housing_affordability_latest.csv
- data/processed/housing_affordability_component_summary.csv
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

from src.config import (
    GALLATIN_PLACE_FIPS,
    PROCESSED_DATA_DIR,
    SUMNER_COUNTY_FIPS,
    TENNESSEE_FIPS,
    classify_risk,
)


# ============================================================
# Environment
# ============================================================

load_dotenv()

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")


# ============================================================
# Input / output files
# ============================================================

FRED_WIDE_FILE = PROCESSED_DATA_DIR / "fred_series_wide.csv"

HOUSING_AFFORDABILITY_OUTPUT = (
    PROCESSED_DATA_DIR / "housing_affordability_scores.csv"
)
HOUSING_AFFORDABILITY_LATEST_OUTPUT = (
    PROCESSED_DATA_DIR / "housing_affordability_latest.csv"
)
HOUSING_AFFORDABILITY_COMPONENT_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "housing_affordability_component_summary.csv"
)


# ============================================================
# Census ACS settings
# ============================================================

ACS_BASE_URL = "https://api.census.gov/data"

# Try most likely recent ACS 5-year releases first.
ACS_YEARS_TO_TRY = [2024, 2023, 2022, 2021, 2020]

ACS_DATASET = "acs/acs5"
ACS_PROFILE_DATASET = "acs/acs5/profile"

# Detailed-table variables. These provide direct counts for cost-burden calculations.
ACS_VARIABLES = {
    "median_household_income": "B19013_001E",
    "median_home_value": "B25077_001E",
    "median_gross_rent": "B25064_001E",
    "rent_burden_total": "B25070_001E",
    "rent_burden_30_34": "B25070_007E",
    "rent_burden_35_39": "B25070_008E",
    "rent_burden_40_49": "B25070_009E",
    "rent_burden_50_plus": "B25070_010E",
    "owner_cost_burden_total": "B25091_001E",
    "owner_cost_burden_30_34": "B25091_008E",
    "owner_cost_burden_35_39": "B25091_009E",
    "owner_cost_burden_40_49": "B25091_010E",
    "owner_cost_burden_50_plus": "B25091_011E",
}

# Profile fallback variables. These are broader but usually more stable.
# DP04_0046PE: occupied rental units paying rent >= 30% of household income.
# DP04_0101PE: owner costs as % of income, selected monthly owner costs >= 30%.
ACS_PROFILE_VARIABLES = {
    "median_household_income": "DP03_0062E",
    "median_home_value": "DP04_0089E",
    "median_gross_rent": "DP04_0134E",
    "renter_cost_burden_share_pct": "DP04_0046PE",
    "owner_cost_burden_share_pct": "DP04_0101PE",
}


# ============================================================
# Scoring weights
# ============================================================

HOUSING_AFFORDABILITY_WEIGHTS = {
    "home_value_to_income_score": 0.30,
    "rent_to_income_score": 0.20,
    "renter_cost_burden_score": 0.20,
    "owner_cost_burden_score": 0.15,
    "mortgage_rate_pressure_score": 0.15,
}


@dataclass
class GeographyRequest:
    geography_level: str
    geography_name: str
    for_clause: str
    in_clause: str


# ============================================================
# Helpers
# ============================================================

def safe_float(value, default=np.nan) -> float:
    """
    Safely convert a value to float.
    """

    try:
        if value is None or pd.isna(value):
            return default

        value = str(value).strip()

        if value in {
            "",
            "null",
            "None",
            "N",
            "-",
            "-666666666",
            "-999999999",
            "-888888888",
            "-222222222",
        }:
            return default

        return float(value)
    except Exception:
        return default


def clamp_score(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    """
    Clamp score to 0-100 range.
    """

    if pd.isna(value):
        return np.nan

    return max(lower, min(upper, float(value)))


def score_home_value_to_income(ratio: float) -> float:
    """
    Score home-value-to-income ratio.

    General interpretation:
    - Below 3.0x income: lower pressure
    - 3.0x to 4.0x: moderate pressure
    - 4.0x to 5.0x: elevated pressure
    - Above 5.0x: high pressure
    """

    if pd.isna(ratio):
        return np.nan

    return clamp_score((ratio - 2.0) / 4.0 * 100)


def score_rent_to_income(ratio: float) -> float:
    """
    Score rent-to-income ratio.

    Ratio is annual gross rent divided by median household income.
    """

    if pd.isna(ratio):
        return np.nan

    return clamp_score((ratio - 0.15) / 0.25 * 100)


def score_cost_burden_share(share: float) -> float:
    """
    Score share of households paying 30% or more of income toward housing costs.
    """

    if pd.isna(share):
        return np.nan

    return clamp_score((share - 0.15) / 0.35 * 100)


def score_mortgage_rate(rate: float) -> float:
    """
    Score 30-year mortgage-rate pressure.
    """

    if pd.isna(rate):
        return np.nan

    return clamp_score((rate - 3.0) / 5.0 * 100)


def weighted_average(scores: dict[str, float], weights: dict[str, float]) -> float:
    """
    Weighted average that ignores missing score components.
    """

    weighted_values = []
    used_weights = []

    for key, weight in weights.items():
        value = scores.get(key)

        if value is None or pd.isna(value):
            continue

        weighted_values.append(float(value) * float(weight))
        used_weights.append(float(weight))

    if not used_weights:
        return np.nan

    return float(sum(weighted_values) / sum(used_weights))


def classify_data_quality(row: pd.Series) -> str:
    """
    Classify housing affordability data quality.
    """

    required = [
        "median_household_income",
        "median_home_value",
        "median_gross_rent",
    ]

    missing_required = [col for col in required if pd.isna(row.get(col))]

    if missing_required:
        return "Partial ACS Data"

    burden_cols = [
        "renter_cost_burden_share",
        "owner_cost_burden_share",
    ]

    missing_burden = [col for col in burden_cols if pd.isna(row.get(col))]

    if missing_burden:
        return "Partial Cost-Burden Data"

    if row.get("acs_dataset") == ACS_PROFILE_DATASET:
        return "ACS Profile Data"

    return "Strong ACS Coverage"


def standardize_acs_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert ACS numeric columns to floats.
    """

    numeric_cols = list(ACS_VARIABLES.keys()) + list(ACS_PROFILE_VARIABLES.keys())

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(safe_float)

    return df


def warn_if_missing_api_key() -> None:
    """
    Warn the user if the Census API key was not found.
    """

    if not CENSUS_API_KEY:
        print(
            "WARNING: CENSUS_API_KEY was not found. "
            "Create a .env file in the project root with: "
            "CENSUS_API_KEY=your_key_here"
        )


# ============================================================
# Census data collection
# ============================================================

def census_geographies() -> list[GeographyRequest]:
    """
    Return the Census geographies used by the model.
    """

    sumner_county_code = SUMNER_COUNTY_FIPS[-3:]
    gallatin_place_code = GALLATIN_PLACE_FIPS[-5:]

    return [
        GeographyRequest(
            geography_level="county",
            geography_name="Sumner County, Tennessee",
            for_clause=f"county:{sumner_county_code}",
            in_clause=f"state:{TENNESSEE_FIPS}",
        ),
        GeographyRequest(
            geography_level="place",
            geography_name="Gallatin city, Tennessee",
            for_clause=f"place:{gallatin_place_code}",
            in_clause=f"state:{TENNESSEE_FIPS}",
        ),
    ]


def fetch_acs_for_geography(
    year: int,
    geography: GeographyRequest,
    dataset: str = ACS_DATASET,
    variable_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Fetch ACS variables for one geography and one ACS year.

    The Census API sometimes returns plain text for variable, key, or geography
    errors, so this function validates the response before parsing JSON.
    """

    if variable_map is None:
        variable_map = ACS_VARIABLES

    variable_codes = ["NAME"] + list(variable_map.values())
    get_clause = ",".join(variable_codes)

    url = f"{ACS_BASE_URL}/{year}/{dataset}"

    params = {
        "get": get_clause,
        "for": geography.for_clause,
        "in": geography.in_clause,
    }

    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    response = requests.get(url, params=params, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"Census ACS request failed for {year} {geography.geography_name} "
            f"using {dataset}: {response.status_code} {response.text[:300]}"
        )

    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError(
            f"Census ACS response was not valid JSON for {year} "
            f"{geography.geography_name} using {dataset}. "
            f"Response preview: {response.text[:300]}"
        ) from exc

    if len(data) < 2:
        raise RuntimeError(
            f"Census ACS returned no rows for {year} {geography.geography_name} "
            f"using {dataset}"
        )

    header = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=header)

    reverse_vars = {code: name for name, code in variable_map.items()}
    df = df.rename(columns=reverse_vars)

    df["acs_year"] = year
    df["geography_level"] = geography.geography_level
    df["geography_name"] = geography.geography_name
    df["acs_dataset"] = dataset

    return df


def collect_acs_housing_data() -> pd.DataFrame:
    """
    Collect ACS housing data for Sumner County and Gallatin.

    First tries ACS detailed tables. If detailed-table variables fail, falls back
    to ACS profile variables.
    """

    warn_if_missing_api_key()

    all_rows = []

    for year in ACS_YEARS_TO_TRY:
        for geography in census_geographies():
            detailed_success = False

            try:
                print(
                    f"Fetching ACS {year} detailed housing data for "
                    f"{geography.geography_name}..."
                )

                geo_df = fetch_acs_for_geography(
                    year=year,
                    geography=geography,
                    dataset=ACS_DATASET,
                    variable_map=ACS_VARIABLES,
                )

                all_rows.append(standardize_acs_numeric_columns(geo_df))
                detailed_success = True
                time.sleep(0.25)

            except Exception as exc:
                print(f"WARNING: Detailed ACS failed: {exc}")

            if detailed_success:
                continue

            try:
                print(
                    f"Fetching ACS {year} profile housing data for "
                    f"{geography.geography_name}..."
                )

                profile_df = fetch_acs_for_geography(
                    year=year,
                    geography=geography,
                    dataset=ACS_PROFILE_DATASET,
                    variable_map=ACS_PROFILE_VARIABLES,
                )

                all_rows.append(standardize_acs_numeric_columns(profile_df))
                time.sleep(0.25)

            except Exception as exc:
                print(f"WARNING: Profile ACS failed: {exc}")

    if not all_rows:
        raise RuntimeError(
            "No ACS housing affordability data could be collected. "
            "Check that CENSUS_API_KEY is set correctly in your .env file."
        )

    df = pd.concat(all_rows, ignore_index=True)

    return df


# ============================================================
# Mortgage-rate input
# ============================================================

def load_latest_mortgage_rate() -> tuple[float, str]:
    """
    Load latest 30-year mortgage rate from fred_series_wide.csv.
    """

    if not FRED_WIDE_FILE.exists():
        print(f"WARNING: Missing FRED file for mortgage rate: {FRED_WIDE_FILE}")
        return np.nan, "N/A"

    fred_df = pd.read_csv(FRED_WIDE_FILE)

    if fred_df.empty or "thirty_year_mortgage_rate" not in fred_df.columns:
        print("WARNING: Mortgage-rate column not found in FRED wide file.")
        return np.nan, "N/A"

    fred_df["date"] = pd.to_datetime(fred_df["date"], errors="coerce")
    mortgage_df = fred_df.dropna(subset=["thirty_year_mortgage_rate"]).copy()

    if mortgage_df.empty:
        return np.nan, "N/A"

    latest = mortgage_df.sort_values("date").tail(1).iloc[0]

    return (
        safe_float(latest["thirty_year_mortgage_rate"]),
        latest["date"].strftime("%Y-%m-%d"),
    )


# ============================================================
# Model
# ============================================================

def build_housing_affordability_model() -> pd.DataFrame:
    """
    Build housing affordability pressure scores.
    """

    acs_df = collect_acs_housing_data()

    mortgage_rate, mortgage_rate_date = load_latest_mortgage_rate()

    rows = []

    for _, row in acs_df.iterrows():
        median_income = safe_float(row.get("median_household_income"))
        median_home_value = safe_float(row.get("median_home_value"))
        median_gross_rent = safe_float(row.get("median_gross_rent"))

        home_value_to_income = (
            median_home_value / median_income
            if median_income and median_income > 0 and not pd.isna(median_home_value)
            else np.nan
        )

        annual_rent = (
            median_gross_rent * 12
            if not pd.isna(median_gross_rent)
            else np.nan
        )

        rent_to_income = (
            annual_rent / median_income
            if median_income and median_income > 0 and not pd.isna(annual_rent)
            else np.nan
        )

        rent_burden_total = safe_float(row.get("rent_burden_total"))
        rent_burden_30_plus = sum(
            safe_float(row.get(col), default=0.0)
            for col in [
                "rent_burden_30_34",
                "rent_burden_35_39",
                "rent_burden_40_49",
                "rent_burden_50_plus",
            ]
        )

        renter_cost_burden_share = (
            rent_burden_30_plus / rent_burden_total
            if rent_burden_total and rent_burden_total > 0
            else np.nan
        )

        if pd.isna(renter_cost_burden_share) and not pd.isna(
            row.get("renter_cost_burden_share_pct")
        ):
            renter_cost_burden_share = (
                safe_float(row.get("renter_cost_burden_share_pct")) / 100
            )

        owner_burden_total = safe_float(row.get("owner_cost_burden_total"))
        owner_burden_30_plus = sum(
            safe_float(row.get(col), default=0.0)
            for col in [
                "owner_cost_burden_30_34",
                "owner_cost_burden_35_39",
                "owner_cost_burden_40_49",
                "owner_cost_burden_50_plus",
            ]
        )

        owner_cost_burden_share = (
            owner_burden_30_plus / owner_burden_total
            if owner_burden_total and owner_burden_total > 0
            else np.nan
        )

        if pd.isna(owner_cost_burden_share) and not pd.isna(
            row.get("owner_cost_burden_share_pct")
        ):
            owner_cost_burden_share = (
                safe_float(row.get("owner_cost_burden_share_pct")) / 100
            )

        component_scores = {
            "home_value_to_income_score": score_home_value_to_income(home_value_to_income),
            "rent_to_income_score": score_rent_to_income(rent_to_income),
            "renter_cost_burden_score": score_cost_burden_share(renter_cost_burden_share),
            "owner_cost_burden_score": score_cost_burden_share(owner_cost_burden_share),
            "mortgage_rate_pressure_score": score_mortgage_rate(mortgage_rate),
        }

        housing_score = weighted_average(
            component_scores,
            HOUSING_AFFORDABILITY_WEIGHTS,
        )

        acs_year = safe_float(row.get("acs_year"))

        output_row = {
            "acs_year": int(acs_year) if not pd.isna(acs_year) else np.nan,
            "date": f"{int(acs_year)}-12-31" if not pd.isna(acs_year) else "N/A",
            "geography_level": row.get("geography_level"),
            "geography_name": row.get("geography_name"),
            "acs_dataset": row.get("acs_dataset", "N/A"),
            "median_household_income": median_income,
            "median_home_value": median_home_value,
            "median_gross_rent": median_gross_rent,
            "home_value_to_income": home_value_to_income,
            "rent_to_income": rent_to_income,
            "renter_cost_burden_share": renter_cost_burden_share,
            "owner_cost_burden_share": owner_cost_burden_share,
            "mortgage_rate": mortgage_rate,
            "mortgage_rate_date": mortgage_rate_date,
            "housing_affordability_pressure_score": housing_score,
            "housing_affordability_pressure_signal": classify_risk(housing_score),
            "data_quality_flag": None,
        }

        for key, value in component_scores.items():
            output_row[key] = value

        output_row["data_quality_flag"] = classify_data_quality(pd.Series(output_row))

        rows.append(output_row)

    result = pd.DataFrame(rows)

    result = result.sort_values(
        ["geography_level", "geography_name", "acs_year"],
        ascending=[True, True, True],
    )

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    result.to_csv(HOUSING_AFFORDABILITY_OUTPUT, index=False)

    latest = (
        result.sort_values("acs_year")
        .groupby(["geography_level", "geography_name"], as_index=False)
        .tail(1)
        .sort_values(["geography_level", "geography_name"])
    )

    # Use Sumner County as the default composite-model input because county-level
    # data is more stable and aligns with the broader project geography.
    county_latest = latest[latest["geography_level"] == "county"].copy()

    if county_latest.empty:
        county_latest = latest.head(1).copy()

    county_latest.to_csv(HOUSING_AFFORDABILITY_LATEST_OUTPUT, index=False)

    component_summary = build_component_summary(county_latest.iloc[0])
    component_summary.to_csv(
        HOUSING_AFFORDABILITY_COMPONENT_SUMMARY_OUTPUT,
        index=False,
    )

    print(f"Saved housing affordability scores to: {HOUSING_AFFORDABILITY_OUTPUT}")
    print(f"Saved latest housing affordability score to: {HOUSING_AFFORDABILITY_LATEST_OUTPUT}")
    print(f"Saved housing affordability component summary to: {HOUSING_AFFORDABILITY_COMPONENT_SUMMARY_OUTPUT}")

    return result


def build_component_summary(latest_row: pd.Series) -> pd.DataFrame:
    """
    Build component summary for latest county housing affordability score.
    """

    rows = []

    component_labels = {
        "home_value_to_income_score": "Home Value to Income",
        "rent_to_income_score": "Rent to Income",
        "renter_cost_burden_score": "Renter Cost Burden",
        "owner_cost_burden_score": "Owner Cost Burden",
        "mortgage_rate_pressure_score": "Mortgage Rate Pressure",
    }

    for component, weight in HOUSING_AFFORDABILITY_WEIGHTS.items():
        score = safe_float(latest_row.get(component))

        rows.append(
            {
                "component": component,
                "component_label": component_labels.get(component, component),
                "weight": weight,
                "score": score,
                "signal": classify_risk(score),
                "weighted_contribution": score * weight if not pd.isna(score) else np.nan,
            }
        )

    summary = pd.DataFrame(rows)

    return summary


def summarize_housing_affordability(result: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Print latest housing affordability result.
    """

    if result is None:
        if not HOUSING_AFFORDABILITY_LATEST_OUTPUT.exists():
            raise FileNotFoundError(
                "No housing affordability latest file found. "
                "Run build_housing_affordability_model() first."
            )

        latest = pd.read_csv(HOUSING_AFFORDABILITY_LATEST_OUTPUT)
    else:
        latest = (
            result.sort_values("acs_year")
            .groupby(["geography_level", "geography_name"], as_index=False)
            .tail(1)
            .sort_values(["geography_level", "geography_name"])
        )

    print()
    print("Housing Affordability Pressure Summary")
    print("--------------------------------------")

    display_cols = [
        "geography_name",
        "acs_year",
        "acs_dataset",
        "median_household_income",
        "median_home_value",
        "median_gross_rent",
        "home_value_to_income",
        "rent_to_income",
        "renter_cost_burden_share",
        "owner_cost_burden_share",
        "mortgage_rate",
        "housing_affordability_pressure_score",
        "housing_affordability_pressure_signal",
        "data_quality_flag",
    ]

    display_cols = [col for col in display_cols if col in latest.columns]

    print(latest[display_cols].to_string(index=False))

    return latest


def main() -> None:
    """
    Run housing affordability module as a script.
    """

    result = build_housing_affordability_model()
    summarize_housing_affordability(result)


if __name__ == "__main__":
    main()