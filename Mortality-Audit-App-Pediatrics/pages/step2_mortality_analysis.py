import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Mortality Audit", layout="wide")
st.title("📈 Step 2: Mortality Audit & Charts")

st.markdown("""
This section analyzes mortality patterns between months, including:
- Mortality rates per month  
- Month-to-month comparison  
- Visual trends for quick insights  
""")

st.divider()

# --- Load data from Step 1 ---
df_current = st.session_state.get("df_current")
df_previous = st.session_state.get("df_previous")

if df_current is None:
    st.warning("⚠️ Please upload and validate at least the current month data in Step 1.")
    st.stop()

# Combine both datasets (if previous month exists)
if df_previous is not None:
    df_all = pd.concat([df_previous, df_current], ignore_index=True)
else:
    df_all = df_current.copy()

# --- Process dates ---
for col in ["admission_date", "death_date"]:
    if col in df_all.columns:
        df_all[col] = pd.to_datetime(df_all[col], errors="coerce")

# --- Create month column ---
df_all["month"] = df_all["admission_date"].dt.to_period("M").astype(str)

# --- Define death indicator ---
death_col_exists = "death_date" in df_all.columns
df_all["is_death"] = (
    df_all["outcome"].astype(str).str.lower().str.contains("dead")
    | (df_all["outcome"].astype(str).str.lower().eq("death"))
)
if death_col_exists:
    df_all["is_death"] = df_all["is_death"] | df_all["death_date"].notna()

# --- Compute monthly summary ---
summary = (
    df_all.groupby("month")
    .agg(
        total_admissions=("patient_id", "count"),
        total_deaths=("is_death", "sum"),
    )
    .reset_index()
    .sort_values("month")
)
summary["mortality_rate"] = (summary["total_deaths"] / summary["total_admissions"] * 100).round(2)

# --- Display results ---
st.subheader("📊 Monthly Mortality Summary")
st.dataframe(summary, use_container_width=True)

# --- Comparison Metrics (if both months available) ---
if len(summary) >= 2:
    current_month = summary.iloc[-1]
    prev_month = summary.iloc[-2]

    current_rate = current_month["mortality_rate"]
    prev_rate = prev_month["mortality_rate"]
    diff = (current_rate - prev_rate).round(2)

    st.markdown("### 📈 Month-to-Month Mortality Comparison")
    col1, col2, col3 = st.columns(3)
    col1.metric(f"{current_month['month']} Mortality (%)", f"{current_rate:.2f}%")
    col2.metric(f"{prev_month['month']} Mortality (%)", f"{prev_rate:.2f}%")
    col3.metric("Change", f"{diff:+.2f}%", delta=diff)

st.divider()

# --- Trend Visualization ---
st.subheader("📉 Mortality Trend Over Time")
fig = px.line(
    summary,
    x="month",
    y="mortality_rate",
    title="Monthly Mortality Rate Trend",
    markers=True,
    text="mortality_rate"
)
fig.update_traces(textposition="top center")
st.plotly_chart(fig, use_container_width=True)