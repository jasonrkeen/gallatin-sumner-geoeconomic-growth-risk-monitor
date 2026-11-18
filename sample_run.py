"""Offline downstream reproduction using stored component scores, not live sources."""
from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
from typing import Any

import numpy as np
import pandas as pd
from src import composite_score as composite
from src import scenario_forecast as scenarios
from src import sensitivity_analysis as sensitivity
from src.config import classify_risk

ROOT = Path(__file__).resolve().parent
INPUT_NAMES = (
    "growth_pressure_latest.csv", "housing_affordability_latest.csv",
    "construction_shock_latest.csv", "infrastructure_strain_latest.csv",
    "development_friction_latest.csv", "geoeconomic_industry_exposure_latest.csv",
    "household_vulnerability_latest.csv", "local_resilience_latest.csv",
    "composite_risk_score_latest.csv",
)


def text_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def destination_path(path: Path) -> Path:
    destination = (ROOT / path).resolve()
    if destination == ROOT or destination in ROOT.parents:
        raise ValueError("Output cannot be the repository or its parent")
    if ROOT in destination.parents and not destination.is_relative_to((ROOT / "outputs/sample").resolve()):
        raise ValueError("Repository output must be under outputs/sample")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {destination}")
    return destination


def calculate_sample() -> dict[str, pd.DataFrame]:
    for name in INPUT_NAMES:
        if not (ROOT / "data/processed" / name).is_file():
            raise FileNotFoundError(f"Required stored input missing: {name}")
    components = composite.collect_component_scores()
    if any(item["source_status"] != "available" or not np.isfinite(item["score"])
           for item in components.values()):
        raise ValueError("Sample requires complete stored component scores; no fallback permitted")
    resilience = composite.load_local_resilience_offset()
    if resilience["source_status"] != "available" or not np.isfinite(resilience["offset"]):
        raise ValueError("Sample requires a stored resilience offset")
    score, detail = composite.calculate_composite_risk(components)
    credit = composite.calculate_resilience_credit(resilience["offset"])
    adjusted = composite.calculate_adjusted_risk(score, credit)
    summary = pd.DataFrame([{
        "composite_risk_score": score,
        "local_resilience_offset": resilience["offset"],
        "resilience_credit_applied": credit,
        "adjusted_geoeconomic_growth_risk_score": adjusted,
        "adjusted_geoeconomic_growth_risk_signal": classify_risk(adjusted),
    }])
    state = scenarios.load_latest_model_state()
    state.update(summary.iloc[0].to_dict())
    forecasts = scenarios.add_scenario_interpretation(scenarios.calculate_scenario_scores(state))
    forecasts = forecasts.sort_values("scenario_adjusted_risk_score", ascending=False).reset_index(drop=True)
    rows = []
    for key, case in sensitivity.SENSITIVITY_WEIGHT_CASES.items():
        weighted, _ = sensitivity.calculate_weighted_score(detail, case["weights"])
        adjusted_case = composite.calculate_adjusted_risk(weighted, credit)
        rows.append({"case_key": key, "case_name": case["name"], "case_description": case["description"],
                     "sensitivity_composite_risk_score": weighted, "local_resilience_offset": resilience["offset"],
                     "resilience_credit_applied": credit, "sensitivity_adjusted_risk_score": adjusted_case,
                     "sensitivity_adjusted_signal": classify_risk(adjusted_case)})
    return {"composite_sample.csv": summary, "component_summary.csv": detail,
            "scenario_forecasts.csv": forecasts, "sensitivity_analysis_results.csv": pd.DataFrame(rows)}


def run_sample(output: Path = Path("outputs/sample")) -> dict[str, Any]:
    destination = destination_path(output)
    tables = calculate_sample()
    destination.mkdir(parents=True, exist_ok=False)
    for name, frame in tables.items():
        frame.to_csv(destination / name, index=False, lineterminator="\n")
    (destination / "README.md").write_text(
        "# Historical downstream reproduction\n\n"
        "Stored component inputs, not current observations or a fresh source-data run.\n"
        "Scores are constructed indicators, not probabilities or official ratings.\n"
        "Inherited live/maturity labels describe the saved model's bookkeeping, not live access or validation.\n"
        "No randomness is used. No seed is applicable. See run_manifest.json for provenance.\n",
        encoding="utf-8", newline="\n")
    paths = [ROOT / "data/processed" / name for name in INPUT_NAMES]
    sources = [ROOT / "sample_run.py", *sorted((ROOT / "src").glob("*.py"))]
    manifest = {
        "status": "HISTORICAL_DOWNSTREAM_REPRODUCTION_NOT_EMPIRICAL_VALIDATION",
        "input_scope": "Stored component scores and metadata associated with the May 19, 2026 saved run; mixed source dates retained",
        "randomness": "None; no seed applicable",
        "environment": {"python": platform.python_version(), "system": platform.system(),
                        "packages": {name: version(name) for name in ("numpy", "pandas")}},
        "input_sha256_lf": {p.relative_to(ROOT).as_posix(): text_digest(p) for p in paths},
        "source_sha256_lf": {p.relative_to(ROOT).as_posix(): text_digest(p) for p in sources},
        "requirements_sha256_lf": text_digest(ROOT / "requirements.txt"),
        "artifact_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(destination.iterdir())},
        "limits": "Same-environment byte repeatability; upstream source collection, historical report regeneration and predictive validity are not verified.",
    }
    (destination / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                                                 encoding="utf-8", newline="\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/sample"))
    args = parser.parse_args()
    try:
        run_sample(args.output_dir)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        parser.error(str(exc))
    print("Offline downstream sample complete. Historical inputs; no live refresh.")


if __name__ == "__main__":
    main()
