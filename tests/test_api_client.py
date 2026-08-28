from unittest.mock import Mock, patch

import pytest
import requests

from dashboard.api_client import (
    APIClientError,
    get_transactions,
    login,
    make_get_request,
)


@patch("dashboard.api_client.requests.get")
def test_make_get_request_sends_username_header(mock_get):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"status": "healthy"}
    mock_get.return_value = response

    result = make_get_request(
        "/api/health",
        username="director",
    )

    assert result == {"status": "healthy"}

    mock_get.assert_called_once_with(
        "http://127.0.0.1:5001/api/health",
        params=None,
        headers={"X-Username": "director"},
        timeout=10,
    )


@patch("dashboard.api_client.requests.get")
def test_make_get_request_without_username_sends_no_header(mock_get):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"status": "healthy"}
    mock_get.return_value = response

    result = make_get_request("/api/health")

    assert result == {"status": "healthy"}

    mock_get.assert_called_once_with(
        "http://127.0.0.1:5001/api/health",
        params=None,
        headers={},
        timeout=10,
    )






@patch("dashboard.api_client.requests.get")
def test_make_get_request_raises_api_error_for_http_error(mock_get):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError(
        "401 Unauthorized"
    )
    mock_get.return_value = response

    with pytest.raises(APIClientError):
        make_get_request(
            "/api/transactions",
            username="director",
        )

@patch("dashboard.api_client.requests.post")
def test_login_returns_api_response(mock_post):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "authenticated": True,
        "user": {
            "username": "director",
            "role": "MANAGING_DIRECTOR",
        },
    }
    mock_post.return_value = response

    result = login("director", "medici-director")

    assert result["authenticated"] is True
    assert result["user"]["username"] == "director"

    mock_post.assert_called_once_with(
        "http://127.0.0.1:5001/api/auth/login",
        json={
            "username": "director",
            "password": "medici-director",
        },
        timeout=10,
    )


@patch("dashboard.api_client.requests.post")
def test_login_returns_none_for_invalid_credentials(mock_post):
    response = Mock()
    response.status_code = 401
    mock_post.return_value = response

    result = login("director", "wrong-password")

    assert result is None


@patch("dashboard.api_client.make_get_request")
def test_get_transactions_builds_expected_params(mock_request):
    mock_request.return_value = {
        "transactions": [],
        "page": 1,
    }

    result = get_transactions(
        branch="Florence",
        start="1420-01-01",
        end="1420-12-31",
        page=2,
        per_page=25,
        transaction_type="deposit",
        username="director",
    )

    assert result == {
        "transactions": [],
        "page": 1,
    }

    mock_request.assert_called_once_with(
        "/api/transactions",
        params={
            "start": "1420-01-01",
            "end": "1420-12-31",
            "page": 2,
            "per_page": 25,
            "branch": "Florence",
            "type": "deposit",
        },
        username="director",
    )