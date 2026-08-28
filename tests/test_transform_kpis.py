"""
Tests for Phase 3: medici/transform/kpis.py (and, indirectly, clean.py) —
built by Sloane.

These mostly check compute_kpis() and its building blocks against
tests/fixtures.py's hand-calculated EXPECTED_FLORENCE_1420_01, which
was worked out by hand during pre-development (Section 3.2 of the
1-Week Plan) before any of this code existed. A couple of tests also
cross-check against the real medici_transactions.csv, independently
re-summing a value in plain Python rather than reusing kpis.py's own
code, so a bug in compute_deposits_withdrawals couldn't accidentally
hide itself from its own test.
"""

from decimal import Decimal

import pytest

from medici.ingestion.dedup import flag_duplicates
from medici.ingestion.loaders import load_csv
from medici.ingestion.validation import validate_all_rows
from medici.transform.clean import to_cleaned_transactions
from medici.transform.kpis import bucket_by_period, compute_kpis, period_bounds
from tests.fixtures import EXPECTED_FLORENCE_1420_01, SAMPLE_TRANSACTIONS


def test_bucket_by_period_separates_branch_and_period():
    """Florence and Venice's January 1420 rows should end up in two
    separate buckets, keyed by (branch, period) — and the duplicate row
    (id 8) should still be included in its bucket, since bucketing
    itself must not drop anything (only compute_kpis excludes it later)."""
    buckets = bucket_by_period(SAMPLE_TRANSACTIONS)

    assert set(buckets.keys()) == {("Florence", "1420-01"), ("Venice", "1420-01")}
    florence_ids = sorted(t.id for t in buckets[("Florence", "1420-01")])
    assert florence_ids == [1, 2, 3, 4, 8]


def test_period_bounds_for_a_31_day_month():
    period_start, period_end = period_bounds("1420-01")
    assert period_start.isoformat() == "1420-01-01"
    assert period_end.isoformat() == "1420-01-31"


def test_compute_kpis_matches_hand_calculated_florence_fixture():
    """The big one: every field compute_kpis produces for Florence,
    January 1420 should match the team's pre-development hand
    calculation exactly — this is the fixture the whole KPI module was
    built to satisfy."""
    result = compute_kpis("Florence", "1420-01", SAMPLE_TRANSACTIONS)
    result_dict = result.model_dump()

    for field_name, expected_value in EXPECTED_FLORENCE_1420_01.items():
        actual_value = result_dict[field_name]
        assert actual_value == expected_value, (
            f"{field_name}: expected {expected_value!r}, got {actual_value!r}"
        )


def test_compute_kpis_excludes_duplicate_from_totals_but_still_counts_it():
    """Transaction id 8 is a flagged duplicate of id 1 (both a $500
    Florence deposit). total_deposits should only count id 1 ($500, not
    $1000) — but excluded_duplicate_count should still be 1, so the
    exclusion is visible rather than the row just vanishing."""
    result = compute_kpis("Florence", "1420-01", SAMPLE_TRANSACTIONS)

    assert result.total_deposits == Decimal("500")
    assert result.deposit_count == 1
    assert result.excluded_duplicate_count == 1


def test_compute_kpis_raises_for_a_branch_period_with_no_data():
    """Asking for a branch/period combination that doesn't exist in the
    dataset should fail loudly (ValueError), not quietly hand back a
    fake all-zero KPIResult that looks like a real "no activity" month."""
    with pytest.raises(ValueError):
        compute_kpis("Constance", "1420-01", SAMPLE_TRANSACTIONS)


def test_cash_balance_carries_over_between_real_consecutive_months():
    """Cross-check against real data: Florence's closing_cash_balance
    for month 2 should equal month 1's closing balance plus month 2's
    own net_cash_movement. This is the part unit tests on fixtures alone
    can't catch, since the sample fixture only has one period — a bug
    that resets the running balance to 0 every period would still pass
    every other test here."""
    rows = load_csv("medici_transactions.csv")
    cleaned_rows, _rejected = validate_all_rows(rows)
    cleaned_rows = flag_duplicates(cleaned_rows)
    cleaned_transactions = to_cleaned_transactions(cleaned_rows)

    periods = sorted({
        f"{t.year}-{t.month:02d}"
        for t in cleaned_transactions
        if t.branch == "Florence"
    })
    first_period, second_period = periods[0], periods[1]

    month_1 = compute_kpis("Florence", first_period, cleaned_transactions)
    month_2 = compute_kpis("Florence", second_period, cleaned_transactions)

    assert month_2.closing_cash_balance == (
        month_1.closing_cash_balance + month_2.net_cash_movement
    )


def test_total_deposits_matches_independent_hand_sum_on_real_data():
    """Cross-check compute_kpis's total_deposits against a plain,
    from-scratch sum over the real CSV — written independently here in
    the test (not by calling anything in kpis.py) — so a bug in
    compute_deposits_withdrawals can't hide by matching its own math."""
    rows = load_csv("medici_transactions.csv")
    cleaned_rows, _rejected = validate_all_rows(rows)
    cleaned_rows = flag_duplicates(cleaned_rows)
    cleaned_transactions = to_cleaned_transactions(cleaned_rows)

    branch, period = "Florence", "1390-01"

    hand_summed_total = Decimal("0")
    for row in cleaned_rows:
        if (
            row["branch"] == branch
            and not row["is_duplicate"]
            and row["type"] == "deposit"
            and f"{row['year']}-{row['month']:02d}" == period
        ):
            hand_summed_total += row["debit_amount"]

    result = compute_kpis(branch, period, cleaned_transactions)
    assert result.total_deposits == hand_summed_total
