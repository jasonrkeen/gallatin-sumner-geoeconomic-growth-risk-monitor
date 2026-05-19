"""
Local resilience scoring module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module estimates a Local Resilience Offset using manually curated local source
notes related to utility coordination, public works capacity, stormwater/flood
mitigation, public safety response, and capital project execution.

Inputs:
- data/raw/local_source_notes.csv

Outputs:
- data/processed/local_resilience_scores.csv
- data/processed/local_resilience_latest.csv
- data/processed/local_resilience_component_summary.csv
- data/processed/local_resilience_source_summary.csv

Interpretation:
- Higher resilience scores reduce the final adjusted geoeconomic growth risk score.
- This module does not measure risk directly; it measures local capacity to absorb stress.
- Version 2 uses evidence tiers and confidence labels so a few keyword matches do not
  automatically create maximum resilience scores.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import (
    LOCAL_SOURCE_NOTES_FILE,
    PROCESSED_DATA_DIR,
    RESILIENCE_OFFSET_WEIGHTS,
)


LOCAL_RESILIENCE_OUTPUT = PROCESSED_DATA_DIR / "local_resilience_scores.csv"
LOCAL_RESILIENCE_LATEST_OUTPUT = PROCESSED_DATA_DIR / "local_resilience_latest.csv"
LOCAL_RESILIENCE_COMPONENT_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "local_resilience_component_summary.csv"
)
LOCAL_RESILIENCE_SOURCE_SUMMARY_OUTPUT = (
    PROCESSED_DATA_DIR / "local_resilience_source_summary.csv"
)


# ============================================================
# Local resilience keyword mapping
# ============================================================

RESILIENCE_COMPONENT_KEYWORDS = {
    "utility_coordination": [
        "utility",
        "utilities",
        "electric",
        "electricity",
        "water",
        "sewer",
        "gas",
        "repairs",
        "service",
        "capacity",
        "coordinate",
        "coordination",
    ],
    "public_works_capacity": [
        "public works",
        "roads",
        "road",
        "salt",
        "plowed",
        "treated",
        "storm response",
        "tree",
        "tree-trimming",
        "crews",
        "lane miles",
        "intersections",
    ],
    "stormwater_flood_mitigation": [
        "stormwater",
        "flood",
        "flood mitigation",
        "drainage",
        "water away",
        "mitigation",
        "realignment",
    ],
    "public_safety_response": [
        "police",
        "fire",
        "emergency",
        "public safety",
        "shelter",
        "crisis",
        "response",
        "recovery",
    ],
    "capital_project_execution": [
        "construction",
        "project",
        "bidding",
        "completion",
        "completed",
        "park",
        "clearview",
        "realignment",
        "investment",
        "roads",
        "materials",
        "weather permitting",
    ],
}


RESILIENCE_RELATED_CHANNELS = {
    "local_resilience",
    "infrastructure_resilience",
    "infrastructure_strain",
    "construction_risk",
}


# Source type weights are intentionally modest.
# Official sources are valuable, but they still require specific evidence.
SOURCE_TYPE_WEIGHTS = {
    "city newsletter": 1.15,
    "official city website": 1.15,
    "official county website": 1.15,
    "economic development website": 1.05,
    "official economic development website": 1.05,
    "public presentation": 1.00,
}


# Maximum score allowed by evidence confidence tier.
# This avoids a small number of notes creating automatic 100s.
CONFIDENCE_SCORE_CAPS = {
    "No Evidence": 0.0,
    "Limited Evidence": 35.0,
    "Moderate Evidence": 55.0,
    "Strong Evidence": 75.0,
    "Very Strong Evidence": 90.0,
}


def load_local_source_notes(path=LOCAL_SOURCE_NOTES_FILE) -> pd.DataFrame:
    """
    Load manually curated local source notes.
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
        print(f"WARNING: Could not find {path}. Local resilience score will be set to zero.")
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


def build_search_text(notes_df: pd.DataFrame) -> pd.Series:
    """
    Combine fields into one lowercase text series for keyword matching.
    """

    if notes_df.empty:
        return pd.Series(dtype=str)

    return (
        notes_df["topic"].fillna("").astype(str)
        + " "
        + notes_df["key_point"].fillna("").astype(str)
        + " "
        + notes_df["risk_channel"].fillna("").astype(str)
        + " "
        + notes_df["source_name"].fillna("").astype(str)
    ).str.lower()


def match_component_notes(
    notes_df: pd.DataFrame,
    keywords: list[str],
) -> pd.DataFrame:
    """
    Return notes matching any component keyword.
    """

    if notes_df.empty:
        return notes_df.copy()

    search_text = build_search_text(notes_df)
    match_mask = pd.Series(False, index=notes_df.index)

    for keyword in keywords:
        match_mask = match_mask | search_text.str.contains(keyword.lower(), regex=False)

    matched = notes_df[match_mask].copy()

    if matched.empty:
        matched["keyword_hit_count"] = []
        return matched

    keyword_hit_counts = []

    for idx in matched.index:
        text = search_text.loc[idx]
        hits = sum(1 for keyword in keywords if keyword.lower() in text)
        keyword_hit_counts.append(hits)

    matched["keyword_hit_count"] = keyword_hit_counts

    return matched


def classify_evidence_confidence(
    evidence_note_count: int,
    unique_source_count: int,
    related_channel_count: int,
    keyword_hit_count: int,
) -> str:
    """
    Classify the strength of evidence supporting a resilience component.

    This is intentionally conservative because local source notes are qualitative.
    """

    if evidence_note_count == 0:
        return "No Evidence"

    if evidence_note_count == 1 and unique_source_count <= 1:
        return "Limited Evidence"

    if evidence_note_count >= 2 and unique_source_count >= 1:
        if related_channel_count >= 2 or keyword_hit_count >= 4:
            return "Moderate Evidence"
        return "Limited Evidence"

    if evidence_note_count >= 3 and unique_source_count >= 2:
        if related_channel_count >= 2 and keyword_hit_count >= 5:
            return "Strong Evidence"
        return "Moderate Evidence"

    if evidence_note_count >= 5 and unique_source_count >= 3:
        if related_channel_count >= 3 and keyword_hit_count >= 8:
            return "Very Strong Evidence"
        return "Strong Evidence"

    return "Moderate Evidence"


def source_type_multiplier(matched_notes: pd.DataFrame) -> float:
    """
    Calculate a modest source-quality multiplier based on source type.
    """

    if matched_notes.empty or "source_type" not in matched_notes.columns:
        return 1.0

    multipliers = []

    for source_type in matched_notes["source_type"].fillna("").astype(str).str.lower():
        multipliers.append(SOURCE_TYPE_WEIGHTS.get(source_type, 1.0))

    if not multipliers:
        return 1.0

    # Average keeps this from becoming too aggressive.
    return float(np.mean(multipliers))


def score_component_from_notes(
    notes_df: pd.DataFrame,
    component: str,
    keywords: list[str],
) -> dict[str, object]:
    """
    Score one resilience component from source notes.

    Version 2 scoring logic:
    - Match relevant notes using component keywords.
    - Count unique source names.
    - Count explicitly related resilience/infrastructure channels.
    - Count total keyword hits.
    - Apply conservative evidence tier caps.
    - Apply a modest source-type multiplier.
    """

    if notes_df.empty:
        return {
            "component": component,
            "component_score": 0.0,
            "evidence_confidence": "No Evidence",
            "evidence_note_count": 0,
            "unique_source_count": 0,
            "related_channel_count": 0,
            "keyword_hit_count": 0,
            "source_type_multiplier": 1.0,
            "score_cap": 0.0,
        }

    matched_notes = match_component_notes(notes_df, keywords)

    if matched_notes.empty:
        return {
            "component": component,
            "component_score": 0.0,
            "evidence_confidence": "No Evidence",
            "evidence_note_count": 0,
            "unique_source_count": 0,
            "related_channel_count": 0,
            "keyword_hit_count": 0,
            "source_type_multiplier": 1.0,
            "score_cap": 0.0,
        }

    evidence_note_count = len(matched_notes)
    unique_source_count = matched_notes["source_name"].nunique()
    related_channel_count = int(
        matched_notes["risk_channel"].isin(RESILIENCE_RELATED_CHANNELS).sum()
    )
    keyword_hit_count = int(matched_notes["keyword_hit_count"].sum())

    confidence = classify_evidence_confidence(
        evidence_note_count=evidence_note_count,
        unique_source_count=unique_source_count,
        related_channel_count=related_channel_count,
        keyword_hit_count=keyword_hit_count,
    )

    score_cap = CONFIDENCE_SCORE_CAPS[confidence]
    multiplier = source_type_multiplier(matched_notes)

    # Base score is intentionally conservative.
    raw_score = (
        evidence_note_count * 12.0
        + unique_source_count * 8.0
        + related_channel_count * 5.0
        + min(keyword_hit_count * 2.0, 20.0)
    )

    adjusted_score = raw_score * multiplier
    component_score = min(adjusted_score, score_cap)

    return {
        "component": component,
        "component_score": float(component_score),
        "evidence_confidence": confidence,
        "evidence_note_count": evidence_note_count,
        "unique_source_count": unique_source_count,
        "related_channel_count": related_channel_count,
        "keyword_hit_count": keyword_hit_count,
        "source_type_multiplier": float(multiplier),
        "score_cap": float(score_cap),
    }


def build_resilience_component_scores(notes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a component score table for local resilience.
    """

    rows = []

    for component, keywords in RESILIENCE_COMPONENT_KEYWORDS.items():
        score_info = score_component_from_notes(notes_df, component, keywords)
        weight = RESILIENCE_OFFSET_WEIGHTS.get(component, 0.0)

        rows.append(
            {
                "component": component,
                "weight": weight,
                "component_score": score_info["component_score"],
                "weighted_contribution": score_info["component_score"] * weight,
                "evidence_confidence": score_info["evidence_confidence"],
                "evidence_note_count": score_info["evidence_note_count"],
                "unique_source_count": score_info["unique_source_count"],
                "related_channel_count": score_info["related_channel_count"],
                "keyword_hit_count": score_info["keyword_hit_count"],
                "source_type_multiplier": score_info["source_type_multiplier"],
                "score_cap": score_info["score_cap"],
            }
        )

    return pd.DataFrame(rows)


def summarize_resilience_sources(notes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize source notes used for local resilience scoring.
    """

    if notes_df.empty:
        source_summary = pd.DataFrame(
            columns=[
                "jurisdiction",
                "risk_channel",
                "source_note_count",
                "unique_sources",
            ]
        )
    else:
        related_notes = notes_df[
            notes_df["risk_channel"].isin(RESILIENCE_RELATED_CHANNELS)
        ].copy()

        if related_notes.empty:
            source_summary = pd.DataFrame(
                columns=[
                    "jurisdiction",
                    "risk_channel",
                    "source_note_count",
                    "unique_sources",
                ]
            )
        else:
            source_summary = (
                related_notes.groupby(["jurisdiction", "risk_channel"], dropna=False)
                .agg(
                    source_note_count=("key_point", "count"),
                    unique_sources=("source_name", "nunique"),
                )
                .reset_index()
                .sort_values(["source_note_count", "unique_sources"], ascending=False)
            )

    source_summary.to_csv(LOCAL_RESILIENCE_SOURCE_SUMMARY_OUTPUT, index=False)

    print(f"Saved local resilience source summary to: {LOCAL_RESILIENCE_SOURCE_SUMMARY_OUTPUT}")

    return source_summary


def calculate_local_resilience_offset(component_summary: pd.DataFrame) -> float:
    """
    Calculate the weighted Local Resilience Offset.
    """

    if component_summary.empty:
        return 0.0

    total_weight = component_summary["weight"].sum()

    if total_weight == 0:
        return 0.0

    resilience_offset = (
        component_summary["weighted_contribution"].sum() / total_weight
    )

    return float(max(min(resilience_offset, 100.0), 0.0))


def classify_resilience(score: float) -> str:
    """
    Classify a 0-100 resilience score.
    """

    if score < 25:
        return "Limited Resilience Offset"
    if score < 50:
        return "Moderate Resilience Offset"
    if score < 75:
        return "Strong Resilience Offset"
    return "Very Strong Resilience Offset"


def classify_resilience_confidence(component_summary: pd.DataFrame) -> str:
    """
    Classify overall confidence in the local resilience offset.
    """

    if component_summary.empty:
        return "No Evidence"

    confidence_order = {
        "No Evidence": 0,
        "Limited Evidence": 1,
        "Moderate Evidence": 2,
        "Strong Evidence": 3,
        "Very Strong Evidence": 4,
    }

    avg_confidence = component_summary["evidence_confidence"].map(confidence_order).mean()

    if pd.isna(avg_confidence):
        return "No Evidence"

    if avg_confidence < 1:
        return "Limited Evidence"
    if avg_confidence < 2:
        return "Moderate Evidence"
    if avg_confidence < 3:
        return "Strong Evidence"
    return "Very Strong Evidence"


def build_local_resilience_model() -> pd.DataFrame:
    """
    Run the full local resilience scoring model.
    """

    notes_df = load_local_source_notes()
    summarize_resilience_sources(notes_df)

    component_summary = build_resilience_component_scores(notes_df)
    component_summary.to_csv(LOCAL_RESILIENCE_COMPONENT_SUMMARY_OUTPUT, index=False)

    resilience_offset = calculate_local_resilience_offset(component_summary)
    resilience_signal = classify_resilience(resilience_offset)
    resilience_confidence = classify_resilience_confidence(component_summary)

    latest_date = pd.Timestamp.today().normalize()

    result = pd.DataFrame(
        [
            {
                "date": latest_date,
                "local_resilience_offset": resilience_offset,
                "local_resilience_signal": resilience_signal,
                "local_resilience_confidence": resilience_confidence,
                "resilience_components_scored": len(component_summary),
                "average_component_score": component_summary["component_score"].mean()
                if not component_summary.empty
                else 0.0,
                "strong_or_better_components": int(
                    component_summary["evidence_confidence"]
                    .isin(["Strong Evidence", "Very Strong Evidence"])
                    .sum()
                )
                if not component_summary.empty
                else 0,
            }
        ]
    )

    for _, row in component_summary.iterrows():
        result[f"{row['component']}_score"] = row["component_score"]

    result.to_csv(LOCAL_RESILIENCE_OUTPUT, index=False)
    result.to_csv(LOCAL_RESILIENCE_LATEST_OUTPUT, index=False)

    print(f"Saved local resilience scores to: {LOCAL_RESILIENCE_OUTPUT}")
    print(f"Saved latest local resilience score to: {LOCAL_RESILIENCE_LATEST_OUTPUT}")
    print(f"Saved local resilience component summary to: {LOCAL_RESILIENCE_COMPONENT_SUMMARY_OUTPUT}")

    print()
    print("Latest Local Resilience Offset")
    print("------------------------------")
    print(f"Date: {latest_date.date()}")
    print(f"Offset: {resilience_offset:.2f}")
    print(f"Signal: {resilience_signal}")
    print(f"Evidence confidence: {resilience_confidence}")

    return result


def summarize_local_resilience(result: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Return the component summary for the latest local resilience model.
    """

    if not LOCAL_RESILIENCE_COMPONENT_SUMMARY_OUTPUT.exists():
        if result is None:
            raise FileNotFoundError(
                "No local resilience component summary found. "
                "Run build_local_resilience_model() first."
            )

    summary = pd.read_csv(LOCAL_RESILIENCE_COMPONENT_SUMMARY_OUTPUT)

    print()
    print("Latest local resilience component scores:")
    print(summary.to_string(index=False))

    return summary


def main() -> None:
    """
    Run local resilience scoring as a script.
    """

    result = build_local_resilience_model()
    summarize_local_resilience(result)


if __name__ == "__main__":
    main()