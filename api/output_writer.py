import csv
import json
from pathlib import Path

from api.alert_service import get_alerts
from api.cashflow_service import get_cashflow
from api.expense_service import get_expense_breakdown
from api.kpi_service import get_kpi_summary
from api.loan_service import get_loan_portfolio

DEFAULT_OUTPUT_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "serving_outputs"
)


def create_branch_slug(branch):
    return (
        branch
        .strip()
        .casefold()
        .replace(" ", "_")
    )


def write_json_file(file_path, data):
    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as output_file:
        json.dump(
            data,
            output_file,
            indent=2
        )


def write_expense_csv(file_path, expense_result):
    categories = (
        expense_result["expense_breakdown"]
        ["categories"]
    )

    fieldnames = [
        "category",
        "counterparty",
        "transaction_count",
        "total_amount",
        "percentage_of_expenses"
    ]

    with open(
        file_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for category in categories:
            for counterparty in category["counterparties"]:
                writer.writerow(
                    {
                        "category": category["category"],
                        "counterparty": (
                            counterparty["name"]
                        ),
                        "transaction_count": (
                            counterparty[
                                "transaction_count"
                            ]
                        ),
                        "total_amount": (
                            counterparty["total_amount"]
                        ),
                        "percentage_of_expenses": (
                            category[
                                "percentage_of_expenses"
                            ]
                        )
                    }
                )


def write_loan_csv(file_path, loan_result):
    loans = loan_result["loans"]

    fieldnames = [
        "loan_id",
        "counterparty",
        "issued_date",
        "due_date",
        "original_principal",
        "outstanding_balance",
        "interest_rate",
        "status"
    ]

    with open(
        file_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for loan in loans:
            writer.writerow(loan)


def generate_serving_outputs(
    branch,
    start,
    end,
    output_directory=None
):
    if output_directory is None:
        output_directory = DEFAULT_OUTPUT_DIRECTORY
    else:
        output_directory = Path(output_directory)

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    branch_slug = create_branch_slug(branch)
    period_slug = f"{start}_to_{end}"

    kpi_result = get_kpi_summary(
        branch=branch,
        start=start,
        end=end
    )

    cashflow_result = get_cashflow(
        branch=branch,
        start=start,
        end=end,
        granularity="monthly"
    )

    alert_result = get_alerts(
        branch=branch,
        start=start,
        end=end
    )

    expense_result = get_expense_breakdown(
        branch=branch,
        start=start,
        end=end
    )

    loan_result = get_loan_portfolio(
        branch=branch
    )

    output_paths = {
        "metrics": (
            output_directory
            / (
                f"metrics_{branch_slug}_"
                f"{period_slug}.json"
            )
        ),
        "time_series": (
            output_directory
            / f"time_series_{branch_slug}.json"
        ),
        "alerts": (
            output_directory
            / (
                f"alerts_{branch_slug}_"
                f"{period_slug}.json"
            )
        ),
        "expenses": (
            output_directory
            / (
                f"expense_breakdown_{branch_slug}_"
                f"{period_slug}.csv"
            )
        ),
        "loans": (
            output_directory
            / (
                f"loan_portfolio_{branch_slug}_"
                f"{period_slug}.csv"
            )
        )
    }

    write_json_file(
        output_paths["metrics"],
        kpi_result
    )

    write_json_file(
        output_paths["time_series"],
        cashflow_result
    )

    write_json_file(
        output_paths["alerts"],
        alert_result
    )

    write_expense_csv(
        output_paths["expenses"],
        expense_result
    )

    write_loan_csv(
        output_paths["loans"],
        loan_result
    )

    return output_paths