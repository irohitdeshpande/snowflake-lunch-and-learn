import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Campaign Effectiveness Dashboard", layout="wide")
st.title("Campaign Effectiveness by Country")

session = get_active_session()

df = session.sql("SELECT TYPE, COUNTRY, CITY, EFFECTIVENESS FROM MARKETING.PUBLIC.CAMPAIGN").to_pandas()

st.sidebar.header("Filters")
selected_types = st.sidebar.multiselect("Campaign Type", options=df["TYPE"].unique(), default=df["TYPE"].unique())
selected_countries = st.sidebar.multiselect("Country", options=df["COUNTRY"].unique(), default=df["COUNTRY"].unique())

filtered_df = df[(df["TYPE"].isin(selected_types)) & (df["COUNTRY"].isin(selected_countries))]

st.subheader("Average Effectiveness by Country")
avg_by_country = filtered_df.groupby("COUNTRY")["EFFECTIVENESS"].mean().reset_index()
avg_by_country.columns = ["Country", "Avg Effectiveness (%)"]
st.bar_chart(avg_by_country, x="Country", y="Avg Effectiveness (%)")

st.subheader("Average Effectiveness by Country and Type")
avg_by_country_type = filtered_df.groupby(["COUNTRY", "TYPE"])["EFFECTIVENESS"].mean().reset_index()
pivot_df = avg_by_country_type.pivot(index="COUNTRY", columns="TYPE", values="EFFECTIVENESS").fillna(0)
st.bar_chart(pivot_df)

st.subheader("Average Effectiveness by City")
avg_by_city = filtered_df.groupby(["COUNTRY", "CITY"])["EFFECTIVENESS"].mean().reset_index()
avg_by_city.columns = ["Country", "City", "Avg Effectiveness (%)"]
st.bar_chart(avg_by_city, x="City", y="Avg Effectiveness (%)", color="Country")

st.subheader("Raw Data")
st.dataframe(filtered_df, use_container_width=True)
