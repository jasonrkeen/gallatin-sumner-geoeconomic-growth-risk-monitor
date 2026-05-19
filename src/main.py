"""
Main entry point for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.
"""

from src.config import (
    PROJECT_NAME,
    PROJECT_SUBTITLE,
    AUTHOR_NAME,
    AUTHOR_EMAIL,
    PRIMARY_GEOGRAPHY,
    LOCAL_CASE_STUDY,
    RISK_SCORE_WEIGHTS,
    RESILIENCE_OFFSET_WEIGHTS,
    SCENARIOS,
    LOCAL_SOURCES,
    classify_risk,
)

from src.fred_data import collect_fred_data, summarize_latest_values

from src.construction_shock import (
    build_construction_shock_model,
    summarize_construction_shock,
)

from src.growth_pressure import (
    build_growth_pressure_model,
    summarize_growth_pressure,
)

from src.housing_affordability import (
    build_housing_affordability_model,
    summarize_housing_affordability,
)

from src.infrastructure_strain import (
    build_infrastructure_strain_model,
    summarize_infrastructure_strain,
)

from src.development_friction import (
    build_development_friction_model,
    summarize_development_friction,
)

from src.geoeconomic_industry_exposure import (
    build_geoeconomic_industry_exposure_model,
    summarize_geoeconomic_industry_exposure,
)

from src.household_vulnerability import (
    build_household_vulnerability_model,
    summarize_household_vulnerability,
)

from src.local_resilience import (
    build_local_resilience_model,
    summarize_local_resilience,
)

from src.composite_score import (
    build_composite_score_model,
    summarize_composite_components,
)

from src.scenario_forecast import (
    build_scenario_forecast_model,
    summarize_scenario_forecasts,
)

from src.change_detection import run_change_detection

from src.sensitivity_analysis import run_sensitivity_analysis

from src.risk_threshold_breaches import run_risk_threshold_breach_monitor

from src.visualization import build_all_charts
from src.report_generator import build_report


def print_project_overview() -> None:
    """
    Print basic project metadata and model design.
    """

    print("=" * 90)
    print(PROJECT_NAME)
    print(PROJECT_SUBTITLE)
    print("=" * 90)
    print(f"Author: {AUTHOR_NAME} | {AUTHOR_EMAIL}")
    print(f"Primary geography: {PRIMARY_GEOGRAPHY}")
    print(f"Local case study: {LOCAL_CASE_STUDY}")
    print()

    print("Composite risk score components:")
    for component, weight in RISK_SCORE_WEIGHTS.items():
        print(f" - {component}: {weight:.0%}")

    print()
    print("Local resilience offset components:")
    for component, weight in RESILIENCE_OFFSET_WEIGHTS.items():
        print(f" - {component}: {weight:.0%}")

    print()
    print("Scenario forecast cases:")
    for scenario in SCENARIOS.values():
        print(f" - {scenario['name']}: {scenario['description']}")

    print()
    print("Local source inventory:")
    for source in LOCAL_SOURCES.values():
        print(f" - {source['name']}: {source['url']}")

    print()
    sample_score = 62.5
    print(f"Sample risk classification for {sample_score}: {classify_risk(sample_score)}")
    print()


def main() -> None:
    """
    Run the full project pipeline.
    """

    print_project_overview()

    print("=" * 90)
    print("Step 1: Collecting FRED macro and shock-proxy data")
    print("=" * 90)

    long_df, _ = collect_fred_data()
    summarize_latest_values(long_df)

    print()
    print("=" * 90)
    print("Step 2: Building Construction Shock Exposure Score")
    print("=" * 90)

    construction_result = build_construction_shock_model()
    summarize_construction_shock(construction_result)

    print()
    print("=" * 90)
    print("Step 3: Building Growth Pressure Score")
    print("=" * 90)

    growth_result = build_growth_pressure_model()
    summarize_growth_pressure(growth_result)

    print()
    print("=" * 90)
    print("Step 4: Building Housing Affordability Pressure Score")
    print("=" * 90)

    housing_result = build_housing_affordability_model()
    summarize_housing_affordability(housing_result)

    print()
    print("=" * 90)
    print("Step 5: Building Infrastructure Strain Score")
    print("=" * 90)

    infrastructure_result = build_infrastructure_strain_model()
    summarize_infrastructure_strain(infrastructure_result)

    print()
    print("=" * 90)
    print("Step 6: Building Development Friction Score")
    print("=" * 90)

    development_result = build_development_friction_model()
    summarize_development_friction(development_result)

    print()
    print("=" * 90)
    print("Step 7: Building Geoeconomic Industry Exposure Score")
    print("=" * 90)

    industry_result = build_geoeconomic_industry_exposure_model()
    summarize_geoeconomic_industry_exposure(industry_result)

    print()
    print("=" * 90)
    print("Step 8: Building Household Vulnerability Score")
    print("=" * 90)

    household_result = build_household_vulnerability_model()
    summarize_household_vulnerability(household_result)

    print()
    print("=" * 90)
    print("Step 9: Building Local Resilience Offset")
    print("=" * 90)

    resilience_result = build_local_resilience_model()
    summarize_local_resilience(resilience_result)

    print()
    print("=" * 90)
    print("Step 10: Building Composite Geoeconomic Growth Risk Score")
    print("=" * 90)

    build_composite_score_model()
    summarize_composite_components()

    print()
    print("=" * 90)
    print("Step 11: Building Scenario Forecasts")
    print("=" * 90)

    build_scenario_forecast_model()
    summarize_scenario_forecasts()

    print()
    print("=" * 90)
    print("Step 12: Running Change Detection")
    print("=" * 90)

    run_change_detection()

    print()
    print("=" * 90)
    print("Step 13: Running Sensitivity Analysis")
    print("=" * 90)

    run_sensitivity_analysis()

    print()
    print("=" * 90)
    print("Step 14: Running Risk Threshold Breach Monitor")
    print("=" * 90)

    run_risk_threshold_breach_monitor()

    print()
    print("=" * 90)
    print("Step 15: Building Charts")
    print("=" * 90)

    build_all_charts()

    print()
    print("=" * 90)
    print("Step 16: Generating PDF Report")
    print("=" * 90)

    build_report()

    print()
    print("=" * 90)
    print("Pipeline complete.")
    print("=" * 90)


if __name__ == "__main__":
    main()
