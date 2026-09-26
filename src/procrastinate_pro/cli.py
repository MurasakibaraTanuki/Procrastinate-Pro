"""Command-line interface for the Procrastinate Pro+ analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .analytics import build_profiles, clean_columns, ltv_and_roi, segment_summary


def load_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load and prepare the three case-study tables."""
    visits = clean_columns(pd.read_csv(data_dir / "visits_info_short.csv"))
    orders = clean_columns(pd.read_csv(data_dir / "orders_info_short.csv"))
    costs = clean_columns(pd.read_csv(data_dir / "costs_info_short.csv"))

    visits["session_start"] = pd.to_datetime(visits["session_start"])
    if "session_end" in visits:
        visits["session_end"] = pd.to_datetime(visits["session_end"])
    orders["event_dt"] = pd.to_datetime(orders["event_dt"])
    costs["dt"] = pd.to_datetime(costs["dt"]).dt.date
    return visits, orders, costs


def run(data_dir: Path, output_dir: Path, horizon: int) -> None:
    """Run the reproducible summary analysis and export CSV results."""
    visits, orders, costs = load_data(data_dir)
    profiles = build_profiles(visits, orders, costs)
    observation_date = max(profiles["dt"])
    output_dir.mkdir(parents=True, exist_ok=True)

    profiles.to_csv(output_dir / "user_profiles.csv", index=False)
    for dimension in ("channel", "region", "device"):
        segment_summary(profiles, dimension).to_csv(
            output_dir / f"summary_by_{dimension}.csv"
        )
        ltv, roi = ltv_and_roi(
            profiles,
            orders,
            observation_date,
            horizon,
            dimensions=[dimension],
        )
        ltv.to_csv(output_dir / f"ltv_by_{dimension}.csv")
        roi.to_csv(output_dir / f"roi_by_{dimension}.csv")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate Procrastinate Pro+ cohort and unit-economics metrics."
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--horizon", type=int, default=14)
    args = parser.parse_args()
    run(args.data_dir, args.output_dir, args.horizon)


if __name__ == "__main__":
    main()
