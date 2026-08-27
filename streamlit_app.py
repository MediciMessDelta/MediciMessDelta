from datetime import date

import pandas as pd
import streamlit as st

from dashboard.api_client import (
    APIClientError,
    check_api_health,
    get_alerts,
    get_cashflow,
    get_expenses,
    get_kpis,
    get_loans,
    get_transactions,
)

BRANCHES = [
    "Avignon",
    "Bruges",
    "Constance",
    "Florence",
    "Geneva",
    "London",
    "Milan",
    "Rome",
    "Venice",
]

EARLIEST_DATE = date(1390, 1, 1)
LATEST_DATE = date(1440, 12, 31)


st.set_page_config(
    page_title="Medici Bank Operations",
    page_icon="🏦",
    layout="wide",
)


@st.cache_data(ttl=30)
def load_api_health():
    return check_api_health()


@st.cache_data(ttl=60)
def load_transaction_page(
    branch,
    start,
    end,
    page,
    per_page,
):
    return get_transactions(
        branch=branch,
        start=start,
        end=end,
        page=page,
        per_page=per_page,
    )

@st.cache_data(ttl=60)
def load_kpis(branch, start, end):
    return get_kpis(
        branch=branch,
        start=start,
        end=end,
    )


def load_cashflow(
    branch,
    start,
    end,
    granularity="monthly",
):
    return get_cashflow(
        branch=branch,
        start=start,
        end=end,
        granularity=granularity,
    )

@st.cache_data(ttl=60)
def load_loans(branch, status=None):
    return get_loans(
        branch=branch,
        status=status,
    )


@st.cache_data(ttl=60)
def load_expenses(branch, start, end):
    return get_expenses(
        branch=branch,
        start=start,
        end=end,
    )


@st.cache_data(ttl=60)
def load_alerts(
    branch,
    start=None,
    end=None,
    severity=None,
    status=None,
):
    return get_alerts(
        branch=branch,
        start=start,
        end=end,
        severity=severity,
        status=status,
    )

@st.cache_data(ttl=60)
def load_bills(branch, start, end):
    return get_transactions(
        branch=branch,
        start=start,
        end=end,
        page=1,
        per_page=100,
        transaction_type="bill_of_exchange",
    )


st.title("Medici Bank Operations Dashboard")

st.write(
    "Explore historical Medici Bank transactions "
    "from 1390 through 1440."
)


try:
    health_data = load_api_health()

except APIClientError:
    st.error(
        "The MediciMess API is unavailable. "
        "Start it with: python -m api.app"
    )
    st.stop()


if health_data["status"] != "healthy":
    st.error("The MediciMess API reported an unhealthy status.")
    st.stop()


st.success("Connected to the MediciMess API.")

st.sidebar.header("Dashboard Filters")

selected_branch = st.sidebar.selectbox(
    "Select a branch",
    ["All Branches"] + BRANCHES,
)

start_date = st.sidebar.date_input(
    "Start date",
    value=EARLIEST_DATE,
    min_value=EARLIEST_DATE,
    max_value=LATEST_DATE,
)

end_date = st.sidebar.date_input(
    "End date",
    value=LATEST_DATE,
    min_value=EARLIEST_DATE,
    max_value=LATEST_DATE,
)

if start_date > end_date:
    st.sidebar.error(
        "Start date must be before the end date."
    )
    st.stop()


try:
    transaction_result = load_transaction_page(
        branch=selected_branch,
        start=start_date,
        end=end_date,
        page=1,
        per_page=100,
    )

except APIClientError:
    st.error(
        "The transaction data could not be loaded "
        "from the API."
    )
    st.stop()


transactions = transaction_result["transactions"]
transactions_df = pd.DataFrame(transactions)

if not transactions_df.empty:
    transactions_df["date"] = pd.to_datetime(
        transactions_df["date"]
    )


total_transactions = transaction_result[
    "total_transactions"
]

st.info(
    f"Found {total_transactions:,} transactions "
    f"for {selected_branch} "
    f"from {start_date} through {end_date}."
)

st.subheader("Dataset Overview")

overview_column_1, overview_column_2, overview_column_3 = (
    st.columns(3)
)

overview_column_1.metric(
    "Matching Transactions",
    f"{total_transactions:,}",
)

overview_column_2.metric(
    "Rows Displayed",
    f"{len(transactions_df):,}",
)

overview_column_3.metric(
    "Total Pages",
    f"{transaction_result['total_pages']:,}",
)

if selected_branch != "All Branches":
    try:
        kpi_result = load_kpis(
            branch=selected_branch,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )

        kpis = kpi_result["kpis"]

        st.subheader("Branch Performance")

        kpi_column_1, kpi_column_2, kpi_column_3, kpi_column_4 = (
            st.columns(4)
        )

        kpi_column_1.metric(
            "Cash Position",
            f"${float(kpis['cash_position']['closing_balance']):,.2f}",
        )

        kpi_column_2.metric(
            "Revenue",
            f"${float(kpis['revenue']['total']):,.2f}",
        )

        kpi_column_3.metric(
            "Operating Expenses",
            f"${float(kpis['operating_expenses']['total']):,.2f}",
        )

        kpi_column_4.metric(
            "Net Income",
            f"${float(kpis['net_income']['total']):,.2f}",
        )

        kpi_column_5, kpi_column_6, kpi_column_7, kpi_column_8 = (
            st.columns(4)
        )

        kpi_column_5.metric(
            "Deposits",
            f"${float(kpis['deposits']['total']):,.2f}",
        )

        kpi_column_6.metric(
            "Withdrawals",
            f"${float(kpis['withdrawals']['total']):,.2f}",
        )

        kpi_column_7.metric(
            "Loans Issued",
            f"${float(kpis['loans']['issued']):,.2f}",
        )

        kpi_column_8.metric(
            "Loans Repaid",
            f"${float(kpis['loans']['repaid']):,.2f}",
        )

    except APIClientError:
        st.error(
            "KPI data could not be loaded from the API."
        )

    try:
        cashflow_result = load_cashflow(
            branch=selected_branch,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            granularity="monthly",
        )

        cashflow_df = pd.DataFrame(
            cashflow_result["time_series"]
        )

        if not cashflow_df.empty:
            cashflow_df["inflows"] = pd.to_numeric(
                cashflow_df["inflows"]
            )

            cashflow_df["outflows"] = pd.to_numeric(
                cashflow_df["outflows"]
            )

            cashflow_df["net_movement"] = pd.to_numeric(
                cashflow_df["net_movement"]
            )

            st.subheader("Monthly Cash Flow")

            chart_df = cashflow_df.set_index("period")[
                ["inflows", "outflows", "net_movement"]
            ]

            st.line_chart(chart_df)

        else:
            st.info(
                "No cash-flow data is available "
                "for the selected filters."
            )

    except APIClientError:
        st.error(
            "Cash-flow data could not be loaded "
            "from the API."
        )

    try:
        loans_result = load_loans(
            branch=selected_branch
        )

        loans = loans_result["loans"]

        st.subheader("Loan Portfolio")

        if loans:
            loans_df = pd.DataFrame(loans)

            loans_df["original_principal"] = pd.to_numeric(
                loans_df["original_principal"]
            )

            loans_df["outstanding_balance"] = pd.to_numeric(
                loans_df["outstanding_balance"]
            )

            loans_df["interest_rate"] = (
                pd.to_numeric(loans_df["interest_rate"]) * 100
            )

            loan_column_1, loan_column_2, loan_column_3 = (
                st.columns(3)
            )

            total_outstanding = loans_df[
                "outstanding_balance"
            ].sum()

            open_loans = loans_df[
                loans_df["status"] == "OPEN"
            ]

            overdue_loans = loans_df[
                loans_df["status"] == "OVERDUE"
            ]

            loan_column_1.metric(
                "Total Outstanding",
                f"${total_outstanding:,.2f}",
            )

            loan_column_2.metric(
                "Open Loans",
                f"{len(open_loans):,}",
            )

            loan_column_3.metric(
                "Overdue Loans",
                f"{len(overdue_loans):,}",
            )

            loans_df["interest_rate"] = (
                loans_df["interest_rate"].map(
                    lambda value: f"{value:.1f}%"
                )
            )

            loans_df["original_principal"] = (
                loans_df["original_principal"].map(
                    lambda value: f"${value:,.2f}"
                )
            )

            loans_df["outstanding_balance"] = (
                loans_df["outstanding_balance"].map(
                    lambda value: f"${value:,.2f}"
                )
            )

            st.dataframe(
                loans_df[
                    [
                        "loan_id",
                        "counterparty",
                        "original_principal",
                        "outstanding_balance",
                        "interest_rate",
                        "issued_date",
                        "due_date",
                        "status",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.info(
                "No loans are available "
                "for the selected branch."
            )

    except APIClientError:
        st.error(
            "Loan portfolio data could not be loaded "
            "from the API."
        )
    try:
        expenses_result = load_expenses(
            branch=selected_branch,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )

        expense_breakdown = expenses_result[
            "expense_breakdown"
        ]

        st.subheader("Expense Breakdown")

        total_expenses = float(
            expense_breakdown["total_expenses"]
        )

        st.metric(
            "Total Expenses",
            f"${total_expenses:,.2f}",
        )

        categories = expense_breakdown["categories"]

        if categories:
            expenses_df = pd.DataFrame(categories)

            expenses_df["total_amount"] = pd.to_numeric(
                expenses_df["total_amount"]
            )

            expenses_df["percentage_of_expenses"] = (
                pd.to_numeric(
                    expenses_df["percentage_of_expenses"]
                ) * 100
            )

            expense_column_1, expense_column_2 = st.columns(2)

            with expense_column_1:
                st.dataframe(
                    expenses_df[
                        [
                            "category",
                            "total_amount",
                            "percentage_of_expenses",
                            "transaction_count",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            with expense_column_2:
                chart_df = expenses_df.set_index(
                    "category"
                )["total_amount"]

                st.bar_chart(chart_df)

        else:
            st.info(
                "No expense data is available "
                "for the selected filters."
            )

    except APIClientError:
        st.error(
            "Expense data could not be loaded "
            "from the API."
        )

    try:
        alerts_result = load_alerts(
            branch=selected_branch,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )

        alerts = alerts_result["alerts"]

        st.subheader("Alerts")

        if alerts:
            alerts_df = pd.DataFrame(alerts)

            high_alerts = alerts_df[
                alerts_df["severity"] == "HIGH"
            ]

            open_alerts = alerts_df[
                alerts_df["status"] == "OPEN"
            ]

            alert_column_1, alert_column_2, alert_column_3 = (
                st.columns(3)
            )

            alert_column_1.metric(
                "Total Alerts",
                f"{len(alerts_df):,}",
            )

            alert_column_2.metric(
                "High Severity",
                f"{len(high_alerts):,}",
            )

            alert_column_3.metric(
                "Open Alerts",
                f"{len(open_alerts):,}",
            )

            st.dataframe(
                alerts_df[
                    [
                        "alert_id",
                        "date",
                        "severity",
                        "status",
                        "counterparty",
                        "description",
                        "rule_code",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.success(
                "No alerts were found "
                "for the selected filters."
            )

    except APIClientError:
        st.error(
            "Alert data could not be loaded "
            "from the API."
        )

    try:
        bills_result = load_bills(
            branch=selected_branch,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )

        bills = bills_result["transactions"]

        st.subheader("Bills of Exchange")

        if bills:
            bills_df = pd.DataFrame(bills)

            bills_df["debit_amount"] = pd.to_numeric(
                bills_df["debit_amount"]
            )

            bills_df["credit_amount"] = pd.to_numeric(
                bills_df["credit_amount"]
            )

            bills_df["credit_amount_2"] = pd.to_numeric(
                bills_df["credit_amount_2"]
            )

            total_bill_value = bills_df[
                "debit_amount"
            ].sum()

            total_exchange_fees = bills_df[
                "credit_amount_2"
            ].sum()

            bill_column_1, bill_column_2, bill_column_3 = (
                st.columns(3)
            )

            bill_column_1.metric(
                "Bills of Exchange",
                f"{len(bills_df):,}",
            )

            bill_column_2.metric(
                "Total Bill Value",
                f"${total_bill_value:,.2f}",
            )

            bill_column_3.metric(
                "Exchange Fee Revenue",
                f"${total_exchange_fees:,.2f}",
            )

            bills_display_df = bills_df.copy()

            bills_display_df["debit_amount"] = (
                bills_display_df["debit_amount"].map(
                    lambda value: f"{value:,.2f}"
                )
            )

            bills_display_df["credit_amount"] = (
                bills_display_df["credit_amount"].map(
                    lambda value: f"{value:,.2f}"
                )
            )

            bills_display_df["credit_amount_2"] = (
                bills_display_df["credit_amount_2"].map(
                    lambda value: f"{value:,.2f}"
                )
            )

            st.dataframe(
                bills_display_df[
                    [
                        "id",
                        "date",
                        "counterparty",
                        "debit_account",
                        "debit_amount",
                        "credit_amount",
                        "credit_amount_2",
                        "currency",
                        "description",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.info(
                "No bills of exchange are available "
                "for the selected filters."
            )

    except APIClientError:
        st.error(
            "Bills of exchange data could not be loaded "
            "from the API."
        )

st.subheader("Transaction Preview")

if transactions_df.empty:
    st.warning(
        "No transactions match the selected filters."
    )

else:
    st.caption(
        "Showing the first 100 matching transactions. "
        "Interactive pagination will be added next."
    )

    st.dataframe(
        transactions_df,
        use_container_width=True,
        hide_index=True,
    )