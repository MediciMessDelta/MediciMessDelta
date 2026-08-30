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
    login,
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

if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

st.image(
    "assets/medici_bank_logo.png",
    width=700,
)

st.markdown(
    """
    <style>
        :root {
            --medici-navy: #10233f;
            --medici-blue: #1769aa;
            --medici-gold: #b08d3c;
            --medici-bg: #f4f6f8;
            --medici-surface: #ffffff;
            --medici-text: #17212b;
            --medici-muted: #667085;
            --medici-border: #d9dee5;
        }

        .stApp {
            background-color: var(--medici-bg);
            color: var(--medici-text);
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* Main title */
        h1 {
            color: var(--medici-navy);
            font-size: 2.35rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 0.15rem;
        }

        h2 {
            color: var(--medici-navy);
            font-size: 1.45rem;
            font-weight: 650;
            border-bottom: 2px solid var(--medici-gold);
            padding-bottom: 0.45rem;
            margin-top: 2rem;
        }

        h3 {
            color: var(--medici-navy);
        }

        /* Header accent */
        .block-container > div:first-child {
            border-top: 4px solid var(--medici-navy);
            padding-top: 0.75rem;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background-color: var(--medici-surface);
            border: 1px solid var(--medici-border);
            border-left: 4px solid var(--medici-blue);
            border-radius: 0.35rem;
            padding: 1rem 1.1rem;
            box-shadow: 0 1px 3px rgba(16, 35, 63, 0.08);
        }

        [data-testid="stMetricLabel"] {
            color: var(--medici-muted);
            font-weight: 600;
        }

        [data-testid="stMetricValue"] {
            color: var(--medici-navy);
            font-weight: 700;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: var(--medici-navy);
        }

        [data-testid="stSidebar"] * {
            color: #ffffff;
        }

        [data-testid="stSidebar"] label {
            font-weight: 600;
        }

        /* Sidebar inputs */
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background-color: #ffffff;
            color: var(--medici-text);
            border-radius: 0.3rem;
        }

        [data-testid="stSidebar"] input {
            background-color: #ffffff;
            color: var(--medici-text);
        }

        /* Status messages */
        [data-testid="stAlert"] {
            border-radius: 0.35rem;
        }

        /* Tables */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--medici-border);
            border-radius: 0.35rem;
            background-color: var(--medici-surface);
        }

        /* Text inputs */
        [data-testid="stTextInput"] input {
            background-color: #ffffff;
            color: var(--medici-text);
            border: 1px solid var(--medici-border);
            border-radius: 0.35rem;
        }

        [data-testid="stTextInput"] input::placeholder {
            color: var(--medici-muted);
            opacity: 1;
        }

        [data-testid="stTextInput"] input:focus {
            border-color: var(--medici-blue);
            box-shadow: 0 0 0 1px var(--medici-blue);
        }

        [data-testid="stTextInput"] input:focus {
            border-color: var(--medici-blue);
            box-shadow: 0 0 0 1px var(--medici-blue);
        }

        /* Caption text */
        .stCaption {
            color: var(--medici-muted);
        }

        /* Horizontal spacing between sections */
        div[data-testid="stVerticalBlock"] > div {
            gap: 0.65rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
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
    username,
):
    return get_transactions(
        branch=branch,
        start=start,
        end=end,
        page=page,
        per_page=per_page,
        username=username
    )

@st.cache_data(ttl=60)
def load_kpis(branch, start, end, username):
    return get_kpis(
        branch=branch,
        start=start,
        end=end,
        username=username
    )


def load_cashflow(
    branch,
    start,
    end,
    username,
    granularity="monthly",
):
    return get_cashflow(
        branch=branch,
        start=start,
        end=end,
        granularity=granularity,
        username=username
    )

@st.cache_data(ttl=60)
def load_loans(branch, start, end, username, status=None,):
    return get_loans(
        branch=branch,
        start=start,
        end=end,
        status=status,
        username=username
    )


@st.cache_data(ttl=60)
def load_expenses(branch, start, end, username):
    return get_expenses(
        branch=branch,
        start=start,
        end=end,
        username=username
    )


@st.cache_data(ttl=60)
def load_alerts(
    branch,
    start=None,
    end=None,
    severity=None,
    status=None,
    username=None
):
    return get_alerts(
        branch=branch,
        start=start,
        end=end,
        severity=severity,
        status=status,
        username=username
    )

@st.cache_data(ttl=60)
def load_bills(branch, start, end, username):
    return get_transactions(
        branch=branch,
        start=start,
        end=end,
        page=1,
        per_page=100,
        transaction_type="bill_of_exchange",
        username=username
    )

def filter_transactions(transactions_df, search_term):
    if transactions_df.empty or not search_term:
        return transactions_df

    search_term = search_term.casefold()

    searchable_columns = [
        "id",
        "counterparty",
        "description",
        "debit_account",
        "credit_account",
        "type",
    ]

    existing_columns = [
        column
        for column in searchable_columns
        if column in transactions_df.columns
    ]

    search_mask = transactions_df[
        existing_columns
    ].astype(str).apply(
        lambda column: column.str.casefold().str.contains(
            search_term,
            na=False,
        )
    ).any(axis=1)

    return transactions_df[search_mask]


def main():
    user = st.session_state.authenticated_user

    if user is None:
        st.subheader("Medici Bank Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input(
                "Password",
                type="password",
            )
            submitted = st.form_submit_button("Sign In")

        if submitted:
            try:
                login_result = login(
                    username=username,
                    password=password,
                )

                st.session_state.authenticated_user = (
                    login_result["user"]
                )
                st.rerun()

            except APIClientError:
                st.error("Invalid username or password.")

        st.stop()

    username = user["username"]

    st.caption(
        "Operations & Financial Intelligence Dashboard"
    )

    st.markdown(
        "Historical banking operations, financial performance, "
        "loan activity, expenses, alerts, and transaction intelligence "
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

    st.sidebar.markdown(
        "## MEDICI BANK"
    )

    st.sidebar.markdown(
        "### Dashboard Controls"
    )

    st.sidebar.caption(
        "Branch and date filters apply across the dashboard."
    )

    user = st.session_state.authenticated_user
    username = user["username"]
    role = user["role"]

    if role == "MANAGING_DIRECTOR":
        available_branches = ["All Branches"] + BRANCHES
    else:
        available_branches = [user["branch"]]

    selected_branch = st.sidebar.selectbox(
        "Select a branch",
        available_branches,
    )

    st.sidebar.markdown(
        f"**Signed in:** {user['username']}"
    )

    st.sidebar.caption(
        f"Role: {role.replace('_', ' ').title()}"
    )

    if st.sidebar.button("Sign Out"):
        st.session_state.authenticated_user = None
        st.rerun()

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
        username=username,
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
                username=username
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
                username=username
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
            branch=selected_branch,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            username=username
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
                    width="stretch",
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
                username=username
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
                        width="stretch",
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
                username=username
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
                    width="stretch",
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
                username=username
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
                    width="stretch",
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

    st.subheader("Transaction Ledger")

    search_term = st.text_input(
        "Search transactions",
        placeholder=(
            "Search by transaction ID, counterparty, "
            "description, account, or type..."
        ),
    )

    ledger_df = filter_transactions(
        transactions_df,
        search_term,
    )

    if search_term:
        st.caption(
            f"Showing {len(ledger_df):,} transactions "
            f"matching '{search_term}'."
        )
    else:
        st.caption(
            f"Showing {len(ledger_df):,} transactions "
            "from the selected filters."
        )

    if ledger_df.empty:
        st.warning(
            "No transactions match the selected filters."
        )

    else:
        st.dataframe(
            ledger_df,
            width="stretch",
            hide_index=True,
        )


if __name__ == "__main__":
    main()
