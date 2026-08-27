import os

import requests


DEFAULT_API_URL = "http://127.0.0.1:5001"

API_BASE_URL = os.getenv(
    "MEDICIMESS_API_URL",
    DEFAULT_API_URL
)


class APIClientError(Exception):
    pass


def make_get_request(endpoint, params=None):
    url = f"{API_BASE_URL}{endpoint}"

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise APIClientError(
            f"Unable to retrieve data from {url}"
        ) from error

    try:
        return response.json()

    except ValueError as error:
        raise APIClientError(
            f"The API returned invalid JSON from {url}"
        ) from error


def check_api_health():
    return make_get_request("/api/health")


def get_transactions(
    branch,
    start,
    end,
    page=1,
    per_page=100,
    transaction_type=None
):
    params = {
        "start": str(start),
        "end": str(end),
        "page": page,
        "per_page": per_page
    }

    if branch != "All Branches":
        params["branch"] = branch

    if transaction_type:
        params["type"] = transaction_type

    return make_get_request(
        "/api/transactions",
        params=params
    )

def get_kpis(branch, start, end):
    params = {
        "branch": branch,
        "start": start,
        "end": end
    }

    return make_get_request(
        "/api/kpis",
        params=params
    )


def get_cashflow(
    branch,
    start,
    end,
    granularity="monthly"
):
    params = {
        "branch": branch,
        "start": start,
        "end": end,
        "granularity": granularity
    }

    return make_get_request(
        "/api/cashflow",
        params=params
    )

def get_loans(branch, status=None):
    params = {
        "branch": branch
    }

    if status:
        params["status"] = status

    return make_get_request(
        "/api/loans",
        params=params
    )


def get_expenses(branch, start, end):
    params = {
        "branch": branch,
        "start": start,
        "end": end
    }

    return make_get_request(
        "/api/expenses",
        params=params
    )


def get_alerts(
    branch,
    start=None,
    end=None,
    severity=None,
    status=None
):
    params = {
        "branch": branch
    }

    if start:
        params["start"] = start

    if end:
        params["end"] = end

    if severity:
        params["severity"] = severity

    if status:
        params["status"] = status

    return make_get_request(
        "/api/alerts",
        params=params
    )