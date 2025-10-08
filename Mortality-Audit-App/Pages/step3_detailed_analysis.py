import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Step 3: Month-to-Month Comparison", layout="wide")
st.title("📅 Step 3: Month-to-Month Mortality Comparison")

# 🧠 Retrieve cleaned dataset from session (from Step 1)
if "df_current" not in st.session_state:
    st.error("❌ No clean dataset found. Please run Step 1 first to upload and clean data.")
    st.stop()

df = st.session_state["df_current"].copy()

# ✅ Ensure month column exists and convert Periods to string
if "month" not in df.columns:
    st.error("⚠️ The dataset must contain a 'month' column.")
    st.stop()

if isinstance(df["month"].iloc[0], pd.Period):
    df["month"] = df["month"].astype(str)

# ✅ Ensure outcome column is standardized
outcome_col = None
for col in ["outcome", "outcome_norm"]:
    if col in df.columns:
        outcome_col = col
        break

if outcome_col is None:
    st.error("⚠️ Could not find outcome column. Expected 'outcome' or 'outcome_norm'.")
    st.stop()

df[outcome_col] = df[outcome_col].astype(str).str.lower()

st.markdown("---")
st.subheader("🔁 Compare Two Months Side by Side")

# Extract unique months dynamically
months = sorted(df["month"].dropna().unique())

if len(months) < 2:
    st.warning("⚠️ You need data from at least two different months to compare.")
    st.stop()

# Month selectors
col1, col2 = st.columns(2)
with col1:
    month1 = st.selectbox("Select First Month:", months, index=0, key="month1")
with col2:
    month2 = st.selectbox("Select Second Month:", months, index=1 if len(months) > 1 else 0, key="month2")

# Function to compute stats
def mortality_stats(sub_df):
    total_adm = len(sub_df)
    total_dead = (sub_df[outcome_col] == "dead").sum()
    mortality_rate = (total_dead / total_adm * 100) if total_adm > 0 else 0
    return total_adm, total_dead, mortality_rate

# Compute stats
df1, df2 = df[df["month"] == month1], df[df["month"] == month2]
adm1, dead1, rate1 = mortality_stats(df1)
adm2, dead2, rate2 = mortality_stats(df2)

# 📊 Summary Table
st.subheader("📊 Summary Table")
st.markdown(f"""
| Metric | {month1} | {month2} |
|--------|----------|----------|
| **Total Admissions** | {adm1} | {adm2} |
| **Total Deaths** | {dead1} | {dead2} |
| **Mortality Rate (%)** | {rate1:.2f}% | {rate2:.2f}% |
""")

# 📈 Bar Chart Comparison
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

# 🔍 Mortality Rate Difference
diff = rate2 - rate1
if diff > 0:
    st.error(f"📈 Mortality Rate increased by **{diff:.2f}%** from {month1} to {month2}.")
elif diff < 0:
    st.success(f"📉 Mortality Rate decreased by **{abs(diff):.2f}%** from {month1} to {month2}.")
else:
    st.info("⚖️ Mortality Rate remained the same between the two months.")

# 🧭 Overall Month-to-Month Trend
st.markdown("---")
st.subheader("📅 Overall Monthly Mortality Trend")

trend_df = (
    df.groupby("month")
    .apply(lambda x: pd.Series({
        "Admissions": len(x),
        "Deaths": (x[outcome_col] == "dead").sum(),
        "Mortality Rate (%)": (x[outcome_col].str.contains("dead", na=False).sum() / len(x) * 100) if len(x) > 0 else 0
    }))
    .reset_index()
)

trend_df["month"] = trend_df["month"].astype(str)

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

st.success("✅ Step 3 complete! You’ve successfully compared monthly mortality trends.")