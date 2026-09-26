"""Core cohort and unit-economics calculations."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta

import numpy as np
import pandas as pd


def clean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with normalised snake-case column names."""
    cleaned = frame.copy()
    cleaned.columns = [
        str(column).strip().lower().replace(" ", "_") for column in cleaned.columns
    ]
    return cleaned


def validate_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    """Raise a useful error when an input table lacks required columns."""
    missing = required.difference(frame.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"{name} is missing required columns: {missing_text}")


def build_profiles(
    sessions: pd.DataFrame,
    orders: pd.DataFrame,
    ad_costs: pd.DataFrame,
) -> pd.DataFrame:
    """Build one acquisition profile per user and calculate individual CAC."""
    validate_columns(
        sessions,
        {"user_id", "session_start", "channel", "device", "region"},
        "sessions",
    )
    validate_columns(orders, {"user_id"}, "orders")
    validate_columns(ad_costs, {"dt", "channel", "costs"}, "ad_costs")

    profiles = (
        sessions.sort_values(["user_id", "session_start"])
        .groupby("user_id", as_index=False)
        .agg(
            first_ts=("session_start", "first"),
            channel=("channel", "first"),
            device=("device", "first"),
            region=("region", "first"),
        )
    )
    profiles["dt"] = profiles["first_ts"].dt.date
    profiles["month"] = profiles["first_ts"].dt.to_period("M").dt.to_timestamp()
    profiles["payer"] = profiles["user_id"].isin(orders["user_id"].unique())

    new_users = (
        profiles.groupby(["dt", "channel"], as_index=False)
        .agg(unique_users=("user_id", "nunique"))
    )
    daily_costs = (
        ad_costs.groupby(["dt", "channel"], as_index=False)
        .agg(costs=("costs", "sum"))
        .merge(new_users, on=["dt", "channel"], how="left")
    )
    daily_costs["acquisition_cost"] = daily_costs["costs"].div(
        daily_costs["unique_users"].replace(0, np.nan)
    )

    profiles = profiles.merge(
        daily_costs[["dt", "channel", "acquisition_cost"]],
        on=["dt", "channel"],
        how="left",
    )
    profiles["acquisition_cost"] = profiles["acquisition_cost"].fillna(0.0)
    return profiles


def _eligible_profiles(
    profiles: pd.DataFrame,
    observation_date: date,
    horizon_days: int,
    ignore_horizon: bool,
) -> pd.DataFrame:
    if horizon_days < 1:
        raise ValueError("horizon_days must be at least 1")
    cutoff = observation_date
    if not ignore_horizon:
        cutoff -= timedelta(days=horizon_days - 1)
    return profiles.loc[profiles["dt"] <= cutoff].copy()


def _dimensions(dimensions: Sequence[str] | None, fallback: str) -> list[str]:
    dims = list(dimensions or [])
    return dims or [fallback]


def retention(
    profiles: pd.DataFrame,
    sessions: pd.DataFrame,
    observation_date: date,
    horizon_days: int,
    dimensions: Sequence[str] | None = None,
    ignore_horizon: bool = False,
) -> pd.DataFrame:
    """Calculate day-level retention by payer status and optional segments."""
    dims = ["payer", *(dimensions or [])]
    eligible = _eligible_profiles(
        profiles, observation_date, horizon_days, ignore_horizon
    )
    raw = eligible.merge(
        sessions[["user_id", "session_start"]], on="user_id", how="left"
    )
    raw["lifetime"] = (raw["session_start"] - raw["first_ts"]).dt.days
    raw = raw.loc[raw["lifetime"].between(0, horizon_days - 1)]

    counts = raw.pivot_table(
        index=dims, columns="lifetime", values="user_id", aggfunc="nunique"
    ).reindex(columns=range(horizon_days), fill_value=0)
    cohort_sizes = eligible.groupby(dims)["user_id"].nunique()
    rates = counts.div(cohort_sizes, axis=0).fillna(0.0)
    rates.insert(0, "cohort_size", cohort_sizes)
    return rates


def conversion(
    profiles: pd.DataFrame,
    purchases: pd.DataFrame,
    observation_date: date,
    horizon_days: int,
    dimensions: Sequence[str] | None = None,
    ignore_horizon: bool = False,
) -> pd.DataFrame:
    """Calculate cumulative first-purchase conversion by lifetime day."""
    eligible = _eligible_profiles(
        profiles, observation_date, horizon_days, ignore_horizon
    )
    dims = list(dimensions or [])
    if not dims:
        eligible["cohort"] = "All users"
        dims = ["cohort"]

    first_purchases = (
        purchases.sort_values(["user_id", "event_dt"])
        .groupby("user_id", as_index=False)
        .agg(event_dt=("event_dt", "first"))
    )
    raw = eligible.merge(first_purchases, on="user_id", how="left")
    raw["lifetime"] = (raw["event_dt"] - raw["first_ts"]).dt.days
    raw = raw.loc[raw["lifetime"].between(0, horizon_days - 1)]

    converted = raw.pivot_table(
        index=dims, columns="lifetime", values="user_id", aggfunc="nunique"
    ).reindex(columns=range(horizon_days), fill_value=0)
    converted = converted.cumsum(axis=1)
    cohort_sizes = eligible.groupby(dims)["user_id"].nunique()
    rates = converted.div(cohort_sizes, axis=0).fillna(0.0)
    rates.insert(0, "cohort_size", cohort_sizes)
    return rates


def ltv_and_roi(
    profiles: pd.DataFrame,
    purchases: pd.DataFrame,
    observation_date: date,
    horizon_days: int,
    dimensions: Sequence[str] | None = None,
    ignore_horizon: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate cumulative LTV and return on acquisition spend."""
    eligible = _eligible_profiles(
        profiles, observation_date, horizon_days, ignore_horizon
    )
    dims = list(dimensions or [])
    if not dims:
        eligible["cohort"] = "All users"
        dims = ["cohort"]

    raw = eligible.merge(
        purchases[["user_id", "event_dt", "revenue"]], on="user_id", how="left"
    )
    raw["lifetime"] = (raw["event_dt"] - raw["first_ts"]).dt.days
    valid = raw.loc[raw["lifetime"].between(0, horizon_days - 1)]
    revenue = valid.pivot_table(
        index=dims, columns="lifetime", values="revenue", aggfunc="sum"
    ).reindex(columns=range(horizon_days), fill_value=0)
    revenue = revenue.cumsum(axis=1)

    cohort_sizes = eligible.groupby(dims)["user_id"].nunique()
    ltv = revenue.div(cohort_sizes, axis=0).fillna(0.0)
    ltv.insert(0, "cohort_size", cohort_sizes)

    cac = eligible.groupby(dims)["acquisition_cost"].mean()
    roi = ltv.drop(columns="cohort_size").div(cac.replace(0, np.nan), axis=0)
    roi = roi.replace([np.inf, -np.inf], np.nan)
    roi.insert(0, "cac", cac)
    roi.insert(0, "cohort_size", cohort_sizes)
    return ltv, roi


def segment_summary(profiles: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Summarise user volume, payer share and mean CAC for one segment."""
    if dimension not in profiles.columns:
        raise ValueError(f"Unknown dimension: {dimension}")
    return (
        profiles.groupby(dimension)
        .agg(
            users=("user_id", "nunique"),
            payer_share=("payer", "mean"),
            mean_cac=("acquisition_cost", "mean"),
        )
        .sort_values("users", ascending=False)
    )
