# FleetIQ

### Fleet Fuel Efficiency and Maintenance Decision Support System

**FleetIQ** is a data engineering and visualization project designed to help logistics companies monitor vehicle fuel efficiency, operating costs, maintenance expenses, and data quality.

## Problem Statement

Logistics companies maintain vehicle registries, trip records, fuel transactions, odometer readings, route summaries, and maintenance records.

However, duplicate fuel entries, inconsistent units, irregular odometer readings, and incomplete trips can distort operational analytics.

FleetIQ aims to clean, validate, standardize, and analyze fleet data to support better operational decisions.

## Key Features

- Duplicate fuel receipt detection.
- Distance and fuel unit standardization.
- Odometer reversal detection.
- Incomplete trip identification.
- Vehicle-wise fuel efficiency analysis.
- Fuel cost per kilometre calculation.
- Maintenance cost analysis.
- Vehicle and route comparisons.
- Data quality and verification reports.
- Interactive fleet dashboard.

## Technology Stack

- Python
- Pandas
- NumPy
- SQLite
- Streamlit
- Plotly
- Git and GitHub

## Project Structure

```text
FLEETIQ/
├── data/
│   ├── raw/
│   ├── processed/
│   └── reports/
├── src/
├── dashboard/
├── database/
├── docs/
├── tests/
├── requirements.txt
├── run_pipeline.py
└── README.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/purushottam08-nova/FleetIQ.git
cd FleetIQ
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Project Execution

Run the data pipeline:

```bash
python run_pipeline.py
```

Run tests:

```bash
python tests/test_pipeline.py
```

## Development Roadmap

- [x] Project initialization
- [ ] Day 1: Data engineering and cleaning
- [ ] Day 2: Fleet analytics and comparisons
- [ ] Day 3: Interactive dashboard and finalization

## Expected Outcome

A reliable fleet analytics application containing cleaned datasets, data quality reports, vehicle comparison insights, and an interactive dashboard.

## Author

Purushottam Pelapkar

GitHub: [purushottam08-nova](https://github.com/purushottam08-nova)
