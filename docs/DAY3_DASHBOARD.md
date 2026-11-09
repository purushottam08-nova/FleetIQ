# FleetIQ — Day 3 Dashboard Documentation

## 1. Overview

Day 3 focuses on developing an interactive fleet analytics dashboard using Streamlit and Plotly.

The dashboard provides fleet managers with a centralized interface to monitor vehicle performance, fuel efficiency, fuel expenditure, route performance, maintenance costs, and data-quality issues.

It builds on the cleaned datasets and analytical reports generated during Day 1 and Day 2.

## 2. Technology Stack

- Python
- Streamlit
- Plotly
- Pandas
- NumPy

## 3. Dashboard Features

### 3.1 Fleet Overview

Displays important fleet-level KPIs:

- Total registered vehicles
- Total clean trips
- Total distance travelled
- Full-tank fuel intervals
- Average fuel efficiency
- Fuel cost per kilometre
- Total maintenance expenditure
- Records requiring verification

### 3.2 Fuel Efficiency Analysis

- Displays vehicle-wise fuel efficiency.
- Compares full-tank interval-based KM/L.
- Shows fuel efficiency trends where date information is available.
- Identifies vehicles with unusually high or low efficiency.

**Calculation principle:**

Fuel efficiency is calculated using consecutive full-tank readings:

`Fuel Efficiency = Distance Travelled / Fuel Consumed`

Fuel purchased is not automatically treated as fuel consumed.

### 3.3 Fuel Cost Analysis

- Displays fuel expenditure.
- Calculates fuel cost per kilometre where supported by the analytical dataset.
- Compares vehicle-level fuel expenditure.
- Highlights unusually high fuel costs.

### 3.4 Vehicle Comparison

Allows comparison of vehicles based on:

- Vehicle category
- Fuel efficiency
- Distance travelled
- Fuel expenditure
- Maintenance expenditure

Comparisons should prioritize similar vehicle types to avoid misleading conclusions.

### 3.5 Route Analysis

Provides route-level insights using:

- Total trips
- Distance travelled
- Average trip distance
- Route activity

Route-level fuel consumption and fuel cost are not attributed unless reliable supporting data exists.

### 3.6 Maintenance Analysis

- Displays total maintenance expenditure.
- Provides monthly maintenance cost trends.
- Compares maintenance expenditure across vehicles.
- Highlights vehicles with relatively high maintenance costs.

### 3.7 Outlier Investigation

Provides detailed evidence for suspicious records.

Users can inspect:

- Vehicle identifiers
- Transaction or trip identifiers
- Recorded values
- Outlier categories
- Data-quality observations

Outliers are treated as investigation candidates, not automatically confirmed errors.

### 3.8 Interactive Filters

Where supported by available data, users can filter dashboard results by:

- Vehicle ID
- Vehicle type
- Date range
- Route

## 4. Data Sources

The dashboard uses the existing processed datasets and analytical reports.

### Processed datasets

- `clean_vehicles.csv`
- `clean_routes.csv`
- `clean_trips.csv`
- `clean_fuel_transactions.csv`
- `clean_maintenance.csv`

### Analytical reports

- `analytics_summary.csv`
- `full_tank_efficiency_intervals.csv`
- `vehicle_efficiency.csv`
- `vehicle_type_comparison.csv`
- `route_comparison.csv`
- `maintenance_monthly.csv`
- `outlier_evidence.csv`

All files are loaded from the project's `data/processed/` and `data/reports/` directories.

## 5. Data Quality Considerations

The dashboard preserves the data-quality decisions made during the data engineering and analytics stages.

Important considerations:

1. Duplicate fuel receipts must not be counted as separate valid transactions.
2. Odometer reversals require investigation.
3. Incomplete trips should not be included in unsupported calculations.
4. Missing values must not be silently interpreted as zero.
5. Fuel purchases and actual fuel consumption must remain separate concepts.
6. Full-tank interval-based fuel efficiency must use valid consecutive readings.
7. Route-level fuel attribution must not be assumed without supporting evidence.
8. Outliers must be reviewed before being classified as errors.

## 6. Installation

Activate the project's virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dashboard dependencies:

```powershell
python -m pip install -r requirements-dashboard.txt
```

## 7. Running the Dashboard

From the project root directory, execute:

```powershell
python -m streamlit run dashboard/app.py
```

Open the following address in your browser:

`http://localhost:8501`

## 8. Testing

Run the dashboard tests:

```powershell
python -m pytest -q tests/test_dashboard.py
```

Run the complete project test suite:

```powershell
python -m pytest -q
```

## 9. Expected Outcome

The final dashboard provides an interactive analytical interface for understanding fleet performance.

It helps identify:

- Fuel efficiency variations
- High fuel expenditure
- Vehicle performance differences
- Route activity patterns
- Increasing maintenance expenditure
- Suspicious or incomplete records

The dashboard supports evidence-based fleet management decisions while preserving the limitations and quality considerations of the underlying data.

## 10. Project Completion

Day 3 completes the visualization stage of FleetIQ.

The project workflow is:

1. **Day 1 — Data Engineering:** Data collection, cleaning, standardization and validation.
2. **Day 2 — Data Analytics:** Fuel efficiency, cost analysis, vehicle comparison, maintenance analysis and outlier detection.
3. **Day 3 — Visualization:** Interactive Streamlit dashboard with Plotly charts, filters, KPIs and investigation features.

**Project:** Fleet Fuel Efficiency and Maintenance Decision Support

**Technology:** Python, Pandas, NumPy, Streamlit and Plotly.