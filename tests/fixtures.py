from datetime import date

from medici.contracts import CleanedTransaction

SAMPLE_TRANSACTIONS = [
    # 1. Florence — deposit
    CleanedTransaction(
        id=1, date=date(1420, 1, 5), branch="Florence", type="deposit",
        counterparty="Bardi Family", description="Cash deposit",
        debit_account="cash", debit_amount=500, credit_account="deposits",
        credit_amount=500, currency="florin", year=1420, month=1,
        quarter="Q1", fiscal_year=1420, debit_account_type="ASSET",
        credit_account_type="LIABILITY", is_duplicate=False,
    ),

    # 2. Florence — withdrawal
    CleanedTransaction(
        id=2, date=date(1420, 1, 8), branch="Florence", type="withdrawal",
        counterparty="Strozzi Family", description="Cash withdrawal",
        debit_account="deposits", debit_amount=150, credit_account="cash",
        credit_amount=150, currency="florin", year=1420, month=1,
        quarter="Q1", fiscal_year=1420, debit_account_type="LIABILITY",
        credit_account_type="ASSET", is_duplicate=False,
    ),

    # 3. Florence — loan issuance
    CleanedTransaction(
        id=3, date=date(1420, 1, 12), branch="Florence", type="loan_issuance",
        counterparty="Wool Guild", description="Loan for wool shipment",
        debit_account="loans_receivable", debit_amount=1200, credit_account="cash",
        credit_amount=1200, currency="florin", year=1420, month=1,
        quarter="Q1", fiscal_year=1420, debit_account_type="ASSET",
        credit_account_type="ASSET", is_duplicate=False,
    ),

    # 4. Florence — operating expense
    CleanedTransaction(
        id=4, date=date(1420, 1, 15), branch="Florence", type="operating_expense",
        counterparty="Local Scribe Guild", description="Ledger clerks' wages",
        debit_account="wages_expense", debit_amount=75, credit_account="cash",
        credit_amount=75, currency="florin", year=1420, month=1,
        quarter="Q1", fiscal_year=1420, debit_account_type="EXPENSE",
        credit_account_type="ASSET", is_duplicate=False,
    ),

    # 5. Venice — deposit
    CleanedTransaction(
        id=5, date=date(1420, 1, 6), branch="Venice", type="deposit",
        counterparty="Contarini Family", description="Cash deposit",
        debit_account="cash", debit_amount=900, credit_account="deposits",
        credit_amount=900, currency="florin", year=1420, month=1,
        quarter="Q1", fiscal_year=1420, debit_account_type="ASSET",
        credit_account_type="LIABILITY", is_duplicate=False,
    ),

    # 6. Venice — loan repayment (includes interest)
    CleanedTransaction(
        id=6, date=date(1420, 1, 20), branch="Venice", type="loan_repayment",
        counterparty="Wool Guild", description="Partial loan repayment + interest",
        debit_account="cash", debit_amount=220, credit_account="loans_receivable",
        credit_amount=200, credit_account_2="interest_income", credit_amount_2=20,
        currency="florin", year=1420, month=1, quarter="Q1", fiscal_year=1420,
        debit_account_type="ASSET", credit_account_type="ASSET", is_duplicate=False,
    ),

    # 7. Venice — alum trade, uses the secondary credit account too
    CleanedTransaction(
        id=7, date=date(1420, 1, 22), branch="Venice", type="alum_trade",
        counterparty="Genoese Trading House", description="Alum shipment sale",
        debit_account="cash", debit_amount=340, credit_account="trading_revenue",
        credit_amount=300, credit_account_2="exchange_fee_revenue", credit_amount_2=40,
        currency="florin", year=1420, month=1, quarter="Q1", fiscal_year=1420,
        debit_account_type="ASSET", credit_account_type="REVENUE", is_duplicate=False,
    ),

    # 8. Florence — duplicate of transaction #1
    # Same (date, branch, type, counterparty, debit_amount, credit_account) as id=1
    CleanedTransaction(
        id=8, date=date(1420, 1, 5), branch="Florence", type="deposit",
        counterparty="Bardi Family", description="Cash deposit (re-entered)",
        debit_account="cash", debit_amount=500, credit_account="deposits",
        credit_amount=500, currency="florin", year=1420, month=1,
        quarter="Q1", fiscal_year=1420, debit_account_type="ASSET",
        credit_account_type="LIABILITY", is_duplicate=True,
    ),

    # 9. Venice — bill of exchange
    CleanedTransaction(
        id=9, date=date(1420, 1, 27), branch="Venice", type="bill_of_exchange",
        counterparty="Medici Rome Branch", description="Bill of exchange settlement",
        debit_account="cash", debit_amount=610, credit_account="exchange_fee_revenue",
        credit_amount=610, currency="florin", year=1420, month=1,
        quarter="Q1", fiscal_year=1420, debit_account_type="ASSET",
        credit_account_type="REVENUE", is_duplicate=False,
    ),
]

EXPECTED_FLORENCE_1420_01 = {
    "branch": "Florence", "period": "1420-01",
    "total_cash_inflows": 500, "total_cash_outflows": 1425,
    "net_cash_movement": -925, "closing_cash_balance": -925,
    "total_deposits": 500, "deposit_count": 1, "avg_deposit_size": 500,
    "total_withdrawals": 150, "withdrawal_count": 1, "avg_withdrawal_size": 150,
    "loans_issued": 1200, "loans_repaid": 0, "interest_earned": 0,
    "loan_portfolio_balance": 1200, "interest_yield": 0,
    "total_operating_expenses": 75,
    "expenses_by_category": {"wages_expense": 75},
    "expense_per_transaction": 75,
    "total_revenue": 0, "net_income": -75, "net_income_margin": None,
    "excluded_duplicate_count": 1,
}
