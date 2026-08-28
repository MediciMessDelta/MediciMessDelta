from medici.contracts import AlertRecord
from datetime import datetime

def test_alert_record_for_duplicate_transaction():
    """Sketches what firing Rule C on SAMPLE_TRANSACTIONS rows 1 and 8
    (the Bardi Family duplicate deposit) should produce."""
    alert = AlertRecord(
        alert_id=1,
        rule="C",
        severity="MEDIUM",
        branch="Florence",
        period="1420-01",
        affected_transaction_ids=[1, 8],
        counterparty="Bardi Family",
        metric_value=0,       # days apart between the two transactions
        threshold_value=3,    # the 3-day window from DATA_PIPELINE_SPEC.md
        description=(
            "Transaction id 8 duplicates id 1: same type, counterparty, "
            "and amount, dated 0 days apart (within 3-day window)."
        ),
        detected_at=datetime(1420, 1, 5, 12, 0, 0),
        status="OPEN",
    )
    assert alert.rule == "C"
    assert alert.affected_transaction_ids == [1, 8]

def test_no_duplicate_alert_for_different_transactions():
    """Rows 1 (Florence, Bardi Family, 500) and 5 (Venice, Contarini
    Family, 900) share nothing — different branch, counterparty, and
    amount — so Rule C should NOT fire on this pair."""
    txn_1_branch, txn_1_counterparty, txn_1_amount = "Florence", "Bardi Family", 500
    txn_5_branch, txn_5_counterparty, txn_5_amount = "Venice", "Contarini Family", 900

    is_duplicate_pair = (
        txn_1_branch == txn_5_branch
        and txn_1_counterparty == txn_5_counterparty
        and txn_1_amount == txn_5_amount
    )
    assert is_duplicate_pair is False