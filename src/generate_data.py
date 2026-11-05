from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)


# --------------------------------
# 1. VEHICLE REGISTRY
# --------------------------------

vehicles = []

vehicle_types = ["Truck", "Van", "Mini Truck"]
fuel_types = ["Diesel", "Diesel", "Petrol"]

for i in range(15):
    vehicles.append({
        "vehicle_id": f"V{i+1:03d}",
        "registration_no": f"MH12AB{i+1:04d}",
        "vehicle_type": vehicle_types[i % 3],
        "fuel_type": fuel_types[i % 3],
        "capacity_tons": [10, 2, 5][i % 3]
    })

vehicles_df = pd.DataFrame(vehicles)


# --------------------------------
# 2. ROUTE REGISTRY
# --------------------------------

routes = [
    ("R001", "Pune-Mumbai", 150),
    ("R002", "Pune-Nashik", 210),
    ("R003", "Mumbai-Surat", 285),
    ("R004", "Pune-Nagpur", 720),
    ("R005", "Mumbai-Goa", 590),
    ("R006", "Nashik-Aurangabad", 185)
]

routes_df = pd.DataFrame(
    routes,
    columns=["route_id", "route_name", "route_distance_km"]
)


# --------------------------------
# 3. TRIP RECORDS
# --------------------------------

trip_records = []
trip_end_readings = {}

base_date = pd.Timestamp("2026-01-01")

for vehicle_index in range(15):

    vehicle_id = f"V{vehicle_index+1:03d}"

    current_odo = 15000 + vehicle_index * 1200

    for trip_number in range(12):

        route = routes[trip_number % len(routes)]

        route_id = route[0]
        route_distance = route[2]

        actual_distance = max(
            30,
            route_distance * rng.uniform(0.90, 1.10)
        )

        distance_unit = (
            "miles" if trip_number % 3 == 0 else "km"
        )

        odo_unit = (
            "miles" if trip_number % 4 == 0 else "km"
        )

        distance_factor = (
            1.60934 if distance_unit == "miles" else 1
        )

        odo_factor = (
            1.60934 if odo_unit == "miles" else 1
        )

        start_odo = current_odo

        end_odo = current_odo + actual_distance

        trip_id = (
            f"T{vehicle_index+1:03d}{trip_number+1:03d}"
        )

        start_time = (
            base_date
            + pd.Timedelta(days=vehicle_index + trip_number * 3)
        )

        end_time = start_time + pd.Timedelta(hours=5)

        reported_distance = actual_distance / distance_factor

        reported_start_odo = start_odo / odo_factor
        reported_end_odo = end_odo / odo_factor

        status = "Completed"

        # Intentional odometer reversal
        if vehicle_index == 1 and trip_number == 5:
            reported_end_odo = (start_odo - 20) / odo_factor

        # Intentional incomplete trip
        if vehicle_index == 0 and trip_number == 3:
            end_time = pd.NaT
            reported_end_odo = np.nan
            reported_distance = np.nan
            status = "Incomplete"

        trip_records.append({
            "trip_id": trip_id,
            "vehicle_id": vehicle_id,
            "route_id": route_id,
            "start_datetime": start_time,
            "end_datetime": end_time,
            "start_odometer": round(reported_start_odo, 2),
            "end_odometer": round(reported_end_odo, 2)
            if pd.notna(reported_end_odo) else np.nan,
            "odometer_unit": odo_unit,
            "distance_value": round(reported_distance, 2)
            if pd.notna(reported_distance) else np.nan,
            "distance_unit": distance_unit,
            "trip_status": status
        })

        trip_end_readings[(vehicle_id, trip_number)] = end_odo

        current_odo = end_odo


trips_df = pd.DataFrame(trip_records)


# --------------------------------
# 4. FUEL TRANSACTIONS
# --------------------------------

fuel_records = []

for vehicle_index in range(15):

    vehicle_id = f"V{vehicle_index+1:03d}"

    for trip_number in [1, 3, 5, 7, 9, 11]:

        odo_km = trip_end_readings[
            (vehicle_id, trip_number)
        ]

        fuel_unit = (
            "gallon"
            if (vehicle_index + trip_number) % 2 == 0
            else "litre"
        )

        odo_unit = (
            "miles" if trip_number % 3 == 0 else "km"
        )

        litres = rng.uniform(80, 160)

        quantity = (
            litres / 3.78541
            if fuel_unit == "gallon"
            else litres
        )

        odo_reading = (
            odo_km / 1.60934
            if odo_unit == "miles"
            else odo_km
        )

        transaction_date = (
            base_date
            + pd.Timedelta(
                days=vehicle_index + trip_number * 3
            )
        )

        receipt_id = (
            f"REC{vehicle_index+1:03d}{trip_number+1:03d}"
        )

        fuel_records.append({
            "receipt_id": receipt_id,
            "vehicle_id": vehicle_id,
            "transaction_date": transaction_date,
            "fuel_quantity": round(quantity, 2),
            "fuel_unit": fuel_unit,
            "fuel_cost_inr": round(litres * 95, 2),
            "odometer_reading": round(odo_reading, 2),
            "odometer_unit": odo_unit,
            "full_tank": True
        })


fuel_df = pd.DataFrame(fuel_records)

# Intentional duplicate receipt
fuel_df = pd.concat(
    [fuel_df, fuel_df.iloc[[0]]],
    ignore_index=True
)


# --------------------------------
# 5. MAINTENANCE RECORDS
# --------------------------------

maintenance_records = []

for vehicle_index in range(15):

    vehicle_id = f"V{vehicle_index+1:03d}"

    for service_number in range(2):

        odo_km = (
            20000
            + vehicle_index * 1200
            + service_number * 5000
        )

        odo_unit = (
            "miles" if service_number == 1 else "km"
        )

        odo_reading = (
            odo_km / 1.60934
            if odo_unit == "miles"
            else odo_km
        )

        maintenance_records.append({
            "service_id": (
                f"M{vehicle_index+1:03d}{service_number+1:02d}"
            ),
            "vehicle_id": vehicle_id,
            "service_date": (
                base_date
                + pd.Timedelta(days=vehicle_index * 10)
            ),
            "maintenance_type": (
                "Oil Change"
                if service_number == 0
                else "General Service"
            ),
            "maintenance_cost_inr": int(
                rng.integers(1500, 10000)
            ),
            "odometer_reading": round(odo_reading, 2),
            "odometer_unit": odo_unit
        })


maintenance_df = pd.DataFrame(maintenance_records)


# --------------------------------
# 6. SAVE RAW DATASETS
# --------------------------------

datasets = {
    "vehicles.csv": vehicles_df,
    "routes.csv": routes_df,
    "trips.csv": trips_df,
    "fuel_transactions.csv": fuel_df,
    "maintenance.csv": maintenance_df
}

for filename, dataframe in datasets.items():

    dataframe.to_csv(
        RAW_DIR / filename,
        index=False
    )

    print(f"Created: {filename} | Rows: {len(dataframe)}")


print("\nAll raw datasets generated successfully!")