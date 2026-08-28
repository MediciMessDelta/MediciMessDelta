from datetime import date

from medici.contracts import CleanedTransaction

# Rows here start at id=100 so they never collide with SAMPLE_TRANSACTIONS (ids 1-9)
# in tests/fixtures.py.

def _txn(id, day, branch, type_, counterparty, debit_account,
         debit_amount, credit_account="cash", **kwargs):
    """Small helper so every generator below doesn't repeat year/month/
    quarter/fiscal_year/currency by hand — those are always the same
    for this exercise (January 1420)."""
    return CleanedTransaction(
        id=id, date=date(1420, 1, day), branch=branch, type=type_,
        counterparty=counterparty, description="generated fixture",
        debit_account=debit_account, debit_amount=debit_amount,
        credit_account=credit_account, credit_amount=debit_amount,
        currency="florin", year=1420, month=1, quarter="Q1",
        fiscal_year=1420, debit_account_type="EXPENSE",
        credit_account_type="ASSET", is_duplicate=False,
        **kwargs,
    )


# ---------------------------------------------------------------------
# Rule A — Benford's Law deviation
# Threshold: flag if MAD > 0.015 or chi-squared p < 0.05, per (branch, type)
# ---------------------------------------------------------------------

def benford_trigger_transactions():
    """Every amount starts with digit 9 — nothing like this occurs
    naturally, so it badly fails Benford's Law (real MAD would be huge)."""
    return [
        _txn(100 + i, 5, "Florence", "operating_expense", "Vendor A",
             "supplies_expense", 900 + i)
        for i in range(30)
    ]

def benford_non_trigger_transactions():
    """Leading digits roughly follow Benford's expected proportions
    (30% start with 1, 18% with 2, etc.) — should NOT trigger."""
    leading_digit_counts = {1: 9, 2: 5, 3: 4, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
    txns, i = [], 0
    for digit, count in leading_digit_counts.items():
        for _ in range(count):
            txns.append(_txn(200 + i, 5, "Florence", "operating_expense",
                              "Vendor B", "supplies_expense", digit * 100 + i))
            i += 1
    return txns


# ---------------------------------------------------------------------
# Rule B — Vendor concentration (operating_expense only)
# Threshold: flag if one counterparty > 5% of a (branch, period,
# debit_account) category's total spend
# ---------------------------------------------------------------------

def vendor_concentration_trigger_transactions():
    """20 transactions of 100 (=2000 total) in wages_expense; one
    counterparty gets 3 of them = 300/2000 = 15% > 5%."""
    txns = [_txn(300, 5, "Florence", "operating_expense", "Dominant Vendor",
                 "wages_expense", 100)]
    txns += [_txn(300 + i, 5, "Florence", "operating_expense", "Dominant Vendor",
                   "wages_expense", 100) for i in range(1, 3)]
    txns += [_txn(303 + i, 6, "Florence", "operating_expense", f"Vendor {i}",
                   "wages_expense", 100) for i in range(17)]
    return txns

def vendor_concentration_non_trigger_transactions():
    """25 transactions of 100 (=2500 total), 25 different counterparties
    — each is 100/2500 = 4% < 5%."""
    return [_txn(400 + i, 5, "Florence", "operating_expense", f"Vendor {i}",
                 "wages_expense", 100) for i in range(25)]


# ---------------------------------------------------------------------
# Rule D — Round-number clustering (operating_expense only)
# Threshold: flag if > 30% of amounts in a (branch, debit_account)
# group are exact multiples of 50
# ---------------------------------------------------------------------

def round_number_trigger_transactions():
    """10 transactions in the same (branch, debit_account) group; 5 of
    them (50%) are exact multiples of 50 — above the 30% threshold."""
    round_amounts = [50, 100, 150, 200, 250]
    irregular_amounts = [37, 68, 91, 114, 129]
    txns = [_txn(500 + i, 5, "Florence", "operating_expense", f"Vendor {i}",
                 "supplies_expense", amt) for i, amt in enumerate(round_amounts)]
    txns += [_txn(505 + i, 5, "Florence", "operating_expense", f"Vendor {i+5}",
                   "supplies_expense", amt) for i, amt in enumerate(irregular_amounts)]
    return txns

def round_number_non_trigger_transactions():
    """10 transactions, only 1 (10%) is a round multiple of 50 —
    below the 30% threshold."""
    amounts = [37, 68, 91, 114, 129, 143, 157, 168, 179, 50]
    return [_txn(600 + i, 5, "Florence", "operating_expense", f"Vendor {i}",
                 "supplies_expense", amt) for i, amt in enumerate(amounts)]


# ---------------------------------------------------------------------
# Rule E — Transaction frequency outlier (by counterparty)
# Threshold: monthly count per (branch, counterparty, type) exceeds
# mean + 3 standard deviations across all months
# ---------------------------------------------------------------------

def frequency_outlier_trigger_transactions():
    """'Baseline Vendor' gets ~2 transactions/month for 4 baseline
    months, then 15 in the 5th month — a sharp, obvious spike."""
    txns = []
    txn_id = 700
    for month in range(1, 5):
        for _ in range(2):
            txns.append(_txn(txn_id, 5, "Florence", "operating_expense",
                              "Baseline Vendor", "supplies_expense", 80))
            txn_id += 1
    for _ in range(15):
        txns.append(_txn(txn_id, 20, "Florence", "operating_expense",
                          "Baseline Vendor", "supplies_expense", 80))
        txn_id += 1
    return txns

def frequency_outlier_non_trigger_transactions():
    """Same counterparty, but a steady ~2/month across all 5 months —
    no spike, nothing unusual."""
    txns = []
    txn_id = 800
    for month in range(1, 6):
        for _ in range(2):
            txns.append(_txn(txn_id, 5, "Florence", "operating_expense",
                              "Steady Vendor", "supplies_expense", 80))
            txn_id += 1
    return txns


# ---------------------------------------------------------------------
# Rule F — Amount below reporting threshold ("smurfing")
# Threshold: individual amounts under ~1,000 florins, but the same
# (branch, counterparty) totals > 10,000 within a 30-day window
# ---------------------------------------------------------------------

def below_threshold_trigger_transactions():
    """12 payments of 900 (each individually under 1,000) within a
    30-day window = 10,800 total > 10,000."""
    return [
        _txn(900 + i, 1 + i * 2, "Florence", "operating_expense",
             "Structuring Vendor", "misc_expense", 900)
        for i in range(12)
    ]

def below_threshold_non_trigger_transactions():
    """5 payments of 900 = 4,500 total — individually under the
    threshold, but the 30-day aggregate never exceeds 10,000."""
    return [
        _txn(1000 + i, 1 + i * 2, "Florence", "operating_expense",
             "Normal Vendor", "misc_expense", 900)
        for i in range(5)
    ]


# ---------------------------------------------------------------------
# Rule G — New counterparty, immediate high volume
# Threshold: first-90-day volume > 3x the average 90-day volume of
# established counterparties in the same (branch, type)
# ---------------------------------------------------------------------

def new_counterparty_trigger_transactions():
    """3 established counterparties averaging ~1,000 in loan_issuance
    volume, plus one brand-new counterparty immediately doing 5,000
    (> 3x the ~1,000 average)."""
    txns = [
        _txn(1100 + i, 5, "Florence", "loan_issuance", f"Established {i}",
             "loans_receivable", 1000) for i in range(3)
    ]
    txns.append(_txn(1103, 6, "Florence", "loan_issuance", "New Vendor",
                      "loans_receivable", 5000))
    return txns

def new_counterparty_non_trigger_transactions():
    """Same 3 established counterparties, plus a new one whose first
    volume (1,200) is close to the ~1,000 average — not 3x it."""
    txns = [
        _txn(1200 + i, 5, "Florence", "loan_issuance", f"Established {i}",
             "loans_receivable", 1000) for i in range(3)
    ]
    txns.append(_txn(1203, 6, "Florence", "loan_issuance", "New Vendor",
                      "loans_receivable", 1200))
    return txns