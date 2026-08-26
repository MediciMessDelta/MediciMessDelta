import pytest

from api.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

def test_health_endpoint(client):
    response = client.get("/api/health")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "healthy"
    assert data["service"] == "MediciMess API"

def test_transactions_can_be_filtered(client):
    response = client.get(
        "/api/transactions"
        "?branch=Rome"
        "&type=deposit"
        "&start=1420-01-01"
        "&end=1420-12-31"
        "&page=1"
        "&per_page=2"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert len(data["transactions"]) == 2

    for transaction in data["transactions"]:
        assert transaction["branch"] == "Rome"
        assert transaction["type"] == "deposit"
        assert transaction["date"].startswith("1420-")

def test_start_date_cannot_be_after_end_date(client):
    response = client.get(
        "/api/transactions"
        "?start=1421-01-01"
        "&end=1420-01-01"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "start date cannot be after end date"
    )


def test_dates_require_correct_format(client):
    response = client.get(
        "/api/transactions?start=01-01-1420"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "start and end must use YYYY-MM-DD format"
    )


def test_per_page_cannot_exceed_100(client):
    response = client.get(
        "/api/transactions?per_page=101"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "per_page must be between 1 and 100"
    )

def test_kpi_endpoint_returns_summary(client):
    response = client.get(
        "/api/kpis"
        "?branch=Florence"
        "&start=1420-01-01"
        "&end=1420-12-31"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["branch"] == "Florence"
    assert data["period"]["start"] == "1420-01-01"
    assert data["period"]["end"] == "1420-12-31"
    assert data["data_source"] == "development_fixture"

    assert "cash_position" in data["kpis"]
    assert "deposits" in data["kpis"]
    assert "withdrawals" in data["kpis"]
    assert "loans" in data["kpis"]
    assert "operating_expenses" in data["kpis"]
    assert "revenue" in data["kpis"]
    assert "net_income" in data["kpis"]

def test_kpi_endpoint_requires_dates(client):
    response = client.get(
        "/api/kpis?branch=Florence"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "missing required parameters"
    )
    assert data["missing"] == ["start", "end"]

def test_kpi_start_date_cannot_be_after_end_date(
    client
):
    response = client.get(
        "/api/kpis"
        "?branch=Florence"
        "&start=1421-01-01"
        "&end=1420-01-01"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "start date cannot be after end date"
    )

def test_cashflow_endpoint_returns_monthly_data(
    client
):
    response = client.get(
        "/api/cashflow"
        "?branch=Florence"
        "&start=1420-01-01"
        "&end=1420-12-31"
        "&granularity=monthly"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["branch"] == "Florence"
    assert data["granularity"] == "monthly"
    assert data["data_source"] == (
        "development_fixture"
    )
    assert len(data["time_series"]) == 3
    assert data["time_series"][0]["period"] == (
        "1420-01"
    )

def test_cashflow_granularity_is_case_insensitive(
    client
):
    response = client.get(
        "/api/cashflow"
        "?branch=Rome"
        "&start=1420-01-01"
        "&end=1420-12-31"
        "&granularity=WEEKLY"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["granularity"] == "weekly"
    assert len(data["time_series"]) == 2

def test_cashflow_rejects_invalid_granularity(
    client
):
    response = client.get(
        "/api/cashflow"
        "?branch=Florence"
        "&start=1420-01-01"
        "&end=1420-12-31"
        "&granularity=yearly"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "granularity must be daily, weekly, "
        "or monthly"
    )

def test_cashflow_requires_branch_and_dates(client):
    response = client.get("/api/cashflow")

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "missing required parameters"
    )
    assert data["missing"] == [
        "branch",
        "start",
        "end"
    ]