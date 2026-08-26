# MediciMess Phase 5 Serving Layer

## Overview

Phase 5 provides the serving layer between the MediciMess data
pipeline and the Streamlit dashboards.

The serving layer includes:

- A Flask REST API
- Paginated transaction access
- KPI, cash-flow, loan, expense, and alert endpoints
- Alert acknowledgement
- JSON and CSV output generation
- Request validation
- Automated integration and performance tests

## Current Data Sources

The transaction endpoint currently reads the historical transaction
CSV directly.

The following endpoints temporarily use development fixtures:

- KPI summary
- Cash-flow time series
- Loan portfolio
- Expense breakdown
- Anomaly alerts

These fixtures define and test the API contracts while the Phase 3
and Phase 4 modules are being completed.

Every fixture-backed response contains:

```json
```json
"data_source": "development_fixture"
```



## Project Structure

```text
api/
├── fixtures/
│   ├── alerts.json
│   ├── cashflow.json
│   ├── expense_breakdown.json
│   ├── kpi_summary.json
│   └── loan_portfolio.json
├── __init__.py
├── alert_service.py
├── app.py
├── cashflow_service.py
├── data_service.py
├── expense_service.py
├── kpi_service.py
├── loan_service.py
└── output_writer.py

tests/
└── test_api.py

generate_serving_outputs.py
```

## Installation

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Verify the installed packages:

```bash
python -m pip check
```

## Start the API

From the project root, run:

```bash
python -m api.app
```

The local development API runs at:

```text
http://127.0.0.1:5001
```

The Flask debug server is for local development only. A production
WSGI server should be used for deployment.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check API health |
| GET | `/api/transactions` | Return filtered, paginated transactions |
| GET | `/api/kpis` | Return a branch KPI summary |
| GET | `/api/cashflow` | Return cash-flow time-series data |
| GET | `/api/loans` | Return the loan portfolio |
| GET | `/api/expenses` | Return the expense breakdown |
| GET | `/api/alerts` | Return anomaly alerts |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge an alert |

## Health Check

```bash
curl http://127.0.0.1:5001/api/health
```

Expected response:

```json
{
  "service": "MediciMess API",
  "status": "healthy"
}
```

## Transactions

### Parameters

| Parameter | Required | Default | Description |
|---|---:|---:|---|
| `branch` | No | All | Branch name |
| `start` | No | None | Start date in `YYYY-MM-DD` |
| `end` | No | None | End date in `YYYY-MM-DD` |
| `type` | No | All | Transaction type |
| `page` | No | `1` | Page number |
| `per_page` | No | `25` | Page size, maximum 100 |

Example:

```bash
curl "http://127.0.0.1:5001/api/transactions?branch=Rome&type=deposit&start=1420-01-01&end=1420-12-31&page=1&per_page=25"
```

Branch and transaction-type filters are case-insensitive.

## KPI Summary

Required parameters:

- `branch`
- `start`
- `end`

Example:

```bash
curl "http://127.0.0.1:5001/api/kpis?branch=Florence&start=1420-01-01&end=1420-12-31"
```

The response includes cash position, deposits, withdrawals, loans,
operating expenses, revenue, and net income.

Financial values are serialized as strings to preserve decimal
precision.

## Cash Flow

Required parameters:

- `branch`
- `start`
- `end`

Optional parameter:

- `granularity`, which defaults to `monthly`

Allowed granularities:

- `daily`
- `weekly`
- `monthly`

Example:

```bash
curl "http://127.0.0.1:5001/api/cashflow?branch=Florence&start=1420-01-01&end=1420-12-31&granularity=monthly"
```

## Loan Portfolio

Required parameter:

- `branch`

Optional status values:

- `OPEN`
- `OVERDUE`
- `REPAID`

Example:

```bash
curl "http://127.0.0.1:5001/api/loans?branch=Florence&status=open"
```

Status filtering is case-insensitive.

## Expense Breakdown

Required parameters:

- `branch`
- `start`
- `end`

Example:

```bash
curl "http://127.0.0.1:5001/api/expenses?branch=Florence&start=1420-01-01&end=1420-12-31"
```

The response includes category totals, counterparties, transaction
counts, percentages, and top counterparties.

## Alerts

Optional parameters:

- `branch`
- `start`
- `end`
- `severity`

Allowed severities:

- `LOW`
- `MEDIUM`
- `HIGH`

Example:

```bash
curl "http://127.0.0.1:5001/api/alerts?branch=Florence&severity=high"
```

Alerts are sorted by severity and date.

## Acknowledge an Alert

The request requires a JSON body containing `user_id` and `note`.

```bash
curl -X POST \
  "http://127.0.0.1:5001/api/alerts/ALT-0001/acknowledge" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"matthew","note":"Reviewed the vendor transactions."}'
```

Possible status codes:

| Status | Meaning |
|---:|---|
| 200 | Alert acknowledged |
| 400 | Invalid or missing request data |
| 404 | Alert does not exist |
| 409 | Alert was already acknowledged |

Fixture acknowledgements are stored in memory and reset when Flask
restarts.

## Generate Output Artifacts

Run:

```bash
python generate_serving_outputs.py \
  --branch Florence \
  --start 1420-01-01 \
  --end 1420-12-31
```

The script creates:

```text
metrics_{branch}_{period}.json
time_series_{branch}.json
alerts_{branch}_{period}.json
expense_breakdown_{branch}_{period}.csv
loan_portfolio_{branch}_{period}.csv
```

Generated files are written to `serving_outputs/`. That directory is
ignored by Git because the files can be regenerated.

## Run Tests

```bash
python -m pytest tests/test_api.py -v
```

The Phase 5 suite currently contains 35 passing tests covering:

- Health checks
- Transaction filtering and pagination
- Input validation
- KPI response contracts
- Cash-flow granularity
- Loan-status filtering
- Expense response contracts
- Alert filtering and acknowledgement
- Output generation
- API response performance

## Run Code-Quality Checks

```bash
python -m ruff check \
  api \
  tests/test_api.py \
  generate_serving_outputs.py
```

## Performance Requirement

Each GET endpoint is tested after cache warm-up and must respond in
under 500 milliseconds.

The current implementation passes this requirement against the
80,230-row transaction dataset.

## Phase 3 and Phase 4 Integration

Replace fixture-loading calls when the upstream modules are ready:

| Service | Final source |
|---|---|
| `kpi_service.py` | Phase 3 KPI module |
| `cashflow_service.py` | Phase 3 time-series results |
| `loan_service.py` | Phase 3 loan portfolio |
| `expense_service.py` | Phase 3 expense breakdown |
| `alert_service.py` | Phase 4 anomaly records |

Keep the public endpoint URLs and response field names stable unless
the team agrees to update the API contract and Streamlit client.

After replacing any fixture:

1. Update the `data_source` field.
2. Update fixture-specific test expectations.
3. Run all tests.
4. Run Ruff.
5. Verify the response-time requirement.
6. Regenerate the serving-layer output files.

## Known Development Limitations

- KPI, cash-flow, loan, expense, and alert values currently use fixtures.
- Alert acknowledgements are not permanently stored.
- Authentication and role-based access are part of Phase 7.
- Flask debug mode is not suitable for production.

