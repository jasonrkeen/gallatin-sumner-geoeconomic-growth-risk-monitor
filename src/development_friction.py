"""
Development friction module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module estimates local development friction using curated local source notes.

Purpose:
- Replace the development_friction placeholder in the composite model.
- Measure pressure from zoning-code updates, planning/permitting activity,
  development pipeline intensity, public notice / agenda activity, and source
  confidence.
- Create a repeatable local policy and development-friction signal for
  Gallatin and Sumner County.

Inputs:
- data/raw/local_source_notes.csv

Outputs:
- data/processed/development_friction_scores.csv
- data/processed/development_friction_latest.csv
- data/processed/development_friction_component_summary.csv
- data/processed/development_friction_source_summary.csv
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

DEVELOPMENT_FRICTION_OUTPUT = (
    PROCESSED_DATA_DIR / "development_friction_scores.csv"
)
DEVELOPMENT_FRICTION_LATEST_OUTPUT = (
    PROCESSED_DATA_DIR / "development_friction_latest.csv"
)
DEVELOPMENT_FRICTION_COMPONENT_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "development_friction_component_summary.csv"
)
DEVELOPMENT_FRICTION_SOURCE_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "development_friction_source_summary.csv"
)


# ============================================================
# Model weights
# ============================================================

DEVELOPMENT_FRICTION_WEIGHTS = {
    "zoning_code_update_signal_score": 0.30,
    "planning_permitting_signal_score": 0.25,
    "development_pipeline_pressure_score": 0.20,
    "public_notice_agenda_activity_score": 0.15,
    "source_confidence_score": 0.10,
}


# ============================================================
# Keyword groups
# ============================================================

ZONING_CODE_KEYWORDS = [
    "zoning",
    "zoning code",
    "zoco",
    "code update",
    "land use",
    "rezoning",
    "planning review",
    "ordinance",
    "overlay",
    "growth pause",
    "policy transition",
]

PLANNING_PERMITTING_KEYWORDS = [
    "planning",
    "permit",
    "permits",
    "permitting",
    "building permit",
    "building permits",
    "building and codes",
    "codes",
    "approval",
    "approvals",
    "commission",
    "planning commission",
    "engineering",
    "review",
    "public notice",
    "agenda",
]

DEVELOPMENT_PIPELINE_KEYWORDS = [
    "development",
    "developments",
    "developer",
    "construction",
    "project",
    "projects",
    "site",
    "sites",
    "developable",
    "business attraction",
    "investment",
    "manufacturing",
    "distribution",
    "logistics",
    "growth",
    "expansion",
]

PUBLIC_NOTICE_AGENDA_KEYWORDS = [
    "agenda",
    "public notice",
    "hearing",
    "meeting",
    "commission",
    "board",
    "council",
    "approval",
    "rezoning",
    "ordinance",
    "review",
    "planning",
]


SOURCE_TYPE_WEIGHTS = {
    "official city website": 1.20,
    "official county website": 1.15,
    "city newsletter": 1.10,
    "public presentation": 1.05,
    "official economic development website": 1.00,
    "economic development website": 1.00,
}


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

        if value in {"", "null", "None", "N", "-"}:
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
        note_count * 8.0
        + unique_source_count * 7.0
        + min(keyword_hits * 3.0, 30.0)
        + min(weighted_source_strength * 4.0, 20.0)
    )

    return clamp_score(raw_score, upper=cap)


def score_source_confidence(
    total_relevant_notes: int,
    unique_sources: int,
    source_type_count: int,
) -> float:
    """
    Score confidence in the development-friction source base.
    """

    raw_score = (
        total_relevant_notes * 5.0
        + unique_sources * 10.0
        + source_type_count * 8.0
    )

    return clamp_score(raw_score, upper=90.0)


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


# ============================================================
# Source loading
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


# ============================================================
# Model
# ============================================================

def build_development_friction_model() -> pd.DataFrame:
    """
    Build development friction score.
    """

    notes_df = load_local_source_notes()

    zoning_subset, zoning_summary = build_signal_subset(
        notes_df=notes_df,
        keywords=ZONING_CODE_KEYWORDS,
        signal_name="zoning_code_update_signal",
    )

    planning_subset, planning_summary = build_signal_subset(
        notes_df=notes_df,
        keywords=PLANNING_PERMITTING_KEYWORDS,
        signal_name="planning_permitting_signal",
    )

    pipeline_subset, pipeline_summary = build_signal_subset(
        notes_df=notes_df,
        keywords=DEVELOPMENT_PIPELINE_KEYWORDS,
        signal_name="development_pipeline_pressure",
    )

    agenda_subset, agenda_summary = build_signal_subset(
        notes_df=notes_df,
        keywords=PUBLIC_NOTICE_AGENDA_KEYWORDS,
        signal_name="public_notice_agenda_activity",
    )

    relevant_notes = pd.concat(
        [zoning_subset, planning_subset, pipeline_subset, agenda_subset],
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
    )

    source_confidence_label = classify_source_confidence(source_confidence_score)

    component_scores = {
        "zoning_code_update_signal_score": zoning_summary[
            "zoning_code_update_signal_score"
        ],
        "planning_permitting_signal_score": planning_summary[
            "planning_permitting_signal_score"
        ],
        "development_pipeline_pressure_score": pipeline_summary[
            "development_pipeline_pressure_score"
        ],
        "public_notice_agenda_activity_score": agenda_summary[
            "public_notice_agenda_activity_score"
        ],
        "source_confidence_score": source_confidence_score,
    }

    development_friction_score = weighted_average(
        component_scores,
        DEVELOPMENT_FRICTION_WEIGHTS,
    )

    result = pd.DataFrame(
        [
            {
                "date": pd.Timestamp.today().normalize(),
                "development_friction_score": development_friction_score,
                "development_friction_signal": safe_classify_risk(
                    development_friction_score
                ),
                "source_confidence_score": source_confidence_score,
                "source_confidence_label": source_confidence_label,
                "total_relevant_notes": total_relevant_notes,
                "unique_sources": unique_sources,
                "source_type_count": source_type_count,
                "zoning_code_note_count": zoning_summary[
                    "zoning_code_update_signal_note_count"
                ],
                "planning_permitting_note_count": planning_summary[
                    "planning_permitting_signal_note_count"
                ],
                "development_pipeline_note_count": pipeline_summary[
                    "development_pipeline_pressure_note_count"
                ],
                "public_notice_agenda_note_count": agenda_summary[
                    "public_notice_agenda_activity_note_count"
                ],
                "data_quality_flag": source_confidence_label,
                **component_scores,
            }
        ]
    )

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    result.to_csv(DEVELOPMENT_FRICTION_OUTPUT, index=False)
    result.to_csv(DEVELOPMENT_FRICTION_LATEST_OUTPUT, index=False)

    component_summary = build_component_summary(result.iloc[0])
    component_summary.to_csv(
        DEVELOPMENT_FRICTION_COMPONENT_SUMMARY_OUTPUT,
        index=False,
    )

    source_summary = build_source_summary(
        zoning_summary=zoning_summary,
        planning_summary=planning_summary,
        pipeline_summary=pipeline_summary,
        agenda_summary=agenda_summary,
        source_confidence_score=source_confidence_score,
        source_confidence_label=source_confidence_label,
        total_relevant_notes=total_relevant_notes,
        unique_sources=unique_sources,
        source_type_count=source_type_count,
    )
    source_summary.to_csv(DEVELOPMENT_FRICTION_SOURCE_SUMMARY_OUTPUT, index=False)

    print(f"Saved development friction scores to: {DEVELOPMENT_FRICTION_OUTPUT}")
    print(f"Saved latest development friction score to: {DEVELOPMENT_FRICTION_LATEST_OUTPUT}")
    print(f"Saved development friction component summary to: {DEVELOPMENT_FRICTION_COMPONENT_SUMMARY_OUTPUT}")
    print(f"Saved development friction source summary to: {DEVELOPMENT_FRICTION_SOURCE_SUMMARY_OUTPUT}")

    return result


def build_component_summary(latest_row: pd.Series) -> pd.DataFrame:
    """
    Build component summary for latest development friction score.
    """

    component_labels = {
        "zoning_code_update_signal_score": "Zoning / Code Update Signal",
        "planning_permitting_signal_score": "Planning / Permitting Signal",
        "development_pipeline_pressure_score": "Development Pipeline Pressure",
        "public_notice_agenda_activity_score": "Public Notice / Agenda Activity",
        "source_confidence_score": "Source Confidence",
    }

    rows = []

    for component, weight in DEVELOPMENT_FRICTION_WEIGHTS.items():
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


def build_source_summary(
    zoning_summary: dict[str, object],
    planning_summary: dict[str, object],
    pipeline_summary: dict[str, object],
    agenda_summary: dict[str, object],
    source_confidence_score: float,
    source_confidence_label: str,
    total_relevant_notes: int,
    unique_sources: int,
    source_type_count: int,
) -> pd.DataFrame:
    """
    Build source summary table.
    """

    return pd.DataFrame(
        [
            {
                "total_relevant_notes": total_relevant_notes,
                "unique_sources": unique_sources,
                "source_type_count": source_type_count,
                "source_confidence_score": source_confidence_score,
                "source_confidence_label": source_confidence_label,
                **zoning_summary,
                **planning_summary,
                **pipeline_summary,
                **agenda_summary,
            }
        ]
    )


def summarize_development_friction(result: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Print latest development friction summary.
    """

    if result is None:
        if not DEVELOPMENT_FRICTION_LATEST_OUTPUT.exists():
            raise FileNotFoundError(
                "No development friction latest file found. "
                "Run build_development_friction_model() first."
            )

        latest = pd.read_csv(DEVELOPMENT_FRICTION_LATEST_OUTPUT)
    else:
        latest = result.copy()

    print()
    print("Development Friction Summary")
    print("----------------------------")

    display_cols = [
        "date",
        "development_friction_score",
        "development_friction_signal",
        "source_confidence_label",
        "total_relevant_notes",
        "unique_sources",
        "zoning_code_note_count",
        "planning_permitting_note_count",
        "development_pipeline_note_count",
        "public_notice_agenda_note_count",
        "data_quality_flag",
    ]

    display_cols = [col for col in display_cols if col in latest.columns]

    print(latest[display_cols].to_string(index=False))

    return latest


def main() -> None:
    """
    Run development friction module as a script.
    """

    result = build_development_friction_model()
    summarize_development_friction(result)


if __name__ == "__main__":
    main()