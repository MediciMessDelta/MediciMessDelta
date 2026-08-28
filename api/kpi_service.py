from datetime import datetime
from functools import lru_cache

from medici.ingestion.dedup import flag_duplicates
from medici.ingestion.loaders import load_csv
from medici.ingestion.validation import validate_all_rows
from medici.transform.clean import to_cleaned_transactions
from medici.transform.kpis import compute_kpis


def _load_cleaned_transactions():
    rows = load_csv("medici_transactions.csv")
    cleaned_rows, _rejected = validate_all_rows(rows)
    cleaned_rows = flag_duplicates(cleaned_rows)

    return to_cleaned_transactions(cleaned_rows)


def _periods_between(start, end):
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")

    periods = []

    year = start_date.year
    month = start_date.month

    while (year, month) <= (end_date.year, end_date.month):
        periods.append(f"{year}-{month:02d}")

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    return periods


def _sum_decimal(results, key):
    return sum(
        (getattr(result, key) for result in results),
        getattr(results[0], key).__class__("0"),
    )

@lru_cache(maxsize=64)
def get_kpi_summary(branch, start, end):
    cleaned_transactions = _load_cleaned_transactions()

    periods = _periods_between(start, end)

    monthly_results = []

    for period in periods:
        try:
            result = compute_kpis(
                branch,
                period,
                cleaned_transactions,
            )
        except ValueError:
            continue

        monthly_results.append(result)

    if not monthly_results:
        raise ValueError(
            "No KPI data found for branch={!r} "
            "between {!r} and {!r}".format(
                branch,
                start,
                end,
            )
        )

    cash_position = {
        "inflows": _sum_decimal(
            monthly_results,
            "total_cash_inflows",
        ),
        "outflows": _sum_decimal(
            monthly_results,
            "total_cash_outflows",
        ),
        "net_movement": _sum_decimal(
            monthly_results,
            "net_cash_movement",
        ),
        "closing_balance": monthly_results[-1].closing_cash_balance,
    }

    deposits = {
        "total": _sum_decimal(
            monthly_results,
            "total_deposits",
        ),
        "average": (
            _sum_decimal(
                monthly_results,
                "total_deposits",
            )
            / _sum_decimal(
                monthly_results,
                "deposit_count",
            )
            if _sum_decimal(monthly_results, "deposit_count")
            else 0
        ),
    }

    withdrawals = {
        "total": _sum_decimal(
            monthly_results,
            "total_withdrawals",
        ),
        "average": (
            _sum_decimal(
                monthly_results,
                "total_withdrawals",
            )
            / _sum_decimal(
                monthly_results,
                "withdrawal_count",
            )
            if _sum_decimal(monthly_results, "withdrawal_count")
            else 0
        ),
    }

    loans = {
        "issued": _sum_decimal(
            monthly_results,
            "loans_issued",
        ),
        "repaid": _sum_decimal(
            monthly_results,
            "loans_repaid",
        ),
        "interest_earned": _sum_decimal(
            monthly_results,
            "interest_earned",
        ),
        "yield": (
            float(
                _sum_decimal(
                    monthly_results,
                    "interest_earned",
                )
                / _sum_decimal(
                    monthly_results,
                    "loans_repaid",
                )
            )
            if _sum_decimal(monthly_results, "loans_repaid")
            else 0.0
        ),
    }

    operating_expenses = {
        "total": _sum_decimal(
            monthly_results,
            "total_operating_expenses",
        ),
    }

    revenue = {
        "total": _sum_decimal(
            monthly_results,
            "total_revenue",
        ),
    }

    net_income_total = _sum_decimal(
        monthly_results,
        "net_income",
    )

    revenue_total = revenue["total"]

    net_income = {
        "total": net_income_total,
        "margin": (
            float(net_income_total / revenue_total)
            if revenue_total
            else None
        ),
    }

    return {
        "branch": branch,
        "period": {
            "start": start,
            "end": end,
        },
        "data_source": "development_fixture",
        "kpis": {
            "cash_position": cash_position,
            "deposits": deposits,
            "withdrawals": withdrawals,
            "loans": loans,
            "operating_expenses": operating_expenses,
            "revenue": revenue,
            "net_income": net_income,
        },
    }
