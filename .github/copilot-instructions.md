# Copilot instructions: Gallatin-Sumner County Geoeconomic Growth Risk Monitor

## Purpose
Python-based local economic intelligence model measuring growth pressure, housing affordability, construction shock exposure, infrastructure strain, development friction, industry exposure, household vulnerability, and resilience capacity in Gallatin and Sumner County, Tennessee.

## Tech stack
- Python; dependencies in `requirements.txt`
- Key libraries: `pandas`, `numpy`, `matplotlib`, `requests`, `python-dotenv`, `reportlab`

## Folder structure
- `data/` (46 files)
- `outputs/` (11 files)
- `src/` (19 files)
- `README.md`
- `requirements.txt`

## Setup, run, test
Commands documented in README.md (referenced files exist):
```bash
python -m venv .venv
python -m pip install --upgrade pip
pip install -r requirements.txt
python-dotenv>=1.0.0
python -m src.main
python -m src.fred_data
python -m src.construction_shock
python -m src.growth_pressure
python -m src.housing_affordability
python -m src.infrastructure_strain
```
- No automated tests exist yet; if adding them, use pytest under `tests/`.

## Conventions observed
- Functions use type hints; keep annotating new code.
- Uses `dataclasses` for structured config/results.
- Config lives in: `src/config.py`; avoid hardcoding parameters elsewhere.
- API keys are loaded from a local `.env` via python-dotenv; `.env` must stay uncommitted.
- Raw data (`data/raw/`) is gitignored; download/fetch it via the pipeline, do not commit it.
- Public data sources referenced: FRED, Census, BLS.
- Write paths relative to the repo root (no absolute local paths).

## Output artifacts
- Generated outputs go to: `outputs/charts/`, `outputs/reports/`, `outputs/snapshots/`
- A PDF report is produced with `reportlab`; keep it in sync with model changes.
- Streamlit dashboard:  (run with `streamlit run <file>`).
- Charts are generated with matplotlib.

## Guardrails
- Never commit secrets, API keys, tokens, or `.env` files.
- Do not commit large raw datasets or binaries; keep data fetched or documented with its source.
- Keep analysis source-backed: cite data sources and assumptions; label scenario/forecast outputs as model estimates, not facts.
- Preserve reproducibility: no unseeded randomness, no hidden manual steps.
