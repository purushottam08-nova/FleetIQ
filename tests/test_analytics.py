
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "data" / "reports"


def test_analytics_outputs_exist():

    required_files = [
        "full_tank_efficiency_intervals.csv",
        "vehicle_efficiency.csv",
        "vehicle_type_comparison.csv",
        "route_comparison.csv",
        "maintenance_monthly.csv",
        "outlier_evidence.csv",
        "analytics_summary.csv"
    ]

    for filename in required_files:
        file_path = REPORTS_DIR / filename

        assert file_path.exists(), (
            f"Missing analytics output: {filename}"
        )


def test_vehicle_efficiency():

    df = pd.read_csv(
        REPORTS_DIR / "vehicle_efficiency.csv"
    )

    if not df.empty:
        assert (df["total_distance_km"] > 0).all()
        assert (df["total_fuel_litres"] > 0).all()
        assert (df["km_per_litre"] > 0).all()


def test_route_comparison():

    df = pd.read_csv(
        REPORTS_DIR / "route_comparison.csv"
    )

    if not df.empty:
        assert df["vehicle_type"].notna().all()
        assert df["route_name"].notna().all()
        assert (df["trip_count"] > 0).all()


def test_maintenance_report():

    df = pd.read_csv(
        REPORTS_DIR / "maintenance_monthly.csv"
    )

    if not df.empty:
        assert (df["service_count"] > 0).all()
        assert (df["maintenance_cost_inr"] >= 0).all()


def test_analytics_summary():

    df = pd.read_csv(
        REPORTS_DIR / "analytics_summary.csv"
    )

    required_metrics = {
        "total_vehicles",
        "total_clean_trips",
        "overall_fuel_efficiency_km_per_litre",
        "total_maintenance_cost_inr",
        "records_requiring_verification"
    }

    actual_metrics = set(df["metric"])

    assert required_metrics.issubset(actual_metrics)


if __name__ == "__main__":

    test_analytics_outputs_exist()
    test_vehicle_efficiency()
    test_route_comparison()
    test_maintenance_report()
    test_analytics_summary()

    print("All Day 2 analytics tests passed!")
