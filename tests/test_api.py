import csv
import json
import time

import pytest

from api.alert_service import reset_alert_fixture
from api.app import create_app
from api.output_writer import generate_serving_outputs


@pytest.fixture
def client():
    reset_alert_fixture()

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

    reset_alert_fixture()


def test_login_authenticates_managing_director(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "director",
            "password": "medici-director",
        },
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["authenticated"] is True
    assert data["user"]["username"] == "director"
    assert data["user"]["role"] == "MANAGING_DIRECTOR"
    assert data["user"]["branch"] is None
    assert "password" not in data["user"]


def test_login_authenticates_branch_user(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "florence_manager",
            "password": "medici-florence",
        },
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["authenticated"] is True
    assert data["user"]["username"] == "florence_manager"
    assert data["user"]["role"] == "BRANCH_USER"
    assert data["user"]["branch"] == "Florence"
    assert "password" not in data["user"]


def test_login_rejects_invalid_credentials(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "director",
            "password": "wrong-password",
        },
    )

    data = response.get_json()

    assert response.status_code == 401
    assert data["error"] == "invalid username or password"


def test_login_requires_credentials(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "director",
        },
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "username and password are required"
    )


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
        "&per_page=2",
        headers={"X-Username": "director"},
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
        "&end=1420-01-01",
        headers={"X-Username": "director"},
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "start date cannot be after end date"
    )

def test_dates_require_correct_format(client):
    response = client.get(
        "/api/transactions?start=01-01-1420",
        headers={"X-Username": "director"},
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "start and end must use YYYY-MM-DD format"
    )


def test_per_page_cannot_exceed_100(client):
    response = client.get(
        "/api/transactions?per_page=101",
        headers={"X-Username": "director"},
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "per_page must be between 1 and 100"
    )


@pytest.mark.parametrize(
    "query_string, expected_error",
    [
        (
            "page=abc",
            "page must be an integer"
        ),
        (
            "per_page=many",
            "per_page must be an integer"
        )
    ]
)
def test_transactions_reject_non_integer_pagination(
    client,
    query_string,
    expected_error
):
    response = client.get(
        f"/api/transactions?{query_string}"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == expected_error

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

def test_loans_endpoint_returns_all_loans(client):
    response = client.get(
        "/api/loans?branch=Florence"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["branch"] == "Florence"
    assert data["data_source"] == (
        "development_fixture"
    )
    assert data["status_filter"] is None
    assert data["total_loans"] == 4
    assert len(data["loans"]) == 4

def test_loans_can_be_filtered_by_status(client):
    response = client.get(
        "/api/loans"
        "?branch=Florence"
        "&status=open"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["status_filter"] == "OPEN"
    assert data["total_loans"] == 2

    for loan in data["loans"]:
        assert loan["status"] == "OPEN"

def test_loans_reject_invalid_status(client):
    response = client.get(
        "/api/loans"
        "?branch=Florence"
        "&status=pending"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "status must be OPEN, OVERDUE, or REPAID"
    )

def test_loans_require_branch(client):
    response = client.get("/api/loans")

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "missing required parameters"
    )
    assert data["missing"] == ["branch"]

def test_expenses_endpoint_returns_breakdown(client):
    response = client.get(
        "/api/expenses"
        "?branch=Florence"
        "&start=1420-01-01"
        "&end=1420-12-31"
    )

    data = response.get_json()
    breakdown = data["expense_breakdown"]

    assert response.status_code == 200
    assert data["branch"] == "Florence"
    assert data["data_source"] == (
        "development_fixture"
    )
    assert breakdown["total_expenses"] == "50000.00"
    assert len(breakdown["categories"]) == 4
    assert len(breakdown["top_counterparties"]) == 4

def test_expenses_require_branch_and_dates(client):
    response = client.get(
        "/api/expenses?branch=Florence"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "missing required parameters"
    )
    assert data["missing"] == ["start", "end"]

def test_expense_start_date_cannot_be_after_end_date(
    client
):
    response = client.get(
        "/api/expenses"
        "?branch=Florence"
        "&start=1421-01-01"
        "&end=1420-01-01"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "start date cannot be after end date"
    )

def test_alerts_endpoint_returns_sorted_alerts(client):
    response = client.get("/api/alerts")

    data = response.get_json()

    assert response.status_code == 200
    assert data["data_source"] == (
        "development_fixture"
    )
    assert data["total_alerts"] == 4
    assert len(data["alerts"]) == 4

    assert data["alerts"][0]["severity"] == "HIGH"
    assert data["alerts"][-1]["severity"] == "LOW"

def test_alerts_can_be_filtered(client):
    response = client.get(
        "/api/alerts"
        "?branch=Florence"
        "&severity=high"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["total_alerts"] == 1
    assert data["alerts"][0]["alert_id"] == (
        "ALT-0001"
    )
    assert data["alerts"][0]["branch"] == "Florence"
    assert data["alerts"][0]["severity"] == "HIGH"

def test_alerts_can_be_filtered_by_date(client):
    response = client.get(
        "/api/alerts"
        "?start=1420-05-01"
        "&end=1420-08-01"
    )

    data = response.get_json()

    alert_ids = [
        alert["alert_id"]
        for alert in data["alerts"]
    ]

    assert response.status_code == 200
    assert data["total_alerts"] == 2
    assert set(alert_ids) == {
        "ALT-0002",
        "ALT-0003"
    }

def test_alerts_reject_invalid_severity(client):
    response = client.get(
        "/api/alerts?severity=critical"
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "severity must be LOW, MEDIUM, or HIGH"
    )

def test_alert_can_be_acknowledged(client):
    response = client.post(
        "/api/alerts/ALT-0001/acknowledge",
        json={
            "user_id": "matthew",
            "note": "Reviewed the vendor transactions."
        }
    )

    data = response.get_json()
    alert = data["alert"]

    assert response.status_code == 200
    assert data["message"] == (
        "alert acknowledged successfully"
    )
    assert alert["status"] == "ACKNOWLEDGED"
    assert alert["acknowledged_by"] == "matthew"
    assert alert["acknowledgement_note"] == (
        "Reviewed the vendor transactions."
    )
    assert alert["acknowledged_at"] is not None

    repeated_response = client.post(
        "/api/alerts/ALT-0001/acknowledge",
        json={
            "user_id": "matthew",
            "note": "Reviewed again."
        }
    )

    repeated_data = repeated_response.get_json()

    assert repeated_response.status_code == 409
    assert repeated_data["error"] == (
        "alert has already been acknowledged"
    )

def test_acknowledge_returns_404_for_missing_alert(
    client
):
    response = client.post(
        "/api/alerts/ALT-9999/acknowledge",
        json={
            "user_id": "matthew",
            "note": "Review attempted."
        }
    )

    data = response.get_json()

    assert response.status_code == 404
    assert data["error"] == "alert not found"
    assert data["alert_id"] == "ALT-9999"

def test_acknowledge_requires_user_and_note(client):
    response = client.post(
        "/api/alerts/ALT-0002/acknowledge",
        json={
            "user_id": "matthew"
        }
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "missing required fields"
    )
    assert data["missing"] == ["note"]

def test_serving_output_writer_creates_files(
    tmp_path
):
    output_paths = generate_serving_outputs(
        branch="Florence",
        start="1420-01-01",
        end="1420-12-31",
        output_directory=tmp_path
    )

    assert set(output_paths.keys()) == {
        "metrics",
        "time_series",
        "alerts",
        "expenses",
        "loans"
    }

    for file_path in output_paths.values():
        assert file_path.exists()
        assert file_path.stat().st_size > 0

    with open(
        output_paths["metrics"],
        "r",
        encoding="utf-8"
    ) as metrics_file:
        metrics_data = json.load(metrics_file)

    assert metrics_data["branch"] == "Florence"
    assert "kpis" in metrics_data

    with open(
        output_paths["expenses"],
        "r",
        encoding="utf-8"
    ) as expenses_file:
        expense_rows = list(
            csv.DictReader(expenses_file)
        )

    assert len(expense_rows) > 0
    assert "category" in expense_rows[0]
    assert "counterparty" in expense_rows[0]

    with open(
        output_paths["loans"],
        "r",
        encoding="utf-8"
    ) as loans_file:
        loan_rows = list(
            csv.DictReader(loans_file)
        )

    assert len(loan_rows) == 4
    assert "loan_id" in loan_rows[0]
    assert "outstanding_balance" in loan_rows[0]

@pytest.mark.parametrize(
    "url",
    [
        (
            "/api/transactions"
            "?branch=Florence"
            "&page=1"
            "&per_page=25"
            "&username=director"
        ),
        (
            "/api/kpis"
            "?branch=Florence"
            "&start=1420-01-01"
            "&end=1420-12-31"
        ),
        (
            "/api/cashflow"
            "?branch=Florence"
            "&start=1420-01-01"
            "&end=1420-12-31"
            "&granularity=monthly"
        ),
        (
            "/api/loans"
            "?branch=Florence"
        ),
        (
            "/api/expenses"
            "?branch=Florence"
            "&start=1420-01-01"
            "&end=1420-12-31"
        ),
        (
            "/api/alerts"
            "?branch=Florence"
        )
    ]
)
def test_get_endpoints_respond_under_500ms(
    client,
    url
):
    warmup_response = client.get(url)

    assert warmup_response.status_code == 200

    start_time = time.perf_counter()

    response = client.get(url)

    elapsed_time = time.perf_counter() - start_time

    assert response.status_code == 200

    assert elapsed_time < 0.5, (
        f"{url} took {elapsed_time:.3f} seconds"
    )

def test_login_returns_managing_director(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "director",
            "password": "medici-director",
        },
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["authenticated"] is True
    assert data["user"]["username"] == "director"
    assert data["user"]["role"] == "MANAGING_DIRECTOR"
    assert data["user"]["branch"] is None
    assert "password" not in data["user"]


def test_login_returns_branch_user(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "florence_manager",
            "password": "medici-florence",
        },
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["authenticated"] is True
    assert data["user"]["username"] == "florence_manager"
    assert data["user"]["role"] == "BRANCH_USER"
    assert data["user"]["branch"] == "Florence"
    assert "password" not in data["user"]



def test_login_requires_username_and_password(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "director",
        },
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "username and password are required"
    )

def test_branch_user_can_access_own_branch(client):
    response = client.get(
        "/api/transactions"
        "?branch=Florence"
        "&page=1"
        "&per_page=25"
        "&username=florence_manager"
    )

    assert response.status_code == 200


def test_branch_user_cannot_access_other_branch(client):
    response = client.get(
        "/api/transactions"
        "?branch=Rome"
        "&page=1"
        "&per_page=25"
        "&username=florence_manager"
    )

    assert response.status_code == 403


def test_managing_director_can_access_any_branch(client):
    response = client.get(
        "/api/transactions"
        "?branch=Rome"
        "&page=1"
        "&per_page=25"
        "&username=director"
    )

    assert response.status_code == 200


def test_unknown_user_is_rejected(client):
    response = client.get(
        "/api/transactions"
        "?branch=Florence"
        "&page=1"
        "&per_page=25"
        "&username=unknown_user"
    )

    assert response.status_code == 401
def test_unauthenticated_user_cannot_access_branch(client):
    response = client.get(
        "/api/transactions"
        "?branch=Florence"
        "&page=1"
        "&per_page=25"
    )

    data = response.get_json()

    assert response.status_code == 401
    assert data["error"] == "authentication required"


@pytest.mark.parametrize(
    "branch",
    ["Florence", "Rome"],
)
def test_managing_director_can_access_each_branch(
    client,
    branch
):
    response = client.get(
        "/api/transactions"
        f"?branch={branch}"
        "&page=1"
        "&per_page=25"
        "&username=director"
    )

    assert response.status_code == 200
