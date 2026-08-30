from datetime import date

from medici.contracts import CleanedTransaction


def test_cleaned_transaction_accepts_valid_data():
    t = CleanedTransaction(
        id=1, date=date(1420, 1, 5), branch="Florence", type="deposit",
        counterparty="Bardi Family", description="test",
        debit_account="cash", debit_amount=100, credit_account="deposits",
        credit_amount=100, currency="florin", year=1420, month=1,
        quarter="Q1", fiscal_year=1420, debit_account_type="ASSET",
        credit_account_type="LIABILITY", is_duplicate=False,
    )
    assert t.id == 1