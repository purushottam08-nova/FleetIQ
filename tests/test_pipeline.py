from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "data" / "reports"
RAW = ROOT / "data" / "raw"


def test_output_files():

    required_files = [
        PROCESSED / "clean_vehicles.csv",
        PROCESSED / "clean_routes.csv",
        PROCESSED / "clean_trips.csv",
        PROCESSED / "clean_fuel_transactions.csv",
        PROCESSED / "clean_maintenance.csv",
        REPORTS / "rejected_records.csv",
        REPORTS / "data_quality_report.csv",
        REPORTS / "standardization_log.csv"
    ]

    for file in required_files:
        assert file.exists(), f"Missing file: {file.name}"


def test_record_counts():

    assert len(pd.read_csv(PROCESSED / "clean_vehicles.csv")) == 15
    assert len(pd.read_csv(PROCESSED / "clean_routes.csv")) == 6
    assert len(pd.read_csv(PROCESSED / "clean_trips.csv")) == 178
    assert len(pd.read_csv(PROCESSED / "clean_fuel_transactions.csv")) == 90
    assert len(pd.read_csv(PROCESSED / "clean_maintenance.csv")) == 30


def test_data_quality_issues():

    rejected = pd.read_csv(
        REPORTS / "rejected_records.csv"
    )

    detected_issues = set(rejected["issue"])

    assert "duplicate_receipt" in detected_issues
    assert "incomplete_trip" in detected_issues
    assert "odometer_reversal_within_trip" in detected_issues


if __name__ == "__main__":

    test_output_files()
    test_record_counts()
    test_data_quality_issues()

    print("\nAll pipeline tests passed!")