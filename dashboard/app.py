from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

# Support both `streamlit run dashboard/app.py` and imports from project root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.data_loader import load_dashboard_data

st.set_page_config(
    page_title="FleetIQ | Fleet Decision Support",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚚 FleetIQ")
st.caption("Fleet Fuel Efficiency and Maintenance Decision Support")
st.markdown(
    "Monitor fleet activity, full-tank fuel efficiency, operating cost, "
    "maintenance and records that need verification."
)

@st.cache_data(show_spinner="Loading FleetIQ datasets...")
def get_data():
    return load_dashboard_data()

try:
    data = get_data()
except (FileNotFoundError, ValueError, pd.errors.ParserError) as exc:
    st.error(f"Could not load FleetIQ data: {exc}")
    st.info("Run the Day 1 pipeline and Day 2 analytics first. See README.md.")
    st.stop()

vehicles = data["vehicles"].copy()
trips = data["trips"].copy()
intervals = data["efficiency_intervals"].copy()
maintenance = data["maintenance"].copy()
monthly = data["maintenance_monthly"].copy()
routes = data["routes"].copy()
vehicle_efficiency = data["vehicle_efficiency"].copy()
outliers = data["outliers"].copy()
quality = data["data_quality"].copy()

# Convert report month labels into dates for filtering.
monthly["month_date"] = pd.to_datetime(monthly["month"] + "-01", errors="coerce")
trips["start_datetime"] = pd.to_datetime(trips["start_datetime"], errors="coerce")
intervals["transaction_date"] = pd.to_datetime(intervals["transaction_date"], errors="coerce")
maintenance["service_date"] = pd.to_datetime(maintenance["service_date"], errors="coerce")

all_types = sorted(vehicles["vehicle_type"].dropna().unique().tolist())
min_dates = []
max_dates = []
for frame, col in [
    (trips, "start_datetime"),
    (intervals, "transaction_date"),
    (maintenance, "service_date"),
]:
    valid = frame[col].dropna()
    if not valid.empty:
        min_dates.append(valid.min().date())
        max_dates.append(valid.max().date())

date_min = min(min_dates) if min_dates else pd.Timestamp.today().date()
date_max = max(max_dates) if max_dates else date_min

st.sidebar.header("Dashboard Filters")
selected_types = st.sidebar.multiselect("Vehicle type", all_types, default=all_types)
type_vehicles = vehicles[vehicles["vehicle_type"].isin(selected_types)]
all_vehicle_ids = sorted(type_vehicles["vehicle_id"].dropna().unique().tolist())
selected_vehicles = st.sidebar.multiselect(
    "Vehicle", all_vehicle_ids, default=all_vehicle_ids
)
date_range = st.sidebar.date_input(
    "Analysis date range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

def in_range(series):
    dates = pd.to_datetime(series, errors="coerce").dt.date
    return dates.ge(start_date) & dates.le(end_date)

trip_f = trips[
    trips["vehicle_id"].isin(selected_vehicles) & in_range(trips["start_datetime"])
].copy()
interval_f = intervals[
    intervals["vehicle_id"].isin(selected_vehicles)
    & in_range(intervals["transaction_date"])
].copy()
maintenance_f = maintenance[
    maintenance["vehicle_id"].isin(selected_vehicles)
    & in_range(maintenance["service_date"])
].copy()
monthly_f = monthly[
    monthly["vehicle_id"].isin(selected_vehicles)
    & monthly["month_date"].dt.date.ge(start_date)
    & monthly["month_date"].dt.date.le(end_date)
].copy()
# Re-aggregate from the already date-filtered refill intervals so the date
# filter also affects vehicle and vehicle-type efficiency comparisons.
if interval_f.empty:
    efficiency_f = pd.DataFrame(columns=[
        "vehicle_id", "vehicle_type", "total_distance_km",
        "total_fuel_litres", "total_fuel_cost_inr",
        "km_per_litre", "fuel_cost_per_km"
    ])
else:
    efficiency_f = interval_f.groupby(
        ["vehicle_id", "vehicle_type"], as_index=False
    ).agg(
        total_distance_km=("distance_between_refills_km", "sum"),
        total_fuel_litres=("fuel_quantity_litres", "sum"),
        total_fuel_cost_inr=("fuel_cost_inr", "sum"),
    )
    efficiency_f["km_per_litre"] = (
        efficiency_f["total_distance_km"] / efficiency_f["total_fuel_litres"]
    )
    efficiency_f["fuel_cost_per_km"] = (
        efficiency_f["total_fuel_cost_inr"] / efficiency_f["total_distance_km"]
    )
outlier_f = outliers[outliers["vehicle_id"].isin(selected_vehicles)].copy()

# Fleet overview metrics: efficiency/cost are interval-weighted, never based on all fuel purchases.
distance_total = pd.to_numeric(trip_f["distance_km"], errors="coerce").sum()
vehicle_count = trip_f["vehicle_id"].nunique()
trip_count = len(trip_f)
if not interval_f.empty:
    interval_distance = interval_f["distance_between_refills_km"].sum()
    interval_litres = interval_f["fuel_quantity_litres"].sum()
    interval_cost = interval_f["fuel_cost_inr"].sum()
    weighted_kml = interval_distance / interval_litres if interval_litres > 0 else float("nan")
    cost_per_km = interval_cost / interval_distance if interval_distance > 0 else float("nan")
else:
    interval_distance = interval_litres = interval_cost = 0
    weighted_kml = cost_per_km = float("nan")
maintenance_cost = maintenance_f["maintenance_cost_inr"].sum()
fuel_purchased_litres = data["fuel"].loc[
    data["fuel"]["vehicle_id"].isin(selected_vehicles)
    & in_range(data["fuel"]["transaction_date"]),
    "fuel_quantity_litres"
].sum()

st.subheader("Fleet overview")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Vehicles active in trips", f"{vehicle_count:,}")
k2.metric("Clean trips", f"{trip_count:,}")
k3.metric("Trip distance", f"{distance_total:,.0f} km")
k4.metric("Full-tank efficiency", f"{weighted_kml:,.2f} km/L" if pd.notna(weighted_kml) else "N/A")
k5.metric("Fuel cost / distance", f"₹{cost_per_km:,.2f}/km" if pd.notna(cost_per_km) else "N/A")

st.caption(
    f"Selected period: {start_date} to {end_date} · "
    f"Full-tank interval distance: {interval_distance:,.1f} km · "
    f"Refill quantity used in intervals: {interval_litres:,.1f} L"
)

with st.expander("Important metric definitions and data caveats"):
    st.markdown(
        "- **KM/L and fuel cost/km** use successive valid full-tank refill intervals only. "
        "The current full-tank refill quantity is treated as fuel used since the previous "
        "full-tank refill (full-to-full assumption).\n"
        "- **Fuel purchased** is a separate transaction total; it is not presented as "
        "fuel consumed or used to calculate KM/L.\n"
        "- Fuel transactions have no route identifier, so this dashboard does **not** "
        "attribute fuel cost or fuel efficiency to individual routes.\n"
        "- Route performance compares recorded trip distance with the route reference "
        "distance; it is not a route-level fuel-cost comparison.\n"
        "- The date filter applies to trip start date, refill transaction date, and "
        "maintenance service date respectively. Vehicle efficiency comparisons are "
        "re-aggregated from the selected refill intervals."
    )

st.divider()
st.subheader("Fuel efficiency and operating cost")
left, right = st.columns(2)
with left:
    if interval_f.empty:
        st.info("No valid full-tank refill intervals for the selected filters.")
    else:
        fig = px.scatter(
            interval_f, x="transaction_date", y="km_per_litre",
            color="vehicle_type", hover_data=["vehicle_id", "distance_between_refills_km",
                                               "fuel_quantity_litres"],
            title="Full-tank interval fuel efficiency",
            labels={"transaction_date": "Refill date", "km_per_litre": "Efficiency (km/L)"},
        )
        st.plotly_chart(fig, use_container_width=True)
with right:
    if interval_f.empty:
        st.info("No full-tank interval cost data for the selected filters.")
    else:
        cost_plot = interval_f.copy()
        cost_plot["month"] = cost_plot["transaction_date"].dt.to_period("M").astype(str)
        cost_month = cost_plot.groupby("month", as_index=False).agg(
            fuel_cost_inr=("fuel_cost_inr", "sum"),
            interval_distance_km=("distance_between_refills_km", "sum"),
        )
        fig = px.bar(
            cost_month, x="month", y="fuel_cost_inr",
            title="Fuel cost recorded in valid full-tank intervals",
            labels={"month": "Month", "fuel_cost_inr": "Fuel cost (₹)"},
            hover_data=["interval_distance_km"],
        )
        st.plotly_chart(fig, use_container_width=True)

st.caption(f"Fuel purchased in selected period (separate transaction measure): **{fuel_purchased_litres:,.1f} L**")

st.divider()
st.subheader("Vehicle and vehicle-type comparison")
left, right = st.columns(2)
with left:
    if efficiency_f.empty:
        st.info("No vehicle efficiency records for selected vehicles.")
    else:
        fig = px.bar(
            efficiency_f.sort_values("km_per_litre", ascending=False),
            x="vehicle_id", y="km_per_litre", color="vehicle_type",
            title="Vehicle-wise weighted full-tank efficiency",
            labels={"vehicle_id": "Vehicle", "km_per_litre": "Efficiency (km/L)"},
            hover_data=["total_distance_km", "total_fuel_litres", "fuel_cost_per_km"],
        )
        st.plotly_chart(fig, use_container_width=True)
with right:
    if efficiency_f.empty:
        st.info("No vehicle type comparison available.")
    else:
        type_summary = efficiency_f.groupby("vehicle_type", as_index=False).agg(
            vehicles=("vehicle_id", "nunique"),
            average_km_per_litre=("km_per_litre", "mean"),
            average_fuel_cost_per_km=("fuel_cost_per_km", "mean"),
        )
        fig = px.bar(
            type_summary, x="vehicle_type", y="average_km_per_litre",
            title="Average vehicle efficiency by vehicle type",
            labels={"vehicle_type": "Vehicle type", "average_km_per_litre": "Average km/L"},
            hover_data=["vehicles", "average_fuel_cost_per_km"],
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Route performance (trip distance only)")
if trip_f.empty:
    st.info("No trips for the selected filters.")
else:
    route_view = trip_f.merge(
        routes[["route_id", "route_name", "route_distance_km"]],
        on="route_id", how="left"
    ).merge(
        vehicles[["vehicle_id", "vehicle_type"]],
        on="vehicle_id", how="left"
    )
    route_view["deviation_pct"] = (
        (route_view["distance_km"] - route_view["route_distance_km"]).abs()
        / route_view["route_distance_km"].replace(0, pd.NA) * 100
    )
    route_summary = route_view.groupby(
        ["vehicle_type", "route_name"], as_index=False
    ).agg(
        trip_count=("trip_id", "count"),
        average_trip_distance_km=("distance_km", "mean"),
        reference_distance_km=("route_distance_km", "first"),
        average_deviation_pct=("deviation_pct", "mean"),
    )
    fig = px.bar(
        route_summary, x="route_name", y="average_trip_distance_km",
        color="vehicle_type", barmode="group",
        title="Average trip distance by route and vehicle type",
        labels={"route_name": "Route", "average_trip_distance_km": "Average trip distance (km)"},
        hover_data=["trip_count", "reference_distance_km", "average_deviation_pct"],
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(route_summary, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Monthly maintenance analysis")
if monthly_f.empty:
    st.info("No maintenance records for the selected filters.")
else:
    monthly_summary = monthly_f.groupby("month", as_index=False).agg(
        maintenance_cost_inr=("maintenance_cost_inr", "sum"),
        service_count=("service_count", "sum"),
    )
    fig = px.bar(
        monthly_summary, x="month", y="maintenance_cost_inr",
        title="Monthly maintenance cost",
        labels={"month": "Month", "maintenance_cost_inr": "Maintenance cost (₹)"},
        hover_data=["service_count"],
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(monthly_f.sort_values(["month", "vehicle_id"]),
                 use_container_width=True, hide_index=True)

st.divider()
st.subheader("Outlier and verification evidence")
st.caption("These are candidate records to investigate, not automatic proof of fraud or mechanical failure.")
if outlier_f.empty:
    st.success("No outlier evidence records for the selected vehicles.")
else:
    st.dataframe(
        outlier_f[[
            "record_type", "record_id", "vehicle_id", "peer_group",
            "metric", "observed_value", "lower_bound", "upper_bound", "reason"
        ]],
        use_container_width=True, hide_index=True
    )

with st.expander("Data quality summary"):
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.write("Rejected / excluded records")
    rejected_path = ROOT / "data" / "reports" / "rejected_records.csv"
    if rejected_path.exists():
        st.dataframe(pd.read_csv(rejected_path), use_container_width=True, hide_index=True)

st.caption("FleetIQ · Decision-support prototype · Validate unusual records before operational action.")
