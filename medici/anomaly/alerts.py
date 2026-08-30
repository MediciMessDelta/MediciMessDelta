"""
Phase 4: Alert Records — built by Sloane.

Turns the plain "hit" dicts that rules.py's rule functions produce into
real AlertRecord objects (medici/contracts.py), which is the shape
Matt's API and dashboards actually consume.
"""

from datetime import datetime

from medici.contracts import AlertRecord


def assign_severity(metric_value, threshold_value):
    """Maps how far a metric exceeded its threshold onto LOW/MEDIUM/HIGH.

    The spec doesn't define an exact metric-to-severity mapping, so this
    is a judgment call, not something written down anywhere: how far
    over the threshold something is, as a ratio, determines severity -
    3x the threshold or more is HIGH, 1.5x-3x is MEDIUM, anything closer
    is LOW. Worth confirming with the team (Matt's dashboards will
    likely color-code by this), but it gives every alert a reasonable
    severity instead of leaving the field blank or hardcoded to one
    value.
    """
    if threshold_value == 0:
        return "HIGH" if metric_value > 0 else "LOW"

    ratio = metric_value / threshold_value

    if ratio >= 3:
        return "HIGH"
    elif ratio >= 1.5:
        return "MEDIUM"
    else:
        return "LOW"


def build_alert_records(hits, starting_alert_id=1, detected_at=None):
    """Converts a list of rule-hit dicts (from rules.py) into a list of
    AlertRecord objects, numbered sequentially starting at
    starting_alert_id, all sharing one detected_at timestamp (the
    moment this pipeline run happened) and status 'OPEN'."""
    detected_at = detected_at if detected_at is not None else datetime.now()

    alert_records = []
    for offset, hit in enumerate(hits):
        alert_records.append(AlertRecord(
            alert_id=starting_alert_id + offset,
            rule=hit["rule"],
            severity=assign_severity(hit["metric_value"], hit["threshold_value"]),
            branch=hit["branch"],
            period=hit["period"],
            affected_transaction_ids=hit["affected_transaction_ids"],
            counterparty=hit.get("counterparty"),
            metric_value=hit["metric_value"],
            threshold_value=hit["threshold_value"],
            description=hit["description"],
            detected_at=detected_at,
            status="OPEN",
        ))

    return alert_records
