from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "data" / "reports"

REQUIRED_FILES = {
    "vehicles": (PROCESSED_DIR / "clean_vehicles.csv",
                 {"vehicle_id", "vehicle_type"}),
    "trips": (PROCESSED_DIR / "clean_trips.csv",
              {"trip_id", "vehicle_id", "route_id", "start_datetime", "distance_km"}),
    "fuel": (PROCESSED_DIR / "clean_fuel_transactions.csv",
             {"receipt_id", "vehicle_id", "transaction_date", "fuel_quantity_litres",
              "fuel_cost_inr", "odometer_km", "full_tank"}),
    "maintenance": (PROCESSED_DIR / "clean_maintenance.csv",
                   {"service_id", "vehicle_id", "service_date", "maintenance_cost_inr"}),
    "routes": (PROCESSED_DIR / "clean_routes.csv",
               {"route_id", "route_name", "route_distance_km"}),
    "efficiency_intervals": (REPORTS_DIR / "full_tank_efficiency_intervals.csv",
                             {"vehicle_id", "vehicle_type", "transaction_date",
                              "distance_between_refills_km", "fuel_quantity_litres",
                              "fuel_cost_inr", "km_per_litre", "fuel_cost_per_km"}),
    "vehicle_efficiency": (REPORTS_DIR / "vehicle_efficiency.csv",
                           {"vehicle_id", "vehicle_type", "km_per_litre",
                            "fuel_cost_per_km", "total_distance_km"}),
    "maintenance_monthly": (REPORTS_DIR / "maintenance_monthly.csv",
                            {"vehicle_id", "vehicle_type", "month",
                             "service_count", "maintenance_cost_inr"}),
    "outliers": (REPORTS_DIR / "outlier_evidence.csv",
                 {"record_type", "record_id", "vehicle_id", "peer_group",
                  "metric", "observed_value", "reason"}),
    "analytics_summary": (REPORTS_DIR / "analytics_summary.csv", {"metric", "value"}),
    "data_quality": (REPORTS_DIR / "data_quality_report.csv",
                     {"dataset", "raw_records", "clean_records", "excluded_records",
                      "quality_percentage"}),
}

DATE_COLUMNS = {
    "trips": ["start_datetime", "end_datetime"],
    "fuel": ["transaction_date"],
    "maintenance": ["service_date"],
    "efficiency_intervals": ["previous_transaction_date", "transaction_date"],
}

def load_dashboard_data(base_dir=None):
    """Load project CSVs and validate their expected columns."""
    base = Path(base_dir) if base_dir else ROOT
    loaded = {}
    for key, (path, required) in REQUIRED_FILES.items():
        if base_dir:
            # Preserve the processed/reports relative path when a test supplies a temp root.
            rel = path.relative_to(ROOT)
            path = base / rel
        if not path.exists():
            raise FileNotFoundError(f"Required FleetIQ file is missing: {path}")
        frame = pd.read_csv(path)
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path.name} is missing columns: {', '.join(sorted(missing))}")
        loaded[key] = frame

    for key, columns in DATE_COLUMNS.items():
        for column in columns:
            if column in loaded[key].columns:
                loaded[key][column] = pd.to_datetime(loaded[key][column], errors="coerce")

    for key, frame in loaded.items():
        for column in frame.columns:
            if column in {
                "distance_km", "distance_between_refills_km", "fuel_quantity_litres",
                "fuel_cost_inr", "km_per_litre", "fuel_cost_per_km",
                "maintenance_cost_inr", "total_distance_km", "service_count",
                "trip_count", "average_trip_distance_km", "route_reference_distance_km",
                "average_deviation_pct", "quality_percentage", "raw_records",
                "clean_records", "excluded_records", "observed_value",
            }:
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return loaded
