import json

from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path


ALERT_FIXTURE_FILE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "alerts.json"
)


@lru_cache(maxsize=1)
def load_alert_fixture():
    with open(
        ALERT_FIXTURE_FILE,
        "r",
        encoding="utf-8"
    ) as fixture_file:
        return json.load(fixture_file)


def get_alerts(
    branch=None,
    start=None,
    end=None,
    severity=None
):
    alerts = deepcopy(load_alert_fixture())

    if branch:
        alerts = [
            alert
            for alert in alerts
            if alert["branch"].casefold()
            == branch.casefold()
        ]

    if start:
        alerts = [
            alert
            for alert in alerts
            if alert["date"] >= start
        ]

    if end:
        alerts = [
            alert
            for alert in alerts
            if alert["date"] <= end
        ]

    if severity:
        alerts = [
            alert
            for alert in alerts
            if alert["severity"] == severity
        ]

    severity_rank = {
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1
    }

    alerts.sort(
        key=lambda alert: (
            severity_rank[alert["severity"]],
            alert["date"]
        ),
        reverse=True
    )

    return {
        "data_source": "development_fixture",
        "filters": {
            "branch": branch,
            "start": start,
            "end": end,
            "severity": severity
        },
        "total_alerts": len(alerts),
        "alerts": alerts
    }


def acknowledge_alert(alert_id, user_id, note):
    alerts = load_alert_fixture()

    for alert in alerts:
        if alert["alert_id"] != alert_id:
            continue

        if alert["status"] == "ACKNOWLEDGED":
            return {
                "outcome": "already_acknowledged",
                "alert": deepcopy(alert)
            }

        alert["status"] = "ACKNOWLEDGED"
        alert["acknowledged_by"] = user_id
        alert["acknowledgement_note"] = note
        alert["acknowledged_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        return {
            "outcome": "acknowledged",
            "alert": deepcopy(alert)
        }

    return {
        "outcome": "not_found",
        "alert": None
    }


def reset_alert_fixture():
    load_alert_fixture.cache_clear()