import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -------------------------------
# PAGE SETUP
# -------------------------------
st.set_page_config(page_title="Step 2: Mortality Audit and Analysis", layout="wide")
st.title("📊 Step 2: Mortality Audit & Charts")

# -------------------------------
# LOAD DATA FROM SESSION
# -------------------------------
if "df_current" not in st.session_state:
    st.error("❌ No validated current month dataset found. Please complete Step 1 first.")
    st.stop()

df_clean = st.session_state["df_current"]
df_previous = st.session_state.get("df_previous")

# -------------------------------
# SELECTED MONTH (optional)
# -------------------------------
chosen_month = st.session_state.get("chosen_month")
if chosen_month:
    st.info(f"📅 Using data for **Month {chosen_month}**")
    df = df_clean[df_clean["month"] == pd.Period(chosen_month)]
else:
    df = df_clean.copy()

# -------------------------------
# SUMMARY METRICS
# -------------------------------
admissions = len(df)
deaths = df["outcome_norm"].str.contains("Dead", case=False, na=False).sum()
mort_rate = (deaths / admissions * 100) if admissions > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Admissions", admissions)
col2.metric("Deaths", deaths)
col3.metric("Mortality Rate (%)", f"{mort_rate:.2f}%")

st.markdown("---")

# -------------------------------
# PIE CHART: CAUSES OF DEATH
# -------------------------------
st.subheader("🧠 Causes of Death by Primary Diagnosis")
deaths_df = df[df["outcome_norm"] == "Dead"]

if not deaths_df.empty and "primary_diagnosis" in deaths_df.columns:
    case_counts = (
        deaths_df["primary_diagnosis"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Diagnosis", "primary_diagnosis": "Count"})
    )
    case_counts.columns = ["Diagnosis", "Count"]

    fig_pie = px.pie(
        case_counts,
        values="Count",
        names="Diagnosis",
        title="Causes of Death"
    )
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("ℹ️ No death records found for this month.")

# -------------------------------
# HISTOGRAM: DURATION OF ADMISSION
# -------------------------------
st.subheader("📉 Deaths by Duration of Admission (Days)")
if "admission_date" in deaths_df.columns and "death_date" in deaths_df.columns:
    deaths_df = deaths_df.copy()
    deaths_df["duration_days"] = (
        deaths_df["death_date"] - deaths_df["admission_date"]
    ).dt.days
    deaths_df = deaths_df[deaths_df["duration_days"].notna() & (deaths_df["duration_days"] >= 0)]

    if not deaths_df.empty:
        fig_dur = px.histogram(
            deaths_df,
            x="duration_days",
            nbins=10,
            title="Deaths by Duration of Admission",
            labels={"duration_days": "Duration (Days)"},
        )
        st.plotly_chart(fig_dur, use_container_width=True)
    else:
        st.info("ℹ️ No valid duration data available for deaths.")
else:
    st.info("ℹ️ Missing admission_date or death_date columns.")

# -------------------------------
# TABLE: MORTALITY PARTICULARS
# -------------------------------
st.subheader("🧾 Mortality Particulars Table")
cols = [c for c in ["initials", "sex_norm", "age_days", "primary_diagnosis", "duration_days"] if c in deaths_df.columns]

if not deaths_df.empty and cols:
    st.dataframe(deaths_df[cols].reset_index(drop=True))
else:
    st.info("ℹ️ No mortality records available to display.")

st.markdown("---")

# -------------------------------
# MONTH-TO-MONTH COMPARISON
# -------------------------------
if df_previous is not None:
    st.subheader("📈 Month-to-Month Mortality Comparison")

    current_deaths = df_clean["outcome_norm"].str.contains("Dead", na=False).sum()
    prev_deaths = df_previous["outcome_norm"].str.contains("Dead", na=False).sum()

    current_total = len(df_clean)
    prev_total = len(df_previous)

    current_rate = current_deaths / current_total * 100 if current_total > 0 else 0
    prev_rate = prev_deaths / prev_total * 100 if prev_total > 0 else 0
    diff = current_rate - prev_rate

    c1, c2, c3 = st.columns(3)
    c1.metric("Current Month Mortality (%)", f"{current_rate:.2f}%")
    c2.metric("Previous Month Mortality (%)", f"{prev_rate:.2f}%")
    c3.metric("Change", f"{diff:+.2f}%")

    st.markdown("---")

# -------------------------------
# RECOMMENDATIONS
# -------------------------------
st.subheader("📝 Recommendations and Take-Home Message")
st.text_area(
    "Write Recommendations Here:",
    placeholder="Example: Strengthen neonatal sepsis management protocols and staff response time."
)
st.success("✅ Analysis Complete")