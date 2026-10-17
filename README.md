# Gallatin-Sumner County Geoeconomic Growth Risk Monitor

A Python-based local economic intelligence project measuring growth pressure, housing affordability pressure, construction risk, infrastructure strain, development friction, geoeconomic industry exposure, household vulnerability, local resilience, and geoeconomic shock sensitivity in Gallatin and Sumner County, Tennessee.

## Project Overview

Gallatin and Sumner County are experiencing rapid growth across population, development, infrastructure, housing demand, and business investment. This project examines whether that growth could become more fragile if local development pressure intersects with broader geopolitical or macroeconomic shocks that raise construction costs, fuel prices, borrowing costs, logistics costs, housing costs, permitting friction, household stress, or supply-chain delays.

The model is designed as a repeatable local geoeconomic risk monitor. It combines public economic indicators, FRED macroeconomic data, Census ACS housing, household, industry, and commute indicators, construction-cost proxies, manually curated local source notes, development-friction signals, scenario forecasting, sensitivity analysis, change detection, threshold-breach monitoring, and a capped local resilience offset.

The final report is intended for portfolio and LinkedIn presentation. It explains how to read the model, how each metric can be used, how each chart should be interpreted, and why the output should be treated as a portfolio-style intelligence indicator rather than an official public-sector forecast or risk rating.

## Research Question

**Can Gallatin and Sumner County sustain rapid growth if local development pressure intersects with geopolitical shocks that raise construction costs, fuel prices, financing costs, housing costs, development friction, household vulnerability, industry exposure, or supply-chain delays?**

## Core Thesis

Local growth risk is not only local. Gallatin and Sumner County may benefit from strong economic expansion, manufacturing investment, logistics access, utility ownership, public infrastructure, and business attraction. However, rapid development can also increase pressure on housing, roads, utilities, land use, public services, permitting capacity, household affordability, and local resilience systems.

If geopolitical or macroeconomic shocks raise project costs, borrowing costs, fuel prices, or supply-chain delays at the same time that local planning and development systems are under pressure, the region's growth path may become more fragile.

## Final Model Status

The current version is fully data-driven across all seven composite risk components.

```text
Model Maturity: Fully Data-Driven
Live / Placeholder Components: 7 live / 0 placeholder
Placeholder Share: 0.0%
Data Quality Flag: Data-Driven Components Available
```

Final headline results from the latest report:

```text
Composite Risk Score: 69.1
Local Resilience Offset: 55.0
Resilience Credit Applied: 8.2
Adjusted Geoeconomic Growth Risk Score: 60.9
Adjusted Risk Signal: Elevated Risk
Highest-Risk Scenario: Overheated Growth
Highest-Risk Scenario Score: 64.7
Highest-Risk Scenario Delta vs. Baseline: +3.8
```

The adjusted score remains in the **Elevated Risk** band even after applying the resilience credit. This suggests that local resilience capacity helps reduce risk, but does not fully offset growth, infrastructure, housing, development, household, and industry-exposure pressure.

## Model Components

The model uses a 0-100 scoring framework. Higher values indicate higher risk pressure.

```text
Composite Risk Score =
  20% Growth Pressure Score
+ 15% Housing Affordability Pressure Score
+ 15% Construction Shock Exposure Score
+ 15% Infrastructure Strain Score
+ 15% Development Friction Index
+ 10% Geoeconomic Industry Exposure Score
+ 10% Household Vulnerability Score
```

The model also calculates a capped resilience adjustment:

```text
Resilience Credit = min(Local Resilience Offset * 0.15, 12.5)

Adjusted Risk Score =
Composite Risk Score - Resilience Credit
```

The capped credit prevents qualitative resilience evidence from overpowering high growth pressure, housing affordability pressure, construction shock exposure, infrastructure strain, development friction, industry exposure, or household vulnerability.

## Latest Module Scores

| Module | Latest Score | Signal / Context |
|---|---:|---|
| Construction Shock Exposure | 40.6 | Moderate Risk; momentum rapidly rising |
| Growth Pressure | 85.4 | High Risk; partial economic data |
| Housing Affordability Pressure | 49.5 | Moderate Risk; strong ACS coverage; ACS 2024 |
| Infrastructure Strain | 69.9 | Elevated Risk; strong ACS commute coverage; strong local signal |
| Development Friction | 84.2 | High Risk; very strong source signal |
| Geoeconomic Industry Exposure | 98.5 | High Risk; very strong source signal; ACS 2024 |
| Household Vulnerability | 55.9 | Elevated Risk; strong ACS household coverage; very strong local signal |
| Local Resilience Offset | 55.0 | Strong resilience offset; strong evidence |

## How to Read the Scores

The scores are normalized monitoring indicators, not probabilities or official risk ratings.

| Score Range | Risk Band | Interpretation |
|---:|---|---|
| 0-24.9 | Low Risk | Limited current pressure; monitor for early movement |
| 25.0-49.9 | Moderate Risk | Manageable pressure; useful as a watchlist signal |
| 50.0-74.9 | Elevated Risk | Meaningful pressure; deserves regular monitoring and explanation |
| 75.0-100 | High Risk | Material pressure; likely a priority risk channel or policy focus area |

A practical reading of the report should start with the **Adjusted Risk Score**, then move to the component table to identify the main drivers. The scenario, sensitivity, threshold-breach, and change-detection sections help determine whether the conclusion is stable or dependent on one assumption.

## Why the Output Matters

The model's most important insight is the interaction between local growth pressure, housing affordability, infrastructure strain, development friction, household vulnerability, industry exposure, and external cost shocks.

The current result suggests that Gallatin and Sumner County may continue to benefit from growth, but that growth could become more difficult to absorb if construction costs, fuel prices, interest rates, housing costs, planning friction, or supply-chain disruptions rise while local development pressure remains high.

The **Overheated Growth** scenario matters because it tests whether rapid development could outpace housing affordability, road capacity, utilities, planning capacity, and public-service absorption.

## Current Live Modules

| Module | Description |
|---|---|
| `config.py` | Stores project metadata, geographies, FRED series, scoring weights, scenario assumptions, output paths, and reporting settings |
| `fred_data.py` | Downloads public FRED data for Sumner County and national shock proxies |
| `construction_shock.py` | Scores construction, materials, fuel, energy, and financing shock exposure |
| `growth_pressure.py` | Scores growth pressure using GDP, unemployment, and curated local growth signals |
| `housing_affordability.py` | Scores housing affordability pressure using Census ACS data and mortgage-rate inputs |
| `infrastructure_strain.py` | Scores infrastructure strain using Census ACS commute indicators and curated local infrastructure notes |
| `development_friction.py` | Scores zoning, planning, permitting, development pipeline, and public-notice friction using curated local source notes |
| `geoeconomic_industry_exposure.py` | Scores exposure to manufacturing, logistics, construction, retail, and trade-sensitive growth channels using employment-exposure indicators and local source evidence |
| `household_vulnerability.py` | Scores poverty, low-income exposure, unemployment, housing cost burden, commute burden, and local vulnerability source evidence |
| `local_resilience.py` | Calculates a local resilience offset from public works, utility, stormwater, public safety, and capital project indicators |
| `composite_score.py` | Combines all seven live components into composite and adjusted risk scores |
| `scenario_forecast.py` | Runs scenario forecasts for growth and shock cases |
| `change_detection.py` | Compares the current run with the prior saved snapshot |
| `sensitivity_analysis.py` | Tests whether the model conclusion changes under alternative weighting assumptions |
| `risk_threshold_breaches.py` | Converts model outputs into an alert-style threshold breach monitor |
| `visualization.py` | Generates project charts |
| `report_generator.py` | Builds a portfolio-ready PDF report with metric explanations, chart explanations, methodology notes, caveats, and source notes |
| `main.py` | Runs the full end-to-end pipeline |

## Scenario Forecasts

The model evaluates four scenarios:

| Scenario | Description |
|---|---|
| Managed Growth | Growth continues, but zoning updates, infrastructure planning, and public investment help absorb development pressure |
| Overheated Growth | Development grows faster than roads, utilities, schools, housing affordability, planning capacity, and public-service absorption |
| Geopolitical Construction Cost Shock | Global or macroeconomic shocks raise materials, fuel, financing, logistics, and project delay risk |
| Growth Pause / Rezoning Constraint | Development approvals slow during zoning reform or planning review, easing some infrastructure pressure but increasing supply uncertainty |

The latest scenario results identify **Overheated Growth** as the highest-risk scenario, with an adjusted scenario risk score of **64.7**.

## Sensitivity Analysis

The sensitivity analysis tests whether the adjusted risk conclusion changes under alternative component-weighting assumptions.

Latest sensitivity conclusion:

```text
Sensitivity Stability: Stable
Minimum Adjusted Risk Score: 55.4
Maximum Adjusted Risk Score: 63.5
Adjusted Risk Score Range: 8.1
Lowest-Risk Weighting Case: Construction-Shock-Heavy Case
Highest-Risk Weighting Case: Infrastructure / Friction Heavy Case
```

A stable sensitivity result means the model's broad risk conclusion is not overly dependent on one weighting framework.

## Risk Threshold Breach Monitor

The breach monitor converts model outputs into an alert-style layer by tracking whether key growth, construction, scenario, resilience, and model-quality thresholds are active.

Latest breach-monitor summary:

```text
Alert Level: Elevated Alert
Total Active Breaches: 4
High-Severity Breaches: 1
Model Quality Breaches: 0
Top Breach Category: Growth Pressure
```

Active breach categories include:

- Composite Risk
- Growth Pressure
- Scenario Stress

## Data Sources

The project uses a combination of live public data, public API data, and manually curated local sources.

### Public Economic, Housing, Household, Infrastructure, Industry, and Macro Data

| Source | Use |
|---|---|
| FRED | Sumner County GDP, unemployment, oil prices, fuel prices, mortgage rates, federal funds rate, and construction material price proxies |
| U.S. Census ACS 5-Year API | Housing affordability inputs, commute indicators, transportation mode shares, household vulnerability indicators, industry exposure indicators, and infrastructure strain signals |
| BLS / FRED series | Construction-cost and labor-market indicators |
| Local source notes | Qualitative growth, zoning, development, infrastructure, resilience, household, affordability, and industry-exposure signals |

### Local Official and Economic Development Sources

| Source | Use |
|---|---|
| Sumner County Government | County government, planning, building and codes, public notices, finance, highway, and property context |
| City of Gallatin Official Website | City planning, zoning, building permits, public works, utilities, agendas, public notices, and infrastructure context |
| City of Gallatin Document Center | Repeatable source hub for planning, zoning, infrastructure, engineering, stormwater, transportation, and policy evidence |
| Developments in Gallatin | Local development pipeline, pending approvals, approved projects, and construction activity |
| Gallatin Zoning Code Update | Zoning-code overhaul, land-use policy transition, and development friction |
| Gallatin Gets It | Economic development, business attraction, infrastructure, utilities, manufacturing, and investment narrative |
| Gallatin Gets It - Location & Infrastructure | Transportation access, road investment, public utilities, water and sewer capacity, fiber connectivity, and logistics positioning |
| Gallatin Gets It - High-Tech Manufacturing | Advanced manufacturing, employer investment, workforce pipeline, distribution expansion, and industry-exposure evidence |
| Gallatin State of the City Address | Qualitative context for growth, infrastructure, public services, and city priorities |
| City of Gallatin February 2026 News | Local resilience, public works, storm response, infrastructure, construction, and flood mitigation context |
| City of Gallatin Strategic Plan | Policy context for growth, development, transportation, affordability, economic diversification, vulnerable residents, capital planning, and performance measurement |

## Project Structure

```text
gallatin_sumner_geoeconomic_growth_risk/
├── data/
│   ├── raw/
│   │   ├── local_source_notes.csv
│   │   ├── policy_events.csv
│   │   └── development_projects.csv
│   └── processed/
│       ├── fred_series_long.csv
│       ├── fred_series_wide.csv
│       ├── fred_latest_values.csv
│       ├── fred_failed_downloads.csv
│       ├── construction_shock_scores.csv
│       ├── construction_shock_latest.csv
│       ├── construction_shock_component_summary.csv
│       ├── construction_shock_category_summary.csv
│       ├── growth_pressure_scores.csv
│       ├── growth_pressure_latest.csv
│       ├── growth_pressure_source_summary.csv
│       ├── growth_pressure_component_summary.csv
│       ├── housing_affordability_scores.csv
│       ├── housing_affordability_latest.csv
│       ├── housing_affordability_component_summary.csv
│       ├── infrastructure_strain_scores.csv
│       ├── infrastructure_strain_latest.csv
│       ├── infrastructure_strain_component_summary.csv
│       ├── infrastructure_strain_source_summary.csv
│       ├── development_friction_scores.csv
│       ├── development_friction_latest.csv
│       ├── development_friction_component_summary.csv
│       ├── development_friction_source_summary.csv
│       ├── geoeconomic_industry_exposure_scores.csv
│       ├── geoeconomic_industry_exposure_latest.csv
│       ├── geoeconomic_industry_exposure_component_summary.csv
│       ├── geoeconomic_industry_exposure_source_summary.csv
│       ├── household_vulnerability_scores.csv
│       ├── household_vulnerability_latest.csv
│       ├── household_vulnerability_component_summary.csv
│       ├── household_vulnerability_source_summary.csv
│       ├── local_resilience_scores.csv
│       ├── local_resilience_latest.csv
│       ├── local_resilience_component_summary.csv
│       ├── composite_risk_score.csv
│       ├── composite_risk_score_latest.csv
│       ├── composite_risk_component_summary.csv
│       ├── scenario_forecast_summary.csv
│       ├── change_detection_summary.csv
│       ├── sensitivity_analysis_results.csv
│       ├── sensitivity_analysis_summary.csv
│       ├── risk_threshold_breaches.csv
│       └── risk_threshold_breach_summary.csv
├── outputs/
│   ├── charts/
│   │   ├── composite_risk_score.png
│   │   ├── scenario_comparison.png
│   │   ├── construction_shock_trend.png
│   │   ├── construction_shock_categories.png
│   │   ├── growth_pressure_trend.png
│   │   ├── local_resilience_offset.png
│   │   ├── sensitivity_analysis.png
│   │   └── risk_threshold_breaches.png
│   ├── reports/
│   │   └── gallatin_sumner_geoeconomic_growth_risk_report.pdf
│   ├── snapshots/
│   │   ├── latest_run_snapshot.json
│   │   └── previous_run_snapshot.json
│   └── tables/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── fred_data.py
│   ├── construction_shock.py
│   ├── growth_pressure.py
│   ├── housing_affordability.py
│   ├── infrastructure_strain.py
│   ├── development_friction.py
│   ├── geoeconomic_industry_exposure.py
│   ├── household_vulnerability.py
│   ├── local_resilience.py
│   ├── composite_score.py
│   ├── scenario_forecast.py
│   ├── change_detection.py
│   ├── sensitivity_analysis.py
│   ├── risk_threshold_breaches.py
│   ├── visualization.py
│   ├── report_generator.py
│   └── main.py
├── .env
├── README.md
└── requirements.txt
```

## Installation

```powershell
git clone https://github.com/jasonrkeen/gallatin-sumner-geoeconomic-growth-risk-monitor.git
cd gallatin-sumner-geoeconomic-growth-risk-monitor

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Requirements

```text
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
requests>=2.31.0
python-dotenv>=1.0.0
reportlab>=4.0.0
```

## Environment Variables

The housing affordability, household vulnerability, infrastructure strain, and geoeconomic industry exposure modules use the Census ACS API. Add a `.env` file in the project root:

```text
CENSUS_API_KEY=your_key_here
```

Do not commit your `.env` file to GitHub.

A `.gitignore` entry should include:

```text
.env
.venv/
__pycache__/
data/raw/*.xlsx
outputs/reports/*.pdf
outputs/snapshots/*.json
```

## Usage

Run the full pipeline:

```powershell
python -m src.main
```

This will:

1. Print the project overview
2. Download FRED macro and shock-proxy data
3. Build the Construction Shock Exposure Score
4. Build the Growth Pressure Score
5. Build the Housing Affordability Pressure Score
6. Build the Infrastructure Strain Score
7. Build the Development Friction Score
8. Build the Geoeconomic Industry Exposure Score
9. Build the Household Vulnerability Score
10. Build the Local Resilience Offset
11. Build the Composite Geoeconomic Growth Risk Score
12. Build Scenario Forecasts
13. Run Change Detection
14. Run Sensitivity Analysis
15. Run the Risk Threshold Breach Monitor
16. Generate charts
17. Generate the final PDF report

You can also run modules individually:

```powershell
python -m src.fred_data
python -m src.construction_shock
python -m src.growth_pressure
python -m src.housing_affordability
python -m src.infrastructure_strain
python -m src.development_friction
python -m src.geoeconomic_industry_exposure
python -m src.household_vulnerability
python -m src.local_resilience
python -m src.composite_score
python -m src.scenario_forecast
python -m src.change_detection
python -m src.sensitivity_analysis
python -m src.risk_threshold_breaches
python -m src.visualization
python -m src.report_generator
```

## Outputs

### Processed Data

Important outputs include:

| File | Description |
|---|---|
| `fred_series_long.csv` | Long-format FRED data |
| `fred_series_wide.csv` | Wide-format FRED data |
| `fred_latest_values.csv` | Latest value summary for FRED indicators |
| `fred_failed_downloads.csv` | Optional failed-download log if one or more FRED series fail |
| `construction_shock_scores.csv` | Monthly construction shock scores |
| `construction_shock_latest.csv` | Latest construction shock score |
| `construction_shock_component_summary.csv` | Latest construction shock component detail |
| `construction_shock_category_summary.csv` | Construction shock category scores |
| `growth_pressure_scores.csv` | Annual growth pressure scores |
| `growth_pressure_latest.csv` | Latest growth pressure score |
| `growth_pressure_source_summary.csv` | Local growth-source signal summary |
| `housing_affordability_scores.csv` | ACS-based housing affordability pressure scores |
| `housing_affordability_latest.csv` | Latest county housing affordability pressure score |
| `housing_affordability_component_summary.csv` | Latest housing affordability component scores |
| `infrastructure_strain_scores.csv` | ACS commute and local-note infrastructure strain scores |
| `infrastructure_strain_latest.csv` | Latest county infrastructure strain score |
| `infrastructure_strain_component_summary.csv` | Latest infrastructure component scores |
| `infrastructure_strain_source_summary.csv` | Local infrastructure source signal summary |
| `development_friction_scores.csv` | Source-note based development friction score |
| `development_friction_latest.csv` | Latest development friction score |
| `development_friction_component_summary.csv` | Latest development friction component scores |
| `development_friction_source_summary.csv` | Development friction source signal summary |
| `geoeconomic_industry_exposure_scores.csv` | ACS and local-source industry-exposure scores |
| `geoeconomic_industry_exposure_latest.csv` | Latest geoeconomic industry exposure score |
| `geoeconomic_industry_exposure_component_summary.csv` | Latest geoeconomic industry component scores |
| `geoeconomic_industry_exposure_source_summary.csv` | Industry-exposure local-source signal summary |
| `household_vulnerability_scores.csv` | ACS and local-source household vulnerability scores |
| `household_vulnerability_latest.csv` | Latest household vulnerability score |
| `household_vulnerability_component_summary.csv` | Latest household vulnerability component scores |
| `household_vulnerability_source_summary.csv` | Household vulnerability local-source signal summary |
| `local_resilience_scores.csv` | Local resilience offset scores |
| `local_resilience_latest.csv` | Latest local resilience offset |
| `local_resilience_component_summary.csv` | Local resilience evidence detail |
| `composite_risk_score_latest.csv` | Latest composite and adjusted risk score |
| `composite_risk_component_summary.csv` | Component-level composite model summary |
| `scenario_forecast_summary.csv` | Scenario forecast summary table |
| `change_detection_summary.csv` | Current-vs-prior run comparison |
| `sensitivity_analysis_results.csv` | Alternative weighting-case results |
| `sensitivity_analysis_summary.csv` | Sensitivity stability summary |
| `risk_threshold_breaches.csv` | Threshold-breach table |
| `risk_threshold_breach_summary.csv` | Alert-level summary |

### Charts

Charts are saved to:

```text
outputs/charts/
```

Current charts include:

- composite risk score and resilience adjustment
- scenario comparison
- construction shock trend
- construction shock category breakdown
- growth pressure trend
- local resilience offset components
- sensitivity analysis
- risk threshold breach monitor

### Report

The final PDF report is saved to:

```text
outputs/reports/gallatin_sumner_geoeconomic_growth_risk_report.pdf
```

The report includes:

- executive summary
- key findings
- latest module scores
- how to read the results
- metric measurement guide
- factual interpretation and validation notes
- change detection summary
- sensitivity analysis
- risk threshold breach monitor
- component and scenario tables
- chart explanations
- module detail sections
- methodology
- model caveats and next improvements
- curated local source notes

## Methodology Notes

### Construction Shock Exposure

The construction shock module uses FRED indicators related to construction materials, lumber, cement, steel, diesel, gasoline, crude oil, mortgage rates, and the federal funds rate. Most price/index indicators are scored using year-over-year changes. Interest-rate indicators are scored using level-based normalization.

### Growth Pressure

The growth pressure module uses Sumner County real GDP growth, unemployment conditions, and manually curated local source-note volume related to growth, development, infrastructure, construction, and economic expansion.

### Housing Affordability Pressure

The housing affordability module uses Census ACS 5-year data and mortgage-rate inputs to estimate median household income, median home value, median gross rent, home-value-to-income ratio, rent-to-income ratio, renter cost-burden share, owner cost-burden share, and mortgage-rate pressure.

The default composite-model housing input uses the latest Sumner County result because county-level ACS data is more stable and aligns with the broader project geography.

### Infrastructure Strain

The infrastructure strain module uses Census ACS commute and transportation indicators plus curated local source notes related to roads, public works, utilities, stormwater, transportation, and development pressure.

The module estimates infrastructure pressure from mean commute time, long-commute share, vehicle dependence, local infrastructure note volume, and public works / road pressure signals.

### Development Friction

The development friction module uses curated local source notes to estimate local policy and development-process pressure. It scores zoning-code update signals, planning/permitting signals, development pipeline pressure, public notice / agenda activity, and source confidence.

This first version is intentionally conservative. It converts qualitative local-source evidence into a structured signal, but future versions can strengthen the module by pulling planning commission agendas, permit records, rezoning cases, meeting minutes, and development approval data.

### Geoeconomic Industry Exposure

The geoeconomic industry exposure module estimates exposure to manufacturing, logistics, construction, retail, and trade-sensitive growth channels using employment-exposure indicators and curated local source evidence.

Counts and percentages should be interpreted within the module's ACS variable definitions and validated before use as official employment totals.

### Household Vulnerability

The household vulnerability module uses Census ACS poverty, income, unemployment, housing cost burden, commute indicators, and curated local source notes related to affordability, vulnerable residents, transportation cost exposure, and social-service capacity.

### Local Resilience Offset

The local resilience module uses curated local notes and keyword mapping to score utility coordination, public works capacity, stormwater and flood mitigation, public safety response, and capital project execution.

The resilience score does not measure risk directly. It measures local capacity that may partially offset risk.

### Composite Risk Score

The composite model now combines seven live components and no placeholder components:

```text
7 live / 0 placeholder
```

Component scores are clearly identified in:

```text
data/processed/composite_risk_component_summary.csv
```

### Scenario Forecasts

The scenario forecast model applies multiplier assumptions from `config.py` to estimate how risk changes under different growth and shock environments.

### Change Detection

The change detection module saves a model-run snapshot and compares the current run against the prior saved snapshot. This helps turn the project from a one-time report into a repeatable risk monitor.

### Sensitivity Analysis

The sensitivity module tests whether the adjusted risk conclusion changes under alternative component-weighting assumptions.

### Risk Threshold Breach Monitor

The breach monitor flags whether key indicators cross configured warning thresholds. It creates an alert-style summary for growth pressure, construction shock, fuel/energy shock, scenario stress, resilience, and model-quality risks.

## Current Limitations

This is a portfolio-style local economic intelligence model, not an official public-sector forecast, public finance assessment, engineering study, or planning analysis.

Known limitations:

- Model scores are normalized monitoring indicators, not probabilities or official public-sector risk ratings
- Source notes are qualitative indicators and should not be treated as official numeric datasets
- Census ACS data is lagged and should be interpreted as a structural local pressure signal, not a real-time market signal
- FRED macro and price series may update at different frequencies, so observation dates should be checked before comparing series
- Geoeconomic industry exposure depends on ACS variable definitions and local-source evidence; counts and percentages should be validated before being treated as official employment totals
- Development friction is currently source-note driven and should later be strengthened with planning commission, rezoning, permitting, agenda, and approval-volume data
- Infrastructure strain is currently based on ACS commute indicators and curated source notes; future versions can add traffic counts, road-capacity datasets, school-capacity data, utility-capacity indicators, and capital-project timelines
- Household vulnerability uses structural ACS indicators and local-source evidence; future versions can add higher-frequency household financial stress, eviction, delinquency, and wage indicators

## Future Enhancements

Potential next upgrades:

| Enhancement | Purpose |
|---|---|
| Streamlit Dashboard | Convert the PDF workflow into an interactive local intelligence dashboard |
| Source Evidence Tracker | Track source age, source type, jurisdiction, confidence, and which model components each source supports |
| Policy Activity Tracker | Convert city/county meeting records, public notices, zoning actions, and planning agendas into a structured policy dataset |
| Forecast Validation | Back-test scenario assumptions and compare model trends against future housing, permit, commute, labor, and industry data |
| Document Center Integration | Use the City of Gallatin Document Center as a repeatable source hub for planning, zoning, infrastructure, and policy evidence |
| Development Friction Upgrade | Add planning commission agendas, rezoning cases, permit volume, approval timelines, and zoning-code update milestones |
| Infrastructure Strain Upgrade | Add traffic counts, road-capacity data, utility-capacity data, school-capacity pressure, and capital-project timelines |

## Suggested Report Interpretation

The model should be interpreted as a local intelligence framework rather than a deterministic forecast. Scores are useful for comparing relative pressure across modules and scenarios, not for predicting exact economic outcomes.

The most important insight is the interaction between local growth pressure, household affordability, infrastructure strain, development friction, household vulnerability, industry exposure, and external cost shocks. Gallatin and Sumner County may continue to benefit from growth, but that growth can become more difficult to absorb if construction costs, fuel prices, interest rates, housing costs, planning friction, or supply-chain disruptions rise at the same time as local development pressure.

## Author

**Jason Keen**  
[LinkedIn](https://www.linkedin.com/in/jason-keen-1887b4218)

## Disclaimer

This project is for research, educational, and portfolio purposes. It uses public data and manually curated source notes. It should not be interpreted as official government analysis, investment advice, legal advice, public finance advice, legal advice, engineering advice, or a substitute for local planning, engineering, public finance, or policy expertise.
