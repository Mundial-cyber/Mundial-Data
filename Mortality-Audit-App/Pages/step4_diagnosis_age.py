import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Step 4: Diagnosis & Age Analysis", layout="wide")
st.title("Step 4: Admissions by Diagnosis & Mortalities By Age Group")

# 🧠 Check if cleaned data exists in session
if "df_clean" in st.session_state:
    df = st.session_state["df_clean"].copy()
elif "df_current" in st.session_state:
    df = st.session_state["df_current"].copy()
else:
    st.error("❌ No clean data found. Please run Step 1 first.")
    st.stop()

# 🧭 Detect outcome column
outcome_col = None
for col in ["outcome_norm", "outcome"]:
    if col in df.columns:
        outcome_col = col
        break

if outcome_col is None:
    st.error("⚠️ Could not find outcome column. Expected `outcome_norm` or `outcome`.")
    st.stop()

df[outcome_col] = df[outcome_col].astype(str).str.lower()

# 📅 Filter by chosen month if selected in Step 1
chosen_month = st.session_state.get("chosen_month")
if chosen_month:
    st.info(f"Using data for chosen month: **{chosen_month}**")
    # Convert to string for matching if month is Period
    if isinstance(df["month"].iloc[0], pd.Period):
        df["month"] = df["month"].astype(str)
    df = df[df["month"] == str(chosen_month)]

# 🏥 Admissions by Primary Diagnosis
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

# ⚰️ Mortalities by Age Group
st.markdown("### ⚰️ Mortalities by Age Group")
if "age_days" in df.columns:
    deaths_df = df[df[outcome_col] == "dead"].copy()
    if deaths_df.empty:
        st.info("No mortality records found for the selected month.")
    else:
        # Create age group classification
        def age_group(days):
            if pd.isna(days): return "Unknown"
            if days < 30: return "<1 month"
            if days < 365: return "1-11 months"
            if days < 5 * 365: return "1-4 years"
            if days < 15 * 365: return "5-14 years"
            return "15+ years"

        deaths_df["age_group"] = deaths_df["age_days"].apply(age_group)
        age_counts = deaths_df["age_group"].value_counts().reset_index()
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
            fig_age_bar.update_layout(xaxis={"categoryorder": "array", "categoryarray": ["<1 month", "1-11 months", "1-4 years", "5-14 years", "15+ years", "Unknown"]})
            st.plotly_chart(fig_age_bar, use_container_width=True)

        with col2:
            st.dataframe(age_counts, use_container_width=True)
else:
    st.warning("⚠️ Column `age_days` is missing in the dataset.")

st.markdown("---")

# 📈 Month-to-Month Trend by Diagnosis
st.subheader("📈 Month-to-Month Admissions Trend by Diagnosis")
if "month" in df.columns and "primary_diagnosis" in df.columns:
    monthly_diag = df.groupby(["month", "primary_diagnosis"]).size().reset_index(name="Admissions")

    # ✅ Convert Period to string (fix JSON issue)
    monthly_diag["month"] = monthly_diag["month"].astype(str)

    # ✅ Sort chronologically by parsed month
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
st.success("✅ You have visualized admissions and mortalities by key demographics successfully.")

