"""
Geoeconomic industry exposure module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module estimates local exposure to geoeconomic shocks through the industry
composition of Sumner County and Gallatin, Tennessee.

Purpose:
- Replace the geoeconomic_industry_exposure placeholder in the composite model.
- Measure exposure to manufacturing, logistics/transportation, construction,
  retail/local demand, and trade-sensitive local growth signals.
- Combine Census ACS industry employment data with curated local source notes.

Inputs:
- Census ACS 5-Year API
- data/raw/local_source_notes.csv
- .env file containing CENSUS_API_KEY

Outputs:
- data/processed/geoeconomic_industry_exposure_scores.csv
- data/processed/geoeconomic_industry_exposure_latest.csv
- data/processed/geoeconomic_industry_exposure_component_summary.csv
- data/processed/geoeconomic_industry_exposure_source_summary.csv
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

GEOECONOMIC_INDUSTRY_EXPOSURE_OUTPUT = (
    PROCESSED_DATA_DIR / "geoeconomic_industry_exposure_scores.csv"
)

GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_OUTPUT = (
    PROCESSED_DATA_DIR / "geoeconomic_industry_exposure_latest.csv"
)

GEOECONOMIC_INDUSTRY_EXPOSURE_COMPONENT_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "geoeconomic_industry_exposure_component_summary.csv"
)

GEOECONOMIC_INDUSTRY_EXPOSURE_SOURCE_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "geoeconomic_industry_exposure_source_summary.csv"
)


# ============================================================
# Census ACS settings
# ============================================================

ACS_BASE_URL = "https://api.census.gov/data"

ACS_YEARS_TO_TRY = [2024, 2023, 2022, 2021, 2020]

ACS_DATASET = "acs/acs5/profile"

# ACS profile industry employment variables.
# DP03 industry employment counts.
ACS_INDUSTRY_VARIABLES = {
    "civilian_employed_total": "DP03_0033E",
    "agriculture_mining_employment": "DP03_0034E",
    "construction_employment": "DP03_0035E",
    "manufacturing_employment": "DP03_0036E",
    "wholesale_trade_employment": "DP03_0037E",
    "retail_trade_employment": "DP03_0038E",
    "transportation_warehousing_utilities_employment": "DP03_0039E",
    "information_employment": "DP03_0040E",
    "finance_real_estate_employment": "DP03_0041E",
    "professional_scientific_management_employment": "DP03_0042E",
    "education_health_social_employment": "DP03_0043E",
    "arts_entertainment_food_employment": "DP03_0044E",
    "other_services_employment": "DP03_0045E",
    "public_administration_employment": "DP03_0046E",
}


# ============================================================
# Model weights
# ============================================================

GEOECONOMIC_INDUSTRY_EXPOSURE_WEIGHTS = {
    "manufacturing_exposure_score": 0.25,
    "logistics_transportation_exposure_score": 0.20,
    "construction_development_exposure_score": 0.20,
    "retail_local_demand_exposure_score": 0.15,
    "trade_sensitive_growth_signal_score": 0.10,
    "source_confidence_score": 0.10,
}


# ============================================================
# Keyword groups
# ============================================================

MANUFACTURING_KEYWORDS = [
    "manufacturing",
    "advanced manufacturing",
    "factory",
    "industrial",
    "supplier",
    "production",
    "plant",
    "assembly",
    "high-tech",
    "high tech",
]

LOGISTICS_KEYWORDS = [
    "logistics",
    "distribution",
    "warehouse",
    "warehousing",
    "transportation",
    "freight",
    "shipping",
    "supply chain",
    "supply-chain",
    "interstate",
    "highway",
]

CONSTRUCTION_DEVELOPMENT_KEYWORDS = [
    "construction",
    "development",
    "developments",
    "developable",
    "site",
    "sites",
    "project",
    "projects",
    "building",
    "infrastructure",
    "road investment",
    "utility",
    "utilities",
]

RETAIL_LOCAL_DEMAND_KEYWORDS = [
    "retail",
    "restaurant",
    "restaurants",
    "shopping",
    "consumer",
    "commercial",
    "downtown",
    "population growth",
    "growth",
    "housing",
]

TRADE_SENSITIVE_KEYWORDS = [
    "manufacturing",
    "distribution",
    "logistics",
    "supply chain",
    "supplier",
    "transportation",
    "investment",
    "business attraction",
    "industrial",
    "construction",
    "materials",
    "fuel",
]


SOURCE_TYPE_WEIGHTS = {
    "official city website": 1.20,
    "official county website": 1.15,
    "city newsletter": 1.10,
    "public presentation": 1.05,
    "official economic development website": 1.05,
    "economic development website": 1.05,
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
    """

    if score is None or pd.isna(score):
        return "Missing Data"

    return classify_risk(float(score))


def clean_text(value) -> str:
    """
    Clean text for keyword matching.
    """

    if value is None or pd.isna(value):
        return ""

    return str(value).strip().lower()


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

    return " ".join(clean_text(row.get(field)) for field in fields)


def keyword_count(text: str, keywords: list[str]) -> int:
    """
    Count keyword hits in a text blob.
    """

    text = clean_text(text)

    return sum(1 for keyword in keywords if keyword.lower() in text)


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


def source_weight(source_type: str) -> float:
    """
    Return source credibility / relevance weight.
    """

    source_type = clean_text(source_type)

    return SOURCE_TYPE_WEIGHTS.get(source_type, 1.0)


def score_share(
    share: float,
    low_threshold: float,
    high_threshold: float,
) -> float:
    """
    Convert an industry employment share into a 0-100 exposure score.
    """

    if pd.isna(share):
        return np.nan

    if high_threshold <= low_threshold:
        return np.nan

    return clamp_score((share - low_threshold) / (high_threshold - low_threshold) * 100)


def score_note_signal(
    note_count: int,
    unique_source_count: int,
    keyword_hits: int,
    weighted_source_strength: float,
    cap: float = 90.0,
) -> float:
    """
    Convert qualitative note volume into a 0-100 signal score.
    """

    raw_score = (
        note_count * 7.0
        + unique_source_count * 7.0
        + min(keyword_hits * 3.0, 30.0)
        + min(weighted_source_strength * 4.0, 20.0)
    )

    return clamp_score(raw_score, upper=cap)


def score_source_confidence(
    total_relevant_notes: int,
    unique_sources: int,
    source_type_count: int,
    acs_data_available: bool,
) -> float:
    """
    Score confidence in the industry exposure source base.
    """

    raw_score = (
        total_relevant_notes * 4.0
        + unique_sources * 8.0
        + source_type_count * 7.0
    )

    if acs_data_available:
        raw_score += 25.0

    return clamp_score(raw_score, upper=95.0)


def classify_source_confidence(score: float) -> str:
    """
    Convert source confidence score into a qualitative label.
    """

    if pd.isna(score) or score <= 0:
        return "No Source Signal"
    if score < 35:
        return "Limited Source Signal"
    if score < 60:
        return "Moderate Source Signal"
    if score < 80:
        return "Strong Source Signal"
    return "Very Strong Source Signal"


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

    numeric_cols = list(ACS_INDUSTRY_VARIABLES.keys())

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(safe_float)

    return df


def load_cached_industry_exposure_data() -> pd.DataFrame:
    """
    Load previously saved industry exposure data if the Census API is unavailable.
    """

    if GEOECONOMIC_INDUSTRY_EXPOSURE_OUTPUT.exists():
        print(
            "WARNING: Census API unavailable. "
            f"Using cached industry exposure data from: {GEOECONOMIC_INDUSTRY_EXPOSURE_OUTPUT}"
        )
        return pd.read_csv(GEOECONOMIC_INDUSTRY_EXPOSURE_OUTPUT)

    if GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_OUTPUT.exists():
        print(
            "WARNING: Census API unavailable. "
            f"Using cached latest industry exposure data from: {GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_OUTPUT}"
        )
        return pd.read_csv(GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_OUTPUT)

    return pd.DataFrame()


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
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    Fetch ACS industry variables for one geography and one ACS year.

    Includes retry logic for temporary Census API 503 busy / maintenance responses.
    """

    variable_codes = ["NAME"] + list(ACS_INDUSTRY_VARIABLES.values())
    get_clause = ",".join(variable_codes)

    url = f"{ACS_BASE_URL}/{year}/{ACS_DATASET}"

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
                    f"{geography.geography_name}. "
                    f"Response preview: {response.text[:300]}"
                ) from exc

            if len(data) < 2:
                raise RuntimeError(
                    f"Census ACS returned no rows for {year} "
                    f"{geography.geography_name}"
                )

            header = data[0]
            rows = data[1:]

            df = pd.DataFrame(rows, columns=header)

            reverse_vars = {
                code: name for name, code in ACS_INDUSTRY_VARIABLES.items()
            }
            df = df.rename(columns=reverse_vars)

            df["acs_year"] = year
            df["geography_level"] = geography.geography_level
            df["geography_name"] = geography.geography_name
            df["acs_dataset"] = ACS_DATASET

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
            f"Census ACS request failed for {year} {geography.geography_name}: "
            f"{response.status_code} {response.text[:300]}"
        )

    raise RuntimeError(
        f"Census ACS request failed after {max_retries} retries for {year} "
        f"{geography.geography_name}. Last response: {last_error_text}"
    )


def collect_acs_industry_data() -> pd.DataFrame:
    """
    Collect ACS industry employment data for Sumner County and Gallatin.
    """

    warn_if_missing_api_key()

    all_rows = []

    for year in ACS_YEARS_TO_TRY:
        for geography in census_geographies():
            try:
                print(
                    f"Fetching ACS {year} industry data for "
                    f"{geography.geography_name}..."
                )

                geo_df = fetch_acs_for_geography(
                    year=year,
                    geography=geography,
                )

                all_rows.append(standardize_acs_numeric_columns(geo_df))
                time.sleep(0.25)

            except Exception as exc:
                print(f"WARNING: ACS industry request failed: {exc}")

    if not all_rows:
        cached_df = load_cached_industry_exposure_data()

        if not cached_df.empty:
            return cached_df

        raise RuntimeError(
            "No ACS industry exposure data could be collected and no cached "
            "industry exposure file was available. The Census API may be temporarily "
            "unavailable. Try again later, or confirm that CENSUS_API_KEY is set "
            "correctly in your .env file."
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
    notes_df["source_type_clean"] = notes_df.get("source_type", "").apply(clean_text)
    notes_df["source_weight"] = notes_df.get("source_type", "").apply(source_weight)

    return notes_df


def build_signal_subset(
    notes_df: pd.DataFrame,
    keywords: list[str],
    signal_name: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """
    Filter notes for a given keyword group and return score inputs.
    """

    if notes_df.empty:
        return notes_df.copy(), {
            f"{signal_name}_note_count": 0,
            f"{signal_name}_unique_sources": 0,
            f"{signal_name}_keyword_hits": 0,
            f"{signal_name}_weighted_source_strength": 0.0,
            f"{signal_name}_score": 0.0,
        }

    hit_col = f"{signal_name}_keyword_hits"

    notes_df = notes_df.copy()
    notes_df[hit_col] = notes_df["text_blob"].apply(
        lambda text: keyword_count(text, keywords)
    )

    subset = notes_df[notes_df[hit_col] > 0].copy()

    source_col = "source_name" if "source_name" in subset.columns else None

    note_count = len(subset)
    unique_sources = subset[source_col].nunique() if source_col and not subset.empty else 0
    keyword_hits = int(subset[hit_col].sum()) if not subset.empty else 0
    weighted_source_strength = (
        float(subset["source_weight"].sum()) if "source_weight" in subset.columns else 0.0
    )

    score = score_note_signal(
        note_count=note_count,
        unique_source_count=unique_sources,
        keyword_hits=keyword_hits,
        weighted_source_strength=weighted_source_strength,
    )

    summary = {
        f"{signal_name}_note_count": note_count,
        f"{signal_name}_unique_sources": unique_sources,
        f"{signal_name}_keyword_hits": keyword_hits,
        f"{signal_name}_weighted_source_strength": weighted_source_strength,
        f"{signal_name}_score": score,
    }

    return subset, summary


def calculate_local_industry_signals(
    acs_data_available: bool,
) -> dict[str, object]:
    """
    Calculate qualitative industry exposure signals from curated notes.
    """

    notes_df = load_local_source_notes()

    manufacturing_subset, manufacturing_summary = build_signal_subset(
        notes_df=notes_df,
        keywords=MANUFACTURING_KEYWORDS,
        signal_name="manufacturing_source_signal",
    )

    logistics_subset, logistics_summary = build_signal_subset(
        notes_df=notes_df,
        keywords=LOGISTICS_KEYWORDS,
        signal_name="logistics_source_signal",
    )

    construction_subset, construction_summary = build_signal_subset(
        notes_df=notes_df,
        keywords=CONSTRUCTION_DEVELOPMENT_KEYWORDS,
        signal_name="construction_development_source_signal",
    )

    retail_subset, retail_summary = build_signal_subset(
        notes_df=notes_df,
        keywords=RETAIL_LOCAL_DEMAND_KEYWORDS,
        signal_name="retail_local_demand_source_signal",
    )

    trade_subset, trade_summary = build_signal_subset(
        notes_df=notes_df,
        keywords=TRADE_SENSITIVE_KEYWORDS,
        signal_name="trade_sensitive_growth_signal",
    )

    relevant_notes = pd.concat(
        [
            manufacturing_subset,
            logistics_subset,
            construction_subset,
            retail_subset,
            trade_subset,
        ],
        ignore_index=True,
    )

    if not relevant_notes.empty:
        relevant_notes = relevant_notes.drop_duplicates()

    source_col = "source_name" if "source_name" in relevant_notes.columns else None
    source_type_col = "source_type" if "source_type" in relevant_notes.columns else None

    total_relevant_notes = len(relevant_notes)

    unique_sources = (
        relevant_notes[source_col].nunique()
        if source_col and not relevant_notes.empty
        else 0
    )

    source_type_count = (
        relevant_notes[source_type_col].nunique()
        if source_type_col and not relevant_notes.empty
        else 0
    )

    source_confidence_score = score_source_confidence(
        total_relevant_notes=total_relevant_notes,
        unique_sources=unique_sources,
        source_type_count=source_type_count,
        acs_data_available=acs_data_available,
    )

    source_confidence_label = classify_source_confidence(source_confidence_score)

    source_summary = pd.DataFrame(
        [
            {
                "total_relevant_notes": total_relevant_notes,
                "unique_sources": unique_sources,
                "source_type_count": source_type_count,
                "source_confidence_score": source_confidence_score,
                "source_confidence_label": source_confidence_label,
                **manufacturing_summary,
                **logistics_summary,
                **construction_summary,
                **retail_summary,
                **trade_summary,
            }
        ]
    )

    source_summary.to_csv(
        GEOECONOMIC_INDUSTRY_EXPOSURE_SOURCE_SUMMARY_OUTPUT,
        index=False,
    )

    return source_summary.iloc[0].to_dict()


# ============================================================
# Model
# ============================================================

def calculate_industry_shares(row: pd.Series) -> dict[str, float]:
    """
    Calculate industry employment shares from ACS employment counts.
    """

    employed_total = safe_float(row.get("civilian_employed_total"))

    if pd.isna(employed_total) or employed_total <= 0:
        return {
            "manufacturing_share": np.nan,
            "logistics_transportation_share": np.nan,
            "construction_share": np.nan,
            "retail_trade_share": np.nan,
            "wholesale_trade_share": np.nan,
            "trade_sensitive_share": np.nan,
        }

    manufacturing = safe_float(row.get("manufacturing_employment"), default=0.0)
    transportation = safe_float(
        row.get("transportation_warehousing_utilities_employment"),
        default=0.0,
    )
    construction = safe_float(row.get("construction_employment"), default=0.0)
    retail = safe_float(row.get("retail_trade_employment"), default=0.0)
    wholesale = safe_float(row.get("wholesale_trade_employment"), default=0.0)

    trade_sensitive = (
        manufacturing
        + transportation
        + construction
        + retail
        + wholesale
    )

    return {
        "manufacturing_share": manufacturing / employed_total,
        "logistics_transportation_share": transportation / employed_total,
        "construction_share": construction / employed_total,
        "retail_trade_share": retail / employed_total,
        "wholesale_trade_share": wholesale / employed_total,
        "trade_sensitive_share": trade_sensitive / employed_total,
    }


def build_geoeconomic_industry_exposure_model() -> pd.DataFrame:
    """
    Build geoeconomic industry exposure scores.
    """

    acs_df = collect_acs_industry_data()
    acs_data_available = not acs_df.empty
    local_signals = calculate_local_industry_signals(
        acs_data_available=acs_data_available,
    )

    rows = []

    for _, row in acs_df.iterrows():
        industry_shares = calculate_industry_shares(row)

        manufacturing_share = industry_shares["manufacturing_share"]
        logistics_transportation_share = industry_shares[
            "logistics_transportation_share"
        ]
        construction_share = industry_shares["construction_share"]
        retail_trade_share = industry_shares["retail_trade_share"]
        wholesale_trade_share = industry_shares["wholesale_trade_share"]
        trade_sensitive_share = industry_shares["trade_sensitive_share"]

        manufacturing_exposure_score = score_share(
            manufacturing_share,
            low_threshold=0.04,
            high_threshold=0.20,
        )

        logistics_transportation_exposure_score = score_share(
            logistics_transportation_share,
            low_threshold=0.03,
            high_threshold=0.14,
        )

        construction_development_exposure_score = score_share(
            construction_share,
            low_threshold=0.04,
            high_threshold=0.14,
        )

        retail_local_demand_exposure_score = score_share(
            retail_trade_share,
            low_threshold=0.07,
            high_threshold=0.18,
        )

        trade_sensitive_growth_signal_score = safe_float(
            local_signals.get("trade_sensitive_growth_signal_score")
        )

        source_confidence_score = safe_float(
            local_signals.get("source_confidence_score")
        )

        component_scores = {
            "manufacturing_exposure_score": manufacturing_exposure_score,
            "logistics_transportation_exposure_score": logistics_transportation_exposure_score,
            "construction_development_exposure_score": construction_development_exposure_score,
            "retail_local_demand_exposure_score": retail_local_demand_exposure_score,
            "trade_sensitive_growth_signal_score": trade_sensitive_growth_signal_score,
            "source_confidence_score": source_confidence_score,
        }

        exposure_score = weighted_average(
            component_scores,
            GEOECONOMIC_INDUSTRY_EXPOSURE_WEIGHTS,
        )

        acs_year = safe_float(row.get("acs_year"))

        output_row = {
            "acs_year": int(acs_year) if not pd.isna(acs_year) else np.nan,
            "date": f"{int(acs_year)}-12-31" if not pd.isna(acs_year) else "N/A",
            "geography_level": row.get("geography_level"),
            "geography_name": row.get("geography_name"),
            "acs_dataset": row.get("acs_dataset", ACS_DATASET),
            "civilian_employed_total": safe_float(row.get("civilian_employed_total")),
            "manufacturing_share": manufacturing_share,
            "logistics_transportation_share": logistics_transportation_share,
            "construction_share": construction_share,
            "retail_trade_share": retail_trade_share,
            "wholesale_trade_share": wholesale_trade_share,
            "trade_sensitive_share": trade_sensitive_share,
            "manufacturing_source_notes": local_signals.get(
                "manufacturing_source_signal_note_count"
            ),
            "logistics_source_notes": local_signals.get(
                "logistics_source_signal_note_count"
            ),
            "construction_development_source_notes": local_signals.get(
                "construction_development_source_signal_note_count"
            ),
            "retail_local_demand_source_notes": local_signals.get(
                "retail_local_demand_source_signal_note_count"
            ),
            "trade_sensitive_source_notes": local_signals.get(
                "trade_sensitive_growth_signal_note_count"
            ),
            "source_confidence_score": source_confidence_score,
            "source_confidence_label": local_signals.get("source_confidence_label"),
            "geoeconomic_industry_exposure_score": exposure_score,
            "geoeconomic_industry_exposure_signal": safe_classify_risk(exposure_score),
            "data_quality_flag": local_signals.get("source_confidence_label"),
        }

        for key, value in component_scores.items():
            output_row[key] = value

        rows.append(output_row)

    result = pd.DataFrame(rows)

    result = result.sort_values(
        ["geography_level", "geography_name", "acs_year"],
        ascending=[True, True, True],
    )

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    result.to_csv(GEOECONOMIC_INDUSTRY_EXPOSURE_OUTPUT, index=False)

    latest = (
        result.sort_values("acs_year")
        .groupby(["geography_level", "geography_name"], as_index=False)
        .tail(1)
        .sort_values(["geography_level", "geography_name"])
    )

    county_latest = latest[latest["geography_level"] == "county"].copy()

    if county_latest.empty:
        county_latest = latest.head(1).copy()

    county_latest.to_csv(
        GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_OUTPUT,
        index=False,
    )

    component_summary = build_component_summary(county_latest.iloc[0])
    component_summary.to_csv(
        GEOECONOMIC_INDUSTRY_EXPOSURE_COMPONENT_SUMMARY_OUTPUT,
        index=False,
    )

    print(
        "Saved geoeconomic industry exposure scores to: "
        f"{GEOECONOMIC_INDUSTRY_EXPOSURE_OUTPUT}"
    )
    print(
        "Saved latest geoeconomic industry exposure score to: "
        f"{GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_OUTPUT}"
    )
    print(
        "Saved geoeconomic industry exposure component summary to: "
        f"{GEOECONOMIC_INDUSTRY_EXPOSURE_COMPONENT_SUMMARY_OUTPUT}"
    )
    print(
        "Saved geoeconomic industry exposure source summary to: "
        f"{GEOECONOMIC_INDUSTRY_EXPOSURE_SOURCE_SUMMARY_OUTPUT}"
    )

    return result


def build_component_summary(latest_row: pd.Series) -> pd.DataFrame:
    """
    Build component summary for latest county geoeconomic industry exposure score.
    """

    component_labels = {
        "manufacturing_exposure_score": "Manufacturing Exposure",
        "logistics_transportation_exposure_score": "Logistics / Transportation Exposure",
        "construction_development_exposure_score": "Construction / Development Exposure",
        "retail_local_demand_exposure_score": "Retail / Local Demand Exposure",
        "trade_sensitive_growth_signal_score": "Trade-Sensitive Growth Signal",
        "source_confidence_score": "Source Confidence",
    }

    rows = []

    for component, weight in GEOECONOMIC_INDUSTRY_EXPOSURE_WEIGHTS.items():
        score = safe_float(latest_row.get(component))

        rows.append(
            {
                "component": component,
                "component_label": component_labels.get(component, component),
                "weight": weight,
                "score": score,
                "signal": safe_classify_risk(score),
                "weighted_contribution": (
                    score * weight if not pd.isna(score) else np.nan
                ),
            }
        )

    return pd.DataFrame(rows)


def summarize_geoeconomic_industry_exposure(
    result: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Print latest geoeconomic industry exposure summary.
    """

    if result is None:
        if not GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_OUTPUT.exists():
            raise FileNotFoundError(
                "No geoeconomic industry exposure latest file found. "
                "Run build_geoeconomic_industry_exposure_model() first."
            )

        latest = pd.read_csv(GEOECONOMIC_INDUSTRY_EXPOSURE_LATEST_OUTPUT)
    else:
        latest = (
            result.sort_values("acs_year")
            .groupby(["geography_level", "geography_name"], as_index=False)
            .tail(1)
            .sort_values(["geography_level", "geography_name"])
        )

    print()
    print("Geoeconomic Industry Exposure Summary")
    print("-------------------------------------")

    display_cols = [
        "geography_name",
        "acs_year",
        "acs_dataset",
        "civilian_employed_total",
        "manufacturing_share",
        "logistics_transportation_share",
        "construction_share",
        "retail_trade_share",
        "trade_sensitive_share",
        "geoeconomic_industry_exposure_score",
        "geoeconomic_industry_exposure_signal",
        "data_quality_flag",
    ]

    display_cols = [col for col in display_cols if col in latest.columns]

    print(latest[display_cols].to_string(index=False))

    return latest


def main() -> None:
    """
    Run geoeconomic industry exposure module as a script.
    """

    result = build_geoeconomic_industry_exposure_model()
    summarize_geoeconomic_industry_exposure(result)


if __name__ == "__main__":
    main()