import pandas as pd
import streamlit as st


st.title("Medici Bank Operations Dashboard")

st.write(
    "Explore historical Medici Bank transactions from 1390 through 1440."
)


@st.cache_data
def load_data():
    transactions = pd.read_csv(
        "medici_transactions.csv",
        parse_dates=["date"]
    )

    return transactions


df = load_data()
st.sidebar.header("Dashboard Filters")
branches = sorted(df["branch"].unique())

selected_branch = st.sidebar.selectbox(
    "Select a branch",
    ["All Branches"] + branches
)
earliest_date = df["date"].min().date()
latest_date = df["date"].max().date()

start_date = st.sidebar.date_input(
    "Start date",
    value=earliest_date,
    min_value=earliest_date,
    max_value=latest_date
)

end_date = st.sidebar.date_input(
    "End date",
    value=latest_date,
    min_value=earliest_date,
    max_value=latest_date
)
if start_date > end_date:
    st.sidebar.error("Start date must be before the end date.")
    st.stop()

filtered_df = df[
    (df["date"] >= pd.Timestamp(start_date))
    & (df["date"] <= pd.Timestamp(end_date))
].copy()
if selected_branch != "All Branches":
    filtered_df = filtered_df[
        filtered_df["branch"] == selected_branch
    ].copy()
st.info(
    f"Showing {len(filtered_df):,} transactions "
    f"for {selected_branch} "
    f"from {start_date} through {end_date}."
)    

st.success("Transaction data loaded successfully!")

st.subheader("Dataset Overview")

st.write("Total transactions:", len(df))
st.write("Total columns:", len(df.columns))
st.write("Earliest transaction:", df["date"].min().date())
st.write("Latest transaction:", df["date"].max().date())

st.subheader("Transaction Preview")

st.dataframe(
    filtered_df.head(100),
    use_container_width=True
)