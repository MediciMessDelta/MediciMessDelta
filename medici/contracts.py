from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal

class CleanedTransaction(BaseModel):
    id: int
    date: date
    branch: str
    type: str
    counterparty: str
    description: str
    debit_account: str
    debit_amount: Decimal
    credit_account: str
    credit_amount: Decimal
    credit_account_2: str | None = None
    credit_amount_2: Decimal = 0
    currency: str
    year: int
    month: int
    quarter: str
    fiscal_year: int
    debit_account_type: str
    credit_account_type: str
    is_duplicate: bool

class KPIResult(BaseModel):
    branch: str
    period: str
    period_start: date
    period_end: date
    excluded_duplicate_count: int = 0
    total_cash_inflows: Decimal
    total_cash_outflows: Decimal
    net_cash_movement: Decimal
    closing_cash_balance: Decimal
    total_deposits: Decimal
    total_withdrawals: Decimal
    deposit_count: int
    withdrawal_count: int
    avg_deposit_size: Decimal
    avg_withdrawal_size: Decimal
    loans_issued: Decimal
    loans_repaid: Decimal
    interest_earned: Decimal
    loan_portfolio_balance: Decimal
    interest_yield: float
    total_operating_expenses: Decimal
    expenses_by_category: dict[str, Decimal]
    expense_per_transaction: Decimal
    top_payees_by_expense: list[dict]
    exchange_fee_revenue: Decimal
    interest_income: Decimal
    trading_revenue: Decimal
    total_revenue: Decimal
    net_income: Decimal
    net_income_margin: float | None = None

class AlertRecord(BaseModel):
    alert_id: int
    rule: str
    severity: str
    branch: str
    period: str
    affected_transaction_ids: list[int]
    counterparty: str | None = None
    metric_value: float
    threshold_value: float
    description: str
    detected_at: datetime
    status: str
