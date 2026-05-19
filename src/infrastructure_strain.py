"""
Infrastructure strain module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module estimates infrastructure strain using Census ACS commute indicators
and curated local source notes.

Purpose:
- Replace the infrastructure_strain placeholder in the composite model.
- Measure infrastructure pressure from commute time, long-commute share,
  vehicle dependence, local infrastructure note volume, and public works /
  road project pressure signals.
- Create a repeatable county/city-level infrastructure strain signal for
  Sumner County and Gallatin.

Inputs:
- Census ACS 5-Year API
- data/raw/local_source_notes.csv
- .env file containing CENSUS_API_KEY

Outputs:
- data/processed/infrastructure_strain_scores.csv
- data/processed/infrastructure_strain_latest.csv
- data/processed/infrastructure_strain_component_summary.csv
- data/processed/infrastructure_strain_source_summary.csv
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
    LOCAL_SOURCE_NOTES_FILE,
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

INFRASTRUCTURE_STRAIN_OUTPUT = (
    PROCESSED_DATA_DIR / "infrastructure_strain_scores.csv"
)
INFRASTRUCTURE_STRAIN_LATEST_OUTPUT = (
    PROCESSED_DATA_DIR / "infrastructure_strain_latest.csv"
)
INFRASTRUCTURE_STRAIN_COMPONENT_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "infrastructure_strain_component_summary.csv"
)
INFRASTRUCTURE_STRAIN_SOURCE_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "infrastructure_strain_source_summary.csv"
)


# ============================================================
# Census ACS settings
# ============================================================

ACS_BASE_URL = "https://api.census.gov/data"

ACS_YEARS_TO_TRY = [2024, 2023, 2022, 2021, 2020]

ACS_DATASET = "acs/acs5"
ACS_PROFILE_DATASET = "acs/acs5/profile"

# Detailed-table variables.
# B08303: Travel time to work.
# B08301: Means of transportation to work.
ACS_VARIABLES = {
    "workers_travel_time_total": "B08303_001E",
    "workers_less_5_min": "B08303_002E",
    "workers_5_9_min": "B08303_003E",
    "workers_10_14_min": "B08303_004E",
    "workers_15_19_min": "B08303_005E",
    "workers_20_24_min": "B08303_006E",
    "workers_25_29_min": "B08303_007E",
    "workers_30_34_min": "B08303_008E",
    "workers_35_44_min": "B08303_009E",
    "workers_45_59_min": "B08303_010E",
    "workers_60_89_min": "B08303_011E",
    "workers_90_plus_min": "B08303_012E",
    "means_transport_total": "B08301_001E",
    "drive_alone_workers": "B08301_003E",
    "carpool_workers": "B08301_004E",
    "public_transport_workers": "B08301_010E",
    "walked_workers": "B08301_019E",
    "worked_from_home_workers": "B08301_021E",
}

# Profile fallback variables.
ACS_PROFILE_VARIABLES = {
    "mean_travel_time_minutes": "DP03_0025E",
    "drive_alone_share_pct": "DP03_0019PE",
    "carpool_share_pct": "DP03_0020PE",
    "public_transport_share_pct": "DP03_0021PE",
    "walked_share_pct": "DP03_0023PE",
    "worked_from_home_share_pct": "DP03_0024PE",
}


# ============================================================
# Scoring weights
# ============================================================

INFRASTRUCTURE_STRAIN_WEIGHTS = {
    "mean_commute_time_pressure_score": 0.30,
    "long_commute_share_score": 0.20,
    "vehicle_dependence_score": 0.20,
    "local_infrastructure_note_signal_score": 0.15,
    "public_works_road_pressure_score": 0.15,
}


LOCAL_INFRASTRUCTURE_KEYWORDS = [
    "infrastructure",
    "road",
    "roads",
    "traffic",
    "transportation",
    "commute",
    "highway",
    "intersection",
    "stormwater",
    "flood",
    "flooding",
    "utility",
    "utilities",
    "water",
    "sewer",
    "public works",
    "engineering",
    "capital project",
    "capacity",
    "development",
    "construction",
]

PUBLIC_WORKS_ROAD_KEYWORDS = [
    "public works",
    "road",
    "roads",
    "street",
    "streets",
    "traffic",
    "intersection",
    "highway",
    "engineering",
    "capital project",
    "construction",
    "stormwater",
    "flood mitigation",
    "utility",
    "utilities",
]


TRAVEL_TIME_MIDPOINTS = {
    "workers_less_5_min": 2.5,
    "workers_5_9_min": 7.0,
    "workers_10_14_min": 12.0,
    "workers_15_19_min": 17.0,
    "workers_20_24_min": 22.0,
    "workers_25_29_min": 27.0,
    "workers_30_34_min": 32.0,
    "workers_35_44_min": 39.5,
    "workers_45_59_min": 52.0,
    "workers_60_89_min": 74.5,
    "workers_90_plus_min": 95.0,
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


def safe_classify_risk(score: float) -> str:
    """
    Classify risk safely.

    Prevents missing values from being labeled as High Risk.
    """

    if score is None or pd.isna(score):
        return "Missing Data"

    return classify_risk(float(score))


def score_mean_commute_time(minutes: float) -> float:
    """
    Score mean commute time.

    General interpretation:
    - Below 20 minutes: lower pressure
    - Around 25-30 minutes: moderate/elevated pressure
    - Above 35 minutes: high pressure
    """

    if pd.isna(minutes):
        return np.nan

    return clamp_score((minutes - 15.0) / 25.0 * 100)


def score_long_commute_share(share: float) -> float:
    """
    Score share of workers commuting 45 minutes or longer.
    """

    if pd.isna(share):
        return np.nan

    return clamp_score((share - 0.05) / 0.30 * 100)


def score_vehicle_dependence(share: float) -> float:
    """
    Score drive-alone / vehicle-dependence pressure.
    """

    if pd.isna(share):
        return np.nan

    return clamp_score((share - 0.60) / 0.35 * 100)


def score_note_signal(note_count: float, unique_sources: float) -> float:
    """
    Score local qualitative infrastructure note pressure.
    """

    if pd.isna(note_count):
        return np.nan

    score = note_count * 5.0 + unique_sources * 8.0

    return clamp_score(score, upper=85.0)


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


def estimate_mean_travel_time_from_bins(row: pd.Series) -> float:
    """
    Estimate mean travel time using ACS B08303 travel-time bins.

    The detailed ACS table provides counts by travel-time interval but not a
    direct mean. This function approximates mean commute time using interval
    midpoints.
    """

    total_workers = safe_float(row.get("workers_travel_time_total"))

    if pd.isna(total_workers) or total_workers <= 0:
        return np.nan

    weighted_minutes = 0.0
    counted_workers = 0.0

    for column, midpoint in TRAVEL_TIME_MIDPOINTS.items():
        workers = safe_float(row.get(column), default=0.0)

        if pd.isna(workers) or workers < 0:
            workers = 0.0

        weighted_minutes += workers * midpoint
        counted_workers += workers

    if counted_workers <= 0:
        return np.nan

    return weighted_minutes / counted_workers


def classify_data_quality(row: pd.Series) -> str:
    """
    Classify infrastructure strain data quality.
    """

    if row.get("acs_dataset") == ACS_DATASET:
        if pd.notna(row.get("mean_travel_time_minutes")):
            return "Strong ACS Commute Coverage"

        return "Strong ACS Commute Coverage - Estimated Mean Commute"

    if row.get("acs_dataset") == ACS_PROFILE_DATASET:
        return "ACS Profile Commute Coverage"

    return "Partial Infrastructure Data"


def warn_if_missing_api_key() -> None:
    """
    Warn if the Census API key was not found.
    """

    if not CENSUS_API_KEY:
        print(
            "WARNING: CENSUS_API_KEY was not found. "
            "Create a .env file in the project root with: "
            "CENSUS_API_KEY=your_key_here"
        )


def standardize_acs_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert ACS numeric columns to floats.
    """

    numeric_cols = list(ACS_VARIABLES.keys()) + list(ACS_PROFILE_VARIABLES.keys())

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(safe_float)

    return df


def build_text_blob(row: pd.Series) -> str:
    """
    Combine local source note fields into one searchable text blob.
    """

    fields = [
        "source_name",
        "source_type",
        "jurisdiction",
        "topic",
        "key_point",
        "risk_channel",
        "url_or_file",
    ]

    values = []

    for field in fields:
        if field in row.index and pd.notna(row.get(field)):
            values.append(str(row.get(field)).lower())

    return " ".join(values)


def keyword_count(text: str, keywords: list[str]) -> int:
    """
    Count keyword hits in a text blob.
    """

    text = str(text).lower()

    return sum(1 for keyword in keywords if keyword.lower() in text)


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


def load_cached_infrastructure_data() -> pd.DataFrame:
    """
    Load previously saved infrastructure strain data if the Census API is unavailable.

    This prevents the full project pipeline from failing during temporary Census
    API maintenance or 503 busy responses.
    """

    if INFRASTRUCTURE_STRAIN_OUTPUT.exists():
        print(
            "WARNING: Census API unavailable. "
            f"Using cached infrastructure data from: {INFRASTRUCTURE_STRAIN_OUTPUT}"
        )
        return pd.read_csv(INFRASTRUCTURE_STRAIN_OUTPUT)

    if INFRASTRUCTURE_STRAIN_LATEST_OUTPUT.exists():
        print(
            "WARNING: Census API unavailable. "
            f"Using cached latest infrastructure data from: {INFRASTRUCTURE_STRAIN_LATEST_OUTPUT}"
        )
        return pd.read_csv(INFRASTRUCTURE_STRAIN_LATEST_OUTPUT)

    return pd.DataFrame()


def fetch_acs_for_geography(
    year: int,
    geography: GeographyRequest,
    dataset: str = ACS_DATASET,
    variable_map: dict[str, str] | None = None,
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    Fetch ACS variables for one geography and one ACS year.

    Includes retry logic for temporary Census API 503 busy / maintenance responses.
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

    last_error_text = ""

    for attempt in range(1, max_retries + 1):
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
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
                    f"Census ACS returned no rows for {year} "
                    f"{geography.geography_name} using {dataset}"
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

        last_error_text = response.text[:300]

        if response.status_code in {429, 500, 502, 503, 504}:
            wait_seconds = attempt * 2
            print(
                f"WARNING: Census ACS request returned {response.status_code}. "
                f"Retrying in {wait_seconds} seconds "
                f"({attempt}/{max_retries})..."
            )
            time.sleep(wait_seconds)
            continue

        raise RuntimeError(
            f"Census ACS request failed for {year} {geography.geography_name} "
            f"using {dataset}: {response.status_code} {response.text[:300]}"
        )

    raise RuntimeError(
        f"Census ACS request failed after {max_retries} retries for {year} "
        f"{geography.geography_name} using {dataset}. "
        f"Last response: {last_error_text}"
    )


def collect_acs_infrastructure_data() -> pd.DataFrame:
    """
    Collect ACS commute and transportation data for Sumner County and Gallatin.
    """

    warn_if_missing_api_key()

    all_rows = []

    for year in ACS_YEARS_TO_TRY:
        for geography in census_geographies():
            detailed_success = False

            try:
                print(
                    f"Fetching ACS {year} detailed commute data for "
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
                    f"Fetching ACS {year} profile commute data for "
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
        cached_df = load_cached_infrastructure_data()

        if not cached_df.empty:
            return cached_df

        raise RuntimeError(
            "No ACS infrastructure strain data could be collected and no cached "
            "infrastructure strain file was available. The Census API appears to be "
            "temporarily unavailable. Try again later, or confirm that CENSUS_API_KEY "
            "is set correctly in your .env file."
        )

    return pd.concat(all_rows, ignore_index=True)


# ============================================================
# Local source-note signals
# ============================================================

def load_local_source_notes() -> pd.DataFrame:
    """
    Load curated local source notes.
    """

    if not LOCAL_SOURCE_NOTES_FILE.exists():
        print(f"WARNING: Missing local source notes file: {LOCAL_SOURCE_NOTES_FILE}")
        return pd.DataFrame()

    notes_df = pd.read_csv(LOCAL_SOURCE_NOTES_FILE)

    if notes_df.empty:
        return notes_df

    notes_df["text_blob"] = notes_df.apply(build_text_blob, axis=1)

    return notes_df


def calculate_local_infrastructure_signals() -> dict[str, object]:
    """
    Calculate local qualitative infrastructure pressure signals from notes.
    """

    notes_df = load_local_source_notes()

    if notes_df.empty:
        return {
            "local_infrastructure_note_count": 0,
            "local_infrastructure_unique_sources": 0,
            "public_works_road_note_count": 0,
            "public_works_road_unique_sources": 0,
            "local_infrastructure_note_signal_score": 0.0,
            "public_works_road_pressure_score": 0.0,
            "source_signal_confidence": "No Local Notes",
        }

    notes_df["infrastructure_keyword_hits"] = notes_df["text_blob"].apply(
        lambda text: keyword_count(text, LOCAL_INFRASTRUCTURE_KEYWORDS)
    )
    notes_df["public_works_road_keyword_hits"] = notes_df["text_blob"].apply(
        lambda text: keyword_count(text, PUBLIC_WORKS_ROAD_KEYWORDS)
    )

    infra_notes = notes_df[notes_df["infrastructure_keyword_hits"] > 0].copy()
    public_works_notes = notes_df[
        notes_df["public_works_road_keyword_hits"] > 0
    ].copy()

    source_col = "source_name" if "source_name" in notes_df.columns else None

    local_infra_note_count = len(infra_notes)
    public_works_note_count = len(public_works_notes)

    local_infra_unique_sources = (
        infra_notes[source_col].nunique() if source_col and not infra_notes.empty else 0
    )
    public_works_unique_sources = (
        public_works_notes[source_col].nunique()
        if source_col and not public_works_notes.empty
        else 0
    )

    local_infrastructure_note_signal_score = score_note_signal(
        note_count=local_infra_note_count,
        unique_sources=local_infra_unique_sources,
    )

    public_works_road_pressure_score = score_note_signal(
        note_count=public_works_note_count,
        unique_sources=public_works_unique_sources,
    )

    total_relevant_notes = local_infra_note_count + public_works_note_count
    total_unique_sources = max(local_infra_unique_sources, public_works_unique_sources)

    if total_relevant_notes >= 10 and total_unique_sources >= 4:
        confidence = "Strong Local Signal"
    elif total_relevant_notes >= 5 and total_unique_sources >= 2:
        confidence = "Moderate Local Signal"
    elif total_relevant_notes > 0:
        confidence = "Limited Local Signal"
    else:
        confidence = "No Local Signal"

    source_summary = pd.DataFrame(
        [
            {
                "local_infrastructure_note_count": local_infra_note_count,
                "local_infrastructure_unique_sources": local_infra_unique_sources,
                "public_works_road_note_count": public_works_note_count,
                "public_works_road_unique_sources": public_works_unique_sources,
                "local_infrastructure_note_signal_score": local_infrastructure_note_signal_score,
                "public_works_road_pressure_score": public_works_road_pressure_score,
                "source_signal_confidence": confidence,
            }
        ]
    )

    source_summary.to_csv(INFRASTRUCTURE_STRAIN_SOURCE_SUMMARY_OUTPUT, index=False)

    return source_summary.iloc[0].to_dict()


# ============================================================
# Model
# ============================================================

def build_infrastructure_strain_model() -> pd.DataFrame:
    """
    Build infrastructure strain scores.
    """

    acs_df = collect_acs_infrastructure_data()
    local_signals = calculate_local_infrastructure_signals()

    rows = []

    for _, row in acs_df.iterrows():
        workers_travel_time_total = safe_float(row.get("workers_travel_time_total"))
        workers_45_59 = safe_float(row.get("workers_45_59_min"), default=0.0)
        workers_60_89 = safe_float(row.get("workers_60_89_min"), default=0.0)
        workers_90_plus = safe_float(row.get("workers_90_plus_min"), default=0.0)

        long_commute_workers = workers_45_59 + workers_60_89 + workers_90_plus

        long_commute_share = (
            long_commute_workers / workers_travel_time_total
            if workers_travel_time_total and workers_travel_time_total > 0
            else np.nan
        )

        means_transport_total = safe_float(row.get("means_transport_total"))
        drive_alone_workers = safe_float(row.get("drive_alone_workers"))
        carpool_workers = safe_float(row.get("carpool_workers"))
        public_transport_workers = safe_float(row.get("public_transport_workers"))
        walked_workers = safe_float(row.get("walked_workers"))
        worked_from_home_workers = safe_float(row.get("worked_from_home_workers"))

        drive_alone_share = (
            drive_alone_workers / means_transport_total
            if means_transport_total
            and means_transport_total > 0
            and not pd.isna(drive_alone_workers)
            else np.nan
        )

        carpool_share = (
            carpool_workers / means_transport_total
            if means_transport_total
            and means_transport_total > 0
            and not pd.isna(carpool_workers)
            else np.nan
        )

        public_transport_share = (
            public_transport_workers / means_transport_total
            if means_transport_total
            and means_transport_total > 0
            and not pd.isna(public_transport_workers)
            else np.nan
        )

        walked_share = (
            walked_workers / means_transport_total
            if means_transport_total
            and means_transport_total > 0
            and not pd.isna(walked_workers)
            else np.nan
        )

        worked_from_home_share = (
            worked_from_home_workers / means_transport_total
            if means_transport_total
            and means_transport_total > 0
            and not pd.isna(worked_from_home_workers)
            else np.nan
        )

        mean_travel_time_minutes = safe_float(row.get("mean_travel_time_minutes"))

        if pd.isna(mean_travel_time_minutes):
            mean_travel_time_minutes = estimate_mean_travel_time_from_bins(row)

        if pd.isna(drive_alone_share) and not pd.isna(row.get("drive_alone_share_pct")):
            drive_alone_share = safe_float(row.get("drive_alone_share_pct")) / 100

        if pd.isna(carpool_share) and not pd.isna(row.get("carpool_share_pct")):
            carpool_share = safe_float(row.get("carpool_share_pct")) / 100

        if pd.isna(public_transport_share) and not pd.isna(
            row.get("public_transport_share_pct")
        ):
            public_transport_share = (
                safe_float(row.get("public_transport_share_pct")) / 100
            )

        if pd.isna(walked_share) and not pd.isna(row.get("walked_share_pct")):
            walked_share = safe_float(row.get("walked_share_pct")) / 100

        if pd.isna(worked_from_home_share) and not pd.isna(
            row.get("worked_from_home_share_pct")
        ):
            worked_from_home_share = (
                safe_float(row.get("worked_from_home_share_pct")) / 100
            )

        component_scores = {
            "mean_commute_time_pressure_score": score_mean_commute_time(
                mean_travel_time_minutes
            ),
            "long_commute_share_score": score_long_commute_share(long_commute_share),
            "vehicle_dependence_score": score_vehicle_dependence(drive_alone_share),
            "local_infrastructure_note_signal_score": safe_float(
                local_signals.get("local_infrastructure_note_signal_score")
            ),
            "public_works_road_pressure_score": safe_float(
                local_signals.get("public_works_road_pressure_score")
            ),
        }

        infrastructure_score = weighted_average(
            component_scores,
            INFRASTRUCTURE_STRAIN_WEIGHTS,
        )

        acs_year = safe_float(row.get("acs_year"))

        output_row = {
            "acs_year": int(acs_year) if not pd.isna(acs_year) else np.nan,
            "date": f"{int(acs_year)}-12-31" if not pd.isna(acs_year) else "N/A",
            "geography_level": row.get("geography_level"),
            "geography_name": row.get("geography_name"),
            "acs_dataset": row.get("acs_dataset", "N/A"),
            "mean_travel_time_minutes": mean_travel_time_minutes,
            "long_commute_share": long_commute_share,
            "drive_alone_share": drive_alone_share,
            "carpool_share": carpool_share,
            "public_transport_share": public_transport_share,
            "walked_share": walked_share,
            "worked_from_home_share": worked_from_home_share,
            "local_infrastructure_note_count": local_signals.get(
                "local_infrastructure_note_count"
            ),
            "local_infrastructure_unique_sources": local_signals.get(
                "local_infrastructure_unique_sources"
            ),
            "public_works_road_note_count": local_signals.get(
                "public_works_road_note_count"
            ),
            "public_works_road_unique_sources": local_signals.get(
                "public_works_road_unique_sources"
            ),
            "source_signal_confidence": local_signals.get(
                "source_signal_confidence"
            ),
            "infrastructure_strain_score": infrastructure_score,
            "infrastructure_strain_signal": safe_classify_risk(infrastructure_score),
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

    result.to_csv(INFRASTRUCTURE_STRAIN_OUTPUT, index=False)

    latest = (
        result.sort_values("acs_year")
        .groupby(["geography_level", "geography_name"], as_index=False)
        .tail(1)
        .sort_values(["geography_level", "geography_name"])
    )

    county_latest = latest[latest["geography_level"] == "county"].copy()

    if county_latest.empty:
        county_latest = latest.head(1).copy()

    county_latest.to_csv(INFRASTRUCTURE_STRAIN_LATEST_OUTPUT, index=False)

    component_summary = build_component_summary(county_latest.iloc[0])
    component_summary.to_csv(
        INFRASTRUCTURE_STRAIN_COMPONENT_SUMMARY_OUTPUT,
        index=False,
    )

    print(f"Saved infrastructure strain scores to: {INFRASTRUCTURE_STRAIN_OUTPUT}")
    print(f"Saved latest infrastructure strain score to: {INFRASTRUCTURE_STRAIN_LATEST_OUTPUT}")
    print(f"Saved infrastructure strain component summary to: {INFRASTRUCTURE_STRAIN_COMPONENT_SUMMARY_OUTPUT}")

    return result


def build_component_summary(latest_row: pd.Series) -> pd.DataFrame:
    """
    Build component summary for latest county infrastructure strain score.
    """

    rows = []

    component_labels = {
        "mean_commute_time_pressure_score": "Mean Commute Time Pressure",
        "long_commute_share_score": "Long Commute Share",
        "vehicle_dependence_score": "Vehicle Dependence",
        "local_infrastructure_note_signal_score": "Local Infrastructure Note Signal",
        "public_works_road_pressure_score": "Public Works / Road Pressure",
    }

    for component, weight in INFRASTRUCTURE_STRAIN_WEIGHTS.items():
        score = safe_float(latest_row.get(component))

        rows.append(
            {
                "component": component,
                "component_label": component_labels.get(component, component),
                "weight": weight,
                "score": score,
                "signal": safe_classify_risk(score),
                "weighted_contribution": score * weight if not pd.isna(score) else np.nan,
            }
        )

    return pd.DataFrame(rows)


def summarize_infrastructure_strain(result: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Print latest infrastructure strain result.
    """

    if result is None:
        if not INFRASTRUCTURE_STRAIN_LATEST_OUTPUT.exists():
            raise FileNotFoundError(
                "No infrastructure strain latest file found. "
                "Run build_infrastructure_strain_model() first."
            )

        latest = pd.read_csv(INFRASTRUCTURE_STRAIN_LATEST_OUTPUT)
    else:
        latest = (
            result.sort_values("acs_year")
            .groupby(["geography_level", "geography_name"], as_index=False)
            .tail(1)
            .sort_values(["geography_level", "geography_name"])
        )

    print()
    print("Infrastructure Strain Summary")
    print("-----------------------------")

    display_cols = [
        "geography_name",
        "acs_year",
        "acs_dataset",
        "mean_travel_time_minutes",
        "long_commute_share",
        "drive_alone_share",
        "local_infrastructure_note_count",
        "public_works_road_note_count",
        "infrastructure_strain_score",
        "infrastructure_strain_signal",
        "data_quality_flag",
    ]

    display_cols = [col for col in display_cols if col in latest.columns]

    print(latest[display_cols].to_string(index=False))

    return latest


def main() -> None:
    """
    Run infrastructure strain module as a script.
    """

    result = build_infrastructure_strain_model()
    summarize_infrastructure_strain(result)


if __name__ == "__main__":
    main()