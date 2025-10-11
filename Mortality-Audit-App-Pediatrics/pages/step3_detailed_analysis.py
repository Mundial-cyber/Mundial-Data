import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Step 3: Month-to-Month Comparison", layout="wide")
st.title("📅 Step 3: Month-to-Month Mortality Comparison")

# --- Retrieve datasets from session ---
if "df_current" not in st.session_state or "df_previous" not in st.session_state:
    st.error("❌ Missing one or both datasets. Please upload both current and previous month files in Step 1.")
    st.stop()

df_current = st.session_state["df_current"].copy()
df_previous = st.session_state["df_previous"].copy()

# --- Merge datasets ---
df = pd.concat([df_previous, df_current], ignore_index=True)

# --- Ensure date and month columns ---
if "admission_date" in df.columns:
    df["admission_date"] = pd.to_datetime(df["admission_date"], errors="coerce")
    df["month"] = df["admission_date"].dt.to_period("M").astype(str)
elif "death_date" in df.columns:
    df["death_date"] = pd.to_datetime(df["death_date"], errors="coerce")
    df["month"] = df["death_date"].dt.to_period("M").astype(str)
else:
    st.error("⚠️ Missing 'admission_date' or 'death_date' columns.")
    st.stop()

# --- Standardize outcome ---
if "outcome" in df.columns:
    df["outcome"] = df["outcome"].astype(str).str.lower().str.strip()
elif "outcome_norm" in df.columns:
    df["outcome"] = df["outcome_norm"].astype(str).str.lower().str.strip()
else:
    df["outcome"] = "unknown"

# --- Define death indicator (same as Step 2) ---
df["is_death"] = df["outcome"].str.contains("dead", na=False)
if "death_date" in df.columns:
    df["death_date"] = pd.to_datetime(df["death_date"], errors="coerce")
    df["is_death"] = df["is_death"] | df["death_date"].notna()

# --- Validate months ---
months = sorted(df["month"].dropna().unique())
if len(months) < 2:
    st.warning("⚠️ You need data from at least two different months to compare.")
    st.stop()

# --- User selection for comparison ---
col1, col2 = st.columns(2)
with col1:
    month1 = st.selectbox("Select First Month:", months, index=0)
with col2:
    month2 = st.selectbox("Select Second Month:", months, index=1 if len(months) > 1 else 0)

# --- Mortality stats function (same as Step 2 logic) ---
def mortality_stats(sub_df):
    total_adm = len(sub_df)
    total_dead = sub_df["is_death"].sum()
    mortality_rate = (total_dead / total_adm * 100).round(2) if total_adm > 0 else 0
    return total_adm, total_dead, mortality_rate

# --- Compute for selected months ---
df1, df2 = df[df["month"] == month1], df[df["month"] == month2]
adm1, dead1, rate1 = mortality_stats(df1)
adm2, dead2, rate2 = mortality_stats(df2)

# --- Summary Table ---
st.subheader("📊 Summary Table")
st.markdown(f"""
| Metric | {month1} | {month2} |
|--------|----------|----------|
| **Total Admissions** | {adm1} | {adm2} |
| **Total Deaths** | {dead1} | {dead2} |
| **Mortality Rate (%)** | {rate1:.2f}% | {rate2:.2f}% |
""")

# --- Bar Chart ---
compare_df = pd.DataFrame({
    "Month": [month1, month2],
    "Admissions": [adm1, adm2],
    "Deaths": [dead1, dead2],
    "Mortality Rate (%)": [rate1, rate2]
})

fig_bar = px.bar(
    compare_df,
    x="Month",
    y=["Admissions", "Deaths"],
    barmode="group",
    text_auto=True,
    title="Admissions vs Deaths per Month",
    labels={"value": "Count", "variable": "Metric"}
)
st.plotly_chart(fig_bar, use_container_width=True)

# --- Mortality rate difference ---
diff = rate2 - rate1
if diff > 0:
    st.error(f"📈 Mortality Rate increased by **{diff:.2f}%** from {month1} to {month2}.")
elif diff < 0:
    st.success(f"📉 Mortality Rate decreased by **{abs(diff):.2f}%** from {month1} to {month2}.")
else:
    st.info("⚖️ Mortality Rate remained the same between the two months.")

# --- Monthly Trend ---
st.markdown("---")
st.subheader("📅 Overall Monthly Mortality Trend")

trend_df = (
    df.groupby("month")
    .agg(
        Admissions=("patient_id", "count"),
        Deaths=("is_death", "sum")
    )
    .reset_index()
)
trend_df["Mortality Rate (%)"] = (trend_df["Deaths"] / trend_df["Admissions"] * 100).round(2)

st.dataframe(trend_df, use_container_width=True)

fig_line = px.line(
    trend_df,
    x="month",
    y="Mortality Rate (%)",
    markers=True,
    text="Mortality Rate (%)",
    title="Mortality Rate Trend Across All Months",
)
fig_line.update_traces(texttemplate="%{text:.2f}%", textposition="top center")
fig_line.update_layout(yaxis_title="Mortality Rate (%)", xaxis_title="Month")
st.plotly_chart(fig_line, use_container_width=True)

st.success("✅ Step 3 complete! Mortality rates Computed.")