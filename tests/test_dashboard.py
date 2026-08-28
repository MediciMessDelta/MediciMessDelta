import pandas as pd

from streamlit_app import filter_transactions


def make_transactions():
    return pd.DataFrame(
        [
            {
                "id": "TX-001",
                "counterparty": "Florentine Wool Guild",
                "description": "Wool purchase",
                "debit_account": "Inventory",
                "credit_account": "Cash",
                "type": "purchase",
            },
            {
                "id": "TX-002",
                "counterparty": "Republic of Florence",
                "description": "Tax payment",
                "debit_account": "Taxes",
                "credit_account": "Cash",
                "type": "expense",
            },
            {
                "id": "TX-003",
                "counterparty": "Venetian Merchant",
                "description": "Silk shipment",
                "debit_account": "Inventory",
                "credit_account": "Payables",
                "type": "purchase",
            },
        ]
    )


def test_empty_search_returns_all_transactions():
    transactions = make_transactions()

    result = filter_transactions(transactions, "")

    assert len(result) == 3


def test_search_matches_counterparty():
    transactions = make_transactions()

    result = filter_transactions(
        transactions,
        "Florentine Wool Guild",
    )

    assert len(result) == 1
    assert result.iloc[0]["id"] == "TX-001"


def test_search_matches_description():
    transactions = make_transactions()

    result = filter_transactions(
        transactions,
        "tax payment",
    )

    assert len(result) == 1
    assert result.iloc[0]["id"] == "TX-002"


def test_search_matches_account():
    transactions = make_transactions()

    result = filter_transactions(
        transactions,
        "payables",
    )

    assert len(result) == 1
    assert result.iloc[0]["id"] == "TX-003"


def test_search_is_case_insensitive():
    transactions = make_transactions()

    result = filter_transactions(
        transactions,
        "VENETIAN",
    )

    assert len(result) == 1
    assert result.iloc[0]["id"] == "TX-003"


def test_search_with_no_match_returns_empty_dataframe():
    transactions = make_transactions()

    result = filter_transactions(
        transactions,
        "does-not-exist",
    )

    assert result.empty


def test_empty_dataframe_stays_empty():
    transactions = pd.DataFrame()

    result = filter_transactions(
        transactions,
        "anything",
    )

    assert result.empty
