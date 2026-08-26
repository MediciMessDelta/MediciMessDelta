from functools import lru_cache
from pathlib import Path

import pandas as pd


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "medici_transactions.csv"
)


@lru_cache(maxsize=1)
def load_transactions():
    transactions = pd.read_csv(
        DATA_FILE,
        parse_dates=["date"]
    )

    return transactions


def get_transaction_page(
    page,
    per_page,
    branch=None,
    start=None,
    end=None,
    transaction_type=None
):
    transactions = load_transactions()

    filtered_transactions = transactions
    if branch:
            filtered_transactions = filtered_transactions[
                filtered_transactions["branch"].str.casefold()
                == branch.casefold()
            ]

    if start:
        filtered_transactions = filtered_transactions[
            filtered_transactions["date"]
            >= pd.Timestamp(start)
        ]

    if end:
        filtered_transactions = filtered_transactions[
            filtered_transactions["date"]
            <= pd.Timestamp(end)
        ]

    if transaction_type:
        filtered_transactions = filtered_transactions[
            filtered_transactions["type"].str.casefold()
            == transaction_type.casefold()
        ]

    filtered_transactions = (
        filtered_transactions
        .sort_values(["date", "id"])
        .reset_index(drop=True)
    )

    start_position = (page - 1) * per_page
    end_position = start_position + per_page

    page_data = filtered_transactions.iloc[
        start_position:end_position
    ].copy()

    page_data["date"] = page_data["date"].dt.strftime(
        "%Y-%m-%d"
    )

    page_data = page_data.astype(object).where(
        pd.notnull(page_data),
        None
    )

    total_transactions = len(filtered_transactions)

    total_pages = (
        total_transactions + per_page - 1
    ) // per_page

    return {
        "transactions": page_data.to_dict(
            orient="records"
        ),
        "page": page,
        "per_page": per_page,
        "total_transactions": total_transactions,
        "total_pages": total_pages,
        "filters": {
            "branch": branch,
            "start": start,
            "end": end,
            "type": transaction_type
        }
    }