# MediciMessDelta — Data-Contract Reference Sheet

*Diagram #4 from the 1-Week Plan. This is the one page every module points to — the exact field names and types passing between Monah's ingestion code, Sloane's KPI/anomaly code, and Matt's API/dashboards. If a field name or type here needs to change, that's a team conversation first (Ground Rule, Section 8), then an edit to this file.*

> **Quick definitions if you're new to this:**
> A **data contract** is just a promise: "my code will always output data shaped exactly like this." As long as everyone honors their contract, it doesn't matter how the code *inside* each module works — the pieces still plug together. **Type** means what kind of value a field holds (a whole number, text, a date, true/false, a list, etc.) — Python calls these `int`, `str`, `date`, `bool`, `list`, `dict`, `Decimal` (a precise number type, better than `float` for money since it avoids rounding errors).

---

## 1. Cleaned Transaction

**Produced by:** Monah's ingestion module (Phase 2) — one row in, one row out, per raw transaction that passes validation.
**Consumed by:** Sloane's KPI and anomaly modules (Phase 3 & 4).

This is the *original* transaction fields (from `TRANSACTION_DATA.md`), plus the enrichment columns the pipeline spec (Section 5.1) requires the ingestion step to add.

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | Unique transaction identifier, unchanged from raw data. |
| `date` | `date` | Coerced from the raw `YYYY-MM-DD` string to a real Python `date` object. |
| `branch` | `str` | Normalized: consistent capitalization, no trailing whitespace. |
| `type` | `str` | One of the 9 transaction types (`deposit`, `withdrawal`, `loan_issuance`, `loan_repayment`, `operating_expense`, `war_financing`, `bill_of_exchange`, `alum_trade`, `ransom_payment`). |
| `counterparty` | `str` | Name of the external party. |
| `description` | `str` | Free-text description, unchanged. |
| `debit_account` | `str` | Account debited. |
| `debit_amount` | `Decimal` | Coerced from float to `Decimal` for exact math. |
| `credit_account` | `str` | Primary account credited. |
| `credit_amount` | `Decimal` | Coerced to `Decimal`. |
| `credit_account_2` | `str \| None` | Secondary credit account. `None` if not used. |
| `credit_amount_2` | `Decimal` | **Blank treated as `0`** (team decision from Section 3.2) — never `None`. |
| `currency` | `str` | Always `"florin"` in this dataset. |
| `year` | `int` | Derived from `date`. |
| `month` | `int` | Derived from `date` (1–12). |
| `quarter` | `str` | Derived from `month`: `"Q1"`–`"Q4"`. |
| `fiscal_year` | `int` | Same as `year` — Medici Bank's fiscal year is 1 Jan–31 Dec (team decision). |
| `debit_account_type` | `str` | One of `ASSET`, `LIABILITY`, `EXPENSE`, `REVENUE`, `EQUITY` — inferred from `debit_account` using the same logic as `medici-banking.py`. |
| `credit_account_type` | `str` | Same inference, applied to `credit_account`. |
| `is_duplicate` | `bool` | `True` if this row shares `(date, branch, type, counterparty, debit_amount, credit_account)` with another row. Duplicates are **flagged, never silently dropped** (Section 4.2). |

**Validation rule enforced before a row becomes a Cleaned Transaction:** `debit_amount == credit_amount + credit_amount_2`. Any row that fails this is logged and excluded — it never reaches this contract.

---

## 2. KPI Result

**Produced by:** Sloane's transform/KPI module (Phase 3), one record per `(branch, period)`.
**Consumed by:** Matt's API and both dashboards (Phases 5–7).

| Field | Type | Notes |
|---|---|---|
| `branch` | `str` | The branch this record summarizes. |
| `period` | `str` | The time bucket, e.g. `"1420-01"` (month) or `"1420-Q1"` — format agreed by the team. |
| `period_start` | `date` | First day of the period. |
| `period_end` | `date` | Last day of the period. |

**Cash position**

| Field | Type |
|---|---|
| `total_cash_inflows` | `Decimal` |
| `total_cash_outflows` | `Decimal` |
| `net_cash_movement` | `Decimal` |
| `closing_cash_balance` | `Decimal` |

**Deposits & withdrawals**

| Field | Type |
|---|---|
| `total_deposits` | `Decimal` |
| `total_withdrawals` | `Decimal` |
| `deposit_count` | `int` |
| `withdrawal_count` | `int` |
| `avg_deposit_size` | `Decimal` |
| `avg_withdrawal_size` | `Decimal` |

**Loan portfolio**

| Field | Type |
|---|---|
| `loans_issued` | `Decimal` |
| `loans_repaid` | `Decimal` |
| `interest_earned` | `Decimal` |
| `loan_portfolio_balance` | `Decimal` |
| `interest_yield` | `float` (percentage) |

**Operating expenses**

| Field | Type |
|---|---|
| `total_operating_expenses` | `Decimal` |
| `expenses_by_category` | `dict[str, Decimal]` — keyed by `debit_account` |
| `expense_per_transaction` | `Decimal` |
| `top_payees_by_expense` | `list[dict]` — each item `{"counterparty": str, "total": Decimal}`, sorted descending |

**Revenue & net income**

| Field | Type |
|---|---|
| `exchange_fee_revenue` | `Decimal` |
| `interest_income` | `Decimal` |
| `trading_revenue` | `Decimal` |
| `total_revenue` | `Decimal` |
| `net_income` | `Decimal` |
| `net_income_margin` | `float` (percentage) |

*Rounding rule: round every `Decimal` to 2 places only at display/serialization time — keep full precision through calculations (team sign-off item, Section 3.2).*

---

## 3. Alert Record

**Produced by:** Sloane's anomaly detection module (Phase 4), one record per rule firing.
**Consumed by:** Matt's API (`/api/alerts`) and both dashboards' alert panels; also the raw input to Sloane's Phase 8 forensic report.

| Field | Type | Notes |
|---|---|---|
| `alert_id` | `int` | Unique identifier. |
| `rule` | `str` | Which rule fired: `"A"` through `"G"` (see rule list below). |
| `severity` | `str` | `"LOW"`, `"MEDIUM"`, or `"HIGH"`. |
| `branch` | `str` | Affected branch. |
| `period` | `str` | Period in which the anomaly was detected. |
| `affected_transaction_ids` | `list[int]` | The Cleaned Transaction `id`s involved — this is the traceability link back to Contract #1. |
| `counterparty` | `str \| None` | Relevant counterparty, if the rule is counterparty-specific. |
| `metric_value` | `float` | The computed value that triggered the rule. |
| `threshold_value` | `float` | The threshold that was exceeded. |
| `description` | `str` | Human-readable explanation. |
| `detected_at` | `datetime` | When the pipeline generated this alert. |
| `status` | `str` | `"OPEN"`, `"ACKNOWLEDGED"`, or `"RESOLVED"`. |

**The 7 rules this feeds (A–G):** A – Benford's Law deviation · B – Vendor concentration · C – Duplicate transaction · D – Round-number clustering · E – Transaction frequency outlier · F – Amount below reporting threshold · G – New counterparty with immediate high volume. Full method/threshold for each is in `DATA_PIPELINE_SPEC.md` Section 5.3 — this sheet only defines the *output shape*, not the detection logic.

---

*Source specs: `DATA_PIPELINE_SPEC.md` (Sections 2.1, 4, 5.1, 5.2, 5.3, 5.4) and `TRANSACTION_DATA.md`. If you change a field here, update this file and tell the team before anyone builds on top of it (Ground Rules, Section 8).*
