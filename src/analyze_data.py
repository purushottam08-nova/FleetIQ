
from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "data" / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. HELPER FUNCTIONS
# --------------------------------------------------

def load_csv(filename):
    """Load a cleaned CSV file from the processed folder."""

    file_path = PROCESSED_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}\n"
            "Run the Day 1 pipeline first."
        )

    return pd.read_csv(file_path)


def require_columns(df, columns, filename):
    """Check whether the required columns exist."""

    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise ValueError(
            f"{filename} is missing required columns: {missing}"
        )


def to_numeric(df, columns):
    """Convert selected columns to numeric values."""

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def is_full_tank(value):
    """Handle boolean values stored as CSV text."""

    return str(value).strip().lower() in {
        "true", "1", "yes", "y"
    }


def save_report(df, filename):
    """Save an analytics report."""

    output_path = REPORTS_DIR / filename
    df.to_csv(output_path, index=False)

    print(f"Saved: {output_path.name}")


# --------------------------------------------------
# 3. LOAD DAY 1 CLEANED DATA
# --------------------------------------------------

def load_cleaned_data():

    vehicles = load_csv("clean_vehicles.csv")
    routes = load_csv("clean_routes.csv")
    trips = load_csv("clean_trips.csv")
    fuel = load_csv("clean_fuel_transactions.csv")
    maintenance = load_csv("clean_maintenance.csv")

    require_columns(
        vehicles,
        ["vehicle_id", "vehicle_type"],
        "clean_vehicles.csv"
    )

    require_columns(
        routes,
        ["route_id", "route_name", "route_distance_km"],
        "clean_routes.csv"
    )

    require_columns(
        trips,
        [
            "trip_id",
            "vehicle_id",
            "route_id",
            "start_datetime",
            "distance_km"
        ],
        "clean_trips.csv"
    )

    require_columns(
        fuel,
        [
            "receipt_id",
            "vehicle_id",
            "transaction_date",
            "fuel_quantity_litres",
            "fuel_cost_inr",
            "odometer_km",
            "full_tank"
        ],
        "clean_fuel_transactions.csv"
    )

    require_columns(
        maintenance,
        [
            "service_id",
            "vehicle_id",
            "service_date",
            "maintenance_cost_inr"
        ],
        "clean_maintenance.csv"
    )

    trips["start_datetime"] = pd.to_datetime(
        trips["start_datetime"],
        errors="coerce"
    )

    fuel["transaction_date"] = pd.to_datetime(
        fuel["transaction_date"],
        errors="coerce"
    )

    maintenance["service_date"] = pd.to_datetime(
        maintenance["service_date"],
        errors="coerce"
    )

    trips = to_numeric(
        trips,
        ["distance_km"]
    )

    routes = to_numeric(
        routes,
        ["route_distance_km"]
    )

    fuel = to_numeric(
        fuel,
        [
            "fuel_quantity_litres",
            "fuel_cost_inr",
            "odometer_km"
        ]
    )

    maintenance = to_numeric(
        maintenance,
        ["maintenance_cost_inr"]
    )

    print("All cleaned datasets loaded successfully.")

    return vehicles, routes, trips, fuel, maintenance


# --------------------------------------------------
# 4. FULL-TANK FUEL EFFICIENCY
# --------------------------------------------------

def calculate_fuel_efficiency(fuel, vehicles):

    print("\nCalculating full-tank fuel efficiency...")

    fuel = fuel.copy()

    fuel["is_full_tank"] = fuel["full_tank"].apply(
        is_full_tank
    )

    full_tank = fuel[
        fuel["is_full_tank"]
    ].copy()

    full_tank = full_tank.dropna(
        subset=[
            "vehicle_id",
            "transaction_date",
            "odometer_km",
            "fuel_quantity_litres",
            "fuel_cost_inr"
        ]
    )

    full_tank = full_tank.sort_values(
        ["vehicle_id", "transaction_date", "receipt_id"]
    )

    # Previous full-tank refill details
    full_tank["previous_odometer_km"] = (
        full_tank.groupby("vehicle_id")["odometer_km"]
        .shift(1)
    )

    full_tank["previous_transaction_date"] = (
        full_tank.groupby("vehicle_id")["transaction_date"]
        .shift(1)
    )

    # Distance travelled between two full-tank refills
    full_tank["distance_between_refills_km"] = (
        full_tank["odometer_km"]
        - full_tank["previous_odometer_km"]
    )

    # The current refill quantity represents fuel
    # consumed since the previous full-tank refill.
    valid_intervals = full_tank[
        (full_tank["distance_between_refills_km"] > 0)
        & (full_tank["fuel_quantity_litres"] > 0)
        & (full_tank["fuel_cost_inr"] >= 0)
    ].copy()

    valid_intervals["km_per_litre"] = (
        valid_intervals["distance_between_refills_km"]
        / valid_intervals["fuel_quantity_litres"]
    )

    valid_intervals["fuel_cost_per_km"] = (
        valid_intervals["fuel_cost_inr"]
        / valid_intervals["distance_between_refills_km"]
    )

    valid_intervals["interval_start_date"] = (
        valid_intervals["previous_transaction_date"]
    )

    valid_intervals["interval_end_date"] = (
        valid_intervals["transaction_date"]
    )

    # Add vehicle type
    valid_intervals = valid_intervals.merge(
        vehicles[["vehicle_id", "vehicle_type"]],
        on="vehicle_id",
        how="left"
    )

    interval_columns = [
        "vehicle_id",
        "vehicle_type",
        "previous_transaction_date",
        "transaction_date",
        "previous_odometer_km",
        "odometer_km",
        "distance_between_refills_km",
        "fuel_quantity_litres",
        "fuel_cost_inr",
        "km_per_litre",
        "fuel_cost_per_km"
    ]

    interval_report = valid_intervals[
        interval_columns
    ].copy()

    # Vehicle-wise weighted metrics
    vehicle_efficiency = (
        valid_intervals.groupby(
            ["vehicle_id", "vehicle_type"],
            as_index=False
        )
        .agg(
            total_distance_km=(
                "distance_between_refills_km", "sum"
            ),
            total_fuel_litres=(
                "fuel_quantity_litres", "sum"
            ),
            total_fuel_cost_inr=(
                "fuel_cost_inr", "sum"
            ),
            valid_refill_intervals=(
                "receipt_id", "count"
            )
        )
    )

    vehicle_efficiency["km_per_litre"] = (
        vehicle_efficiency["total_distance_km"]
        / vehicle_efficiency["total_fuel_litres"]
    )

    vehicle_efficiency["fuel_cost_per_km"] = (
        vehicle_efficiency["total_fuel_cost_inr"]
        / vehicle_efficiency["total_distance_km"]
    )

    print(
        f"Valid full-tank intervals: {len(interval_report)}"
    )

    return interval_report, vehicle_efficiency


# --------------------------------------------------
# 5. VEHICLE TYPE COMPARISON
# --------------------------------------------------

def compare_vehicle_types(vehicle_efficiency, vehicles):

    print("\nComparing similar vehicle types...")

    comparison = vehicle_efficiency.groupby(
        "vehicle_type",
        as_index=False
    ).agg(
        vehicle_count=("vehicle_id", "nunique"),
        average_km_per_litre=("km_per_litre", "mean"),
        average_fuel_cost_per_km=(
            "fuel_cost_per_km", "mean"
        ),
        total_distance_km=("total_distance_km", "sum"),
        total_fuel_cost_inr=(
            "total_fuel_cost_inr", "sum"
        )
    )

    comparison = comparison.sort_values(
        "average_km_per_litre",
        ascending=False
    )

    return comparison


# --------------------------------------------------
# 6. ROUTE ANALYSIS
# --------------------------------------------------

def analyze_routes(trips, routes, vehicles):

    print("\nAnalyzing route performance...")

    route_data = trips.merge(
        routes[
            ["route_id", "route_name", "route_distance_km"]
        ],
        on="route_id",
        how="left"
    )

    route_data = route_data.merge(
        vehicles[["vehicle_id", "vehicle_type"]],
        on="vehicle_id",
        how="left"
    )

    route_data["distance_deviation_km"] = (
        route_data["distance_km"]
        - route_data["route_distance_km"]
    )

    route_data["distance_deviation_pct"] = (
        route_data["distance_deviation_km"].abs()
        / route_data["route_distance_km"].replace(0, np.nan)
        * 100
    )

    # Compare same vehicle types on the same routes
    route_comparison = (
        route_data.groupby(
            ["vehicle_type", "route_id", "route_name"],
            as_index=False
        )
        .agg(
            trip_count=("trip_id", "count"),
            average_trip_distance_km=(
                "distance_km", "mean"
            ),
            route_reference_distance_km=(
                "route_distance_km", "first"
            ),
            average_deviation_pct=(
                "distance_deviation_pct", "mean"
            )
        )
    )

    route_comparison = route_comparison.sort_values(
        ["vehicle_type", "route_name"]
    )

    return route_data, route_comparison


# --------------------------------------------------
# 7. MONTHLY MAINTENANCE ANALYSIS
# --------------------------------------------------

def analyze_maintenance(maintenance, vehicles):

    print("\nAnalyzing maintenance expenses...")

    maintenance = maintenance.copy()

    maintenance["month"] = (
        maintenance["service_date"]
        .dt.to_period("M")
        .astype(str)
    )

    maintenance = maintenance.merge(
        vehicles[["vehicle_id", "vehicle_type"]],
        on="vehicle_id",
        how="left"
    )

    monthly_report = (
        maintenance.groupby(
            ["vehicle_id", "vehicle_type", "month"],
            as_index=False
        )
        .agg(
            service_count=("service_id", "count"),
            maintenance_cost_inr=(
                "maintenance_cost_inr", "sum"
            )
        )
    )

    return monthly_report


# --------------------------------------------------
# 8. OUTLIER DETECTION USING IQR
# --------------------------------------------------

def detect_iqr_outliers(
    df,
    metric,
    group_columns,
    label_column,
    metric_name
):

    outliers = []

    for group_values, group in df.groupby(
        group_columns,
        dropna=False
    ):

        values = group[metric].dropna()

        # Need enough peer observations for a useful comparison
        if len(values) < 4:
            continue

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        unusual = group[
            (group[metric] < lower_bound)
            | (group[metric] > upper_bound)
        ]

        if not isinstance(group_values, tuple):
            group_values = (group_values,)

        peer_group = " | ".join(
            str(value) for value in group_values
        )

        for _, row in unusual.iterrows():

            outliers.append({
                "record_type": "vehicle_metric",
                "record_id": row[label_column],
                "vehicle_id": row.get("vehicle_id"),
                "peer_group": peer_group,
                "metric": metric_name,
                "observed_value": row[metric],
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "reason": (
                    f"{metric_name} is outside the "
                    "peer-group IQR range"
                )
            })

    return outliers


# --------------------------------------------------
# 9. BUILD OUTLIER EVIDENCE REPORT
# --------------------------------------------------

def create_outlier_report(
    vehicle_efficiency,
    maintenance_monthly,
    route_data
):

    print("\nDetecting unusual records...")

    outliers = []

    # Fuel efficiency outliers within vehicle types
    outliers.extend(
        detect_iqr_outliers(
            vehicle_efficiency,
            "km_per_litre",
            ["vehicle_type"],
            "vehicle_id",
            "km_per_litre"
        )
    )

    # Fuel cost outliers within vehicle types
    outliers.extend(
        detect_iqr_outliers(
            vehicle_efficiency,
            "fuel_cost_per_km",
            ["vehicle_type"],
            "vehicle_id",
            "fuel_cost_per_km"
        )
    )

    # Maintenance cost outliers within same vehicle type and month
    outliers.extend(
        detect_iqr_outliers(
            maintenance_monthly,
            "maintenance_cost_inr",
            ["vehicle_type", "month"],
            "vehicle_id",
            "monthly_maintenance_cost_inr"
        )
    )

    # Trip distance deviations from the route reference
    unusual_trips = route_data[
        route_data["distance_deviation_pct"] > 20
    ].copy()

    for _, row in unusual_trips.iterrows():

        outliers.append({
            "record_type": "trip",
            "record_id": row["trip_id"],
            "vehicle_id": row["vehicle_id"],
            "peer_group": (
                f'{row["vehicle_type"]} | {row["route_name"]}'
            ),
            "metric": "route_distance_deviation_pct",
            "observed_value": row["distance_deviation_pct"],
            "lower_bound": 0,
            "upper_bound": 20,
            "reason": (
                "Trip distance differs from route reference "
                "by more than 20%; verify route and odometer"
            )
        })

    columns = [
        "record_type",
        "record_id",
        "vehicle_id",
        "peer_group",
        "metric",
        "observed_value",
        "lower_bound",
        "upper_bound",
        "reason"
    ]

    return pd.DataFrame(outliers, columns=columns)


# --------------------------------------------------
# 10. ANALYTICS SUMMARY
# --------------------------------------------------

def create_analytics_summary(
    vehicles,
    trips,
    fuel_intervals,
    vehicle_efficiency,
    maintenance_monthly,
    outlier_report
):

    total_fuel_distance = (
        fuel_intervals["distance_between_refills_km"].sum()
    )

    total_fuel_litres = (
        fuel_intervals["fuel_quantity_litres"].sum()
    )

    total_fuel_cost = (
        fuel_intervals["fuel_cost_inr"].sum()
    )

    total_maintenance = (
        maintenance_monthly["maintenance_cost_inr"].sum()
    )

    overall_km_per_litre = (
        total_fuel_distance / total_fuel_litres
        if total_fuel_litres > 0 else np.nan
    )

    overall_fuel_cost_per_km = (
        total_fuel_cost / total_fuel_distance
        if total_fuel_distance > 0 else np.nan
    )

    summary = pd.DataFrame([
        {
            "metric": "total_vehicles",
            "value": vehicles["vehicle_id"].nunique()
        },
        {
            "metric": "total_clean_trips",
            "value": len(trips)
        },
        {
            "metric": "valid_full_tank_intervals",
            "value": len(fuel_intervals)
        },
        {
            "metric": "vehicles_with_efficiency_data",
            "value": vehicle_efficiency["vehicle_id"].nunique()
        },
        {
            "metric": "total_distance_between_refills_km",
            "value": round(total_fuel_distance, 2)
        },
        {
            "metric": "total_fuel_litres_in_intervals",
            "value": round(total_fuel_litres, 2)
        },
        {
            "metric": "overall_fuel_efficiency_km_per_litre",
            "value": round(overall_km_per_litre, 2)
            if pd.notna(overall_km_per_litre) else np.nan
        },
        {
            "metric": "overall_fuel_cost_per_km",
            "value": round(overall_fuel_cost_per_km, 2)
            if pd.notna(overall_fuel_cost_per_km) else np.nan
        },
        {
            "metric": "total_maintenance_cost_inr",
            "value": round(total_maintenance, 2)
        },
        {
            "metric": "records_requiring_verification",
            "value": len(outlier_report)
        }
    ])

    return summary


# --------------------------------------------------
# 11. MAIN EXECUTION
# --------------------------------------------------

def main():

    print("=" * 55)
    print("FLEETIQ - DAY 2 ANALYTICS PIPELINE")
    print("=" * 55)

    # Load cleaned datasets
    vehicles, routes, trips, fuel, maintenance = (
        load_cleaned_data()
    )

    # Fuel efficiency
    fuel_intervals, vehicle_efficiency = (
        calculate_fuel_efficiency(fuel, vehicles)
    )

    # Vehicle type comparison
    vehicle_type_comparison = compare_vehicle_types(
        vehicle_efficiency,
        vehicles
    )

    # Route analysis
    route_data, route_comparison = analyze_routes(
        trips,
        routes,
        vehicles
    )

    # Monthly maintenance
    maintenance_monthly = analyze_maintenance(
        maintenance,
        vehicles
    )

    # Outlier detection
    outlier_report = create_outlier_report(
        vehicle_efficiency,
        maintenance_monthly,
        route_data
    )

    # Overall summary
    analytics_summary = create_analytics_summary(
        vehicles,
        trips,
        fuel_intervals,
        vehicle_efficiency,
        maintenance_monthly,
        outlier_report
    )

    # Save all analytics outputs
    save_report(
        fuel_intervals,
        "full_tank_efficiency_intervals.csv"
    )

    save_report(
        vehicle_efficiency,
        "vehicle_efficiency.csv"
    )

    save_report(
        vehicle_type_comparison,
        "vehicle_type_comparison.csv"
    )

    save_report(
        route_comparison,
        "route_comparison.csv"
    )

    save_report(
        maintenance_monthly,
        "maintenance_monthly.csv"
    )

    save_report(
        outlier_report,
        "outlier_evidence.csv"
    )

    save_report(
        analytics_summary,
        "analytics_summary.csv"
    )

    print("\n" + "=" * 55)
    print("DAY 2 ANALYTICS COMPLETED SUCCESSFULLY!")
    print("=" * 55)

    print("\nAnalytics Summary:")
    print(analytics_summary.to_string(index=False))

    print(
        f"\nAll reports saved inside: {REPORTS_DIR}"
    )


if __name__ == "__main__":
    main()
