import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Step 4: Diagnosis & Age Analysis", layout="wide")
st.title("Step 4: Admissions by Diagnosis & Mortalities By Age Group")

# 🧠 Load datasets
df = None
if "df_previous" in st.session_state and "df_current" in st.session_state:
    df_prev = st.session_state["df_previous"].copy()
    df_curr = st.session_state["df_current"].copy()
    df = pd.concat([df_prev, df_curr], ignore_index=True)
    st.info("Using both previous and current month datasets for comparison.")
elif "df_current" in st.session_state:
    df = st.session_state["df_current"].copy()
else:
    st.error("❌ No clean data found. Please complete Step 1 first.")
    st.stop()

# 🧭 Detect outcome column
outcome_col = None
for col in ["outcome_norm", "outcome"]:
    if col in df.columns:
        outcome_col = col
        break
if outcome_col is None:
    st.error("⚠️ Could not find outcome column (`outcome_norm` or `outcome`).")
    st.stop()

df[outcome_col] = df[outcome_col].astype(str).str.lower()

# 🧩 Ensure 'month' column exists and is string
if "month" in df.columns:
    if isinstance(df["month"].iloc[0], pd.Period):
        df["month"] = df["month"].astype(str)
else:
    df["month"] = "Unknown"

# --------------------------------------------------
# 🧒 Normalize Age (handle days, months, years)
# --------------------------------------------------
def compute_age_days(row):
    if pd.notna(row.get("age_days")):
        return row["age_days"]
    if pd.notna(row.get("age_months")):
        return row["age_months"] * 30
    if pd.notna(row.get("age_years")):
        return row["age_years"] * 365
    return np.nan

df["age_days"] = df.apply(compute_age_days, axis=1)

# --------------------------------------------------
# 📊 Admissions by Primary Diagnosis
# --------------------------------------------------
st.markdown("### 📊 Admissions by Primary Diagnosis")
if "primary_diagnosis" in df.columns:
    diag_counts = df["primary_diagnosis"].value_counts().reset_index()
    diag_counts.columns = ["Diagnosis", "Admissions"]

    fig_diag = px.bar(
        diag_counts,
        x="Diagnosis",
        y="Admissions",
        title="Admissions by Primary Diagnosis",
        text="Admissions"
    )
    fig_diag.update_layout(xaxis={"categoryorder": "total descending"})
    st.plotly_chart(fig_diag, use_container_width=True)
else:
    st.warning("⚠️ Column `primary_diagnosis` not found in dataset.")

st.markdown("---")

# --------------------------------------------------
# ⚰️ Mortalities by Age Group
# --------------------------------------------------
st.markdown("### ⚰️ Mortalities by Age Group")

deaths_df = df[df[outcome_col] == "dead"].copy()
if deaths_df.empty:
    st.info("No mortality records found.")
else:
    # Define age groups based on days
    def age_group(days):
        if pd.isna(days): return "Unknown"
        if days < 30: return "<1 month"
        if days < 365: return "1–11 months"
        if days < 5 * 365: return "1–4 years"
        if days < 15 * 365: return "5–14 years"
        return "15+ years"

    deaths_df["age_group"] = deaths_df["age_days"].apply(age_group)
    age_counts = deaths_df["age_group"].value_counts().reindex(
        ["<1 month", "1–11 months", "1–4 years", "5–14 years", "15+ years", "Unknown"]
    ).dropna().reset_index()
    age_counts.columns = ["Age Group", "Deaths"]

    col1, col2 = st.columns(2)
    with col1:
        fig_age_bar = px.bar(
            age_counts,
            x="Age Group",
            y="Deaths",
            text="Deaths",
            title="Deaths by Age Group"
        )
        fig_age_bar.update_layout(
            xaxis={"categoryorder": "array",
                   "categoryarray": ["<1 month", "1–11 months", "1–4 years", "5–14 years", "15+ years", "Unknown"]}
        )
        st.plotly_chart(fig_age_bar, use_container_width=True)

    with col2:
        st.dataframe(age_counts, use_container_width=True)

    # ➕ Add Age Distribution Histogram
    st.markdown("### 📊 Distribution of Age (Days) Among Mortalities")
    fig_hist = px.histogram(
        deaths_df,
        x="age_days",
        nbins=20,
        title="Distribution of Age in Mortalities (Days)",
        labels={"age_days": "Age (Days)"},
    )
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")

# --------------------------------------------------
# 📈 Month-to-Month Admissions Trend by Diagnosis
# --------------------------------------------------
st.subheader("📈 Month-to-Month Admissions Trend by Diagnosis")
if "month" in df.columns and "primary_diagnosis" in df.columns:
    monthly_diag = (
        df.groupby(["month", "primary_diagnosis"])
        .size()
        .reset_index(name="Admissions")
    )

    # Sort by chronological order if possible
    try:
        monthly_diag["month_sort"] = pd.to_datetime(monthly_diag["month"], errors="coerce")
        monthly_diag = monthly_diag.sort_values("month_sort")
    except Exception:
        monthly_diag = monthly_diag.sort_values("month")

    fig_trend = px.line(
        monthly_diag,
        x="month",
        y="Admissions",
        color="primary_diagnosis",
        markers=True,
        title="Admissions Trend Over Months by Diagnosis"
    )
    fig_trend.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Admissions",
        legend_title="Diagnosis"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.warning("⚠️ Missing `month` or `primary_diagnosis` column. Cannot generate trend chart.")

st.markdown("---")
st.success("✅ You have visualized admissions and mortalities by diagnosis and age successfully.")