import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

EXPENSE_FIXTURE_FILE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "expense_breakdown.json"
)


@lru_cache(maxsize=1)
def load_expense_fixture():
    with open(
        EXPENSE_FIXTURE_FILE,
        "r",
        encoding="utf-8"
    ) as fixture_file:
        return json.load(fixture_file)


def get_expense_breakdown(branch, start, end):
    expense_data = deepcopy(
        load_expense_fixture()
    )

    return {
        "branch": branch,
        "period": {
            "start": start,
            "end": end
        },
        "data_source": "development_fixture",
        "expense_breakdown": expense_data
    }