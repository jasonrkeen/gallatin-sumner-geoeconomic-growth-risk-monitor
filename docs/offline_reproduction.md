# Offline reproduction and validation scope

Evidence date: November 18, 2026.

## What the sample reproduces

`python sample_run.py` reads nine stored files in `data/processed/` and calls the original composite, resilience-credit, scenario, and sensitivity functions. It recomputes the composite from the seven stored component scores, applies the original resilience credit, and passes the recomputed baseline into the scenario calculations. Sensitivity cases reuse the original weighting definitions and weighted-score function.

These are historical processed inputs associated with the saved May 19, 2026 run, with differing underlying source dates. The sample does not download Census or FRED data, recode local evidence, recompute the upstream component scores, advance monitoring snapshots, or regenerate the published report. It requires no credentials and uses no randomness; a seed is not applicable.

The original full pipeline writes to fixed data, report, chart, and snapshot locations. The sample calls calculation functions and writes only to a new sample destination. Original configuration imports can create missing empty directory scaffolding; they do not rewrite saved files. Production modules and their behavior are unchanged.

## Environment and command

Use Python 3.13.5 in an activated virtual environment:

```bash
python -m pip install -r requirements.txt
python sample_run.py
```

Runtime and resolved transitive dependencies are pinned exactly; tests have separate pins in `requirements-dev.txt`. These pins identify a tested installation environment, not the undocumented environment that originally produced the historical report. They are not an archive of package distributions or operating-system dependencies.

The default destination is `outputs/sample/`. Existing destinations are refused. Relative paths resolve from the repository root, and in-repository destinations must be under `outputs/sample/`. New external directories are supported. Repeat with `python sample_run.py --output-dir outputs/sample/repeat`.

Artifacts comprise `composite_sample.csv`, `component_summary.csv`, `scenario_forecasts.csv`, `sensitivity_analysis_results.csv`, an interpretation note, and `run_manifest.json`. The manifest records input/source/dependency-file hashes, environment, and artifact hashes. It excludes timestamps and machine-specific paths for repeatability. Original component source dates are retained; no new observation date is asserted.

Expected composite score: **69.13628443151912**; resilience credit: **8.25**; adjusted score: **60.886284431519115**, or **Elevated Risk**. These are historical constructed indicators, not a current assessment. Inherited fields such as `live_components_used` and `Fully Data-Driven` describe the original program's bookkeeping, not a live request, independent validation, or empirical accuracy.

## Verified evidence

All 25 tests pass locally on Windows using Python 3.13.5. Checks cover hand-calculated weights, capped resilience credit, risk-band boundaries, missing-component renormalization, empty inputs, scenario arithmetic, sensitivity normalization, published-table regression, same-environment artifact repeatability, independent network-blocked subprocesses, destination protection, and preservation hashes. The network is blocked during tests.

Recomputed composite fields, all four scenario rows, and all six sensitivity rows match stored counterparts at absolute tolerance `1e-10` with zero relative tolerance. This tolerance permits floating-point differences; it does not permit model or published-result changes. Repeat-run artifacts match byte for byte within the recorded environment. Cross-platform byte identity is not claimed.

[GitHub Actions](../.github/workflows/tests.yml) installs the pinned environment, checks dependencies, runs the tests and sample on Windows and Ubuntu, checks that tracked files remain unchanged, and uploads artifacts. See [actual run results](https://github.com/jasonrkeen/gallatin-sumner-geoeconomic-growth-risk-monitor/actions/workflows/tests.yml) for execution evidence.

[Preservation hashes](../tests/preserved_files.json) cover all original model modules, tracked data, charts, report, and snapshots at commit `69a9f662cd5b078ee9c6ee8d5365dd4f5f5ca601`. Text hashes normalize checkout line endings; binary hashes preserve exact bytes. Git attributes prevent Windows from converting PDF/PNG line endings. Do not update preservation references merely to make tests pass; changes to protected model or published files require authorization.

## Limits

No model logic, published data/results, snapshots, or releases are changed. This verifies downstream numerical reproduction, not the complete live-data pipeline, source accuracy, analyst coding, predictive validity, or independent replication. The full historical report's byte reproduction and current external API compatibility remain unverified.
