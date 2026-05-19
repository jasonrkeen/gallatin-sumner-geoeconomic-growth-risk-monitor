"""
PDF report generator for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module creates a LinkedIn / portfolio-ready PDF report using ReportLab.

Inputs:
- data/processed/composite_risk_score_latest.csv
- data/processed/scenario_forecast_summary.csv
- data/processed/construction_shock_latest.csv
- data/processed/construction_shock_component_summary.csv
- data/processed/construction_shock_category_summary.csv
- data/processed/growth_pressure_latest.csv
- data/processed/housing_affordability_latest.csv
- data/processed/housing_affordability_component_summary.csv
- data/processed/infrastructure_strain_latest.csv
- data/processed/infrastructure_strain_component_summary.csv
- data/processed/development_friction_latest.csv
- data/processed/development_friction_component_summary.csv
- data/processed/geoeconomic_industry_exposure_latest.csv
- data/processed/geoeconomic_industry_exposure_component_summary.csv
- data/processed/household_vulnerability_latest.csv
- data/processed/household_vulnerability_component_summary.csv
- data/processed/household_vulnerability_source_summary.csv
- data/processed/local_resilience_latest.csv
- data/processed/local_resilience_component_summary.csv
- data/processed/composite_risk_component_summary.csv
- data/processed/change_detection_summary.csv
- data/processed/sensitivity_analysis_results.csv
- data/processed/sensitivity_analysis_summary.csv
- data/processed/risk_threshold_breaches.csv
- data/processed/risk_threshold_breach_summary.csv
- data/raw/local_source_notes.csv
- outputs/charts/*.png

Output:
- outputs/reports/gallatin_sumner_geoeconomic_growth_risk_report.pdf
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.config import (
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    CHARTS_DIR,
    LOCAL_SOURCE_NOTES_FILE,
    PROJECT_NAME,
    PROJECT_SUBTITLE,
    REPORT_FILENAME,
    REPORTS_DIR,
    PROCESSED_DATA_DIR,
)


# ============================================================
# Input files
# ============================================================

COMPOSITE_LATEST_FILE = PROCESSED_DATA_DIR / "composite_risk_score_latest.csv"
SCENARIO_SUMMARY_FILE = PROCESSED_DATA_DIR / "scenario_forecast_summary.csv"

CONSTRUCTION_LATEST_FILE = PROCESSED_DATA_DIR / "construction_shock_latest.csv"
CONSTRUCTION_COMPONENT_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "construction_shock_component_summary.csv"
)
CONSTRUCTION_CATEGORY_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "construction_shock_category_summary.csv"
)

GROWTH_LATEST_FILE = PROCESSED_DATA_DIR / "growth_pressure_latest.csv"

HOUSING_LATEST_FILE = PROCESSED_DATA_DIR / "housing_affordability_latest.csv"
HOUSING_COMPONENT_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "housing_affordability_component_summary.csv"
)

INFRASTRUCTURE_LATEST_FILE = PROCESSED_DATA_DIR / "infrastructure_strain_latest.csv"
INFRASTRUCTURE_COMPONENT_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "infrastructure_strain_component_summary.csv"
)

DEVELOPMENT_FRICTION_LATEST_FILE = (
    PROCESSED_DATA_DIR / "development_friction_latest.csv"
)
DEVELOPMENT_FRICTION_COMPONENT_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "development_friction_component_summary.csv"
)

GEOECONOMIC_INDUSTRY_LATEST_FILE = (
    PROCESSED_DATA_DIR / "geoeconomic_industry_exposure_latest.csv"
)
GEOECONOMIC_INDUSTRY_COMPONENT_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "geoeconomic_industry_exposure_component_summary.csv"
)

HOUSEHOLD_VULNERABILITY_LATEST_FILE = (
    PROCESSED_DATA_DIR / "household_vulnerability_latest.csv"
)
HOUSEHOLD_VULNERABILITY_COMPONENT_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "household_vulnerability_component_summary.csv"
)
HOUSEHOLD_VULNERABILITY_SOURCE_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "household_vulnerability_source_summary.csv"
)

RESILIENCE_LATEST_FILE = PROCESSED_DATA_DIR / "local_resilience_latest.csv"
RESILIENCE_COMPONENT_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "local_resilience_component_summary.csv"
)

COMPOSITE_COMPONENT_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "composite_risk_component_summary.csv"
)

CHANGE_DETECTION_FILE = PROCESSED_DATA_DIR / "change_detection_summary.csv"
SENSITIVITY_RESULTS_FILE = PROCESSED_DATA_DIR / "sensitivity_analysis_results.csv"
SENSITIVITY_SUMMARY_FILE = PROCESSED_DATA_DIR / "sensitivity_analysis_summary.csv"

RISK_THRESHOLD_BREACH_FILE = PROCESSED_DATA_DIR / "risk_threshold_breaches.csv"
RISK_THRESHOLD_BREACH_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "risk_threshold_breach_summary.csv"
)

REPORT_OUTPUT_PATH = REPORTS_DIR / REPORT_FILENAME


# ============================================================
# Chart files
# ============================================================

CHART_FILES = {
    "Composite Risk Score and Resilience Adjustment": CHARTS_DIR / "composite_risk_score.png",
    "Scenario Forecast Comparison": CHARTS_DIR / "scenario_comparison.png",
    "Construction Shock Trend": CHARTS_DIR / "construction_shock_trend.png",
    "Construction Shock Category Breakdown": CHARTS_DIR / "construction_shock_categories.png",
    "Growth Pressure Trend": CHARTS_DIR / "growth_pressure_trend.png",
    "Local Resilience Offset Components": CHARTS_DIR / "local_resilience_offset.png",
    "Sensitivity Analysis": CHARTS_DIR / "sensitivity_analysis.png",
    "Risk Threshold Breach Monitor": CHARTS_DIR / "risk_threshold_breaches.png",
}


# ============================================================
# Helpers
# ============================================================

def read_csv_if_exists(path: Path) -> pd.DataFrame:
    """
    Read a CSV if it exists, otherwise return an empty DataFrame.
    """

    if not path.exists():
        print(f"WARNING: Missing report input file: {path}")
        return pd.DataFrame()

    return pd.read_csv(path)


def safe_value(df: pd.DataFrame, column: str, default="N/A"):
    """
    Safely return a value from the first row of a DataFrame.
    """

    if df.empty or column not in df.columns:
        return default

    value = df.iloc[0][column]

    if pd.isna(value):
        return default

    return value


def parse_bool(value) -> bool:
    """
    Parse bool-like values safely from booleans, strings, or numbers.
    """

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def fmt_score(value) -> str:
    """
    Format score values for report display.
    """

    try:
        return f"{float(value):.1f}"
    except Exception:
        return "N/A"


def fmt_delta(value) -> str:
    """
    Format scenario/change delta values.
    """

    try:
        return f"{float(value):+.1f}"
    except Exception:
        return "N/A"


def is_missing_display_value(value) -> bool:
    """
    Return True for None, NaN, blank strings, and stringified NaN values.
    """

    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except Exception:
        pass

    return str(value).strip().lower() in {"", "nan", "+nan", "-nan", "none", "nat"}


def fmt_display(value) -> str:
    """
    Display mixed numeric/string values safely.
    """

    if is_missing_display_value(value):
        return "N/A"

    return str(value)


def fmt_change_delta(value) -> str:
    """
    Format change-detection deltas while avoiding +nan display.
    """

    if is_missing_display_value(value):
        return "N/A"

    return fmt_delta(value)


def fmt_pct(value) -> str:
    """
    Format percentage values for report display.

    If the value is stored as 0.714, this displays 71.4%.
    If the value is already 71.4, this displays 71.4%.
    """

    try:
        value = float(value)
        if abs(value) <= 1:
            value = value * 100
        return f"{value:.1f}%"
    except Exception:
        return "N/A"


def fmt_currency(value) -> str:
    """
    Format dollar values for report display.
    """

    try:
        value = float(value)
        return f"${value:,.0f}"
    except Exception:
        return "N/A"


def fmt_ratio(value) -> str:
    """
    Format ratio values for report display.
    """

    try:
        return f"{float(value):.2f}x"
    except Exception:
        return "N/A"


def clean_label(value: str) -> str:
    """
    Convert snake_case labels to title case for tables.
    """

    return str(value).replace("_", " ").title()


def make_styles():
    """
    Create ReportLab paragraph styles.
    """

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#444444"),
            spaceAfter=16,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor("#1F2937"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubHeading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=6,
            textColor=colors.HexColor("#1F2937"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallText",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#555555"),
        )
    )

    return styles


def make_table(data, col_widths=None, font_size=8):
    """
    Build a styled report table.
    """

    table = Table(data, colWidths=col_widths, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("LEADING", (0, 0), (-1, -1), font_size + 2),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCCCCC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    return table


def as_paragraph(value, style, bold: bool = False) -> Paragraph:
    """
    Convert a table cell value into a ReportLab Paragraph so long text wraps cleanly.
    """

    text = "" if value is None else str(value)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    if bold:
        text = f"<b>{text}</b>"

    return Paragraph(text, style)


def make_wrapped_table(
    data,
    styles,
    col_widths=None,
    font_size: float = 7.0,
    header_font_size: float | None = None,
    body_style_name: str = "TableCell",
    header_style_name: str = "TableHeader",
):
    """
    Build a styled table that wraps long text instead of letting it crowd columns.

    Use this for explanatory tables, long metric labels, narrative columns, and any
    table with sentence-length content.
    """

    header_font_size = header_font_size or font_size

    if body_style_name not in styles:
        styles.add(
            ParagraphStyle(
                name=body_style_name,
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=font_size,
                leading=font_size + 1.2,
                spaceAfter=0,
                wordWrap="CJK",
            )
        )

    if header_style_name not in styles:
        styles.add(
            ParagraphStyle(
                name=header_style_name,
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=header_font_size,
                leading=header_font_size + 1.2,
                textColor=colors.white,
                spaceAfter=0,
                wordWrap="CJK",
            )
        )

    wrapped_data = []

    for row_idx, row in enumerate(data):
        row_style = styles[header_style_name] if row_idx == 0 else styles[body_style_name]
        wrapped_data.append(
            [
                as_paragraph(cell, row_style)
                for cell in row
            ]
        )

    table = Table(wrapped_data, colWidths=col_widths, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCCCCC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    return table


def add_image_if_exists(story, image_path: Path, title: str, styles, width=6.15 * inch):
    """
    Add a chart image if it exists, followed by a plain-English explanation.
    """

    explanation = CHART_EXPLANATIONS.get(title)

    if not image_path.exists():
        story.append(
            Paragraph(
                f"<b>{title}</b>: Chart not found at {image_path}",
                styles["SmallText"],
            )
        )
        if explanation:
            story.append(Paragraph(explanation, styles["SmallText"]))
        story.append(Spacer(1, 0.1 * inch))
        return

    img = Image(str(image_path))
    img._restrictSize(width, 3.75 * inch)

    chart_elements = [
        Paragraph(title, styles["SubHeading"]),
        img,
    ]

    if explanation:
        chart_elements.append(Paragraph(explanation, styles["SmallText"]))

    chart_elements.append(Spacer(1, 0.18 * inch))

    story.append(KeepTogether(chart_elements))


def add_page_number(canvas, doc):
    """
    Add footer with page number and author.
    """

    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))

    footer_text = f"{AUTHOR_NAME} | {AUTHOR_EMAIL}"
    page_text = f"Page {doc.page}"

    canvas.drawString(0.6 * inch, 0.35 * inch, footer_text)
    canvas.drawRightString(7.9 * inch, 0.35 * inch, page_text)

    canvas.restoreState()


# ============================================================
# Interpretation guides
# ============================================================

CHART_EXPLANATIONS = {
    "Composite Risk Score and Resilience Adjustment": (
        "How to read this chart: the first bar shows the gross composite risk score before "
        "any offset, the middle bar shows the capped resilience credit applied, and the "
        "final bar shows the adjusted risk score. If the adjusted score remains elevated "
        "after the resilience credit, local capacity is helpful but not enough to eliminate "
        "the underlying growth, affordability, infrastructure, and industry-exposure pressure."
    ),
    "Scenario Forecast Comparison": (
        "How to read this chart: each bar is a stress-case estimate of adjusted risk under "
        "different assumptions. The label in parentheses shows the change versus the current "
        "adjusted baseline. The highest bar identifies the scenario that would create the "
        "most pressure on the local system."
    ),
    "Construction Shock Trend": (
        "How to read this chart: the line tracks construction-cost shock exposure through "
        "time, while the moving averages smooth short-term noise. Rising momentum indicates "
        "that materials, fuel, or financing conditions are becoming less favorable for local "
        "projects and development execution."
    ),
    "Construction Shock Category Breakdown": (
        "How to read this chart: the bars separate the construction-shock score into materials, "
        "fuel and energy, and financing conditions. This helps identify whether current pressure "
        "is being driven by input costs, energy/logistics costs, or interest-rate conditions."
    ),
    "Growth Pressure Trend": (
        "How to read this chart: the trend shows how local growth pressure has evolved over "
        "time. High or rising values suggest stronger absorption risk, meaning population, "
        "labor, development, and infrastructure demand may be moving faster than local systems "
        "can comfortably support."
    ),
    "Local Resilience Offset Components": (
        "How to read this chart: each bar shows a resilience evidence tier for a local capacity "
        "channel. Higher values indicate stronger evidence of response capacity, but these scores "
        "are converted into a capped credit so resilience reduces risk without overpowering the "
        "core risk signals."
    ),
    "Sensitivity Analysis": (
        "How to read this chart: each bar recalculates adjusted risk under a different weighting "
        "case. If all bars remain in the same broad risk band, the conclusion is stable and not "
        "overly dependent on one weighting framework."
    ),
    "Risk Threshold Breach Monitor": (
        "How to read this chart: each bar shows how far an active metric is beyond its configured "
        "warning threshold. Longer bars indicate larger threshold breaches and therefore clearer "
        "monitoring priorities."
    ),
}


def score_band_text(score) -> str:
    """
    Convert a numeric score into an interpretation band for explanatory text.
    """

    try:
        score = float(score)
    except Exception:
        return "N/A"

    if score < 25:
        return "Low Risk"
    if score < 50:
        return "Moderate Risk"
    if score < 75:
        return "Elevated Risk"
    return "High Risk"


def add_results_reading_guide(story, styles, composite_df, scenario_df, breach_summary_df):
    """
    Explain how to read the model outputs and final results.
    """

    story.append(Paragraph("How to Read the Results", styles["SectionHeading"]))

    adjusted_score = safe_value(composite_df, "adjusted_geoeconomic_growth_risk_score")
    adjusted_signal = safe_value(composite_df, "adjusted_geoeconomic_growth_risk_signal")
    composite_score = safe_value(composite_df, "composite_risk_score")
    resilience_credit = safe_value(composite_df, "resilience_credit_applied")
    live_count = safe_value(composite_df, "live_components_used")
    placeholder_count = safe_value(composite_df, "placeholder_components_used")
    placeholder_share = safe_value(composite_df, "placeholder_share")
    model_maturity = safe_value(composite_df, "model_maturity_level")
    alert_level = safe_value(breach_summary_df, "alert_level", default="N/A")

    highest_scenario = "N/A"
    highest_scenario_score = "N/A"
    highest_scenario_delta = "N/A"

    if not scenario_df.empty and "scenario_adjusted_risk_score" in scenario_df.columns:
        top = scenario_df.sort_values("scenario_adjusted_risk_score", ascending=False).iloc[0]
        highest_scenario = top.get("scenario_name", "N/A")
        highest_scenario_score = fmt_score(top.get("scenario_adjusted_risk_score", "N/A"))
        highest_scenario_delta = fmt_delta(top.get("scenario_delta_vs_adjusted_baseline", "N/A"))

    story.append(
        Paragraph(
            "The model uses a 0-100 scoring framework. Higher values indicate more pressure, "
            "not a guaranteed outcome. The scores should be read as an intelligence dashboard: "
            "they show where local growth, affordability, infrastructure, development, industry, "
            "and household stress signals are concentrated and how those signals move over time.",
            styles["BodyTextCustom"],
        )
    )

    scale_data = [
        ["Score Range", "Risk Band", "How to Interpret"],
        ["0-24.9", "Low Risk", "Limited current pressure; monitor for early movement."],
        ["25.0-49.9", "Moderate Risk", "Manageable pressure; useful as a watchlist signal."],
        ["50.0-74.9", "Elevated Risk", "Meaningful pressure; deserves regular monitoring and explanation."],
        ["75.0-100", "High Risk", "Material pressure; likely a priority risk channel or policy focus area."],
    ]

    story.append(
        make_wrapped_table(
            scale_data,
            styles,
            col_widths=[0.85 * inch, 1.05 * inch, 4.5 * inch],
            font_size=6.9,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    interpretation_data = [
        ["Result", "Current Reading", "How to Use It"],
        [
            "Composite Risk Score",
            f"{fmt_score(composite_score)} / {score_band_text(composite_score)}",
            "Read this as the gross local risk pressure before resilience is applied.",
        ],
        [
            "Adjusted Risk Score",
            f"{fmt_score(adjusted_score)} / {adjusted_signal}",
            "Use this as the headline result because it reflects both risk pressure and the capped local resilience credit.",
        ],
        [
            "Resilience Credit",
            fmt_score(resilience_credit),
            "Shows how much local response capacity reduced the gross composite score. It is capped so it cannot erase high underlying risk.",
        ],
        [
            "Highest-Risk Scenario",
            f"{highest_scenario} ({highest_scenario_score}, {highest_scenario_delta})",
            "Identifies the stress case that would most increase local risk relative to the adjusted baseline.",
        ],
        [
            "Breach Monitor",
            str(alert_level),
            "Summarizes whether any metrics crossed configured warning thresholds.",
        ],
        [
            "Model Maturity",
            f"{model_maturity}; {live_count} live / {placeholder_count} placeholder; {fmt_pct(placeholder_share)} placeholder share",
            "Shows whether the model is driven by live data modules or placeholder assumptions.",
        ],
    ]

    story.append(
        make_wrapped_table(
            interpretation_data,
            styles,
            col_widths=[1.35 * inch, 1.75 * inch, 3.3 * inch],
            font_size=6.5,
        )
    )

    story.append(
        Paragraph(
            "A practical reading of the report should start with the adjusted risk score, "
            "then move to the component table to identify which modules are driving the result, "
            "then review scenarios, sensitivity analysis, and threshold breaches to determine "
            "whether the conclusion is robust or dependent on one assumption.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.15 * inch))


def add_metric_measurement_guide(story, styles):
    """
    Explain each metric, how it is measured, and how it can be used.

    The guide is split into smaller tables so the final PDF remains readable.
    """

    story.append(Paragraph("Metric Measurement Guide", styles["SectionHeading"]))

    story.append(
        Paragraph(
            "This section explains the main metrics used in the report. Each metric is designed "
            "to translate raw economic, demographic, source-note, and market data into a repeatable "
            "0-100 monitoring signal. The scores are decision-support indicators, not probabilities "
            "or official forecasts.",
            styles["BodyTextCustom"],
        )
    )

    core_results = [
        ["Metric", "What It Measures", "How It Can Be Used"],
        [
            "Composite Risk Score",
            "Weighted average of the seven live risk components before resilience adjustment.",
            "Use as the broadest measure of local geoeconomic growth pressure.",
        ],
        [
            "Adjusted Risk Score",
            "Composite score minus a capped resilience credit.",
            "Use as the headline risk reading because it includes local response capacity.",
        ],
        [
            "Local Resilience Offset",
            "Evidence of utility coordination, public works capacity, flood mitigation, public safety response, and capital execution.",
            "Use to measure local response capacity, but only as a capped risk reducer.",
        ],
    ]

    risk_components = [
        ["Metric", "What It Measures", "How It Can Be Used"],
        [
            "Growth Pressure",
            "Local growth, labor-market, and source-note signals tied to development demand.",
            "Use to monitor whether growth is becoming difficult to absorb.",
        ],
        [
            "Housing Affordability",
            "ACS income, home value, rent, cost-burden, and mortgage-rate pressure.",
            "Use to assess whether households can absorb local housing and financing costs.",
        ],
        [
            "Construction Shock Exposure",
            "FRED-based materials, fuel/energy, and financing cost pressure.",
            "Use to monitor external cost shocks that can delay or reprice local projects.",
        ],
        [
            "Infrastructure Strain",
            "ACS commute patterns, vehicle dependence, long-commute exposure, and infrastructure source notes.",
            "Use to assess pressure on roads, transportation systems, utilities, and public works capacity.",
        ],
        [
            "Development Friction",
            "Local source evidence on zoning, planning, permitting, development pipeline, and public notices.",
            "Use to monitor whether policy, process, or development complexity is increasing.",
        ],
        [
            "Geoeconomic Industry Exposure",
            "Employment-exposure indicators plus local evidence for manufacturing, logistics, construction, retail, and trade-sensitive sectors.",
            "Use to understand how external shocks could transmit through the local economic base.",
        ],
        [
            "Household Vulnerability",
            "ACS poverty, low-income exposure, unemployment, housing burden, commute burden, and local vulnerability notes.",
            "Use to identify whether households may be more sensitive to inflation, housing, job, or transportation shocks.",
        ],
    ]

    monitoring_layers = [
        ["Metric", "What It Measures", "How It Can Be Used"],
        [
            "Scenario Scores",
            "Stress-test outputs under managed growth, overheated growth, construction shock, and rezoning constraint cases.",
            "Use to compare which future condition creates the greatest local risk pressure.",
        ],
        [
            "Sensitivity Analysis",
            "Alternative weighting cases that emphasize different risk channels.",
            "Use to test whether the report conclusion remains stable under different assumptions.",
        ],
        [
            "Risk Threshold Breaches",
            "Configured warning thresholds for key risk, scenario, resilience, and model-quality metrics.",
            "Use as an alert layer to prioritize which metrics need attention first.",
        ],
        [
            "Change Detection",
            "Current model values compared with the prior saved run snapshot.",
            "Use to monitor whether risk pressure is improving, worsening, or stable over time.",
        ],
    ]

    for title, table_data in [
        ("Core Result Metrics", core_results),
        ("Risk Component Metrics", risk_components),
        ("Monitoring and Validation Metrics", monitoring_layers),
    ]:
        story.append(Paragraph(title, styles["SubHeading"]))
        story.append(
            make_wrapped_table(
                table_data,
                styles,
                col_widths=[1.35 * inch, 2.55 * inch, 2.50 * inch],
                font_size=5.9,
                header_font_size=6.1,
            )
        )
        story.append(Spacer(1, 0.08 * inch))

    story.append(
        Paragraph(
            "The metric values should not be interpreted as probabilities. They are normalized "
            "monitoring scores intended to support comparison across risk channels, identify trend "
            "changes, and guide where deeper local research or policy review may be needed.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.15 * inch))


def add_fact_checking_and_validation_notes(story, styles):
    """
    Add factual interpretation and validation notes for finalized portfolio use.
    """

    story.append(Paragraph("Factual Interpretation and Validation Notes", styles["SectionHeading"]))

    story.append(
        Paragraph(
            "This report should be read as a repeatable local intelligence model rather than an official "
            "government forecast or a deterministic prediction. The scores should be interpreted as "
            "portfolio-style intelligence indicators, not official public-sector risk ratings. The analysis "
            "combines public economic data, ACS demographic indicators, FRED market indicators, and curated "
            "local source notes. Where the report uses source-note evidence, those notes strengthen local "
            "context and confidence but do not replace official numeric datasets.",
            styles["BodyTextCustom"],
        )
    )

    validation_data = [
        ["Area", "What to Check", "Why It Matters"],
        [
            "ACS Indicators",
            "Confirm geography, year, dataset, variable definitions, and whether values are counts, percentages, or normalized model inputs.",
            "Prevents unit errors and avoids overstating demographic or employment totals.",
        ],
        [
            "FRED Indicators",
            "Confirm latest observation dates and whether a series is daily, weekly, monthly, or annual.",
            "Prevents comparing stale or differently timed macro indicators as if they were equivalent.",
        ],
        [
            "Local Source Notes",
            "Confirm source date, jurisdiction, topic, and risk channel before treating a note as evidence.",
            "Keeps qualitative signals grounded in documented local sources.",
        ],
        [
            "Composite Scores",
            "Read scores as normalized monitoring indicators, not probabilities or official risk ratings.",
            "Prevents overclaiming what the model can measure.",
        ],
        [
            "Scenario Results",
            "Treat scenario scores as assumption-based stress tests, not forecasts.",
            "Keeps scenario analysis framed as decision support rather than prediction.",
        ],
    ]

    story.append(
        make_wrapped_table(
            validation_data,
            styles,
            col_widths=[1.25 * inch, 2.75 * inch, 2.40 * inch],
            font_size=5.9,
            header_font_size=6.1,
        )
    )

    story.append(
        Paragraph(
            "Recommended proofread pass before publication: verify that every numeric value has a clear source, "
            "that source-note claims are described as qualitative evidence, and that all forward-looking language "
            "uses terms such as could, may, scenario, pressure, or exposure rather than certainty.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.15 * inch))


def add_component_reading_notes(story, styles):
    """
    Add brief notes explaining how to read the component and scenario pages.
    """

    story.append(Paragraph("How to Read the Component and Scenario Tables", styles["SectionHeading"]))

    notes_data = [
        ["Table", "How to Read It"],
        [
            "Composite Risk Component Summary",
            "Focus first on components above 75, then components between 50 and 75. High components show the strongest current pressure channels.",
        ],
        [
            "Component Weight",
            "The weight shows how much each module contributes to the composite score. A high score with a high weight has more impact on the headline result.",
        ],
        [
            "Signal",
            "The signal converts a numeric score into a readable risk band: Low, Moderate, Elevated, or High.",
        ],
        [
            "Status",
            "Live means the component is driven by a dedicated module or dataset. Placeholder would mean a temporary assumption, but the current model has no placeholder components.",
        ],
        [
            "Scenario Delta",
            "Positive delta means the scenario increases risk versus the adjusted baseline. Negative delta means the scenario reduces risk versus the adjusted baseline.",
        ],
        [
            "Primary Risk Driver",
            "This field explains which local channel is most responsible for each scenario result.",
        ],
    ]

    story.append(
        make_wrapped_table(
            notes_data,
            styles,
            col_widths=[1.75 * inch, 4.65 * inch],
            font_size=6.6,
        )
    )
    story.append(Spacer(1, 0.15 * inch))


def add_chart_interpretation_intro(story, styles):
    """
    Add an overview paragraph before the chart section.
    """

    story.append(Paragraph("How to Read the Charts", styles["SectionHeading"]))
    story.append(
        Paragraph(
            "The charts translate the model outputs into a visual monitoring layer. Read each "
            "chart from left to right or top to bottom, then compare the chart signal with the "
            "numeric tables. The most useful pattern is not a single chart value, but whether "
            "multiple charts point to the same risk channel: growth absorption, affordability, "
            "infrastructure strain, cost shocks, planning friction, or resilience capacity.",
            styles["BodyTextCustom"],
        )
    )
    story.append(Spacer(1, 0.08 * inch))


# ============================================================
# Report sections
# ============================================================

def add_title_section(story, styles):
    """
    Add report title and subtitle.
    """

    story.append(Paragraph(PROJECT_NAME, styles["ReportTitle"]))
    story.append(Paragraph(PROJECT_SUBTITLE, styles["ReportSubtitle"]))
    story.append(
        Paragraph(
            f"Prepared by {AUTHOR_NAME} | {AUTHOR_EMAIL}<br/>"
            f"Generated: {datetime.today().strftime('%B %d, %Y')}",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))


def add_executive_summary(story, styles, composite_df, scenario_df):
    """
    Add executive summary.
    """

    adjusted_score = safe_value(
        composite_df,
        "adjusted_geoeconomic_growth_risk_score",
    )
    adjusted_signal = safe_value(
        composite_df,
        "adjusted_geoeconomic_growth_risk_signal",
    )
    composite_score = safe_value(composite_df, "composite_risk_score")
    resilience_offset = safe_value(composite_df, "local_resilience_offset")
    resilience_credit = safe_value(composite_df, "resilience_credit_applied")
    model_maturity = safe_value(composite_df, "model_maturity_level")
    data_quality = safe_value(composite_df, "data_quality_flag")
    placeholder_share = safe_value(composite_df, "placeholder_share")
    placeholder_count = safe_value(composite_df, "placeholder_components_used")
    live_count = safe_value(composite_df, "live_components_used")

    highest_scenario = "N/A"
    highest_scenario_score = "N/A"
    highest_scenario_delta = "N/A"

    if not scenario_df.empty and "scenario_adjusted_risk_score" in scenario_df.columns:
        top = scenario_df.sort_values("scenario_adjusted_risk_score", ascending=False).iloc[0]
        highest_scenario = top.get("scenario_name", "N/A")
        highest_scenario_score = fmt_score(top.get("scenario_adjusted_risk_score", "N/A"))
        highest_scenario_delta = fmt_delta(
            top.get("scenario_delta_vs_adjusted_baseline", "N/A")
        )

    story.append(Paragraph("Executive Summary", styles["SectionHeading"]))

    story.append(
        Paragraph(
            "This report develops a local economic intelligence model for Gallatin "
            "and Sumner County, Tennessee. The model evaluates whether rapid local "
            "growth could become more fragile if development pressure intersects "
            "with geopolitical or macroeconomic shocks affecting construction costs, "
            "fuel prices, financing costs, logistics costs, housing affordability, "
            "infrastructure strain, household vulnerability, industry exposure, and "
            "supply chains.",
            styles["BodyTextCustom"],
        )
    )

    story.append(
        Paragraph(
            "This version is a fully data-driven local risk monitor. Growth pressure, "
            "construction shock exposure, housing affordability pressure, infrastructure "
            "strain, development friction, geoeconomic industry exposure, household "
            "vulnerability, and local resilience are all active model modules. No "
            "composite risk component is currently treated as a placeholder.",
            styles["BodyTextCustom"],
        )
    )

    story.append(
        Paragraph(
            "Because the adjusted score remains in the Elevated Risk band even after "
            "the resilience credit, the model suggests that local resilience capacity "
            "helps reduce risk but does not fully offset growth, infrastructure, "
            "housing, development, and industry-exposure pressure.",
            styles["BodyTextCustom"],
        )
    )

    story.append(
        Paragraph(
            "The Overheated Growth scenario matters because it tests whether rapid "
            "development could outpace housing affordability, road capacity, utilities, "
            "planning capacity, and public-service absorption.",
            styles["BodyTextCustom"],
        )
    )

    summary_data = [
        ["Metric", "Latest Value"],
        ["Composite Risk Score", fmt_score(composite_score)],
        ["Local Resilience Offset", fmt_score(resilience_offset)],
        ["Resilience Credit Applied", fmt_score(resilience_credit)],
        ["Adjusted Geoeconomic Growth Risk Score", fmt_score(adjusted_score)],
        ["Adjusted Risk Signal", str(adjusted_signal)],
        ["Highest-Risk Scenario", str(highest_scenario)],
        ["Highest-Risk Scenario Score", str(highest_scenario_score)],
        ["Highest-Risk Scenario Delta vs. Baseline", str(highest_scenario_delta)],
        ["Model Maturity", str(model_maturity)],
        ["Data Quality Flag", str(data_quality)],
        ["Live / Placeholder Components", f"{live_count} live / {placeholder_count} placeholder"],
        ["Placeholder Share", fmt_pct(placeholder_share)],
    ]

    story.append(make_table(summary_data, col_widths=[3.25 * inch, 3.15 * inch], font_size=8.0))
    story.append(Spacer(1, 0.15 * inch))


def add_key_findings(
    story,
    styles,
    composite_df,
    scenario_df,
    construction_df,
    growth_df,
    housing_df,
    infrastructure_df,
    development_df,
    industry_df,
    household_df,
    resilience_df,
):
    """
    Add key findings based on latest model outputs.
    """

    story.append(Paragraph("Key Findings", styles["SectionHeading"]))

    adjusted_score = fmt_score(
        safe_value(composite_df, "adjusted_geoeconomic_growth_risk_score")
    )
    composite_score = fmt_score(safe_value(composite_df, "composite_risk_score"))
    resilience_credit = fmt_score(safe_value(composite_df, "resilience_credit_applied"))

    growth_score = fmt_score(safe_value(growth_df, "growth_pressure_score"))

    housing_score = fmt_score(
        safe_value(housing_df, "housing_affordability_pressure_score")
    )
    housing_signal = safe_value(
        housing_df,
        "housing_affordability_pressure_signal",
        default="N/A",
    )

    infrastructure_score = fmt_score(
        safe_value(infrastructure_df, "infrastructure_strain_score")
    )
    infrastructure_signal = safe_value(
        infrastructure_df,
        "infrastructure_strain_signal",
        default="N/A",
    )

    development_score = fmt_score(
        safe_value(development_df, "development_friction_score")
    )
    development_signal = safe_value(
        development_df,
        "development_friction_signal",
        default="N/A",
    )

    industry_score = fmt_score(
        safe_value(industry_df, "geoeconomic_industry_exposure_score")
    )
    industry_signal = safe_value(
        industry_df,
        "geoeconomic_industry_exposure_signal",
        default="N/A",
    )

    household_score = fmt_score(
        safe_value(household_df, "household_vulnerability_score")
    )
    household_signal = safe_value(
        household_df,
        "household_vulnerability_signal",
        default="N/A",
    )

    construction_score = fmt_score(safe_value(construction_df, "construction_shock_score"))
    momentum_signal = safe_value(
        construction_df,
        "construction_shock_momentum_signal",
        default="N/A",
    )

    resilience_confidence = safe_value(
        resilience_df,
        "local_resilience_confidence",
        default="N/A",
    )

    highest_scenario = "N/A"
    highest_scenario_score = "N/A"

    if not scenario_df.empty and "scenario_adjusted_risk_score" in scenario_df.columns:
        top = scenario_df.sort_values("scenario_adjusted_risk_score", ascending=False).iloc[0]
        highest_scenario = top.get("scenario_name", "N/A")
        highest_scenario_score = fmt_score(top.get("scenario_adjusted_risk_score", "N/A"))

    findings = [
        [
            "1",
            (
                f"The current composite risk score is {composite_score}, while the "
                f"adjusted risk score is {adjusted_score} after applying a capped "
                f"resilience credit of {resilience_credit}."
            ),
        ],
        [
            "2",
            (
                f"Growth pressure remains one of the most important weighted local "
                f"risk signals, with a latest score of {growth_score} and a 20% "
                f"composite weight."
            ),
        ],
        [
            "3",
            (
                f"Housing affordability pressure is a live module, with a latest "
                f"score of {housing_score} and signal of {housing_signal}."
            ),
        ],
        [
            "4",
            (
                f"Infrastructure strain is a live module, with a latest score of "
                f"{infrastructure_score} and signal of {infrastructure_signal}."
            ),
        ],
        [
            "5",
            (
                f"Development friction is a live module, with a latest score of "
                f"{development_score} and signal of {development_signal}."
            ),
        ],
        [
            "6",
            (
                f"Geoeconomic industry exposure is a live module, with a latest score "
                f"of {industry_score} and signal of {industry_signal}."
            ),
        ],
        [
            "7",
            (
                f"Household vulnerability is a live module, with a latest score of "
                f"{household_score} and signal of {household_signal}."
            ),
        ],
        [
            "8",
            (
                f"Construction shock exposure is currently {construction_score}. "
                f"The latest short-term momentum signal is: {momentum_signal}."
            ),
        ],
        [
            "9",
            (
                f"The highest-risk scenario is {highest_scenario}, with an adjusted "
                f"scenario risk score of {highest_scenario_score}."
            ),
        ],
        [
            "10",
            (
                f"Local resilience evidence confidence is currently classified as "
                f"{resilience_confidence}, based on curated source notes."
            ),
        ],
    ]

    story.append(make_table([["#", "Finding"]] + findings, col_widths=[0.35 * inch, 6.05 * inch], font_size=7.2))
    story.append(Spacer(1, 0.15 * inch))


def add_latest_module_scores(
    story,
    styles,
    construction_df,
    growth_df,
    housing_df,
    infrastructure_df,
    development_df,
    industry_df,
    household_df,
    resilience_df,
):
    """
    Add latest scores from individual modules.
    """

    story.append(Paragraph("Latest Module Scores", styles["SectionHeading"]))

    construction_context = str(safe_value(construction_df, "construction_shock_signal"))

    if safe_value(construction_df, "construction_shock_momentum_signal") != "N/A":
        construction_context += (
            f" | Momentum: "
            f"{safe_value(construction_df, 'construction_shock_momentum_signal')}"
        )

    growth_context = str(safe_value(growth_df, "growth_pressure_signal"))

    if safe_value(growth_df, "data_quality_flag") != "N/A":
        growth_context += f" | {safe_value(growth_df, 'data_quality_flag')}"

    housing_context = str(
        safe_value(housing_df, "housing_affordability_pressure_signal")
    )

    if safe_value(housing_df, "data_quality_flag") != "N/A":
        housing_context += f" | {safe_value(housing_df, 'data_quality_flag')}"

    if safe_value(housing_df, "acs_year") != "N/A":
        housing_context += f" | ACS {safe_value(housing_df, 'acs_year')}"

    infrastructure_context = str(
        safe_value(infrastructure_df, "infrastructure_strain_signal")
    )

    if safe_value(infrastructure_df, "data_quality_flag") != "N/A":
        infrastructure_context += (
            f" | {safe_value(infrastructure_df, 'data_quality_flag')}"
        )

    if safe_value(infrastructure_df, "source_signal_confidence") != "N/A":
        infrastructure_context += (
            f" | Local signal: "
            f"{safe_value(infrastructure_df, 'source_signal_confidence')}"
        )

    development_context = str(
        safe_value(development_df, "development_friction_signal")
    )

    if safe_value(development_df, "source_confidence_label") != "N/A":
        development_context += (
            f" | Source signal: "
            f"{safe_value(development_df, 'source_confidence_label')}"
        )

    industry_context = str(
        safe_value(industry_df, "geoeconomic_industry_exposure_signal")
    )

    if safe_value(industry_df, "data_quality_flag") != "N/A":
        industry_context += f" | {safe_value(industry_df, 'data_quality_flag')}"

    if safe_value(industry_df, "acs_year") != "N/A":
        industry_context += f" | ACS {safe_value(industry_df, 'acs_year')}"

    household_context = str(
        safe_value(household_df, "household_vulnerability_signal")
    )

    if safe_value(household_df, "data_quality_flag") != "N/A":
        household_context += f" | {safe_value(household_df, 'data_quality_flag')}"

    if safe_value(household_df, "local_vulnerability_source_signal_label") != "N/A":
        household_context += (
            f" | Local signal: "
            f"{str(safe_value(household_df, 'local_vulnerability_source_signal_label')).replace('Very Strong Local Vulnerability Signal', 'Very Strong Local Signal')}"
        )

    resilience_context = str(safe_value(resilience_df, "local_resilience_signal"))

    if safe_value(resilience_df, "local_resilience_confidence") != "N/A":
        resilience_context += (
            f" | Confidence: "
            f"{safe_value(resilience_df, 'local_resilience_confidence')}"
        )

    data = [
        ["Module", "Latest Score", "Signal / Context"],
        [
            "Construction Shock Exposure",
            fmt_score(safe_value(construction_df, "construction_shock_score")),
            construction_context,
        ],
        [
            "Growth Pressure",
            fmt_score(safe_value(growth_df, "growth_pressure_score")),
            growth_context,
        ],
        [
            "Housing Affordability Pressure",
            fmt_score(safe_value(housing_df, "housing_affordability_pressure_score")),
            housing_context,
        ],
        [
            "Infrastructure Strain",
            fmt_score(safe_value(infrastructure_df, "infrastructure_strain_score")),
            infrastructure_context,
        ],
        [
            "Development Friction",
            fmt_score(safe_value(development_df, "development_friction_score")),
            development_context,
        ],
        [
            "Geoeconomic Industry Exposure",
            fmt_score(safe_value(industry_df, "geoeconomic_industry_exposure_score")),
            industry_context,
        ],
        [
            "Household Vulnerability",
            fmt_score(safe_value(household_df, "household_vulnerability_score")),
            household_context,
        ],
        [
            "Local Resilience Offset",
            fmt_score(safe_value(resilience_df, "local_resilience_offset")),
            resilience_context,
        ],
    ]

    story.append(
        make_wrapped_table(
            data,
            styles,
            col_widths=[1.85 * inch, 0.75 * inch, 3.80 * inch],
            font_size=6.1,
            header_font_size=6.4,
        )
    )
    story.append(Spacer(1, 0.15 * inch))


def add_change_detection_section(story, styles, change_df):
    """
    Add change detection summary.
    """

    story.append(Paragraph("Change Detection Summary", styles["SectionHeading"]))

    if change_df.empty:
        story.append(
            Paragraph(
                "Change detection data was not available. Run change_detection.py before generating the report.",
                styles["BodyTextCustom"],
            )
        )
        return

    summary_text = safe_value(change_df, "summary_text", default="No change summary available.")

    story.append(Paragraph(str(summary_text), styles["BodyTextCustom"]))

    display_metrics = [
        "composite_risk_score",
        "adjusted_geoeconomic_growth_risk_score",
        "growth_pressure_score",
        "housing_affordability_pressure_score",
        "construction_shock_score",
        "fuel_energy_shock_score",
        "infrastructure_strain_score",
        "development_friction_score",
        "geoeconomic_industry_exposure_score",
        "household_vulnerability_score",
        "local_resilience_offset",
        "highest_risk_scenario_score",
        "highest_risk_scenario",
    ]

    display_df = change_df[change_df["metric"].isin(display_metrics)].copy()

    if display_df.empty:
        story.append(Paragraph("No tracked change metrics were available.", styles["BodyTextCustom"]))
        return

    table_data = [["Metric", "Current", "Previous", "Delta", "Direction", "Materiality"]]

    qualitative_metrics = {
        "highest_risk_scenario",
    }

    for _, row in display_df.iterrows():
        metric = row.get("metric", "N/A")
        current_value = row.get("current_value", "N/A")
        previous_value = row.get("previous_value", "N/A")
        delta = row.get("delta", "N/A")

        if metric in qualitative_metrics:
            current_display = fmt_display(current_value)
            previous_display = fmt_display(previous_value)
            delta_display = "N/A"
        else:
            current_display = fmt_score(current_value)
            previous_display = fmt_score(previous_value)
            delta_display = fmt_change_delta(delta)

        table_data.append(
            [
                clean_label(metric),
                current_display,
                previous_display,
                delta_display,
                fmt_display(row.get("change_direction", "N/A")),
                fmt_display(row.get("change_materiality", "N/A")),
            ]
        )

    story.append(
        make_wrapped_table(
            table_data,
            styles,
            col_widths=[
                1.85 * inch,
                0.72 * inch,
                0.72 * inch,
                0.54 * inch,
                0.76 * inch,
                0.76 * inch,
            ],
            font_size=5.6,
            header_font_size=5.8,
        )
    )

    story.append(
        Paragraph(
            "Change detection compares the current model run against the prior saved snapshot. "
            "The first run establishes the baseline for future comparisons.",
            styles["SmallText"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))


def add_sensitivity_analysis_section(story, styles, sensitivity_summary_df, sensitivity_results_df):
    """
    Add sensitivity analysis summary.
    """

    story.append(Paragraph("Sensitivity Analysis", styles["SectionHeading"]))

    if sensitivity_summary_df.empty or sensitivity_results_df.empty:
        story.append(
            Paragraph(
                "Sensitivity analysis data was not available. Run sensitivity_analysis.py before generating the report.",
                styles["BodyTextCustom"],
            )
        )
        return

    stability = safe_value(
        sensitivity_summary_df,
        "sensitivity_stability",
        default="N/A",
    )
    min_score = fmt_score(
        safe_value(sensitivity_summary_df, "min_adjusted_risk_score")
    )
    max_score = fmt_score(
        safe_value(sensitivity_summary_df, "max_adjusted_risk_score")
    )
    score_range = fmt_score(
        safe_value(sensitivity_summary_df, "adjusted_risk_score_range")
    )
    lowest_case = safe_value(
        sensitivity_summary_df,
        "lowest_risk_case",
        default="N/A",
    )
    highest_case = safe_value(
        sensitivity_summary_df,
        "highest_risk_case",
        default="N/A",
    )

    story.append(
        Paragraph(
            "The sensitivity analysis tests whether the model conclusion changes "
            "under alternative weighting assumptions. This is useful for checking "
            "whether the conclusion is driven by one model component or remains "
            "stable across alternative risk-emphasis cases.",
            styles["BodyTextCustom"],
        )
    )

    summary_data = [
        ["Metric", "Value"],
        ["Sensitivity Stability", str(stability)],
        ["Minimum Adjusted Risk Score", min_score],
        ["Maximum Adjusted Risk Score", max_score],
        ["Adjusted Risk Score Range", score_range],
        ["Lowest-Risk Weighting Case", str(lowest_case)],
        ["Highest-Risk Weighting Case", str(highest_case)],
    ]

    story.append(
        make_table(
            summary_data,
            col_widths=[2.8 * inch, 3.2 * inch],
            font_size=7.8,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    table_data = [["Weighting Case", "Composite", "Adjusted", "Signal"]]

    for _, row in sensitivity_results_df.iterrows():
        table_data.append(
            [
                str(row.get("case_name", "N/A")),
                fmt_score(row.get("sensitivity_composite_risk_score", "N/A")),
                fmt_score(row.get("sensitivity_adjusted_risk_score", "N/A")),
                str(row.get("sensitivity_adjusted_signal", "N/A")),
            ]
        )

    story.append(
        make_table(
            table_data,
            col_widths=[2.4 * inch, 0.9 * inch, 0.9 * inch, 1.5 * inch],
            font_size=7.0,
        )
    )

    story.append(
        Paragraph(
            "A stable sensitivity result means the model's broad risk conclusion is not overly dependent "
            "on one weighting framework.",
            styles["SmallText"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))


def add_risk_threshold_breach_section(story, styles, breach_summary_df, breach_df):
    """
    Add risk threshold breach monitor summary.
    """

    story.append(Paragraph("Risk Threshold Breach Monitor", styles["SectionHeading"]))

    if breach_summary_df.empty:
        story.append(
            Paragraph(
                "Risk threshold breach data was not available. "
                "Run risk_threshold_breaches.py before generating the report.",
                styles["BodyTextCustom"],
            )
        )
        return

    alert_level = safe_value(breach_summary_df, "alert_level", default="N/A")
    total_active = safe_value(breach_summary_df, "total_active_breaches", default="N/A")
    high_active = safe_value(breach_summary_df, "high_severity_breaches", default="N/A")
    model_quality = safe_value(breach_summary_df, "model_quality_breaches", default="N/A")
    top_category = safe_value(breach_summary_df, "top_breach_category", default="N/A")
    top_description = safe_value(
        breach_summary_df,
        "top_breach_description",
        default="N/A",
    )
    breached_categories = safe_value(
        breach_summary_df,
        "breached_categories",
        default="N/A",
    )
    summary_text = safe_value(
        breach_summary_df,
        "summary_text",
        default="No breach summary available.",
    )

    story.append(Paragraph(str(summary_text), styles["BodyTextCustom"]))

    summary_data = [
        ["Metric", "Value"],
        ["Alert Level", str(alert_level)],
        ["Total Active Breaches", str(total_active)],
        ["High-Severity Breaches", str(high_active)],
        ["Model Quality Breaches", str(model_quality)],
        ["Top Breach Category", str(top_category)],
        ["Top Breach Description", str(top_description)],
        ["Breached Categories", str(breached_categories)],
    ]

    story.append(
        make_table(
            summary_data,
            col_widths=[2.25 * inch, 4.15 * inch],
            font_size=7.4,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    if breach_df.empty or "is_breached" not in breach_df.columns:
        story.append(
            Paragraph(
                "No detailed breach table was available.",
                styles["SmallText"],
            )
        )
        story.append(Spacer(1, 0.15 * inch))
        return

    active_df = breach_df[breach_df["is_breached"] == True].copy()

    if active_df.empty:
        story.append(
            Paragraph(
                "No active risk threshold breaches were detected.",
                styles["SmallText"],
            )
        )
        story.append(Spacer(1, 0.15 * inch))
        return

    active_df = active_df.sort_values(
        ["severity_score", "distance_to_threshold"],
        ascending=[False, False],
    ).head(8)

    table_data = [["Category", "Metric", "Value", "Threshold", "Severity"]]

    for _, row in active_df.iterrows():
        table_data.append(
            [
                str(row.get("category", "N/A")),
                clean_label(row.get("metric", "N/A")),
                fmt_score(row.get("current_value", "N/A")),
                fmt_score(row.get("threshold", "N/A")),
                str(row.get("severity", "N/A")),
            ]
        )

    story.append(
        make_table(
            table_data,
            col_widths=[
                1.35 * inch,
                2.25 * inch,
                0.75 * inch,
                0.75 * inch,
                0.9 * inch,
            ],
            font_size=6.7,
        )
    )

    story.append(
        Paragraph(
            "The breach monitor converts model outputs into an alert-style layer by "
            "tracking whether key growth, construction, scenario, resilience, and "
            "model-quality thresholds are active.",
            styles["SmallText"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))


def add_component_summary(story, styles, component_df):
    """
    Add composite component summary table.
    """

    story.append(Paragraph("Composite Risk Component Summary", styles["SectionHeading"]))

    if component_df.empty:
        story.append(Paragraph("Component summary data was not available.", styles["BodyTextCustom"]))
        return

    table_data = [["Component", "Weight", "Score", "Signal", "Status"]]

    for _, row in component_df.iterrows():
        status = "Placeholder" if parse_bool(row.get("is_placeholder", False)) else "Live"
        table_data.append(
            [
                clean_label(row.get("component", "")),
                f"{float(row.get('weight', 0)):.0%}",
                fmt_score(row.get("score", "N/A")),
                str(row.get("signal", "N/A")),
                status,
            ]
        )

    story.append(
        make_table(
            table_data,
            col_widths=[2.15 * inch, 0.65 * inch, 0.65 * inch, 1.35 * inch, 0.9 * inch],
            font_size=7.2,
        )
    )
    story.append(Spacer(1, 0.12 * inch))


def add_scenario_section(story, styles, scenario_df):
    """
    Add scenario forecast table.
    """

    story.append(Paragraph("Scenario Forecasts", styles["SectionHeading"]))

    if scenario_df.empty:
        story.append(Paragraph("Scenario forecast data was not available.", styles["BodyTextCustom"]))
        return

    story.append(
        Paragraph(
            "The scenario model estimates how local growth risk could change under "
            "alternative growth, construction-cost, infrastructure, housing, and "
            "planning conditions. The delta column compares each scenario with the "
            "latest adjusted baseline risk score.",
            styles["BodyTextCustom"],
        )
    )

    table_data = [["Scenario", "Score", "Delta", "Signal", "Primary Risk Driver"]]

    for _, row in scenario_df.iterrows():
        table_data.append(
            [
                str(row.get("scenario_name", "")),
                fmt_score(row.get("scenario_adjusted_risk_score", "N/A")),
                fmt_delta(row.get("scenario_delta_vs_adjusted_baseline", "N/A")),
                str(row.get("scenario_signal", "N/A")),
                str(row.get("primary_risk_driver", "N/A")),
            ]
        )

    story.append(
        make_wrapped_table(
            table_data,
            styles,
            col_widths=[1.25 * inch, 0.55 * inch, 0.55 * inch, 0.9 * inch, 3.15 * inch],
            font_size=6.4,
        )
    )

    if "severity_note" in scenario_df.columns:
        top_notes = scenario_df[["scenario_name", "severity_note"]].dropna().head(4)

        if not top_notes.empty:
            note_data = [["Scenario", "Interpretation Note"]]

            for _, row in top_notes.iterrows():
                note_data.append(
                    [
                        str(row.get("scenario_name", "N/A")),
                        str(row.get("severity_note", "N/A")),
                    ]
                )

            story.append(Spacer(1, 0.1 * inch))
            story.append(
                make_wrapped_table(
                    note_data,
                    styles,
                    col_widths=[1.45 * inch, 4.95 * inch],
                    font_size=6.3,
                )
            )

    story.append(Spacer(1, 0.15 * inch))


def add_housing_detail_section(story, styles, housing_df, housing_component_df):
    """
    Add housing affordability detail section.
    """

    story.append(Paragraph("Housing Affordability Detail", styles["SectionHeading"]))

    if housing_df.empty:
        story.append(
            Paragraph(
                "Housing affordability data was not available. Run housing_affordability.py before generating the report.",
                styles["BodyTextCustom"],
            )
        )
        return

    summary_data = [
        ["Metric", "Value"],
        ["Geography", str(safe_value(housing_df, "geography_name"))],
        ["ACS Year", str(safe_value(housing_df, "acs_year"))],
        ["ACS Dataset", str(safe_value(housing_df, "acs_dataset"))],
        ["Median Household Income", fmt_currency(safe_value(housing_df, "median_household_income"))],
        ["Median Home Value", fmt_currency(safe_value(housing_df, "median_home_value"))],
        ["Median Gross Rent", fmt_currency(safe_value(housing_df, "median_gross_rent"))],
        ["Home Value to Income", fmt_ratio(safe_value(housing_df, "home_value_to_income"))],
        ["Rent to Income", fmt_pct(safe_value(housing_df, "rent_to_income"))],
        ["Renter Cost-Burden Share", fmt_pct(safe_value(housing_df, "renter_cost_burden_share"))],
        ["Owner Cost-Burden Share", fmt_pct(safe_value(housing_df, "owner_cost_burden_share"))],
        ["Mortgage Rate", fmt_pct(safe_value(housing_df, "mortgage_rate"))],
        ["Housing Affordability Pressure Score", fmt_score(safe_value(housing_df, "housing_affordability_pressure_score"))],
        ["Housing Affordability Signal", str(safe_value(housing_df, "housing_affordability_pressure_signal"))],
        ["Data Quality", str(safe_value(housing_df, "data_quality_flag"))],
    ]

    story.append(
        make_table(
            summary_data,
            col_widths=[2.65 * inch, 3.45 * inch],
            font_size=7.2,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    if not housing_component_df.empty:
        component_data = [["Component", "Weight", "Score", "Signal"]]

        for _, row in housing_component_df.iterrows():
            component_data.append(
                [
                    str(row.get("component_label", clean_label(row.get("component", "")))),
                    f"{float(row.get('weight', 0)):.0%}",
                    fmt_score(row.get("score", "N/A")),
                    str(row.get("signal", "N/A")),
                ]
            )

        story.append(Paragraph("Housing Component Scores", styles["SubHeading"]))
        story.append(
            make_table(
                component_data,
                col_widths=[2.5 * inch, 0.8 * inch, 0.8 * inch, 1.5 * inch],
                font_size=7.1,
            )
        )

    story.append(
        Paragraph(
            "The housing affordability module uses ACS income, home value, rent, cost-burden, "
            "and mortgage-rate indicators to estimate household affordability pressure.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.12 * inch))


def add_infrastructure_detail_section(story, styles, infrastructure_df, infrastructure_component_df):
    """
    Add infrastructure strain detail section.
    """

    story.append(Paragraph("Infrastructure Strain Detail", styles["SectionHeading"]))

    if infrastructure_df.empty:
        story.append(
            Paragraph(
                "Infrastructure strain data was not available. Run infrastructure_strain.py before generating the report.",
                styles["BodyTextCustom"],
            )
        )
        return

    summary_data = [
        ["Metric", "Value"],
        ["Geography", str(safe_value(infrastructure_df, "geography_name"))],
        ["ACS Year", str(safe_value(infrastructure_df, "acs_year"))],
        ["ACS Dataset", str(safe_value(infrastructure_df, "acs_dataset"))],
        ["Mean Travel Time", fmt_score(safe_value(infrastructure_df, "mean_travel_time_minutes")) + " minutes"],
        ["Long Commute Share", fmt_pct(safe_value(infrastructure_df, "long_commute_share"))],
        ["Drive-Alone Share", fmt_pct(safe_value(infrastructure_df, "drive_alone_share"))],
        ["Carpool Share", fmt_pct(safe_value(infrastructure_df, "carpool_share"))],
        ["Public Transport Share", fmt_pct(safe_value(infrastructure_df, "public_transport_share"))],
        ["Worked From Home Share", fmt_pct(safe_value(infrastructure_df, "worked_from_home_share"))],
        ["Local Infrastructure Notes", str(safe_value(infrastructure_df, "local_infrastructure_note_count"))],
        ["Public Works / Road Notes", str(safe_value(infrastructure_df, "public_works_road_note_count"))],
        ["Source Signal Confidence", str(safe_value(infrastructure_df, "source_signal_confidence"))],
        ["Infrastructure Strain Score", fmt_score(safe_value(infrastructure_df, "infrastructure_strain_score"))],
        ["Infrastructure Strain Signal", str(safe_value(infrastructure_df, "infrastructure_strain_signal"))],
        ["Data Quality", str(safe_value(infrastructure_df, "data_quality_flag"))],
    ]

    story.append(
        make_table(
            summary_data,
            col_widths=[2.65 * inch, 3.45 * inch],
            font_size=7.0,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    if not infrastructure_component_df.empty:
        component_data = [["Component", "Weight", "Score", "Signal"]]

        for _, row in infrastructure_component_df.iterrows():
            component_data.append(
                [
                    str(row.get("component_label", clean_label(row.get("component", "")))),
                    f"{float(row.get('weight', 0)):.0%}",
                    fmt_score(row.get("score", "N/A")),
                    str(row.get("signal", "N/A")),
                ]
            )

        story.append(Paragraph("Infrastructure Component Scores", styles["SubHeading"]))
        story.append(
            make_table(
                component_data,
                col_widths=[2.65 * inch, 0.8 * inch, 0.8 * inch, 1.5 * inch],
                font_size=7.1,
            )
        )

    story.append(
        Paragraph(
            "The infrastructure strain module uses ACS commute and transportation indicators "
            "plus curated local source notes related to roads, public works, utilities, "
            "stormwater, and development pressure.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.12 * inch))


def add_development_friction_detail_section(
    story,
    styles,
    development_df,
    development_component_df,
):
    """
    Add development friction detail section.
    """

    story.append(Paragraph("Development Friction Detail", styles["SectionHeading"]))

    if development_df.empty:
        story.append(
            Paragraph(
                "Development friction data was not available. Run development_friction.py before generating the report.",
                styles["BodyTextCustom"],
            )
        )
        return

    summary_data = [
        ["Metric", "Value"],
        ["Development Friction Score", fmt_score(safe_value(development_df, "development_friction_score"))],
        ["Development Friction Signal", str(safe_value(development_df, "development_friction_signal"))],
        ["Source Confidence Score", fmt_score(safe_value(development_df, "source_confidence_score"))],
        ["Source Confidence Label", str(safe_value(development_df, "source_confidence_label"))],
        ["Total Relevant Notes", str(safe_value(development_df, "total_relevant_notes"))],
        ["Unique Sources", str(safe_value(development_df, "unique_sources"))],
        ["Source Type Count", str(safe_value(development_df, "source_type_count"))],
        ["Zoning / Code Notes", str(safe_value(development_df, "zoning_code_note_count"))],
        ["Planning / Permitting Notes", str(safe_value(development_df, "planning_permitting_note_count"))],
        ["Development Pipeline Notes", str(safe_value(development_df, "development_pipeline_note_count"))],
        ["Public Notice / Agenda Notes", str(safe_value(development_df, "public_notice_agenda_note_count"))],
        ["Data Quality", str(safe_value(development_df, "data_quality_flag"))],
    ]

    story.append(
        make_table(
            summary_data,
            col_widths=[2.65 * inch, 3.45 * inch],
            font_size=7.0,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    if not development_component_df.empty:
        component_data = [["Component", "Weight", "Score", "Signal"]]

        for _, row in development_component_df.iterrows():
            component_data.append(
                [
                    str(row.get("component_label", clean_label(row.get("component", "")))),
                    f"{float(row.get('weight', 0)):.0%}",
                    fmt_score(row.get("score", "N/A")),
                    str(row.get("signal", "N/A")),
                ]
            )

        story.append(Paragraph("Development Friction Component Scores", styles["SubHeading"]))
        story.append(
            make_table(
                component_data,
                col_widths=[2.65 * inch, 0.8 * inch, 0.8 * inch, 1.5 * inch],
                font_size=7.1,
            )
        )

    story.append(
        Paragraph(
            "The development friction module uses curated local source notes to estimate "
            "pressure from zoning-code updates, planning/permitting activity, public "
            "notice and agenda activity, and the development pipeline.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.12 * inch))


def add_geoeconomic_industry_detail_section(story, styles, industry_df, industry_component_df):
    """
    Add geoeconomic industry exposure detail section.
    """

    story.append(Paragraph("Geoeconomic Industry Exposure Detail", styles["SectionHeading"]))

    if industry_df.empty:
        story.append(
            Paragraph(
                "Geoeconomic industry exposure data was not available. Run geoeconomic_industry_exposure.py before generating the report.",
                styles["BodyTextCustom"],
            )
        )
        return

    summary_data = [
        ["Metric", "Value"],
        ["Geography", str(safe_value(industry_df, "geography_name"))],
        ["ACS Year", str(safe_value(industry_df, "acs_year"))],
        ["ACS Dataset", str(safe_value(industry_df, "acs_dataset"))],
        ["ACS Industry Base Count", fmt_score(safe_value(industry_df, "civilian_employed_total"))],
        ["Manufacturing Share", fmt_pct(safe_value(industry_df, "manufacturing_share"))],
        ["Logistics / Transportation Share", fmt_pct(safe_value(industry_df, "logistics_transportation_share"))],
        ["Construction Share", fmt_pct(safe_value(industry_df, "construction_share"))],
        ["Retail Trade Share", fmt_pct(safe_value(industry_df, "retail_trade_share"))],
        ["Wholesale Trade Share", fmt_pct(safe_value(industry_df, "wholesale_trade_share"))],
        ["Trade-Sensitive Share", fmt_pct(safe_value(industry_df, "trade_sensitive_share"))],
        ["Manufacturing Source Notes", str(safe_value(industry_df, "manufacturing_source_notes"))],
        ["Logistics Source Notes", str(safe_value(industry_df, "logistics_source_notes"))],
        ["Trade-Sensitive Source Notes", str(safe_value(industry_df, "trade_sensitive_source_notes"))],
        ["Source Confidence", str(safe_value(industry_df, "source_confidence_label"))],
        ["Industry Exposure Score", fmt_score(safe_value(industry_df, "geoeconomic_industry_exposure_score"))],
        ["Industry Exposure Signal", str(safe_value(industry_df, "geoeconomic_industry_exposure_signal"))],
        ["Data Quality", str(safe_value(industry_df, "data_quality_flag"))],
    ]

    story.append(
        make_table(
            summary_data,
            col_widths=[2.75 * inch, 3.35 * inch],
            font_size=6.8,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    if not industry_component_df.empty:
        component_data = [["Component", "Weight", "Score", "Signal"]]

        for _, row in industry_component_df.iterrows():
            component_data.append(
                [
                    str(row.get("component_label", clean_label(row.get("component", "")))),
                    f"{float(row.get('weight', 0)):.0%}",
                    fmt_score(row.get("score", "N/A")),
                    str(row.get("signal", "N/A")),
                ]
            )

        story.append(Paragraph("Industry Exposure Component Scores", styles["SubHeading"]))
        story.append(
            make_table(
                component_data,
                col_widths=[2.75 * inch, 0.8 * inch, 0.8 * inch, 1.5 * inch],
                font_size=6.9,
            )
        )

    story.append(
        Paragraph(
            "The geoeconomic industry exposure module combines employment-exposure indicators "
            "with curated local source notes to estimate exposure to manufacturing, logistics, "
            "construction, retail, and trade-sensitive growth channels. Counts and percentages "
            "should be interpreted within the module's ACS variable definitions and validated "
            "before use as official employment totals.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.12 * inch))


def add_household_vulnerability_detail_section(
    story,
    styles,
    household_df,
    household_component_df,
    household_source_df,
):
    """
    Add household vulnerability detail section.
    """

    story.append(Paragraph("Household Vulnerability Detail", styles["SectionHeading"]))

    if household_df.empty:
        story.append(
            Paragraph(
                "Household vulnerability data was not available. Run household_vulnerability.py before generating the report.",
                styles["BodyTextCustom"],
            )
        )
        return

    local_vulnerability_note_count = safe_value(
        household_df,
        "local_vulnerability_note_count",
        default=safe_value(household_source_df, "total_relevant_notes"),
    )

    summary_data = [
        ["Metric", "Value"],
        ["Geography", str(safe_value(household_df, "geography_name"))],
        ["ACS Year", str(safe_value(household_df, "acs_year"))],
        ["ACS Dataset", str(safe_value(household_df, "acs_dataset"))],
        ["Households Total", fmt_score(safe_value(household_df, "households_total"))],
        ["Median Household Income", fmt_currency(safe_value(household_df, "median_household_income"))],
        ["Per Capita Income", fmt_currency(safe_value(household_df, "per_capita_income"))],
        ["Poverty Rate", fmt_pct(safe_value(household_df, "poverty_rate"))],
        ["Unemployment Rate", fmt_pct(safe_value(household_df, "unemployment_rate"))],
        ["Low-Income Household Share", fmt_pct(safe_value(household_df, "low_income_household_share"))],
        ["Housing Cost-Burden Share", fmt_pct(safe_value(household_df, "housing_cost_burden_share"))],
        ["Mean Travel Time", fmt_score(safe_value(household_df, "mean_travel_time_minutes")) + " minutes"],
        ["Local Vulnerability Notes", str(local_vulnerability_note_count)],
        ["Local Vulnerability Signal", str(safe_value(household_df, "local_vulnerability_source_signal_label"))],
        ["Household Vulnerability Score", fmt_score(safe_value(household_df, "household_vulnerability_score"))],
        ["Household Vulnerability Signal", str(safe_value(household_df, "household_vulnerability_signal"))],
        ["Data Quality", str(safe_value(household_df, "data_quality_flag"))],
    ]

    story.append(
        make_table(
            summary_data,
            col_widths=[2.75 * inch, 3.35 * inch],
            font_size=6.8,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    if not household_component_df.empty:
        component_data = [["Component", "Weight", "Score", "Signal"]]

        for _, row in household_component_df.iterrows():
            component_data.append(
                [
                    str(row.get("component_label", clean_label(row.get("component", "")))),
                    f"{float(row.get('weight', 0)):.0%}",
                    fmt_score(row.get("score", "N/A")),
                    str(row.get("signal", "N/A")),
                ]
            )

        story.append(Paragraph("Household Vulnerability Component Scores", styles["SubHeading"]))
        story.append(
            make_table(
                component_data,
                col_widths=[2.75 * inch, 0.8 * inch, 0.8 * inch, 1.5 * inch],
                font_size=6.9,
            )
        )
        story.append(Spacer(1, 0.1 * inch))

    if not household_source_df.empty:
        source_data = [["Metric", "Value"]]
        for column in [
            "total_relevant_notes",
            "unique_sources",
            "source_type_count",
            "local_vulnerability_source_signal_score",
            "local_vulnerability_source_signal_label",
        ]:
            if column in household_source_df.columns:
                source_data.append([clean_label(column), str(safe_value(household_source_df, column))])

        if len(source_data) > 1:
            story.append(Paragraph("Household Vulnerability Source Signal", styles["SubHeading"]))
            story.append(
                make_table(
                    source_data,
                    col_widths=[2.75 * inch, 3.35 * inch],
                    font_size=6.8,
                )
            )

    story.append(
        Paragraph(
            "The household vulnerability module uses ACS poverty, income, unemployment, "
            "housing cost burden, and commute indicators, plus curated local source notes "
            "related to affordability, vulnerable residents, transportation cost exposure, "
            "and social-service capacity.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.12 * inch))


def add_construction_detail_section(story, styles, construction_category_df, construction_component_df):
    """
    Add construction shock category and component detail.
    """

    story.append(Paragraph("Construction Shock Detail", styles["SectionHeading"]))

    if not construction_category_df.empty:
        category_data = [["Category", "Score", "Signal"]]

        for _, row in construction_category_df.iterrows():
            category_data.append(
                [
                    str(row.get("category_label", clean_label(row.get("category", "")))),
                    fmt_score(row.get("category_score", "N/A")),
                    str(row.get("category_signal", "N/A")),
                ]
            )

        story.append(Paragraph("Category Breakdown", styles["SubHeading"]))
        story.append(
            make_table(
                category_data,
                col_widths=[2.5 * inch, 1.0 * inch, 2.0 * inch],
                font_size=7.8,
            )
        )
        story.append(Spacer(1, 0.12 * inch))

    if not construction_component_df.empty:
        component_data = [["Component", "Category", "Score", "YoY %", "Weight"]]

        for _, row in construction_component_df.iterrows():
            component_data.append(
                [
                    str(row.get("label", clean_label(row.get("component", "")))),
                    clean_label(row.get("category", "")),
                    fmt_score(row.get("component_score", "N/A")),
                    fmt_score(row.get("latest_yoy_pct", "N/A")),
                    f"{float(row.get('weight', 0)):.0%}",
                ]
            )

        story.append(Paragraph("Latest Component Scores", styles["SubHeading"]))
        story.append(
            make_table(
                component_data,
                col_widths=[2.25 * inch, 1.25 * inch, 0.7 * inch, 0.7 * inch, 0.6 * inch],
                font_size=6.6,
            )
        )
        story.append(Spacer(1, 0.12 * inch))


def add_resilience_detail_section(story, styles, resilience_component_df):
    """
    Add local resilience component detail.
    """

    story.append(Paragraph("Local Resilience Evidence Detail", styles["SectionHeading"]))

    if resilience_component_df.empty:
        story.append(Paragraph("Local resilience component detail was not available.", styles["BodyTextCustom"]))
        return

    table_data = [["Component", "Score", "Confidence", "Notes", "Sources"]]

    for _, row in resilience_component_df.iterrows():
        table_data.append(
            [
                clean_label(row.get("component", "")),
                fmt_score(row.get("component_score", "N/A")),
                str(row.get("evidence_confidence", "N/A")),
                str(row.get("evidence_note_count", "N/A")),
                str(row.get("unique_source_count", "N/A")),
            ]
        )

    story.append(
        make_table(
            table_data,
            col_widths=[2.0 * inch, 0.65 * inch, 1.55 * inch, 0.65 * inch, 0.65 * inch],
            font_size=7.0,
        )
    )

    story.append(
        Paragraph(
            "The resilience module uses conservative evidence tiers so a small number "
            "of keyword matches does not automatically create maximum resilience scores.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.12 * inch))


def add_methodology_section(story, styles):
    """
    Add methodology overview.
    """

    story.append(Paragraph("Methodology", styles["SectionHeading"]))

    story.append(
        Paragraph(
            "The model uses a 0-100 scoring framework. Higher values indicate higher "
            "risk pressure. The current version is fully data-driven across all seven "
            "composite components: growth pressure, housing affordability, construction "
            "shock exposure, infrastructure strain, development friction, geoeconomic "
            "industry exposure, and household vulnerability. The Local Resilience Offset "
            "is handled separately as a capped risk-reduction credit.",
            styles["BodyTextCustom"],
        )
    )

    methodology_data = [
        ["Component", "Model Role"],
        ["Growth Pressure", "Measures GDP growth, labor-market tightness, and current local growth/development signals."],
        ["Housing Affordability", "Measures income, home value, rent, cost-burden, and mortgage-rate pressure."],
        ["Construction Shock Exposure", "Measures sensitivity to materials, fuel, energy, and financing costs."],
        ["Infrastructure Strain", "Measures commute pressure, vehicle dependence, long-commute exposure, and local infrastructure-note pressure."],
        ["Development Friction", "Measures zoning, planning, permitting, development-pipeline, and public-notice pressure."],
        ["Geoeconomic Industry Exposure", "Measures exposure to manufacturing, logistics, construction, retail, and trade-sensitive growth channels using employment-exposure indicators and local source evidence."],
        ["Household Vulnerability", "Measures poverty, low-income exposure, unemployment, housing cost burden, commute burden, and local vulnerability evidence."],
        ["Local Resilience Offset", "Measures utility coordination, public works capacity, flood mitigation, public safety response, and project execution."],
        ["Capped Resilience Credit", "Converts resilience into a capped risk reduction so resilience does not overpower risk pressure."],
        ["Scenario Forecasts", "Stress-tests the model under managed growth, overheated growth, construction cost shock, and rezoning-constraint cases."],
        ["Change Detection", "Compares the current run with the previous run snapshot to support repeatable monitoring."],
        ["Sensitivity Analysis", "Tests whether the model conclusion changes under alternative weighting assumptions."],
        ["Risk Threshold Breach Monitor", "Tracks whether key model indicators cross material warning thresholds."],
    ]

    story.append(
        make_wrapped_table(
            methodology_data,
            styles,
            col_widths=[1.40 * inch, 5.00 * inch],
            font_size=6.05,
            header_font_size=6.35,
        )
    )
    story.append(Spacer(1, 0.15 * inch))


def add_limitations_section(story, styles, composite_df):
    """
    Add model limitations and next steps.
    """

    story.append(Paragraph("Model Caveats and Next Improvements", styles["SectionHeading"]))

    placeholder_count = safe_value(composite_df, "placeholder_components_used")
    placeholder_share = fmt_pct(safe_value(composite_df, "placeholder_share"))
    model_maturity = safe_value(composite_df, "model_maturity_level")

    story.append(
        Paragraph(
            f"The current model maturity level is <b>{model_maturity}</b>. "
            f"The composite model currently uses {placeholder_count} placeholder "
            f"components, representing approximately {placeholder_share} of the "
            "composite component count. Future work should focus on validation, "
            "automation, source expansion, and dashboard delivery rather than replacing "
            "placeholder components.",
            styles["BodyTextCustom"],
        )
    )

    caveat_data = [
        ["Future Enhancement", "Purpose"],
        ["Streamlit Dashboard", "Convert the PDF workflow into an interactive local intelligence dashboard."],
        ["Source Evidence Tracker", "Track source age, source type, jurisdiction, confidence, and which model components each source supports."],
        ["Policy Activity Tracker", "Convert city/county meeting records, public notices, zoning actions, and planning agendas into a structured policy dataset."],
        ["Forecast Validation", "Back-test scenario assumptions and compare model trends against future housing, permit, commute, labor, and industry data."],
        ["Document Center Integration", "Use the City of Gallatin Document Center as a repeatable source hub for planning, zoning, infrastructure, and policy evidence."],
    ]

    story.append(
        make_wrapped_table(
            caveat_data,
            styles,
            col_widths=[1.45 * inch, 4.95 * inch],
            font_size=6.15,
            header_font_size=6.4,
        )
    )
    story.append(Spacer(1, 0.15 * inch))


def add_local_source_notes_section(story, styles):
    """
    Add curated local source notes table.
    """

    story.append(Paragraph("Curated Local Source Notes", styles["SectionHeading"]))

    notes_df = read_csv_if_exists(LOCAL_SOURCE_NOTES_FILE)

    if notes_df.empty:
        story.append(Paragraph("No local source notes were available.", styles["BodyTextCustom"]))
        return

    display_cols = ["date", "source_name", "topic", "risk_channel"]
    display_cols = [col for col in display_cols if col in notes_df.columns]

    notes_display = notes_df[display_cols].tail(16).copy()

    table_data = [display_cols]

    for _, row in notes_display.iterrows():
        table_data.append([str(row[col]) for col in display_cols])

    story.append(
        make_wrapped_table(
            table_data,
            styles,
            col_widths=[0.65 * inch, 2.05 * inch, 2.25 * inch, 1.45 * inch],
            font_size=5.9,
            header_font_size=6.1,
        )
    )

    story.append(
        Paragraph(
            "Note: Source notes are used as qualitative local indicators and are "
            "not treated as official numeric datasets. They are used to strengthen "
            "context and source confidence around local planning, infrastructure, "
            "affordability, resilience, and policy evidence.",
            styles["SmallText"],
        )
    )


# ============================================================
# Build report
# ============================================================

def build_report() -> Path:
    """
    Build the PDF report.
    """

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    styles = make_styles()

    composite_df = read_csv_if_exists(COMPOSITE_LATEST_FILE)
    scenario_df = read_csv_if_exists(SCENARIO_SUMMARY_FILE)
    construction_df = read_csv_if_exists(CONSTRUCTION_LATEST_FILE)
    construction_component_df = read_csv_if_exists(CONSTRUCTION_COMPONENT_SUMMARY_FILE)
    construction_category_df = read_csv_if_exists(CONSTRUCTION_CATEGORY_SUMMARY_FILE)
    growth_df = read_csv_if_exists(GROWTH_LATEST_FILE)
    housing_df = read_csv_if_exists(HOUSING_LATEST_FILE)
    housing_component_df = read_csv_if_exists(HOUSING_COMPONENT_SUMMARY_FILE)
    infrastructure_df = read_csv_if_exists(INFRASTRUCTURE_LATEST_FILE)
    infrastructure_component_df = read_csv_if_exists(INFRASTRUCTURE_COMPONENT_SUMMARY_FILE)
    development_df = read_csv_if_exists(DEVELOPMENT_FRICTION_LATEST_FILE)
    development_component_df = read_csv_if_exists(DEVELOPMENT_FRICTION_COMPONENT_SUMMARY_FILE)
    industry_df = read_csv_if_exists(GEOECONOMIC_INDUSTRY_LATEST_FILE)
    industry_component_df = read_csv_if_exists(GEOECONOMIC_INDUSTRY_COMPONENT_SUMMARY_FILE)
    household_df = read_csv_if_exists(HOUSEHOLD_VULNERABILITY_LATEST_FILE)
    household_component_df = read_csv_if_exists(HOUSEHOLD_VULNERABILITY_COMPONENT_SUMMARY_FILE)
    household_source_df = read_csv_if_exists(HOUSEHOLD_VULNERABILITY_SOURCE_SUMMARY_FILE)
    resilience_df = read_csv_if_exists(RESILIENCE_LATEST_FILE)
    resilience_component_df = read_csv_if_exists(RESILIENCE_COMPONENT_SUMMARY_FILE)
    component_df = read_csv_if_exists(COMPOSITE_COMPONENT_SUMMARY_FILE)
    change_df = read_csv_if_exists(CHANGE_DETECTION_FILE)
    sensitivity_results_df = read_csv_if_exists(SENSITIVITY_RESULTS_FILE)
    sensitivity_summary_df = read_csv_if_exists(SENSITIVITY_SUMMARY_FILE)
    breach_df = read_csv_if_exists(RISK_THRESHOLD_BREACH_FILE)
    breach_summary_df = read_csv_if_exists(RISK_THRESHOLD_BREACH_SUMMARY_FILE)

    doc = SimpleDocTemplate(
        str(REPORT_OUTPUT_PATH),
        pagesize=LETTER,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    story = []

    add_title_section(story, styles)
    add_executive_summary(story, styles, composite_df, scenario_df)
    add_key_findings(
        story,
        styles,
        composite_df,
        scenario_df,
        construction_df,
        growth_df,
        housing_df,
        infrastructure_df,
        development_df,
        industry_df,
        household_df,
        resilience_df,
    )
    add_latest_module_scores(
        story,
        styles,
        construction_df,
        growth_df,
        housing_df,
        infrastructure_df,
        development_df,
        industry_df,
        household_df,
        resilience_df,
    )

    story.append(PageBreak())

    add_results_reading_guide(
        story,
        styles,
        composite_df,
        scenario_df,
        breach_summary_df,
    )
    add_metric_measurement_guide(story, styles)
    add_fact_checking_and_validation_notes(story, styles)

    story.append(PageBreak())

    add_change_detection_section(story, styles, change_df)
    add_sensitivity_analysis_section(
        story,
        styles,
        sensitivity_summary_df,
        sensitivity_results_df,
    )
    add_risk_threshold_breach_section(
        story,
        styles,
        breach_summary_df,
        breach_df,
    )

    story.append(PageBreak())

    add_component_reading_notes(story, styles)
    add_component_summary(story, styles, component_df)
    add_scenario_section(story, styles, scenario_df)

    story.append(PageBreak())

    add_chart_interpretation_intro(story, styles)
    for title, chart_path in CHART_FILES.items():
        add_image_if_exists(story, chart_path, title, styles)

    story.append(PageBreak())

    add_housing_detail_section(
        story,
        styles,
        housing_df,
        housing_component_df,
    )
    add_infrastructure_detail_section(
        story,
        styles,
        infrastructure_df,
        infrastructure_component_df,
    )
    add_development_friction_detail_section(
        story,
        styles,
        development_df,
        development_component_df,
    )
    add_geoeconomic_industry_detail_section(
        story,
        styles,
        industry_df,
        industry_component_df,
    )
    add_household_vulnerability_detail_section(
        story,
        styles,
        household_df,
        household_component_df,
        household_source_df,
    )
    add_construction_detail_section(
        story,
        styles,
        construction_category_df,
        construction_component_df,
    )
    add_resilience_detail_section(story, styles, resilience_component_df)

    story.append(PageBreak())

    add_methodology_section(story, styles)
    add_limitations_section(story, styles, composite_df)
    add_local_source_notes_section(story, styles)

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    print(f"PDF report created: {REPORT_OUTPUT_PATH}")

    return REPORT_OUTPUT_PATH


def main() -> None:
    """
    Run report generation as a script.
    """

    build_report()


if __name__ == "__main__":
    main()
