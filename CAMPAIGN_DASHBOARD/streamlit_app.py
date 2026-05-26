import streamlit as st
import pandas as pd
import plotly.express as px
from snowflake.snowpark.context import get_active_session

st.set_page_config(
    page_title="Campaign effectiveness dashboard",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, .stMetric, .stSidebar {
    font-family: 'Inter', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

session = get_active_session()

@st.cache_data
def load_data():
    return session.sql("SELECT TYPE, COUNTRY, CITY, EFFECTIVENESS FROM MARKETING.PUBLIC.CAMPAIGN").to_pandas()

st.title("Campaign effectiveness dashboard")

st.sidebar.header("Filters")
df_all = load_data()
selected_types = st.sidebar.multiselect("Campaign type", options=sorted(df_all["TYPE"].unique()), default=sorted(df_all["TYPE"].unique()))
selected_countries = st.sidebar.multiselect("Country", options=sorted(df_all["COUNTRY"].unique()), default=sorted(df_all["COUNTRY"].unique()))
st.sidebar.button("Refresh data", on_click=load_data.clear)

df = df_all[df_all["TYPE"].isin(selected_types) & df_all["COUNTRY"].isin(selected_countries)]

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif"),
    margin=dict(l=10, r=10, t=36, b=10),
)
GRID = dict(showgrid=True, gridcolor="rgba(128,128,128,0.12)", zeroline=False)
NO_GRID = dict(showgrid=False, zeroline=False)

total = len(df)
avg_eff = df["EFFECTIVENESS"].mean() if total > 0 else 0
median_eff = df["EFFECTIVENESS"].median() if total > 0 else 0
best_country = df.groupby("COUNTRY")["EFFECTIVENESS"].mean().idxmax() if total > 0 else "N/A"
best_type = df.groupby("TYPE")["EFFECTIVENESS"].mean().idxmax() if total > 0 else "N/A"
top_city = df.groupby("CITY")["EFFECTIVENESS"].mean().idxmax() if total > 0 else "N/A"

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total campaigns", total)
k2.metric("Avg effectiveness", f"{avg_eff:.1f}%")
k3.metric("Median effectiveness", f"{median_eff:.1f}%")
k4.metric("Top country", best_country)
k5.metric("Top type", best_type)
k6.metric("Top city", top_city)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Avg effectiveness by country")
    avg_country = (
        df.groupby("COUNTRY")["EFFECTIVENESS"]
        .agg(avg="mean", campaigns="count", std="std")
        .reset_index().sort_values("avg", ascending=False)
    )
    fig = px.bar(
        avg_country, x="COUNTRY", y="avg",
        color="avg", color_continuous_scale="Blues", text="avg",
        hover_data={"campaigns": True, "std": ":.1f", "avg": ":.1f"},
        labels={"COUNTRY": "Country", "avg": "Avg effectiveness (%)", "campaigns": "Campaigns", "std": "Std dev"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(**LAYOUT, coloraxis_showscale=False, xaxis_tickangle=-30)
    fig.update_xaxes(**NO_GRID)
    fig.update_yaxes(**GRID)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Effectiveness distribution by type")
    fig = px.box(
        df, x="TYPE", y="EFFECTIVENESS", color="TYPE",
        points="outliers", hover_data=["COUNTRY", "CITY"],
        labels={"TYPE": "Campaign type", "EFFECTIVENESS": "Effectiveness (%)", "COUNTRY": "Country", "CITY": "City"},
    )
    fig.update_layout(**LAYOUT, showlegend=False, xaxis_tickangle=-20)
    fig.update_xaxes(**NO_GRID)
    fig.update_yaxes(**GRID)
    st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Avg effectiveness by country & type")
    avg_ct = df.groupby(["COUNTRY", "TYPE"])["EFFECTIVENESS"].mean().reset_index()
    avg_ct.columns = ["Country", "Type", "Avg effectiveness"]
    fig = px.bar(
        avg_ct, x="Country", y="Avg effectiveness", color="Type",
        barmode="group", hover_data={"Avg effectiveness": ":.1f"},
        labels={"Avg effectiveness": "Avg effectiveness (%)"},
    )
    fig.update_layout(**LAYOUT, xaxis_tickangle=-30,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(**NO_GRID)
    fig.update_yaxes(**GRID)
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader("Effectiveness heatmap (Country × Type)")
    pivot = df.groupby(["COUNTRY", "TYPE"])["EFFECTIVENESS"].mean().unstack(fill_value=0)
    fig = px.imshow(pivot, text_auto=".1f", color_continuous_scale="YlOrRd", aspect="auto",
        labels={"color": "Avg effectiveness (%)"})
    fig.update_layout(**LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Avg effectiveness by city")
avg_city = (
    df.groupby(["CITY", "COUNTRY"])["EFFECTIVENESS"]
    .agg(avg="mean", campaigns="count").reset_index().sort_values("avg", ascending=False)
)
fig = px.bar(
    avg_city, x="CITY", y="avg", color="COUNTRY", text="avg",
    hover_data={"campaigns": True, "avg": ":.1f"},
    labels={"CITY": "City", "avg": "Avg effectiveness (%)", "COUNTRY": "Country", "campaigns": "Campaigns"},
)
fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig.update_layout(**LAYOUT, xaxis_tickangle=-45,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
fig.update_xaxes(**NO_GRID)
fig.update_yaxes(**GRID)
st.plotly_chart(fig, use_container_width=True)

col5, col6 = st.columns(2)

with col5:
    st.subheader("Effectiveness by city (scatter)")
    fig = px.strip(
        df, x="CITY", y="EFFECTIVENESS", color="COUNTRY", hover_data=["TYPE"],
        labels={"CITY": "City", "EFFECTIVENESS": "Effectiveness (%)", "COUNTRY": "Country", "TYPE": "Type"},
    )
    fig.update_traces(jitter=0.4, opacity=0.7)
    fig.update_layout(**LAYOUT, xaxis_tickangle=-30,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(**NO_GRID)
    fig.update_yaxes(**GRID)
    st.plotly_chart(fig, use_container_width=True)

with col6:
    st.subheader("Effectiveness distribution (histogram)")
    fig = px.histogram(
        df, x="EFFECTIVENESS", color="TYPE",
        nbins=20, barmode="overlay", opacity=0.7, marginal="rug",
        labels={"EFFECTIVENESS": "Effectiveness (%)", "TYPE": "Type"},
    )
    fig.update_layout(**LAYOUT, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(**NO_GRID)
    fig.update_yaxes(**GRID)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Raw data"):
    st.caption(f"{total:,} rows · {len(df_all):,} total")
    st.dataframe(df)