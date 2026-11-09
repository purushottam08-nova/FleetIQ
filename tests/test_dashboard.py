from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.data_loader import load_dashboard_data


def test_dashboard_data_loads():
    data = load_dashboard_data()
    expected = {
        "vehicles", "trips", "fuel", "maintenance", "routes",
        "efficiency_intervals", "vehicle_efficiency", "maintenance_monthly",
        "outliers", "analytics_summary", "data_quality",
    }
    assert expected.issubset(data)
    assert len(data["vehicles"]) > 0
    assert len(data["trips"]) > 0


def test_required_dashboard_columns_and_dates():
    data = load_dashboard_data()
    assert pd.api.types.is_datetime64_any_dtype(data["trips"]["start_datetime"])
    assert pd.api.types.is_datetime64_any_dtype(data["efficiency_intervals"]["transaction_date"])
    assert (data["efficiency_intervals"]["km_per_litre"].dropna() > 0).all()


def test_fuel_efficiency_is_interval_based():
    data = load_dashboard_data()
    intervals = data["efficiency_intervals"]
    assert {"distance_between_refills_km", "fuel_quantity_litres"}.issubset(intervals.columns)
    assert (intervals["distance_between_refills_km"] > 0).all()
    assert (intervals["fuel_quantity_litres"] > 0).all()


if __name__ == "__main__":
    test_dashboard_data_loads()
    test_required_dashboard_columns_and_dates()
    test_fuel_efficiency_is_interval_based()
    print("All Day 3 dashboard data tests passed!")
