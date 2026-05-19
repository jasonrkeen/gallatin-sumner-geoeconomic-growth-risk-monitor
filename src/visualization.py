"""
Visualization module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module creates chart outputs for:
- Composite geoeconomic growth risk score
- Scenario forecast comparison
- Construction shock trend
- Construction shock category scores
- Growth pressure trend
- Local resilience offset components
- Sensitivity analysis results
- Risk threshold breach monitor

Inputs:
- data/processed/composite_risk_score_latest.csv
- data/processed/scenario_forecast_summary.csv
- data/processed/construction_shock_scores.csv
- data/processed/construction_shock_category_summary.csv
- data/processed/growth_pressure_scores.csv
- data/processed/local_resilience_component_summary.csv
- data/processed/sensitivity_analysis_results.csv
- data/processed/sensitivity_analysis_summary.csv
- data/processed/risk_threshold_breaches.csv
- data/processed/risk_threshold_breach_summary.csv

Outputs:
- outputs/charts/composite_risk_score.png
- outputs/charts/scenario_comparison.png
- outputs/charts/construction_shock_trend.png
- outputs/charts/construction_shock_categories.png
- outputs/charts/growth_pressure_trend.png
- outputs/charts/local_resilience_offset.png
- outputs/charts/sensitivity_analysis.png
- outputs/charts/risk_threshold_breaches.png
"""

from __future__ import annotations

import textwrap

import matplotlib.pyplot as plt
import pandas as pd

from src.config import CHARTS_DIR, PROCESSED_DATA_DIR


# ============================================================
# Input files
# ============================================================

COMPOSITE_LATEST_FILE = PROCESSED_DATA_DIR / "composite_risk_score_latest.csv"
SCENARIO_SUMMARY_FILE = PROCESSED_DATA_DIR / "scenario_forecast_summary.csv"
CONSTRUCTION_SHOCK_FILE = PROCESSED_DATA_DIR / "construction_shock_scores.csv"
CONSTRUCTION_CATEGORY_FILE = PROCESSED_DATA_DIR / "construction_shock_category_summary.csv"
GROWTH_PRESSURE_FILE = PROCESSED_DATA_DIR / "growth_pressure_scores.csv"
LOCAL_RESILIENCE_COMPONENT_FILE = (
    PROCESSED_DATA_DIR / "local_resilience_component_summary.csv"
)
SENSITIVITY_RESULTS_FILE = PROCESSED_DATA_DIR / "sensitivity_analysis_results.csv"
SENSITIVITY_SUMMARY_FILE = PROCESSED_DATA_DIR / "sensitivity_analysis_summary.csv"
RISK_THRESHOLD_BREACH_FILE = PROCESSED_DATA_DIR / "risk_threshold_breaches.csv"
RISK_THRESHOLD_BREACH_SUMMARY_FILE = (
    PROCESSED_DATA_DIR / "risk_threshold_breach_summary.csv"
)


# ============================================================
# Output chart files
# ============================================================

COMPOSITE_RISK_CHART = CHARTS_DIR / "composite_risk_score.png"
SCENARIO_COMPARISON_CHART = CHARTS_DIR / "scenario_comparison.png"
CONSTRUCTION_SHOCK_TREND_CHART = CHARTS_DIR / "construction_shock_trend.png"
CONSTRUCTION_CATEGORY_CHART = CHARTS_DIR / "construction_shock_categories.png"
GROWTH_PRESSURE_TREND_CHART = CHARTS_DIR / "growth_pressure_trend.png"
LOCAL_RESILIENCE_CHART = CHARTS_DIR / "local_resilience_offset.png"
SENSITIVITY_ANALYSIS_CHART = CHARTS_DIR / "sensitivity_analysis.png"
RISK_THRESHOLD_BREACH_CHART = CHARTS_DIR / "risk_threshold_breaches.png"


# ============================================================
# Helpers
# ============================================================

def wrap_labels(labels: list[str], width: int = 22) -> list[str]:
    """
    Wrap long chart labels.
    """

    return ["\n".join(textwrap.wrap(str(label), width=width)) for label in labels]


def load_csv(path) -> pd.DataFrame:
    """
    Load a CSV with a clear error if it is missing.
    """

    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    return pd.read_csv(path)


def add_score_bands(ax, orientation: str = "horizontal") -> None:
    """
    Add score bands for 0-100 risk interpretation.
    """

    if orientation == "horizontal":
        ax.axhspan(0, 25, alpha=0.08)
        ax.axhspan(25, 50, alpha=0.08)
        ax.axhspan(50, 75, alpha=0.08)
        ax.axhspan(75, 100, alpha=0.08)

        ax.axhline(25, linewidth=1, linestyle="--", alpha=0.6)
        ax.axhline(50, linewidth=1, linestyle="--", alpha=0.6)
        ax.axhline(75, linewidth=1, linestyle="--", alpha=0.6)

        ax.text(0.01, 0.22, "Low", transform=ax.transAxes, fontsize=8, alpha=0.8)
        ax.text(0.01, 0.47, "Moderate", transform=ax.transAxes, fontsize=8, alpha=0.8)
        ax.text(0.01, 0.72, "Elevated", transform=ax.transAxes, fontsize=8, alpha=0.8)
        ax.text(0.01, 0.93, "High", transform=ax.transAxes, fontsize=8, alpha=0.8)

    elif orientation == "vertical":
        ax.axvspan(0, 25, alpha=0.08)
        ax.axvspan(25, 50, alpha=0.08)
        ax.axvspan(50, 75, alpha=0.08)
        ax.axvspan(75, 100, alpha=0.08)

        ax.axvline(25, linewidth=1, linestyle="--", alpha=0.6)
        ax.axvline(50, linewidth=1, linestyle="--", alpha=0.6)
        ax.axvline(75, linewidth=1, linestyle="--", alpha=0.6)


def add_chart_footer(fig, text: str) -> None:
    """
    Add a small source / methodology note at the bottom of a chart.
    """

    fig.text(
        0.01,
        0.01,
        text,
        ha="left",
        va="bottom",
        fontsize=7,
        alpha=0.75,
    )


def safe_float(value, default=0.0) -> float:
    """
    Safely convert a value to float.
    """

    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def fmt_score(value) -> str:
    """
    Format score values for chart labels.
    """

    try:
        return f"{float(value):.1f}"
    except Exception:
        return "N/A"


def parse_bool(value) -> bool:
    """
    Parse bool-like values safely from booleans, strings, or numbers.
    """

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    return str(value).strip().lower() in {"true", "1", "yes", "y"}


# ============================================================
# Chart builders
# ============================================================

def save_composite_risk_chart() -> str:
    """
    Save a chart showing composite risk, resilience credit, and adjusted risk.
    """

    df = load_csv(COMPOSITE_LATEST_FILE)

    if df.empty:
        raise ValueError(f"{COMPOSITE_LATEST_FILE} is empty.")

    row = df.iloc[0]

    chart_df = pd.DataFrame(
        {
            "metric": [
                "Composite Risk Score",
                "Resilience Credit Applied",
                "Adjusted Risk Score",
            ],
            "score": [
                safe_float(row.get("composite_risk_score", 0)),
                safe_float(row.get("resilience_credit_applied", 0)),
                safe_float(row.get("adjusted_geoeconomic_growth_risk_score", 0)),
            ],
        }
    )

    model_maturity = row.get("model_maturity_level", "N/A")
    data_quality = row.get("data_quality_flag", "N/A")
    placeholder_share = safe_float(row.get("placeholder_share", 0)) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(chart_df["metric"], chart_df["score"])

    for idx, value in enumerate(chart_df["score"]):
        ax.text(idx, value + 2, f"{value:.1f}", ha="center", fontsize=10)

    add_score_bands(ax, orientation="horizontal")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Score, 0-100")
    ax.set_title("Gallatin-Sumner Composite Risk and Resilience Adjustment")
    ax.set_xticks(range(len(chart_df)))
    ax.set_xticklabels(wrap_labels(chart_df["metric"].tolist(), width=18))
    ax.grid(axis="y", alpha=0.25)

    add_chart_footer(
        fig,
        f"Model maturity: {model_maturity} | Data quality: {data_quality} | "
        f"Placeholder share: {placeholder_share:.1f}%",
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(COMPOSITE_RISK_CHART, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved composite risk chart to: {COMPOSITE_RISK_CHART}")
    return str(COMPOSITE_RISK_CHART)


def save_scenario_comparison_chart() -> str:
    """
    Save scenario forecast comparison chart.
    """

    df = load_csv(SCENARIO_SUMMARY_FILE)

    if df.empty:
        raise ValueError(f"{SCENARIO_SUMMARY_FILE} is empty.")

    df = df.sort_values("scenario_adjusted_risk_score", ascending=True).copy()

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.barh(df["scenario_name"], df["scenario_adjusted_risk_score"])

    for idx, value in enumerate(df["scenario_adjusted_risk_score"]):
        label = f"{value:.1f}"

        if "scenario_delta_vs_adjusted_baseline" in df.columns:
            delta = df.iloc[idx]["scenario_delta_vs_adjusted_baseline"]
            if pd.notna(delta):
                label = f"{value:.1f} ({delta:+.1f})"

        ax.text(value + 1.5, idx, label, va="center", fontsize=9)

    add_score_bands(ax, orientation="vertical")
    ax.set_xlim(0, 110)
    ax.set_xlabel("Scenario Adjusted Risk Score, 0-100")
    ax.set_title("Scenario Forecast Risk Comparison")
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(wrap_labels(df["scenario_name"].tolist(), width=24))
    ax.grid(axis="x", alpha=0.25)

    if "model_maturity_level" in df.columns and "data_quality_flag" in df.columns:
        add_chart_footer(
            fig,
            f"Labels show score and delta vs. adjusted baseline where available. "
            f"Model maturity: {df.iloc[0]['model_maturity_level']} | "
            f"Data quality: {df.iloc[0]['data_quality_flag']}",
        )
    else:
        add_chart_footer(
            fig,
            "Labels show score and delta vs. adjusted baseline where available.",
        )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(SCENARIO_COMPARISON_CHART, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved scenario comparison chart to: {SCENARIO_COMPARISON_CHART}")
    return str(SCENARIO_COMPARISON_CHART)


def save_construction_shock_trend_chart() -> str:
    """
    Save construction shock score trend chart.
    """

    df = load_csv(CONSTRUCTION_SHOCK_FILE)

    if df.empty:
        raise ValueError(f"{CONSTRUCTION_SHOCK_FILE} is empty.")

    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["construction_shock_score"]).sort_values("date")

    if len(df) > 120:
        df = df.tail(120)

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        df["date"],
        df["construction_shock_score"],
        linewidth=2,
        label="Construction Shock Score",
    )

    if "construction_shock_score_3m_ma" in df.columns:
        ax.plot(
            df["date"],
            df["construction_shock_score_3m_ma"],
            linewidth=1.5,
            linestyle="--",
            label="3-Month Average",
        )

    if "construction_shock_score_12m_ma" in df.columns:
        ax.plot(
            df["date"],
            df["construction_shock_score_12m_ma"],
            linewidth=1.5,
            linestyle=":",
            label="12-Month Average",
        )

    add_score_bands(ax, orientation="horizontal")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Construction Shock Score, 0-100")
    ax.set_title("Construction Shock Exposure Trend")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)

    latest = df.tail(1).iloc[0]
    footer = "Construction shock score uses input-cost, fuel/energy, and financing indicators."

    if "construction_shock_momentum_signal" in latest.index:
        footer += f" Latest momentum: {latest['construction_shock_momentum_signal']}."

    if "data_quality_flag" in latest.index:
        footer += f" Data quality: {latest['data_quality_flag']}."

    add_chart_footer(fig, footer)

    fig.autofmt_xdate()
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(CONSTRUCTION_SHOCK_TREND_CHART, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved construction shock trend chart to: {CONSTRUCTION_SHOCK_TREND_CHART}")
    return str(CONSTRUCTION_SHOCK_TREND_CHART)


def save_construction_category_chart() -> str:
    """
    Save latest construction shock category chart.
    """

    df = load_csv(CONSTRUCTION_CATEGORY_FILE)

    if df.empty:
        raise ValueError(f"{CONSTRUCTION_CATEGORY_FILE} is empty.")

    if "category_label" not in df.columns:
        df["category_label"] = df["category"]

    df = df.sort_values("category_score", ascending=True).copy()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["category_label"], df["category_score"])

    for idx, value in enumerate(df["category_score"]):
        ax.text(value + 1.5, idx, f"{value:.1f}", va="center", fontsize=9)

    add_score_bands(ax, orientation="vertical")
    ax.set_xlim(0, 110)
    ax.set_xlabel("Category Shock Score, 0-100")
    ax.set_title("Construction Shock Category Breakdown")
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(wrap_labels(df["category_label"].tolist(), width=24))
    ax.grid(axis="x", alpha=0.25)

    add_chart_footer(
        fig,
        "Category scores summarize materials, fuel/energy, and financing conditions.",
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(CONSTRUCTION_CATEGORY_CHART, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved construction category chart to: {CONSTRUCTION_CATEGORY_CHART}")
    return str(CONSTRUCTION_CATEGORY_CHART)


def save_growth_pressure_trend_chart() -> str:
    """
    Save growth pressure trend chart.
    """

    df = load_csv(GROWTH_PRESSURE_FILE)

    if df.empty:
        raise ValueError(f"{GROWTH_PRESSURE_FILE} is empty.")

    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["growth_pressure_score"]).sort_values("date")

    fig, ax = plt.subplots(figsize=(11, 6))

    if "historical_growth_pressure_score" in df.columns:
        ax.plot(
            df["date"],
            df["historical_growth_pressure_score"],
            marker="o",
            linewidth=1.5,
            linestyle="--",
            label="Historical Economic Score",
        )

    ax.plot(
        df["date"],
        df["growth_pressure_score"],
        marker="o",
        linewidth=2,
        label="Growth Pressure Score",
    )

    add_score_bands(ax, orientation="horizontal")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Growth Pressure Score, 0-100")
    ax.set_title("Sumner County Growth Pressure Trend")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)

    latest = df.tail(1).iloc[0]
    footer = "Historical scores use economic data. Latest score may include current local-source signal."

    if "local_source_signal_confidence" in latest.index:
        footer += f" Local signal: {latest['local_source_signal_confidence']}."

    if "data_quality_flag" in latest.index:
        footer += f" Data quality: {latest['data_quality_flag']}."

    add_chart_footer(fig, footer)

    fig.autofmt_xdate()
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(GROWTH_PRESSURE_TREND_CHART, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved growth pressure trend chart to: {GROWTH_PRESSURE_TREND_CHART}")
    return str(GROWTH_PRESSURE_TREND_CHART)


def save_local_resilience_chart() -> str:
    """
    Save local resilience offset component chart.
    """

    df = load_csv(LOCAL_RESILIENCE_COMPONENT_FILE)

    if df.empty:
        raise ValueError(f"{LOCAL_RESILIENCE_COMPONENT_FILE} is empty.")

    required_cols = {"component", "component_score"}

    if not required_cols.issubset(set(df.columns)):
        raise ValueError(
            f"{LOCAL_RESILIENCE_COMPONENT_FILE} must contain columns: {required_cols}"
        )

    chart_df = df.copy()
    chart_df["component_label"] = (
        chart_df["component"].astype(str).str.replace("_", " ").str.title()
    )

    chart_df = chart_df.sort_values("component_score", ascending=True)

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.barh(chart_df["component_label"], chart_df["component_score"])

    for idx, value in enumerate(chart_df["component_score"]):
        label = f"{value:.1f}"

        if "evidence_confidence" in chart_df.columns:
            confidence = chart_df.iloc[idx]["evidence_confidence"]
            label = f"{value:.1f} | {confidence}"

        ax.text(value + 1.5, idx, label, va="center", fontsize=8)

    add_score_bands(ax, orientation="vertical")
    ax.set_xlim(0, 110)
    ax.set_xlabel("Resilience Component Score, 0-100")
    ax.set_title("Local Resilience Offset Components")
    ax.set_yticks(range(len(chart_df)))
    ax.set_yticklabels(wrap_labels(chart_df["component_label"].tolist(), width=28))
    ax.grid(axis="x", alpha=0.25)

    add_chart_footer(
        fig,
        "Resilience scores use conservative evidence tiers from curated local source notes.",
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(LOCAL_RESILIENCE_CHART, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved local resilience chart to: {LOCAL_RESILIENCE_CHART}")
    return str(LOCAL_RESILIENCE_CHART)


def save_sensitivity_analysis_chart() -> str:
    """
    Save sensitivity analysis chart.
    """

    df = load_csv(SENSITIVITY_RESULTS_FILE)

    if df.empty:
        raise ValueError(f"{SENSITIVITY_RESULTS_FILE} is empty.")

    df = df.sort_values("sensitivity_adjusted_risk_score", ascending=True).copy()

    fig, ax = plt.subplots(figsize=(11, 7))

    ax.barh(df["case_name"], df["sensitivity_adjusted_risk_score"])

    for idx, row in df.reset_index(drop=True).iterrows():
        value = row["sensitivity_adjusted_risk_score"]
        signal = row.get("sensitivity_adjusted_signal", "N/A")
        ax.text(value + 1.5, idx, f"{value:.1f} | {signal}", va="center", fontsize=8)

    add_score_bands(ax, orientation="vertical")
    ax.set_xlim(0, 110)
    ax.set_xlabel("Adjusted Risk Score, 0-100")
    ax.set_title("Sensitivity Analysis: Adjusted Risk by Weighting Case")
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(wrap_labels(df["case_name"].tolist(), width=28))
    ax.grid(axis="x", alpha=0.25)

    footer = (
        "Sensitivity analysis tests whether the model conclusion changes under "
        "alternative weighting assumptions."
    )

    try:
        summary_df = load_csv(SENSITIVITY_SUMMARY_FILE)
        if not summary_df.empty:
            stability = summary_df.iloc[0].get("sensitivity_stability", "N/A")
            score_range = summary_df.iloc[0].get("adjusted_risk_score_range", "N/A")
            footer += f" Stability: {stability}. Score range: {float(score_range):.1f}."
    except Exception:
        pass

    add_chart_footer(fig, footer)

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(SENSITIVITY_ANALYSIS_CHART, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved sensitivity analysis chart to: {SENSITIVITY_ANALYSIS_CHART}")
    return str(SENSITIVITY_ANALYSIS_CHART)


def save_risk_threshold_breach_chart() -> str:
    """
    Save risk threshold breach monitor chart.
    """

    df = load_csv(RISK_THRESHOLD_BREACH_FILE)

    if df.empty:
        raise ValueError(f"{RISK_THRESHOLD_BREACH_FILE} is empty.")

    if "is_breached" not in df.columns:
        raise ValueError(f"{RISK_THRESHOLD_BREACH_FILE} must contain is_breached.")

    df = df.copy()
    df["is_breached_bool"] = df["is_breached"].apply(parse_bool)
    active_df = df[df["is_breached_bool"]].copy()

    if active_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.axis("off")
        ax.text(
            0.5,
            0.55,
            "No Active Threshold Breaches",
            ha="center",
            va="center",
            fontsize=18,
            fontweight="bold",
        )
        ax.text(
            0.5,
            0.42,
            "The current run did not cross configured breach thresholds.",
            ha="center",
            va="center",
            fontsize=10,
        )

        add_chart_footer(
            fig,
            "Threshold breach monitor tracks growth, construction, scenario, resilience, and model-quality warning levels.",
        )

        fig.tight_layout(rect=[0, 0.04, 1, 1])
        fig.savefig(RISK_THRESHOLD_BREACH_CHART, dpi=300, bbox_inches="tight")
        plt.close(fig)

        print(f"Saved risk threshold breach chart to: {RISK_THRESHOLD_BREACH_CHART}")
        return str(RISK_THRESHOLD_BREACH_CHART)

    active_df["distance_to_threshold"] = active_df["distance_to_threshold"].apply(
        lambda value: safe_float(value, 0.0)
    )
    active_df["severity_score"] = active_df["severity_score"].apply(
        lambda value: safe_float(value, 0.0)
    )

    active_df = active_df.sort_values(
        ["severity_score", "distance_to_threshold"],
        ascending=[False, False],
    ).head(10)

    active_df["label"] = (
        active_df["category"].astype(str)
        + ": "
        + active_df["metric"].astype(str).str.replace("_", " ").str.title()
    )

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.barh(active_df["label"], active_df["distance_to_threshold"])

    for idx, row in active_df.reset_index(drop=True).iterrows():
        value = safe_float(row.get("distance_to_threshold"), 0.0)
        current_value = fmt_score(row.get("current_value", "N/A"))
        threshold = fmt_score(row.get("threshold", "N/A"))
        severity = row.get("severity", "N/A")

        ax.text(
            value + 0.5,
            idx,
            f"+{value:.1f} | {current_value} vs {threshold} | {severity}",
            va="center",
            fontsize=7.5,
        )

    ax.set_xlabel("Distance Beyond Threshold")
    ax.set_title("Risk Threshold Breach Monitor: Active Breaches")
    ax.set_yticks(range(len(active_df)))
    ax.set_yticklabels(wrap_labels(active_df["label"].tolist(), width=35))
    ax.grid(axis="x", alpha=0.25)

    footer = "Bars show how far each active metric is beyond its configured warning threshold."

    try:
        summary_df = load_csv(RISK_THRESHOLD_BREACH_SUMMARY_FILE)
        if not summary_df.empty:
            alert_level = summary_df.iloc[0].get("alert_level", "N/A")
            top_category = summary_df.iloc[0].get("top_breach_category", "N/A")
            footer += f" Alert level: {alert_level}. Top category: {top_category}."
    except Exception:
        pass

    add_chart_footer(fig, footer)

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(RISK_THRESHOLD_BREACH_CHART, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved risk threshold breach chart to: {RISK_THRESHOLD_BREACH_CHART}")
    return str(RISK_THRESHOLD_BREACH_CHART)


# ============================================================
# Build all charts
# ============================================================

def build_all_charts() -> list[str]:
    """
    Build all project charts.
    """

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    chart_paths = []

    chart_functions = [
        save_composite_risk_chart,
        save_scenario_comparison_chart,
        save_construction_shock_trend_chart,
        save_construction_category_chart,
        save_growth_pressure_trend_chart,
        save_local_resilience_chart,
        save_sensitivity_analysis_chart,
        save_risk_threshold_breach_chart,
    ]

    for chart_function in chart_functions:
        try:
            chart_paths.append(chart_function())
        except Exception as exc:
            print(f"WARNING: Failed to build chart {chart_function.__name__}: {exc}")

    return chart_paths


def main() -> None:
    """
    Run visualization module as a script.
    """

    chart_paths = build_all_charts()

    print()
    print("Chart build complete.")
    for path in chart_paths:
        print(f" - {path}")


if __name__ == "__main__":
    main()