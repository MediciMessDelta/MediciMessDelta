"""
Tests for Phase 4: medici/anomaly/rules.py and alerts.py — built by
Sloane.

One trigger test + one non-trigger test per rule (A-G), all built
against tests/anomaly_fixtures.py's sample data, plus a couple of tests
for build_alert_records() itself. The two tests that were here before
(sketches of what a Rule C alert *should* look like, written before
rules.py existed) are replaced with a real test that actually calls
rule_c_duplicate_transactions().
"""

from medici.anomaly.alerts import assign_severity, build_alert_records
from medici.anomaly.rules import (
    rule_a_benford_deviation,
    rule_b_vendor_concentration,
    rule_c_duplicate_transactions,
    rule_d_round_number_clustering,
    rule_e_frequency_outlier,
    rule_f_below_reporting_threshold,
    rule_g_new_counterparty_high_volume,
    run_all_rules,
)
from tests.anomaly_fixtures import (
    benford_trigger_transactions,
    benford_non_trigger_transactions,
    vendor_concentration_trigger_transactions,
    vendor_concentration_non_trigger_transactions,
    round_number_trigger_transactions,
    round_number_non_trigger_transactions,
    frequency_outlier_trigger_transactions,
    frequency_outlier_non_trigger_transactions,
    below_threshold_trigger_transactions,
    below_threshold_non_trigger_transactions,
    new_counterparty_trigger_transactions,
    new_counterparty_non_trigger_transactions,
)
from tests.fixtures import SAMPLE_TRANSACTIONS


def test_rule_a_fires_on_all_nines_but_not_on_benford_shaped_data():
    assert len(rule_a_benford_deviation(benford_trigger_transactions())) == 1
    assert len(rule_a_benford_deviation(benford_non_trigger_transactions())) == 0


def test_rule_b_fires_when_one_vendor_is_15_percent_of_spend():
    hits = rule_b_vendor_concentration(vendor_concentration_trigger_transactions())
    assert len(hits) == 1
    assert hits[0]["counterparty"] == "Dominant Vendor"
    assert hits[0]["metric_value"] == 15.0


def test_rule_b_does_not_fire_when_spend_is_evenly_spread():
    hits = rule_b_vendor_concentration(vendor_concentration_non_trigger_transactions())
    assert hits == []


def test_rule_c_fires_on_the_bardi_family_duplicate_deposit():
    """Transactions 1 and 8 in SAMPLE_TRANSACTIONS are the same $500
    Florence deposit from Bardi Family, dated 0 days apart."""
    hits = rule_c_duplicate_transactions(SAMPLE_TRANSACTIONS)
    assert len(hits) == 1
    assert hits[0]["affected_transaction_ids"] == [1, 8]
    assert hits[0]["metric_value"] == 0.0


def test_rule_c_does_not_fire_on_unrelated_transactions():
    """Rows 5, 6, 7, 9 (Venice) share no branch/type/counterparty/amount
    combination with each other or with Florence's rows."""
    venice_only = [t for t in SAMPLE_TRANSACTIONS if t.branch == "Venice"]
    assert rule_c_duplicate_transactions(venice_only) == []


def test_rule_d_fires_when_half_the_amounts_are_round_numbers():
    hits = rule_d_round_number_clustering(round_number_trigger_transactions())
    assert len(hits) == 1
    assert hits[0]["metric_value"] == 50.0


def test_rule_d_does_not_fire_when_few_amounts_are_round():
    assert rule_d_round_number_clustering(round_number_non_trigger_transactions()) == []


def test_rule_e_fires_on_a_15_transaction_spike_after_a_steady_baseline():
    hits = rule_e_frequency_outlier(frequency_outlier_trigger_transactions())
    assert len(hits) == 1
    assert hits[0]["period"] == "1420-05"
    assert hits[0]["metric_value"] == 15.0


def test_rule_e_does_not_fire_on_a_steady_monthly_pattern():
    assert rule_e_frequency_outlier(frequency_outlier_non_trigger_transactions()) == []


def test_rule_f_fires_when_small_payments_add_up_past_10000():
    hits = rule_f_below_reporting_threshold(below_threshold_trigger_transactions())
    assert len(hits) == 1
    assert hits[0]["metric_value"] == 10800.0
    assert len(hits[0]["affected_transaction_ids"]) == 12


def test_rule_f_does_not_fire_when_the_30_day_total_stays_under_10000():
    assert rule_f_below_reporting_threshold(below_threshold_non_trigger_transactions()) == []


def test_rule_g_fires_when_a_new_counterparty_dwarfs_the_established_average():
    hits = rule_g_new_counterparty_high_volume(new_counterparty_trigger_transactions())
    assert len(hits) == 1
    assert hits[0]["counterparty"] == "New Vendor"
    assert hits[0]["metric_value"] == 5000.0


def test_rule_g_does_not_fire_when_the_new_counterparty_is_in_line_with_the_average():
    assert rule_g_new_counterparty_high_volume(new_counterparty_non_trigger_transactions()) == []


def test_run_all_rules_combines_every_rule():
    """A sanity check that the orchestrator actually calls every rule -
    mixes fixtures from three different rules together and confirms all
    three show up, not just the first one that happens to match."""
    mixed_transactions = (
        vendor_concentration_trigger_transactions()
        + round_number_trigger_transactions()
        + below_threshold_trigger_transactions()
    )
    hits = run_all_rules(mixed_transactions)
    fired_rules = {hit["rule"] for hit in hits}
    assert {"B", "D", "F"}.issubset(fired_rules)


def test_assign_severity_scales_with_how_far_past_threshold():
    assert assign_severity(metric_value=15, threshold_value=5) == "HIGH"    # 3x
    assert assign_severity(metric_value=9, threshold_value=5) == "MEDIUM"   # 1.8x
    assert assign_severity(metric_value=6, threshold_value=5) == "LOW"      # 1.2x


def test_build_alert_records_produces_valid_alert_records():
    hits = rule_c_duplicate_transactions(SAMPLE_TRANSACTIONS)
    alerts = build_alert_records(hits, starting_alert_id=1)

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_id == 1
    assert alert.rule == "C"
    assert alert.status == "OPEN"
    assert alert.affected_transaction_ids == [1, 8]
