"""
Transform: KPI Computations (Phase 3, steps 4-10) — built by Sloane.

Takes the CleanedTransaction records that clean.py produces and computes
every KPI from DATA_PIPELINE_SPEC.md Section 5.2, grouped by (branch,
period). The result of compute_kpis() is a single KPIResult (see
medici/contracts.py) per (branch, period) pair.

Ground rules from the data contract sheet, worth remembering while
filling these in:
    - Rows with is_duplicate=True are EXCLUDED from every total, but
      counted in excluded_duplicate_count (never silently dropped).
    - Keep full Decimal precision through every calculation; only round
      to 2 places at the very end, when a result is displayed/serialized.
    - net_income_margin must return None (not raise/crash) when
      total_revenue == 0 — divide-by-zero is expected, not an error.

compute_cash_position through compute_kpis are still stubs (steps 5-10).
Expected outputs to test against: tests/fixtures.py
(EXPECTED_FLORENCE_1420_01) already has hand-calculated values for one
branch/period, from the team's pre-development sign-off.
"""

import calendar
from datetime import date
from decimal import Decimal

from medici.contracts import KPIResult


def period_key(transaction):
    """Build the period string for one CleanedTransaction, e.g. year=1420,
    month=1 -> '1420-01'. Matches the KPIResult.period format the data
    contract sheet specifies (zero-padded 2-digit month)."""
    return "{}-{:02d}".format(transaction.year, transaction.month)


def bucket_by_period(cleaned_transactions):
    """Group a list of CleanedTransactions into {(branch, period): [rows]}
    buckets, e.g. all of Florence's January 1420 rows together under
    ('Florence', '1420-01'). Every KPI function below runs on one bucket
    at a time.

    Note: this groups ALL rows, including ones with is_duplicate=True.
    Excluding duplicates from the actual KPI totals happens later, in
    compute_kpis (step 10) — bucketing itself shouldn't hide any rows,
    since excluded_duplicate_count still needs to count them per bucket.
    """
    buckets = {}
    for transaction in cleaned_transactions:
        key = (transaction.branch, period_key(transaction))
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(transaction)
    return buckets


def compute_cash_position(transactions, opening_cash_balance=Decimal("0")):
    """total_cash_inflows, total_cash_outflows, net_cash_movement,
    closing_cash_balance for one (branch, period) bucket.

    Formulas (DATA_PIPELINE_SPEC.md Section 5.2):
        total_cash_inflows  = sum of debit_amount  where debit_account  == 'Cash'
        total_cash_outflows = sum of credit_amount where credit_account == 'Cash'
        net_cash_movement   = total_cash_inflows - total_cash_outflows
        closing_cash_balance = cumulative net_cash_movement, start of
            dataset through end of this period.

    That last one is the tricky part: this function only sees ONE
    period's transactions, so it can't calculate a running total on its
    own. Instead it accepts opening_cash_balance - the closing balance
    carried over from the period before this one - and adds this
    period's net_cash_movement to it. compute_kpis (step 10) is
    responsible for walking through periods in date order and passing
    each one's opening balance in as the previous period's closing
    balance (0 for the very first period in the dataset).

    Note on matching 'Cash': compared case-insensitively
    (account_name.strip().lower() == 'cash') rather than an exact
    string match. Real ingested data capitalizes it ('Cash'), but the
    hand-written fixtures in tests/fixtures.py use lowercase ('cash') -
    matching case-insensitively (the same trick medici/ingestion/
    validation.py's get_account_type already uses) means this works
    against both without depending on everyone typing the account name
    identically.
    """
    total_cash_inflows = Decimal("0")
    total_cash_outflows = Decimal("0")

    for transaction in transactions:
        if transaction.debit_account.strip().lower() == "cash":
            total_cash_inflows += transaction.debit_amount
        if transaction.credit_account.strip().lower() == "cash":
            total_cash_outflows += transaction.credit_amount

    net_cash_movement = total_cash_inflows - total_cash_outflows
    closing_cash_balance = opening_cash_balance + net_cash_movement

    return {
        "total_cash_inflows": total_cash_inflows,
        "total_cash_outflows": total_cash_outflows,
        "net_cash_movement": net_cash_movement,
        "closing_cash_balance": closing_cash_balance,
    }


def compute_deposits_withdrawals(transactions):
    """total_deposits, total_withdrawals, deposit_count,
    withdrawal_count, avg_deposit_size, avg_withdrawal_size for one
    (branch, period) bucket.

    Formulas (DATA_PIPELINE_SPEC.md Section 5.2):
        total_deposits       = sum of debit_amount where type == 'deposit'
        total_withdrawals    = sum of debit_amount where type == 'withdrawal'
        deposit_count        = count of type == 'deposit' rows
        withdrawal_count     = count of type == 'withdrawal' rows
        avg_deposit_size     = total_deposits / deposit_count
        avg_withdrawal_size  = total_withdrawals / withdrawal_count

    Edge case: if there were no deposits (or no withdrawals) at all in
    this period, deposit_count/withdrawal_count is 0 and the "divide by
    the count" formula above would crash. The data contract sheet
    doesn't call this field out as nullable the way it does
    net_income_margin, so - unlike that one - this returns Decimal('0')
    for the average instead of None when the count is 0. A branch with
    zero withdrawals that month should show "$0 average", not blow up
    the whole KPI calculation.

    Note: `type` here is an exact match ('deposit', 'withdrawal') - not
    lowercased like the account-name checks in compute_cash_position -
    because transaction type is a controlled value written by the
    ingestion pipeline itself (see medici/contracts.py), not
    free-typed by a person, so there's no real-world casing drift to
    guard against.
    """
    total_deposits = Decimal("0")
    total_withdrawals = Decimal("0")
    deposit_count = 0
    withdrawal_count = 0

    for transaction in transactions:
        if transaction.type == "deposit":
            total_deposits += transaction.debit_amount
            deposit_count += 1
        elif transaction.type == "withdrawal":
            total_withdrawals += transaction.debit_amount
            withdrawal_count += 1

    if deposit_count > 0:
        avg_deposit_size = total_deposits / deposit_count
    else:
        avg_deposit_size = Decimal("0")

    if withdrawal_count > 0:
        avg_withdrawal_size = total_withdrawals / withdrawal_count
    else:
        avg_withdrawal_size = Decimal("0")

    return {
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "deposit_count": deposit_count,
        "withdrawal_count": withdrawal_count,
        "avg_deposit_size": avg_deposit_size,
        "avg_withdrawal_size": avg_withdrawal_size,
    }


def compute_loan_portfolio(transactions, opening_loan_balance=Decimal("0")):
    """loans_issued, loans_repaid, interest_earned,
    loan_portfolio_balance (cumulative), interest_yield for one
    (branch, period) bucket.

    Formulas (DATA_PIPELINE_SPEC.md Section 5.2):
        loans_issued  = sum of debit_amount where type == 'loan_issuance'
        loans_repaid  = sum of credit_amount where type == 'loan_repayment'
                        and credit_account == 'Loans Receivable'
        interest_earned = sum of credit_amount_2 where type == 'loan_repayment'
        loan_portfolio_balance = cumulative (loans_issued - loans_repaid),
                        start of dataset through end of this period
        interest_yield = interest_earned / loans_repaid, as a percentage

    Same cumulative-balance pattern as compute_cash_position (step 5):
    this function only sees one period, so it takes
    opening_loan_balance - the running balance carried over from the
    previous period - and returns opening_loan_balance plus this
    period's (loans_issued - loans_repaid). compute_kpis (step 10)
    threads periods together in date order, same as it does for cash.

    Note on matching the loan-receivable account: I checked real rows
    in medici_transactions.csv - loan_issuance always uses credit_account
    'Cash' / debit_account 'Loans Receivable', and loan_repayment always
    uses debit_account 'Cash' / credit_account 'Loans Receivable'. But
    the hand-written tests/fixtures.py spells it 'loans_receivable'
    (lowercase, underscore instead of space). Rather than an exact
    string match against 'Loans Receivable' - which would silently
    return 0 against the fixtures - this checks for the substring
    'receivable' (case-insensitive), which matches both spellings.
    Since `type` already narrows the rows to loan_repayment, this is
    safe: those rows only ever credit the receivable account.

    Edge case: interest_yield divides by loans_repaid, which can be 0
    (e.g. a period with issuances but no repayments yet). Like
    avg_deposit_size in step 6, and because the contract doesn't mark
    this field nullable, this returns 0.0 instead of raising or
    returning None.
    """
    loans_issued = Decimal("0")
    loans_repaid = Decimal("0")
    interest_earned = Decimal("0")

    for transaction in transactions:
        if transaction.type == "loan_issuance":
            loans_issued += transaction.debit_amount
        elif transaction.type == "loan_repayment":
            interest_earned += transaction.credit_amount_2
            if "receivable" in transaction.credit_account.lower():
                loans_repaid += transaction.credit_amount

    loan_portfolio_balance = opening_loan_balance + (loans_issued - loans_repaid)

    if loans_repaid > 0:
        interest_yield = float(interest_earned / loans_repaid) * 100
    else:
        interest_yield = 0.0

    return {
        "loans_issued": loans_issued,
        "loans_repaid": loans_repaid,
        "interest_earned": interest_earned,
        "loan_portfolio_balance": loan_portfolio_balance,
        "interest_yield": interest_yield,
    }


def compute_operating_expenses(transactions):
    """total_operating_expenses, expenses_by_category (grouped by
    debit_account), expense_per_transaction, top_payees_by_expense for
    one (branch, period) bucket.

    Formulas (DATA_PIPELINE_SPEC.md Section 5.2):
        total_operating_expenses = sum of debit_amount where
                                    type == 'operating_expense'
        expenses_by_category     = sum of debit_amount, grouped by
                                    debit_account, where
                                    type == 'operating_expense'
        expense_per_transaction  = total_operating_expenses / transaction_count
        top_payees_by_expense    = counterparty totals, ranked highest first

    Note on expense_per_transaction: the spec's "transaction_count" is
    ambiguous - all transactions in the period, or just the expense
    ones? I went with "count of operating_expense transactions", since
    an average that includes deposits/loans/etc. in the denominator
    wouldn't actually answer "how much do we spend per expense
    transaction" - it'd just shrink for branches that happen to do a
    lot of unrelated business. If the team disagrees, this is a one-
    line change (swap expense_transaction_count for len(transactions)),
    flagging it here in case it needs revisiting together per the
    Ground Rules (Section 8: KPI formula changes are a team conversation).

    top_payees_by_expense only looks at operating_expense rows too -
    it's listed under "Operating Expense Metrics" in the spec, not a
    general counterparty ranking across every transaction type.

    Edge case: expense_per_transaction divides by the expense
    transaction count, which can be 0 in a period with no operating
    expenses - same as steps 6 and 7, this returns Decimal('0')
    instead of raising.
    """
    total_operating_expenses = Decimal("0")
    expenses_by_category = {}
    payee_totals = {}
    expense_transaction_count = 0

    for transaction in transactions:
        if transaction.type != "operating_expense":
            continue

        total_operating_expenses += transaction.debit_amount
        expense_transaction_count += 1

        category = transaction.debit_account
        expenses_by_category[category] = (
            expenses_by_category.get(category, Decimal("0")) + transaction.debit_amount
        )

        payee = transaction.counterparty
        payee_totals[payee] = payee_totals.get(payee, Decimal("0")) + transaction.debit_amount

    if expense_transaction_count > 0:
        expense_per_transaction = total_operating_expenses / expense_transaction_count
    else:
        expense_per_transaction = Decimal("0")

    top_payees_by_expense = [
        {"counterparty": payee, "total": total}
        for payee, total in payee_totals.items()
    ]
    top_payees_by_expense.sort(key=lambda item: item["total"], reverse=True)

    return {
        "total_operating_expenses": total_operating_expenses,
        "expenses_by_category": expenses_by_category,
        "expense_per_transaction": expense_per_transaction,
        "top_payees_by_expense": top_payees_by_expense,
    }


def _normalize_account_name(name):
    """Same idea as the case-insensitive checks in earlier steps, but
    also swaps underscores for spaces first. Real ingested data spells
    accounts like 'Trading Revenue' / 'Interest Income'; the
    hand-written tests/fixtures.py spells them 'trading_revenue' /
    'interest_income'. Normalizing both to 'trading revenue' /
    'interest income' before comparing means one comparison works
    against either source."""
    if name is None:
        return None
    return name.replace("_", " ").strip().lower()


def compute_revenue_and_net_income(transactions, total_operating_expenses):
    """exchange_fee_revenue, interest_income, trading_revenue,
    total_revenue, net_income, net_income_margin for one (branch,
    period) bucket.

    Formulas (DATA_PIPELINE_SPEC.md Section 5.2):
        exchange_fee_revenue = sum of credit_amount_2 where
                                type == 'bill_of_exchange'
        interest_income       = sum of credit_amount_2 where
                                credit_account_2 == 'Interest Income'
        trading_revenue        = sum of credit_amount where
                                credit_account == 'Trading Revenue'
        total_revenue          = sum of all revenue-type credits
        net_income              = total_revenue - total_operating_expenses
        net_income_margin       = net_income / total_revenue, as a
                                percentage - explicitly undefined
                                (None) when total_revenue == 0

    total_revenue is defined here as exchange_fee_revenue +
    interest_income + trading_revenue - the sum of the three metrics
    right above it, rather than a generic "every credit to a REVENUE-
    type account" scan. I checked this against real rows in
    medici_transactions.csv before deciding: a bill_of_exchange row's
    PRIMARY credit_account is 'Cash' (an ASSET account) - the actual
    revenue lands in credit_amount_2 under credit_account_2 =
    'Exchange Fee Revenue'. A generic "sum wherever credit_account_type
    == REVENUE" scan would completely miss that money, since the
    primary credit_account on those rows isn't a revenue account at
    all. Summing the three named metrics is the only approach that
    matches how the real data is actually structured.

    net_income needs total_operating_expenses, which step 8's
    compute_operating_expenses calculates - not something this
    function can see on its own from `transactions` alone. Same
    pattern as opening_cash_balance/opening_loan_balance in steps 5
    and 7: rather than recompute it here, it's passed in as a
    parameter. compute_kpis (step 10) will call compute_operating_expenses
    first and hand its total into this function.

    One thing worth flagging to the team (not something I changed
    silently): tests/fixtures.py's Venice transactions don't fully
    follow the real-data pattern above - e.g. its bill_of_exchange
    fixture (id=9) puts the revenue amount in credit_amount instead of
    credit_amount_2, so it wouldn't be counted by this formula. There's
    no EXPECTED_VENICE_1420_01 fixture to test against, only Florence's,
    so this doesn't block anything, but if we later add a Venice
    expected-values test, that fixture may need a fix to match the
    real transaction shape.
    """
    exchange_fee_revenue = Decimal("0")
    interest_income = Decimal("0")
    trading_revenue = Decimal("0")

    for transaction in transactions:
        if transaction.type == "bill_of_exchange":
            exchange_fee_revenue += transaction.credit_amount_2

        if _normalize_account_name(transaction.credit_account_2) == "interest income":
            interest_income += transaction.credit_amount_2

        if _normalize_account_name(transaction.credit_account) == "trading revenue":
            trading_revenue += transaction.credit_amount

    total_revenue = exchange_fee_revenue + interest_income + trading_revenue
    net_income = total_revenue - total_operating_expenses

    if total_revenue != 0:
        net_income_margin = float(net_income / total_revenue) * 100
    else:
        net_income_margin = None

    return {
        "exchange_fee_revenue": exchange_fee_revenue,
        "interest_income": interest_income,
        "trading_revenue": trading_revenue,
        "total_revenue": total_revenue,
        "net_income": net_income,
        "net_income_margin": net_income_margin,
    }


def period_bounds(period):
    """Given a period string like '1420-01', return
    (period_start, period_end) - the first and last calendar day of
    that month, as real date objects. KPIResult needs both."""
    year_text, month_text = period.split("-")
    year = int(year_text)
    month = int(month_text)
    period_start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    period_end = date(year, month, last_day)
    return period_start, period_end


def compute_kpis(branch, period, cleaned_transactions):
    """Ties steps 4-9 together into one KPIResult for (branch, period).

    Important: cleaned_transactions should be EVERY CleanedTransaction
    in the dataset (all branches, all periods) - not pre-filtered down
    to just this branch/period. That's because closing_cash_balance and
    loan_portfolio_balance are cumulative from the start of the
    dataset (steps 5 & 7), so this function needs to see every earlier
    period for this branch to add up a correct running balance, even
    though the KPIResult it hands back only covers `period` itself.

    How it works:
      1. Keep only this branch's transactions, then bucket them by
         period (step 4) and keep the periods at-or-before the target,
         sorted oldest-first - '1420-01' <= '1420-02' as plain string
         comparison works here because periods are always written
         'YYYY-MM' with a zero-padded month.
      2. Walk those periods oldest to newest, calling
         compute_cash_position and compute_loan_portfolio on each and
         carrying each period's closing balance forward as the next
         period's opening balance (this is the actual point of doing
         a chronological walk instead of jumping straight to the
         target period).
      3. For the target period only, also run
         compute_deposits_withdrawals, compute_operating_expenses, and
         compute_revenue_and_net_income - these three aren't
         cumulative, so they only need that one period's rows.
      4. Assemble every piece into a single KPIResult (medici/contracts.py).

    Duplicates (is_duplicate=True) are excluded from every calculation
    above - filtered out before any compute_* function ever sees them -
    but the target period's duplicate rows are still counted in
    excluded_duplicate_count, so that exclusion stays visible rather
    than silently dropping data (data contract sheet, Section 8 ground
    rules).

    Known limitation: if `branch`/`period` has zero transactions in the
    dataset, this raises ValueError rather than guessing what a "zero
    activity" KPIResult should look like - flagging this as a real "no
    such period" problem (e.g. a typo) felt safer than silently
    returning an all-zero result that could be mistaken for a branch
    that really did have no activity that month.
    """
    branch_transactions = [
        transaction for transaction in cleaned_transactions
        if transaction.branch == branch
    ]
    buckets = bucket_by_period(branch_transactions)

    if (branch, period) not in buckets:
        raise ValueError(
            "No transactions found for branch={!r} period={!r}".format(branch, period)
        )

    periods_through_target = sorted(
        key for key in buckets if key[1] <= period
    )

    opening_cash_balance = Decimal("0")
    opening_loan_balance = Decimal("0")
    target_transactions = None
    target_excluded_duplicate_count = 0
    target_cash = None
    target_loans = None

    for bucket_key in periods_through_target:
        bucket_transactions = buckets[bucket_key]
        non_duplicates = [t for t in bucket_transactions if not t.is_duplicate]

        cash = compute_cash_position(non_duplicates, opening_cash_balance)
        loans = compute_loan_portfolio(non_duplicates, opening_loan_balance)

        opening_cash_balance = cash["closing_cash_balance"]
        opening_loan_balance = loans["loan_portfolio_balance"]

        if bucket_key == (branch, period):
            target_transactions = non_duplicates
            target_excluded_duplicate_count = sum(
                1 for t in bucket_transactions if t.is_duplicate
            )
            target_cash = cash
            target_loans = loans

    deposits_withdrawals = compute_deposits_withdrawals(target_transactions)
    operating_expenses = compute_operating_expenses(target_transactions)
    revenue_and_net_income = compute_revenue_and_net_income(
        target_transactions, operating_expenses["total_operating_expenses"]
    )

    period_start, period_end = period_bounds(period)

    return KPIResult(
        branch=branch,
        period=period,
        period_start=period_start,
        period_end=period_end,
        excluded_duplicate_count=target_excluded_duplicate_count,
        **target_cash,
        **deposits_withdrawals,
        **target_loans,
        **operating_expenses,
        **revenue_and_net_income,
    )
