"""
Configuration settings for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This project measures local growth pressure, construction risk, infrastructure strain,
development friction, household vulnerability, industry exposure, and geoeconomic
shock sensitivity for Gallatin and Sumner County, Tennessee.
"""

from __future__ import annotations

from pathlib import Path


# ============================================================
# Project metadata
# ============================================================

PROJECT_NAME = "Gallatin-Sumner County Geoeconomic Growth Risk Monitor"

PROJECT_SUBTITLE = (
    "A Python-based local economic intelligence model measuring growth pressure, "
    "construction risk, infrastructure strain, development friction, household "
    "vulnerability, industry exposure, and geoeconomic shock sensitivity in "
    "Gallatin and Sumner County, Tennessee."
)

AUTHOR_NAME = "Jason Keen"
AUTHOR_EMAIL = "keenjasonr@gmail.com"

PRIMARY_GEOGRAPHY = "Sumner County, Tennessee"
LOCAL_CASE_STUDY = "Gallatin, Tennessee"
STATE = "Tennessee"

REPORT_FILENAME = "gallatin_sumner_geoeconomic_growth_risk_report.pdf"


# ============================================================
# Directory structure
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

OUTPUTS_DIR = BASE_DIR / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"
TABLES_DIR = OUTPUTS_DIR / "tables"
REPORTS_DIR = OUTPUTS_DIR / "reports"

for directory in [
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    OUTPUTS_DIR,
    CHARTS_DIR,
    TABLES_DIR,
    REPORTS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# Geography identifiers
# ============================================================

TENNESSEE_FIPS = "47"
SUMNER_COUNTY_FIPS = "47165"
GALLATIN_PLACE_FIPS = "4728540"

SUMNER_COUNTY_GEO_NAME = "Sumner County, Tennessee"
GALLATIN_CITY_GEO_NAME = "Gallatin city, Tennessee"


# ============================================================
# FRED series candidates
# ============================================================

FRED_SERIES = {
    # Sumner County macro / labor
    "sumner_real_gdp": "REALGDPALL47165",
    "sumner_unemployment_rate": "TNSUMN5URN",

    # National macro and geopolitical cost-shock proxies
    "wti_crude_oil": "DCOILWTICO",
    "retail_gasoline": "GASREGW",
    "diesel_price": "GASDESW",
    "thirty_year_mortgage_rate": "MORTGAGE30US",
    "federal_funds_rate": "FEDFUNDS",

    # Construction cost proxies
    "construction_materials_ppi": "WPUSI012011",
    "lumber_ppi": "WPU081",
    "cement_ppi": "PCU327310327310",
    "steel_mill_products_ppi": "WPU1017",
}


# ============================================================
# Official / local source inventory
# ============================================================

LOCAL_SOURCES = {
    "sumner_county_government": {
        "name": "Sumner County Government",
        "url": "https://sumnercountytn.gov/government/",
        "use": (
            "County commission records, public notices, planning and engineering "
            "references, building and codes context, finance, highway department "
            "references, property tax context, and GIS property search."
        ),
    },
    "city_of_gallatin": {
        "name": "City of Gallatin Official Website",
        "url": "https://www.gallatintn.gov/",
        "use": (
            "Building permits, planning department, engineering, public works, "
            "utilities, economic development, city council agendas, planning "
            "commission meetings, public notices, and zoning context."
        ),
    },
    "gallatin_document_center": {
        "name": "City of Gallatin Document Center",
        "url": "https://www.gallatintn.gov/DocumentCenter",
        "use": (
            "Planning, zoning, development review, land-development regulations, "
            "engineering, stormwater, transportation, board and commission records, "
            "annexation notifications, zoning-code update references, and related "
            "public documents."
        ),
    },
    "gallatin_development_page": {
        "name": "Developments in Gallatin",
        "url": "https://www.gallatintn.gov/1722/Developments-in-Gallatin",
        "use": (
            "Local development pipeline, approved projects, pending zoning actions, "
            "and construction activity context."
        ),
    },
    "gallatin_zoning_update": {
        "name": "Gallatin Zoning Code Update",
        "url": "https://www.gallatintn.gov/2286/ZoCo-Zoning-Code-Update-2026",
        "use": (
            "Zoning-code overhaul context, land-use policy transition, and "
            "development friction analysis."
        ),
    },
    "gallatin_strategic_plan": {
        "name": "City of Gallatin Strategic Plan",
        "url": "Gallatin Strategic Plan Publication Final_201807131355303703.pdf",
        "use": (
            "Baseline policy context for growth, development, transportation, "
            "affordability, economic diversification, community vulnerability, "
            "capital planning, citizen engagement, and performance measurement."
        ),
    },
    "gallatin_state_of_city_2025": {
        "name": "2025 Gallatin State of the City Address",
        "url": "https://www.youtube.com/watch?v=ltyt8MDDdKQ",
        "use": (
            "Qualitative context for growth, infrastructure priorities, public "
            "services, development, and city leadership narrative."
        ),
    },
    "gallatin_economic_development_agency": {
        "name": "Gallatin Economic Development Agency - Gallatin Gets It",
        "url": "https://www.gallatingetsit.com/",
        "use": (
            "Economic-development narrative, business attraction, growth claims, "
            "available sites, infrastructure advantages, labor shed, manufacturing "
            "concentration, corporate and tech positioning, and local investment examples."
        ),
    },
    "gallatin_gets_it_location_infrastructure": {
        "name": "Gallatin Gets It - Location & Infrastructure",
        "url": "https://www.gallatingetsit.com/location-infrastructure",
        "use": (
            "Transportation access, road investment, publicly owned utilities, "
            "water and sewer capacity, fiber connectivity, interstate access, "
            "airport access, and logistics positioning."
        ),
    },
    "gallatin_gets_it_high_tech": {
        "name": "Gallatin Gets It - High-Tech Manufacturing",
        "url": "https://www.gallatingetsit.com/high-tech",
        "use": (
            "Advanced manufacturing concentration, recent investment, workforce pipeline, "
            "labor shed, major employer examples, available industrial/corporate sites, "
            "and distribution/logistics expansion examples."
        ),
    },
    "city_of_gallatin_february_2026_news": {
        "name": "City of Gallatin February 2026 News",
        "url": "2026 Feb News Master sm.pdf",
        "use": (
            "Local resilience, winter storm response, public works coordination, "
            "utility coordination, Clearview Park construction progress, stormwater "
            "mitigation, traffic improvements, and public safety context."
        ),
    },
}


# ============================================================
# Manual local files
# ============================================================

LOCAL_SOURCE_NOTES_FILE = RAW_DATA_DIR / "local_source_notes.csv"
POLICY_EVENTS_FILE = RAW_DATA_DIR / "policy_events.csv"
DEVELOPMENT_PROJECTS_FILE = RAW_DATA_DIR / "development_projects.csv"


# ============================================================
# Risk score weights
# ============================================================

RISK_SCORE_WEIGHTS = {
    "growth_pressure": 0.20,
    "housing_affordability_pressure": 0.15,
    "construction_shock_exposure": 0.15,
    "infrastructure_strain": 0.15,
    "development_friction": 0.15,
    "geoeconomic_industry_exposure": 0.10,
    "household_vulnerability": 0.10,
}

RESILIENCE_OFFSET_WEIGHTS = {
    "utility_coordination": 0.20,
    "public_works_capacity": 0.20,
    "stormwater_flood_mitigation": 0.20,
    "public_safety_response": 0.20,
    "capital_project_execution": 0.20,
}


# ============================================================
# Final model status metadata
# ============================================================

MODEL_COMPONENT_COUNT = len(RISK_SCORE_WEIGHTS)
TARGET_LIVE_COMPONENTS = 7
TARGET_PLACEHOLDER_COMPONENTS = 0
TARGET_PLACEHOLDER_SHARE = 0.0
TARGET_MODEL_MATURITY = "Fully Data-Driven"


# ============================================================
# Resilience credit assumptions
# ============================================================

# The resilience offset is not subtracted directly from the composite score.
# It is converted into a capped credit so local resilience evidence can reduce
# risk without overwhelming high growth pressure or construction shock exposure.
RESILIENCE_CREDIT_RATE = 0.15
MAX_RESILIENCE_CREDIT = 12.5


# ============================================================
# Scenario risk weights
# ============================================================

SCENARIO_RISK_WEIGHTS = {
    "composite_baseline": 0.30,
    "scenario_growth_pressure": 0.25,
    "scenario_construction_shock": 0.25,
    "scenario_local_stress_proxy": 0.20,
}


# ============================================================
# Risk signal thresholds
# ============================================================

RISK_THRESHOLDS = {
    "low": 25,
    "moderate": 50,
    "elevated": 75,
    "high": 100,
}


def classify_risk(score: float) -> str:
    """
    Classify a 0-100 risk score into a qualitative signal.
    """

    if score is None:
        return "Insufficient Data"

    try:
        score = float(score)
    except Exception:
        return "Insufficient Data"

    if score < RISK_THRESHOLDS["low"]:
        return "Low Risk"
    if score < RISK_THRESHOLDS["moderate"]:
        return "Moderate Risk"
    if score < RISK_THRESHOLDS["elevated"]:
        return "Elevated Risk"
    return "High Risk"


# ============================================================
# Resilience signal thresholds
# ============================================================

RESILIENCE_THRESHOLDS = {
    "limited": 25,
    "moderate": 50,
    "strong": 75,
    "very_strong": 100,
}


def classify_resilience(score: float) -> str:
    """
    Classify a 0-100 resilience score into a qualitative signal.
    """

    if score is None:
        return "Insufficient Data"

    try:
        score = float(score)
    except Exception:
        return "Insufficient Data"

    if score < RESILIENCE_THRESHOLDS["limited"]:
        return "Limited Resilience Offset"
    if score < RESILIENCE_THRESHOLDS["moderate"]:
        return "Moderate Resilience Offset"
    if score < RESILIENCE_THRESHOLDS["strong"]:
        return "Strong Resilience Offset"
    return "Very Strong Resilience Offset"


# ============================================================
# Model maturity assumptions
# ============================================================

MODEL_MATURITY_THRESHOLDS = {
    "fully_data_driven_placeholder_share": 0.00,
    "mostly_data_driven_max_placeholder_share": 0.25,
    "partially_data_driven_max_placeholder_share": 0.50,
}


# ============================================================
# Scenario assumptions
# ============================================================

SCENARIOS = {
    "managed_growth": {
        "name": "Managed Growth",
        "description": (
            "Growth continues, but zoning updates, infrastructure planning, and "
            "public investment help the city and county absorb development pressure."
        ),
        "growth_multiplier": 1.00,
        "housing_multiplier": 1.00,
        "construction_cost_multiplier": 1.00,
        "infrastructure_multiplier": 1.00,
        "development_friction_multiplier": 1.00,
    },
    "overheated_growth": {
        "name": "Overheated Growth",
        "description": (
            "Development continues faster than roads, utilities, schools, housing "
            "affordability, and planning capacity can absorb."
        ),
        "growth_multiplier": 1.25,
        "housing_multiplier": 1.25,
        "construction_cost_multiplier": 1.10,
        "infrastructure_multiplier": 1.30,
        "development_friction_multiplier": 1.25,
    },
    "construction_cost_shock": {
        "name": "Geopolitical Construction Cost Shock",
        "description": (
            "A geopolitical or macroeconomic shock raises construction materials, "
            "fuel, financing costs, logistics costs, and project delay risk."
        ),
        "growth_multiplier": 1.00,
        "housing_multiplier": 1.20,
        "construction_cost_multiplier": 1.40,
        "infrastructure_multiplier": 1.15,
        "development_friction_multiplier": 1.10,
    },
    "growth_pause_rezoning_constraint": {
        "name": "Growth Pause / Rezoning Constraint",
        "description": (
            "Development approvals slow during zoning reform or planning review. "
            "Infrastructure pressure may ease, but housing supply and developer "
            "certainty may weaken."
        ),
        "growth_multiplier": 0.85,
        "housing_multiplier": 1.20,
        "construction_cost_multiplier": 1.05,
        "infrastructure_multiplier": 0.90,
        "development_friction_multiplier": 1.35,
    },
}


# ============================================================
# Output filenames
# ============================================================

OUTPUT_TABLES = {
    "risk_scores": TABLES_DIR / "risk_scores.csv",
    "scenario_forecasts": TABLES_DIR / "scenario_forecasts.csv",
    "local_source_notes": TABLES_DIR / "local_source_notes_processed.csv",
}

OUTPUT_CHARTS = {
    "composite_risk_score": CHARTS_DIR / "composite_risk_score.png",
    "scenario_comparison": CHARTS_DIR / "scenario_comparison.png",
    "construction_shock_trend": CHARTS_DIR / "construction_shock_trend.png",
    "construction_shock_categories": CHARTS_DIR / "construction_shock_categories.png",
    "growth_pressure_trend": CHARTS_DIR / "growth_pressure_trend.png",
    "local_resilience_offset": CHARTS_DIR / "local_resilience_offset.png",
    "sensitivity_analysis": CHARTS_DIR / "sensitivity_analysis.png",
    "risk_threshold_breaches": CHARTS_DIR / "risk_threshold_breaches.png",
    "unemployment_trend": CHARTS_DIR / "sumner_unemployment_trend.png",
    "gdp_trend": CHARTS_DIR / "sumner_real_gdp_trend.png",
}


# ============================================================
# Report section toggles
# ============================================================

REPORT_INCLUDE_CHARTS = True
REPORT_INCLUDE_SOURCE_NOTES = True
REPORT_INCLUDE_LIMITATIONS = True
REPORT_INCLUDE_METHODOLOGY = True

# Backward-compatible alias for older code that may still import the typo.
REPORT_INCLUDE_METHODLOGY = REPORT_INCLUDE_METHODOLOGY


# ============================================================
# Console formatting
# ============================================================

SECTION_BREAK = "=" * 90
SUBSECTION_BREAK = "-" * 70
