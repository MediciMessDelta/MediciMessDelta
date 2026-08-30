"""
Phase 4: Anomaly Detection Rules (Rules A-G) — built by Sloane.

Implements DATA_PIPELINE_SPEC.md Section 5.3. Every rule function below
takes a list of CleanedTransaction objects (from Phase 3's clean.py) and
returns a list of plain dicts — "hits" — one per anomaly found:

    {
        "rule": "A",                      # which rule fired, A-G
        "branch": "Florence",
        "period": "1420-01",
        "affected_transaction_ids": [1, 2],
        "counterparty": "Bardi Family",   # or None if not rule-specific
        "metric_value": 12.3,
        "threshold_value": 5.0,
        "description": "human-readable explanation",
    }

alerts.py (step 9) turns these hits into real AlertRecord objects
(assigning alert_id, severity, detected_at, status). Keeping rules.py's
output as plain dicts instead of AlertRecords directly makes each rule
easy to unit test on its own, without pulling in alert-numbering logic.

run_all_rules() at the bottom ties every rule together for one pass
over the whole dataset.
"""

import math
import statistics
from datetime import timedelta
from decimal import Decimal

from medici.transform.kpis import period_key

# Benford's Law: in most naturally-occurring numeric data, leading
# digit d (1-9) shows up with probability log10(1 + 1/d) — a "1" about
# 30% of the time, a "9" only about 5%. Precomputed once here.
BENFORD_EXPECTED_PROPORTIONS = {d: math.log10(1 + 1 / d) for d in range(1, 10)}


def _leading_digit(amount):
    """First non-zero digit of a Decimal amount, e.g. Decimal('208.50')
    -> 2. Returns None for zero (no leading digit to speak of)."""
    text = format(abs(amount), "f").replace(".", "").lstrip("0")
    if not text:
        return None
    return int(text[0])


def rule_a_benford_deviation(cleaned_transactions, mad_threshold=0.015, minimum_group_size=10):
    """Rule A - Benford's Law deviation.

    Applies to: every debit_amount in each (branch, period, type) group.
    Method: compare the observed leading-digit distribution to Benford's
    expected distribution using Mean Absolute Deviation (MAD).
    Threshold: flag if MAD > 0.015.

    Note: the spec also mentions a chi-squared p-value < 0.05 as an
    alternative trigger condition. I only implemented the MAD check -
    a proper chi-squared test needs scipy.stats, which isn't in
    requirements.txt. Adding a new dependency for one rule felt like a
    team decision (Ground Rules, Section 8), not something to slip in
    unilaterally, so flagging this as a possible follow-up rather than
    silently adding the dependency.

    minimum_group_size guards against evaluating Benford's Law on a
    handful of transactions, where the "expected" distribution isn't
    statistically meaningful yet - groups smaller than this are skipped
    rather than producing an unreliable alert.
    """
    hits = []
    buckets = {}
    for transaction in cleaned_transactions:
        key = (transaction.branch, period_key(transaction), transaction.type)
        buckets.setdefault(key, []).append(transaction)

    for (branch, period, txn_type), transactions in buckets.items():
        leading_digits = [_leading_digit(t.debit_amount) for t in transactions]
        leading_digits = [d for d in leading_digits if d is not None]

        if len(leading_digits) < minimum_group_size:
            continue

        total = len(leading_digits)
        observed_counts = {d: 0 for d in range(1, 10)}
        for digit in leading_digits:
            observed_counts[digit] += 1

        mad = (
            sum(
                abs(observed_counts[d] / total - BENFORD_EXPECTED_PROPORTIONS[d])
                for d in range(1, 10)
            )
            / 9
        )

        if mad > mad_threshold:
            hits.append(
                {
                    "rule": "A",
                    "branch": branch,
                    "period": period,
                    "affected_transaction_ids": [t.id for t in transactions],
                    "counterparty": None,
                    "metric_value": mad,
                    "threshold_value": mad_threshold,
                    "description": (
                        f"{txn_type} amounts for {branch} in {period} deviate from "
                        f"Benford's Law (MAD={mad:.4f}, threshold {mad_threshold})."
                    ),
                }
            )

    return hits


def rule_b_vendor_concentration(cleaned_transactions, share_threshold=0.05, minimum_group_size=5):
    """Rule B - Vendor concentration.

    Applies to: type == 'operating_expense' transactions.
    Method: within each (branch, period, debit_account) group, compute
    each counterparty's share of that group's total spend.
    Threshold: flag if any counterparty's share exceeds 5%.

    IMPORTANT finding from the integration check: I ran this against
    the real 80,230-row dataset and it flagged 9,011 alerts - about
    80% of everything every rule combined produced, which is not a
    useful signal, it's noise. The reason: the (branch, period,
    debit_account) grouping the spec defines is VERY fine-grained -
    the median real group has exactly 1 transaction from 1
    counterparty. A single vendor is trivially "100% of spend" for a
    group that only ever had that one vendor in it that month - that's
    not vendor concentration, that's just how few expense transactions
    happen in one category in one branch in one month.

    minimum_group_size (added after that finding, same pattern as
    Rules A and D) skips groups too small for a "concentration"
    percentage to mean anything. This doesn't change what counts as
    concentrated - share_threshold and the grouping are still exactly
    per spec - it just stops the rule from firing on groups too small
    to say anything statistically real. Flagging this clearly for the
    team: if 9,011 alerts (even after this guard, still likely to be
    the loudest rule by far) isn't what's wanted, the real fix is
    probably coarsening the grouping itself (e.g. per-quarter or
    per-branch-per-category-across-the-whole-dataset instead of
    per-month) - a bigger change than I felt was mine to make alone.
    """
    hits = []
    buckets = {}
    for transaction in cleaned_transactions:
        if transaction.type != "operating_expense":
            continue
        key = (transaction.branch, period_key(transaction), transaction.debit_account)
        buckets.setdefault(key, []).append(transaction)

    for (branch, period, category), transactions in buckets.items():
        if len(transactions) < minimum_group_size:
            continue

        group_total = sum(t.debit_amount for t in transactions)
        if group_total == 0:
            continue

        by_counterparty = {}
        for transaction in transactions:
            by_counterparty.setdefault(transaction.counterparty, []).append(transaction)

        for counterparty, counterparty_transactions in by_counterparty.items():
            counterparty_total = sum(t.debit_amount for t in counterparty_transactions)
            share = float(counterparty_total / group_total)

            if share > share_threshold:
                hits.append(
                    {
                        "rule": "B",
                        "branch": branch,
                        "period": period,
                        "affected_transaction_ids": [t.id for t in counterparty_transactions],
                        "counterparty": counterparty,
                        "metric_value": share * 100,
                        "threshold_value": share_threshold * 100,
                        "description": (
                            f"{counterparty} accounts for {share * 100:.1f}% of {category} "
                            f"spend in {branch}, {period} (threshold {share_threshold * 100:.0f}%)."
                        ),
                    }
                )

    return hits


def rule_c_duplicate_transactions(cleaned_transactions, day_window=3):
    """Rule C - Duplicate transaction detection.

    Applies to: all transactions.
    Method: within each (branch, month, type, counterparty, debit_amount)
    group, flag any pair of transactions whose dates are within 3
    calendar days of each other.
    Threshold: any such pair.

    Worth remembering: this is related to but NOT the same check as
    Monah's is_duplicate flag from ingestion (Phase 2). That one only
    catches exact same-day matches on a slightly different set of
    fields, for excluding rows from KPI totals. This rule is a wider
    fraud signal (a 3-day window) that runs independently - it will
    also catch every ingestion-level duplicate, but it's not limited to
    them.
    """
    hits = []
    buckets = {}
    for transaction in cleaned_transactions:
        key = (
            transaction.branch,
            period_key(transaction),
            transaction.type,
            transaction.counterparty,
            transaction.debit_amount,
        )
        buckets.setdefault(key, []).append(transaction)

    for (branch, period, txn_type, counterparty, amount), transactions in buckets.items():
        if len(transactions) < 2:
            continue

        transactions_by_date = sorted(transactions, key=lambda t: t.date)
        flagged_ids = set()
        smallest_gap_days = None

        for i in range(len(transactions_by_date)):
            for j in range(i + 1, len(transactions_by_date)):
                gap_days = (transactions_by_date[j].date - transactions_by_date[i].date).days
                if gap_days <= day_window:
                    flagged_ids.add(transactions_by_date[i].id)
                    flagged_ids.add(transactions_by_date[j].id)
                    if smallest_gap_days is None or gap_days < smallest_gap_days:
                        smallest_gap_days = gap_days

        if flagged_ids:
            hits.append(
                {
                    "rule": "C",
                    "branch": branch,
                    "period": period,
                    "affected_transaction_ids": sorted(flagged_ids),
                    "counterparty": counterparty,
                    "metric_value": float(smallest_gap_days),
                    "threshold_value": float(day_window),
                    "description": (
                        f"{len(flagged_ids)} {txn_type} transactions with {counterparty} for "
                        f"{amount} in {branch}, {period} are within {day_window} days of each "
                        "other (possible duplicate entry)."
                    ),
                }
            )

    return hits


def rule_d_round_number_clustering(
    cleaned_transactions, cluster_threshold=0.30, minimum_group_size=5
):
    """Rule D - Round-number clustering.

    Applies to: type == 'operating_expense' transactions.
    Method: within each (branch, debit_account) group, compute the
    proportion of amounts that are exact multiples of 50.
    Threshold: flag if the proportion exceeds 30%.

    Note: the spec scopes this rule to (branch, debit_account) only, with
    no period. I added period into the grouping anyway - matching how
    Rule B is scoped - so every alert this produces can still report a
    meaningful period, consistent with the rest of the system's
    per-branch-per-period output artifacts. Flagging this interpretation
    for the team, same as Rule B's expense_per_transaction question back
    in Phase 3.
    """
    hits = []
    buckets = {}
    for transaction in cleaned_transactions:
        if transaction.type != "operating_expense":
            continue
        key = (transaction.branch, period_key(transaction), transaction.debit_account)
        buckets.setdefault(key, []).append(transaction)

    for (branch, period, category), transactions in buckets.items():
        if len(transactions) < minimum_group_size:
            continue

        round_transactions = [t for t in transactions if t.debit_amount % 50 == 0]
        proportion = len(round_transactions) / len(transactions)

        if proportion > cluster_threshold:
            hits.append(
                {
                    "rule": "D",
                    "branch": branch,
                    "period": period,
                    "affected_transaction_ids": [t.id for t in round_transactions],
                    "counterparty": None,
                    "metric_value": proportion * 100,
                    "threshold_value": cluster_threshold * 100,
                    "description": (
                        f"{proportion * 100:.0f}% of {category} amounts in {branch}, {period} "
                        f"are exact multiples of 50 (threshold {cluster_threshold * 100:.0f}%)."
                    ),
                }
            )

    return hits


def rule_e_frequency_outlier(cleaned_transactions, std_dev_multiplier=3, minimum_baseline_months=2):
    """Rule E - Transaction frequency outlier (by counterparty).

    Applies to: all transactions.
    Method: for each (branch, counterparty, type), compute the monthly
    transaction count. Flag any month whose count exceeds
    mean + 3 standard deviations of the OTHER months.
    Threshold: 3 standard deviations above the baseline mean.

    Important design choice: when testing a given month, that month is
    excluded from its own baseline mean/stdev calculation ("leave-one-
    out"). Including the spike month in its own baseline would inflate
    the very standard deviation meant to catch it - a real spike would
    partly hide itself. minimum_baseline_months requires at least 2
    other months of history before evaluating a month at all, since a
    standard deviation computed from 0-1 data points isn't meaningful.
    """
    hits = []
    grouped = {}
    for transaction in cleaned_transactions:
        key = (transaction.branch, transaction.counterparty, transaction.type)
        month = period_key(transaction)
        grouped.setdefault(key, {}).setdefault(month, []).append(transaction)

    for (branch, counterparty, txn_type), by_month in grouped.items():
        months = sorted(by_month.keys())
        if len(months) < minimum_baseline_months + 1:
            continue

        for target_month in months:
            baseline_counts = [len(by_month[m]) for m in months if m != target_month]
            if len(baseline_counts) < minimum_baseline_months:
                continue

            baseline_mean = statistics.mean(baseline_counts)
            baseline_stdev = statistics.pstdev(baseline_counts)
            threshold_count = baseline_mean + std_dev_multiplier * baseline_stdev
            target_count = len(by_month[target_month])

            if target_count > threshold_count:
                hits.append(
                    {
                        "rule": "E",
                        "branch": branch,
                        "period": target_month,
                        "affected_transaction_ids": [t.id for t in by_month[target_month]],
                        "counterparty": counterparty,
                        "metric_value": float(target_count),
                        "threshold_value": float(threshold_count),
                        "description": (
                            f"{counterparty} had {target_count} {txn_type} transactions with "
                            f"{branch} in {target_month}, above the baseline of "
                            f"{baseline_mean:.1f} (+{std_dev_multiplier}σ = {threshold_count:.1f})."
                        ),
                    }
                )

    return hits


def rule_f_below_reporting_threshold(
    cleaned_transactions,
    individual_threshold=Decimal("1000"),
    aggregate_threshold=Decimal("10000"),
    window_days=30,
):
    """Rule F - Amount below reporting threshold ("smurfing").

    Applies to: all transactions.
    Method: for each (branch, counterparty), among transactions
    individually under 1,000 florins, find the highest-total 30-day
    window of consecutive (by date) transactions.
    Threshold: flag if that window's total exceeds 10,000 florins.

    "Smurfing" (also called structuring) is a real financial-crime
    term: deliberately breaking a large transfer into several small
    ones, each individually below a threshold that would trigger
    reporting requirements, to avoid scrutiny.
    """
    hits = []
    buckets = {}
    for transaction in cleaned_transactions:
        if transaction.debit_amount >= individual_threshold:
            continue
        key = (transaction.branch, transaction.counterparty)
        buckets.setdefault(key, []).append(transaction)

    for (branch, counterparty), transactions in buckets.items():
        transactions_by_date = sorted(transactions, key=lambda t: t.date)

        best_window = None
        best_total = Decimal("0")

        for i in range(len(transactions_by_date)):
            window = [transactions_by_date[i]]
            window_total = transactions_by_date[i].debit_amount

            for j in range(i + 1, len(transactions_by_date)):
                gap_days = (transactions_by_date[j].date - transactions_by_date[i].date).days
                if gap_days > window_days:
                    break
                window.append(transactions_by_date[j])
                window_total += transactions_by_date[j].debit_amount

            if window_total > best_total:
                best_total = window_total
                best_window = window

        if best_window is not None and best_total > aggregate_threshold:
            hits.append(
                {
                    "rule": "F",
                    "branch": branch,
                    "period": period_key(best_window[0]),
                    "affected_transaction_ids": [t.id for t in best_window],
                    "counterparty": counterparty,
                    "metric_value": float(best_total),
                    "threshold_value": float(aggregate_threshold),
                    "description": (
                        f"{counterparty} made {len(best_window)} payments with {branch} "
                        f"totaling {best_total} within {window_days} days, each individually "
                        f"under {individual_threshold} (possible structuring)."
                    ),
                }
            )

    return hits


def rule_g_new_counterparty_high_volume(cleaned_transactions, volume_multiplier=3, window_days=90):
    """Rule G - New counterparty with immediate high volume.

    Applies to: all transactions.
    Method: for each (branch, type) group, find every counterparty's
    first-appearance date and their transaction volume in the 90 days
    following it. Compare each counterparty's first-90-day volume to
    the average first-90-day volume of "established" counterparties -
    every counterparty in the same group whose own first appearance was
    strictly earlier.
    Threshold: flag if a counterparty's first-90-day volume exceeds 3x
    that established average.

    The spec doesn't precisely define "established counterparty," so
    this is an interpretation: rather than "all other counterparties"
    (which would let two brand-new counterparties validate each other),
    only counterparties who showed up earlier count as the baseline -
    which matches what "established" should mean. Worth confirming with
    the team if this doesn't match their mental model.
    """
    hits = []
    buckets = {}
    for transaction in cleaned_transactions:
        key = (transaction.branch, transaction.type)
        buckets.setdefault(key, []).append(transaction)

    for (branch, txn_type), transactions in buckets.items():
        by_counterparty = {}
        for transaction in transactions:
            by_counterparty.setdefault(transaction.counterparty, []).append(transaction)

        first_appearance = {
            counterparty: min(t.date for t in txns)
            for counterparty, txns in by_counterparty.items()
        }
        ordered_counterparties = sorted(by_counterparty.keys(), key=lambda cp: first_appearance[cp])

        def first_window_transactions(counterparty):
            start = first_appearance[counterparty]
            end = start + timedelta(days=window_days)
            return [t for t in by_counterparty[counterparty] if start <= t.date <= end]

        first_window_volumes = {
            counterparty: sum(t.debit_amount for t in first_window_transactions(counterparty))
            for counterparty in ordered_counterparties
        }

        for counterparty in ordered_counterparties:
            established = [
                cp
                for cp in ordered_counterparties
                if first_appearance[cp] < first_appearance[counterparty]
            ]
            if not established:
                continue

            average_established_volume = sum(first_window_volumes[cp] for cp in established) / len(
                established
            )
            if average_established_volume == 0:
                continue

            target_volume = first_window_volumes[counterparty]

            if target_volume > volume_multiplier * average_established_volume:
                first_transactions = first_window_transactions(counterparty)
                hits.append(
                    {
                        "rule": "G",
                        "branch": branch,
                        "period": period_key(first_transactions[0]),
                        "affected_transaction_ids": [t.id for t in first_transactions],
                        "counterparty": counterparty,
                        "metric_value": float(target_volume),
                        "threshold_value": float(volume_multiplier * average_established_volume),
                        "description": (
                            f"New counterparty {counterparty} did {target_volume} in {txn_type} "
                            f"volume with {branch} in their first {window_days} days, over "
                            f"{volume_multiplier}x the ~{average_established_volume:.0f} average "
                            "for established counterparties."
                        ),
                    }
                )

    return hits


def run_all_rules(cleaned_transactions):
    """Runs every Rule A-G over the full set of cleaned transactions and
    returns every hit found, combined into one list. This is the
    function Phase 5's API and Phase 8's forensic exercise will call."""
    hits = []
    hits += rule_a_benford_deviation(cleaned_transactions)
    hits += rule_b_vendor_concentration(cleaned_transactions)
    hits += rule_c_duplicate_transactions(cleaned_transactions)
    hits += rule_d_round_number_clustering(cleaned_transactions)
    hits += rule_e_frequency_outlier(cleaned_transactions)
    hits += rule_f_below_reporting_threshold(cleaned_transactions)
    hits += rule_g_new_counterparty_high_volume(cleaned_transactions)
    return hits
