"""
FRED data collection module for the Gallatin-Sumner County Geoeconomic Growth Risk Monitor.

This module downloads public FRED CSV series directly using the FRED graph endpoint.
No API key is required for this basic workflow.

Outputs:
- data/processed/fred_series_wide.csv
- data/processed/fred_series_long.csv
- data/processed/fred_latest_values.csv
"""

from __future__ import annotations

import time
from io import StringIO
from typing import Dict

import pandas as pd
import requests

from src.config import FRED_SERIES, PROCESSED_DATA_DIR


FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

FRED_LONG_OUTPUT = PROCESSED_DATA_DIR / "fred_series_long.csv"
FRED_WIDE_OUTPUT = PROCESSED_DATA_DIR / "fred_series_wide.csv"
FRED_LATEST_OUTPUT = PROCESSED_DATA_DIR / "fred_latest_values.csv"


def fetch_fred_series(
    series_name: str,
    series_id: str,
    max_retries: int = 3,
    pause_seconds: float = 1.5,
) -> pd.DataFrame:
    """
    Download a single FRED series as a tidy DataFrame.

    Parameters
    ----------
    series_name:
        Friendly internal name for the series.
    series_id:
        FRED series ID.
    max_retries:
        Number of retry attempts for temporary request failures.
    pause_seconds:
        Base pause between retries.

    Returns
    -------
    pd.DataFrame
        Columns: date, series_name, series_id, value
    """

    url = FRED_CSV_URL.format(series_id=series_id)

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=30)

            if response.status_code in {429, 500, 502, 503, 504}:
                raise RuntimeError(
                    f"Temporary FRED response {response.status_code}: "
                    f"{response.text[:200]}"
                )

            response.raise_for_status()

            df = pd.read_csv(StringIO(response.text))

            if "observation_date" not in df.columns:
                raise ValueError(f"Unexpected FRED response format for {series_id}")

            value_columns = [col for col in df.columns if col != "observation_date"]

            if not value_columns:
                raise ValueError(f"No value column found in FRED response for {series_id}")

            value_col = value_columns[0]

            df = df.rename(
                columns={
                    "observation_date": "date",
                    value_col: "value",
                }
            )

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df["series_name"] = series_name
            df["series_id"] = series_id

            df = df[["date", "series_name", "series_id", "value"]]
            df = df.dropna(subset=["date", "value"])
            df = df.sort_values("date").reset_index(drop=True)

            if df.empty:
                raise ValueError(f"FRED series {series_id} returned no usable observations.")

            return df

        except Exception as exc:
            last_error = exc

            if attempt < max_retries:
                wait_time = pause_seconds * attempt
                print(
                    f"WARNING: Failed attempt {attempt}/{max_retries} for "
                    f"{series_name} ({series_id}). Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            else:
                break

    raise RuntimeError(
        f"Failed to download FRED series {series_name} ({series_id}) "
        f"after {max_retries} attempts: {last_error}"
    )


def load_cached_fred_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load cached FRED long/wide data if available.
    """

    if FRED_LONG_OUTPUT.exists() and FRED_WIDE_OUTPUT.exists():
        print("WARNING: Using cached FRED data because no new series were downloaded.")
        long_df = pd.read_csv(FRED_LONG_OUTPUT)
        wide_df = pd.read_csv(FRED_WIDE_OUTPUT)

        if "date" in long_df.columns:
            long_df["date"] = pd.to_datetime(long_df["date"], errors="coerce")

        if "date" in wide_df.columns:
            wide_df["date"] = pd.to_datetime(wide_df["date"], errors="coerce")

        return long_df, wide_df

    return pd.DataFrame(), pd.DataFrame()


def collect_fred_data(
    series_map: Dict[str, str] | None = None,
    allow_cached_fallback: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Download all configured FRED series and save long and wide versions.

    Parameters
    ----------
    series_map:
        Optional mapping of friendly series names to FRED series IDs.
        If None, uses FRED_SERIES from config.py.
    allow_cached_fallback:
        If True, use previously saved FRED files if all downloads fail.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        long_df, wide_df
    """

    if series_map is None:
        series_map = FRED_SERIES

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_series = []
    failed_series = []

    for series_name, series_id in series_map.items():
        print(f"Downloading FRED series: {series_name} ({series_id})")

        try:
            series_df = fetch_fred_series(series_name, series_id)
            all_series.append(series_df)
        except Exception as exc:
            failed_series.append(
                {
                    "series_name": series_name,
                    "series_id": series_id,
                    "error": str(exc),
                }
            )
            print(f"WARNING: Failed to download {series_name} ({series_id}): {exc}")

    if not all_series:
        if allow_cached_fallback:
            cached_long, cached_wide = load_cached_fred_data()

            if not cached_long.empty and not cached_wide.empty:
                summarize_latest_values(cached_long)
                return cached_long, cached_wide

        raise RuntimeError("No FRED series were successfully downloaded.")

    long_df = pd.concat(all_series, ignore_index=True)
    long_df = long_df.sort_values(["series_name", "date"]).reset_index(drop=True)

    wide_df = (
        long_df.pivot_table(
            index="date",
            columns="series_name",
            values="value",
            aggfunc="last",
        )
        .sort_index()
        .reset_index()
    )

    long_df.to_csv(FRED_LONG_OUTPUT, index=False)
    wide_df.to_csv(FRED_WIDE_OUTPUT, index=False)

    print(f"\nSaved long FRED dataset to: {FRED_LONG_OUTPUT}")
    print(f"Saved wide FRED dataset to: {FRED_WIDE_OUTPUT}")
    print(f"Long shape: {long_df.shape}")
    print(f"Wide shape: {wide_df.shape}")

    if failed_series:
        failed_df = pd.DataFrame(failed_series)
        failed_output = PROCESSED_DATA_DIR / "fred_failed_downloads.csv"
        failed_df.to_csv(failed_output, index=False)
        print(f"Saved failed FRED download log to: {failed_output}")

    return long_df, wide_df


def summarize_latest_values(long_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a latest-value summary table for all downloaded FRED series.
    """

    if long_df.empty:
        raise ValueError("Cannot summarize latest FRED values because long_df is empty.")

    df = long_df.copy()

    if "date" not in df.columns:
        raise ValueError("FRED long DataFrame is missing required column: date")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.dropna(subset=["date", "value"])

    latest = (
        df.sort_values("date")
        .groupby(["series_name", "series_id"], as_index=False)
        .tail(1)
        .sort_values("series_name")
        .reset_index(drop=True)
    )

    history_summary = (
        df.groupby(["series_name", "series_id"], as_index=False)
        .agg(
            first_observation_date=("date", "min"),
            latest_observation_date=("date", "max"),
            observation_count=("value", "count"),
            latest_value=("value", "last"),
        )
    )

    latest = latest.merge(
        history_summary,
        on=["series_name", "series_id"],
        how="left",
    )

    latest = latest.rename(
        columns={
            "date": "latest_date",
            "value": "latest_value_from_latest_row",
        }
    )

    latest["latest_value"] = latest["latest_value_from_latest_row"]
    latest = latest.drop(columns=["latest_value_from_latest_row"])

    latest.to_csv(FRED_LATEST_OUTPUT, index=False)

    print(f"Saved latest FRED values to: {FRED_LATEST_OUTPUT}")

    return latest


def main() -> None:
    """
    Run the FRED data collection module as a script.
    """

    long_df, _ = collect_fred_data()
    latest = summarize_latest_values(long_df)

    print("\nLatest FRED values:")

    display_cols = [
        "series_name",
        "series_id",
        "latest_date",
        "latest_value",
        "observation_count",
    ]

    display_cols = [col for col in display_cols if col in latest.columns]

    print(latest[display_cols].to_string(index=False))


if __name__ == "__main__":
    main()