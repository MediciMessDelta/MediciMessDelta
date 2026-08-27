from datetime import date

import pandas as pd
import streamlit as st

from dashboard.api_client import (
    APIClientError,
    check_api_health,
    get_cashflow,
    get_kpis,
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