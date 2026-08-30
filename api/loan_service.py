import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

LOAN_FIXTURE_FILE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "loan_portfolio.json"
)


@lru_cache(maxsize=1)
def load_loan_fixture():
    with open(
        LOAN_FIXTURE_FILE,
        "r",
        encoding="utf-8"
    ) as fixture_file:
        return json.load(fixture_file)


def get_loan_portfolio(
    branch,
    status=None,
    start=None,
    end=None,
):
    loans = deepcopy(load_loan_fixture())

    if start:
        loans = [
            loan
            for loan in loans
            if loan["issued_date"] >= start
        ]

    if end:
        loans = [
            loan
            for loan in loans
            if loan["issued_date"] <= end
        ]

    if status:
        loans = [
            loan
            for loan in loans
            if loan["status"].casefold()
            == status.casefold()
        ]

    return {
        "branch": branch,
        "status_filter": status,
        "data_source": "development_fixture",
        "total_loans": len(loans),
        "loans": loans
    }