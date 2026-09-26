from datetime import date

import pandas as pd
import pytest

from procrastinate_pro.analytics import (
    build_profiles,
    clean_columns,
    conversion,
    ltv_and_roi,
    retention,
)


@pytest.fixture
def sample_data():
    sessions = pd.DataFrame(
        {
            "user_id": [1, 1, 2, 2],
            "session_start": pd.to_datetime(
                ["2019-10-01", "2019-10-02", "2019-10-01", "2019-10-03"]
            ),
            "channel": ["Ads", "Ads", "Ads", "Ads"],
            "device": ["PC", "PC", "Mobile", "Mobile"],
            "region": ["UK", "UK", "US", "US"],
        }
    )
    orders = pd.DataFrame(
        {
            "user_id": [1],
            "event_dt": pd.to_datetime(["2019-10-02"]),
            "revenue": [8.0],
        }
    )
    costs = pd.DataFrame(
        {"dt": [date(2019, 10, 1)], "channel": ["Ads"], "costs": [10.0]}
    )
    return sessions, orders, costs


def test_clean_columns_returns_copy():
    original = pd.DataFrame(columns=["User Id", " Event Dt "])
    cleaned = clean_columns(original)
    assert list(cleaned.columns) == ["user_id", "event_dt"]
    assert list(original.columns) == ["User Id", " Event Dt "]


def test_profiles_allocate_daily_cost(sample_data):
    sessions, orders, costs = sample_data
    profiles = build_profiles(sessions, orders, costs)
    assert profiles["acquisition_cost"].tolist() == [5.0, 5.0]
    assert profiles["payer"].tolist() == [True, False]


def test_metrics_on_known_cohort(sample_data):
    sessions, orders, costs = sample_data
    profiles = build_profiles(sessions, orders, costs)

    ltv, roi = ltv_and_roi(profiles, orders, date(2019, 10, 3), 3)
    conv = conversion(profiles, orders, date(2019, 10, 3), 3)
    ret = retention(profiles, sessions, date(2019, 10, 3), 3)

    assert ltv.loc["All users", 1] == pytest.approx(4.0)
    assert roi.loc["All users", 1] == pytest.approx(0.8)
    assert conv.loc["All users", 1] == pytest.approx(0.5)
    assert ret.loc[True, 1] == pytest.approx(1.0)
