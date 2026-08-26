import json

from copy import deepcopy
from functools import lru_cache
from pathlib import Path


CASHFLOW_FIXTURE_FILE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "cashflow.json"
)


@lru_cache(maxsize=1)
def load_cashflow_fixture():
    with open(
        CASHFLOW_FIXTURE_FILE,
        "r",
        encoding="utf-8"
    ) as fixture_file:
        return json.load(fixture_file)


def get_cashflow(
    branch,
    start,
    end,
    granularity
):
    fixture = load_cashflow_fixture()

    time_series = deepcopy(
        fixture[granularity]
    )

    return {
        "branch": branch,
        "period": {
            "start": start,
            "end": end
        },
        "granularity": granularity,
        "data_source": "development_fixture",
        "time_series": time_series
    }