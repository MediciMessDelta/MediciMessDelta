import json

from copy import deepcopy
from functools import lru_cache
from pathlib import Path


KPI_FIXTURE_FILE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "kpi_summary.json"
)


@lru_cache(maxsize=1)
def load_kpi_fixture():
    with open(
        KPI_FIXTURE_FILE,
        "r",
        encoding="utf-8"
    ) as fixture_file:
        return json.load(fixture_file)


def get_kpi_summary(branch, start, end):
    fixture = deepcopy(load_kpi_fixture())

    return {
        "branch": branch,
        "period": {
            "start": start,
            "end": end
        },
        "data_source": "development_fixture",
        "kpis": fixture
    }