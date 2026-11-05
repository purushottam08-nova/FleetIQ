from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "data" / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------
# UNIT CONVERSION HELPERS
# --------------------------------

def convert_distance(values, units):

    factors = {
        "km": 1,
        "kilometre": 1,
        "kilometer": 1,
        "mile": 1.60934,
        "miles": 1.60934,
        "mi": 1.60934
    }

    unit_series = (
        units.astype("string").str.lower().str.strip()
    )

    factor = unit_series.map(factors)

    return pd.to_numeric(
        values, errors="coerce"
    ) * factor


def convert_fuel(values, units):

    factors = {
        "litre": 1,
        "litres": 1,
        "liter": 1,
        "liters": 1,
        "l": 1,
        "gallon": 3.78541,
        "gallons": 3.78541,
        "us_gallon": 3.78541
    }

    unit_series = (
        units.astype("string").str.lower().str.strip()
    )

    factor = unit_series.map(factors)

    return pd.to_numeric(
        values, errors="coerce"
    ) * factor


def load_csv(filename):

    return pd.read_csv(RAW_DIR / filename)


# --------------------------------
# ISSUE TRACKING
# --------------------------------

review_records = []


def add_issue(source, record_id, issue, decision):

    review_records.append({
        "source_table": source,
        "record_id": record_id,
        "issue": issue,
        "decision": decision
    })


# --------------------------------
# LOAD RAW DATA
# --------------------------------

vehicles = load_csv("vehicles.csv")
routes = load_csv("routes.csv")
trips = load_csv("trips.csv")
fuel = load_csv("fuel_transactions.csv")
maintenance = load_csv("maintenance.csv")


raw_counts = {
    "vehicles": len(vehicles),
    "routes": len(routes),
    "trips": len(trips),
    "fuel_transactions": len(fuel),
    "maintenance": len(maintenance)
}


# --------------------------------
# 1. VEHICLE AND ROUTE CLEANING
# --------------------------------

vehicles = vehicles.drop_duplicates(
    subset=["vehicle_id"],
    keep="first"
)

routes = routes.drop_duplicates(
    subset=["route_id"],
    keep="first"
)

valid_vehicle_ids = set(vehicles["vehicle_id"])
valid_route_ids = set(routes["route_id"])


# --------------------------------
# 2. TRIP CLEANING
# --------------------------------

trips["start_datetime"] = pd.to_datetime(
    trips["start_datetime"],
    errors="coerce"
)

trips["end_datetime"] = pd.to_datetime(
    trips["end_datetime"],
    errors="coerce"
)

trips["start_odometer_km"] = convert_distance(
    trips["start_odometer"],
    trips["odometer_unit"]
)

trips["end_odometer_km"] = convert_distance(
    trips["end_odometer"],
    trips["odometer_unit"]
)

trips["distance_km"] = convert_distance(
    trips["distance_value"],
    trips["distance_unit"]
)

trips["odometer_distance_km"] = (
    trips["end_odometer_km"]
    - trips["start_odometer_km"]
)

trips["distance_difference_km"] = (
    trips["distance_km"]
    - trips["odometer_distance_km"]
)

trips["distance_unit_standard"] = "KM"
trips["odometer_unit_standard"] = "KM"

valid_trips = []
previous_odo = {}

trips = trips.sort_values(
    ["vehicle_id", "start_datetime"]
)

for _, row in trips.iterrows():

    trip_id = row["trip_id"]
    vehicle_id = row["vehicle_id"]

    issues = []

    required_fields = [
        row["start_datetime"],
        row["end_datetime"],
        row["start_odometer_km"],
        row["end_odometer_km"],
        row["distance_km"]
    ]

    if any(pd.isna(value) for value in required_fields):
        issues.append("incomplete_trip")

    if row["trip_status"] != "Completed":
        issues.append("trip_not_completed")

    if vehicle_id not in valid_vehicle_ids:
        issues.append("unknown_vehicle")

    if row["route_id"] not in valid_route_ids:
        issues.append("unknown_route")

    start_odo = row["start_odometer_km"]
    end_odo = row["end_odometer_km"]

    if pd.notna(start_odo) and pd.notna(end_odo):

        if end_odo < start_odo:
            issues.append("odometer_reversal_within_trip")

        previous = previous_odo.get(vehicle_id)

        if previous is not None and start_odo < previous - 1:
            issues.append("odometer_sequence_reversal")

    if issues:

        for issue in issues:
            add_issue(
                "trips",
                trip_id,
                issue,
                "excluded_from_analytics_pending_verification"
            )

    else:

        valid_trips.append(row.to_dict())

        previous_odo[vehicle_id] = end_odo


clean_trips = pd.DataFrame(valid_trips)


# --------------------------------
# 3. FUEL TRANSACTION CLEANING
# --------------------------------

fuel["transaction_date"] = pd.to_datetime(
    fuel["transaction_date"],
    errors="coerce"
)

fuel["fuel_quantity_litres"] = convert_fuel(
    fuel["fuel_quantity"],
    fuel["fuel_unit"]
)

fuel["odometer_km"] = convert_distance(
    fuel["odometer_reading"],
    fuel["odometer_unit"]
)

fuel["fuel_cost_inr"] = pd.to_numeric(
    fuel["fuel_cost_inr"],
    errors="coerce"
)

fuel["fuel_unit_standard"] = "LITRE"
fuel["odometer_unit_standard"] = "KM"

fuel = fuel.sort_values(
    ["vehicle_id", "transaction_date"]
)

duplicate_mask = fuel.duplicated(
    subset=["receipt_id"],
    keep="first"
)

unique_fuel = fuel.loc[~duplicate_mask].copy()

for _, row in fuel.loc[duplicate_mask].iterrows():

    add_issue(
        "fuel_transactions",
        row["receipt_id"],
        "duplicate_receipt",
        "duplicate_excluded"
    )


valid_fuel = []
previous_fuel_odo = {}

for _, row in unique_fuel.iterrows():

    receipt_id = row["receipt_id"]
    vehicle_id = row["vehicle_id"]

    issues = []

    if pd.isna(row["transaction_date"]):
        issues.append("missing_transaction_date")

    if pd.isna(row["fuel_quantity_litres"]):
        issues.append("invalid_fuel_quantity_or_unit")

    elif row["fuel_quantity_litres"] <= 0:
        issues.append("non_positive_fuel_quantity")

    if pd.isna(row["fuel_cost_inr"]):
        issues.append("missing_fuel_cost")

    elif row["fuel_cost_inr"] < 0:
        issues.append("negative_fuel_cost")

    if pd.isna(row["odometer_km"]):
        issues.append("invalid_odometer_or_unit")

    if vehicle_id not in valid_vehicle_ids:
        issues.append("unknown_vehicle")

    odo = row["odometer_km"]

    if pd.notna(odo):

        previous = previous_fuel_odo.get(vehicle_id)

        if previous is not None and odo < previous - 1:
            issues.append("fuel_odometer_reversal")

    if issues:

        for issue in issues:
            add_issue(
                "fuel_transactions",
                receipt_id,
                issue,
                "excluded_from_analytics_pending_verification"
            )

    else:

        valid_fuel.append(row.to_dict())

        previous_fuel_odo[vehicle_id] = odo


clean_fuel = pd.DataFrame(valid_fuel)


# --------------------------------
# 4. MAINTENANCE CLEANING
# --------------------------------

maintenance["service_date"] = pd.to_datetime(
    maintenance["service_date"],
    errors="coerce"
)

maintenance["odometer_km"] = convert_distance(
    maintenance["odometer_reading"],
    maintenance["odometer_unit"]
)

maintenance["maintenance_cost_inr"] = pd.to_numeric(
    maintenance["maintenance_cost_inr"],
    errors="coerce"
)

maintenance["odometer_unit_standard"] = "KM"

valid_maintenance = []

for _, row in maintenance.iterrows():

    service_id = row["service_id"]
    issues = []

    if pd.isna(row["service_date"]):
        issues.append("missing_service_date")

    if pd.isna(row["maintenance_cost_inr"]):
        issues.append("missing_maintenance_cost")

    elif row["maintenance_cost_inr"] < 0:
        issues.append("negative_maintenance_cost")

    if row["vehicle_id"] not in valid_vehicle_ids:
        issues.append("unknown_vehicle")

    if pd.isna(row["odometer_km"]):
        issues.append("invalid_maintenance_odometer")

    if issues:

        for issue in issues:
            add_issue(
                "maintenance",
                service_id,
                issue,
                "excluded_from_analytics_pending_verification"
            )

    else:

        valid_maintenance.append(row.to_dict())


clean_maintenance = pd.DataFrame(valid_maintenance)


# --------------------------------
# 5. SAVE CLEANED DATASETS
# --------------------------------

clean_datasets = {
    "clean_vehicles.csv": vehicles,
    "clean_routes.csv": routes,
    "clean_trips.csv": clean_trips,
    "clean_fuel_transactions.csv": clean_fuel,
    "clean_maintenance.csv": clean_maintenance
}

clean_counts = {}

for filename, dataframe in clean_datasets.items():

    dataframe.to_csv(
        PROCESSED_DIR / filename,
        index=False
    )

    print(
        f"Saved {filename}: {len(dataframe)} rows"
    )

    clean_counts[filename] = len(dataframe)


# --------------------------------
# 6. VERIFICATION REPORT
# --------------------------------

review_df = pd.DataFrame(
    review_records,
    columns=[
        "source_table",
        "record_id",
        "issue",
        "decision"
    ]
)

review_df.to_csv(
    REPORT_DIR / "rejected_records.csv",
    index=False
)


# --------------------------------
# 7. DATA QUALITY REPORT
# --------------------------------

source_to_clean = {
    "vehicles": "clean_vehicles.csv",
    "routes": "clean_routes.csv",
    "trips": "clean_trips.csv",
    "fuel_transactions": "clean_fuel_transactions.csv",
    "maintenance": "clean_maintenance.csv"
}

quality_rows = []

for source, raw_count in raw_counts.items():

    clean_count = clean_counts[
        source_to_clean[source]
    ]

    excluded_count = raw_count - clean_count

    quality_rows.append({
        "dataset": source,
        "raw_records": raw_count,
        "clean_records": clean_count,
        "excluded_records": excluded_count,
        "quality_percentage": round(
            clean_count / raw_count * 100, 2
        ) if raw_count else 0
    })


quality_df = pd.DataFrame(quality_rows)

quality_df.to_csv(
    REPORT_DIR / "data_quality_report.csv",
    index=False
)


# --------------------------------
# 8. STANDARDIZATION REPORT
# --------------------------------

standardization = pd.DataFrame([
    {
        "dataset": "trips",
        "column": "distance_value",
        "source_unit": "miles",
        "target_unit": "km",
        "conversion_factor": 1.60934,
        "records_converted": trips["distance_unit"].astype(str).str.lower().eq("miles").sum()
    },
    {
        "dataset": "trips",
        "column": "odometer_reading",
        "source_unit": "miles",
        "target_unit": "km",
        "conversion_factor": 1.60934,
        "records_converted": trips["odometer_unit"].astype(str).str.lower().eq("miles").sum()
    },
    {
        "dataset": "fuel_transactions",
        "column": "fuel_quantity",
        "source_unit": "gallon",
        "target_unit": "litre",
        "conversion_factor": 3.78541,
        "records_converted": fuel["fuel_unit"].astype(str).str.lower().isin(
            ["gallon", "gallons", "us_gallon"]
        ).sum()
    },
    {
        "dataset": "fuel_transactions",
        "column": "odometer_reading",
        "source_unit": "miles",
        "target_unit": "km",
        "conversion_factor": 1.60934,
        "records_converted": fuel["odometer_unit"].astype(str).str.lower().isin(
            ["mile", "miles", "mi"]
        ).sum()
    },
    {
        "dataset": "maintenance",
        "column": "odometer_reading",
        "source_unit": "miles",
        "target_unit": "km",
        "conversion_factor": 1.60934,
        "records_converted": maintenance["odometer_unit"].astype(str).str.lower().isin(
            ["mile", "miles", "mi"]
        ).sum()
    }
])

standardization.to_csv(
    REPORT_DIR / "standardization_log.csv",
    index=False
)

standardization.to_csv(
    REPORT_DIR / "standardization_log.csv",
    index=False
)


# --------------------------------
# 9. FINAL SUMMARY
# --------------------------------

print("\n========== DATA QUALITY REPORT ==========")

print(quality_df.to_string(index=False))

print("\n========== ISSUES FOUND ==========")

if not review_df.empty:
    print(
        review_df["issue"]
        .value_counts()
        .to_string()
    )
else:
    print("No issues found.")

print("\nDay 1 cleaning pipeline completed!")