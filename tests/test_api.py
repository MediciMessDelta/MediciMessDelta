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