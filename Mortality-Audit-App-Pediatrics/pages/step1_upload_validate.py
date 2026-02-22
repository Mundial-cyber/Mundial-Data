import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from datetime import datetime


st.set_page_config("Mortality Audit : Upload and Validate", layout="wide")
st.title("Mortality Audit - Upload and Validate Data")
st.markdown(
    """
Upload the admissions CSV for a month (or multiple months). This step validates the file, normalizes columns,
and extracts the timeframe options. Use the sample CSV to format your data if needed.

**Minimal required columns:**
- `patient_id` (recommended)
- `sex` (M/F)
- `age_days` or `age_months` or `age_years` or `age`
- `ward` (NBU / Pediatrics / other)
- `admission_date` (YYYY-MM-DD)
- `outcome` (Alive / Dead)
- `primary_diagnosis` (text)
"""
)


sample_df = pd.DataFrame([
    {
        "patient_id": "45991",
        "initials": "J.M.M",
        "sex": "M",
        "age_days": 10,
        "ward": "NBU",
        "admission_date": "2025-09-01",
        "discharge_date": "0000-00-00",
        "outcome": "Dead",
        "death_date": "2025-09-04",
        "primary_diagnosis": "Neonatal Sepsis",
        "Notes": "SP puncture done"
    },
    {
        "patient_id": "46781",
        "initials": "D.S.J",
        "sex": "F",
        "age_months": 10,
        "ward": "Pediatrics",
        "admission_date": "2025-09-02",
        "discharge_date": "2025-09-09",
        "outcome": "Alive",
        "death_date": "2025-09-04",
        "primary_diagnosis": "Severe Pneumonia",
        "Notes": "Counseled on danger signs"
    }
])

recognized_date_cols = ["admission_date", "discharge_date", "death_date"]

def make_sample_csv_bytes():
    buf = BytesIO()
    sample_df.to_csv(buf, index=False)
    buf.seek(0)
    return buf.getvalue()

def col_exists_any(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def validate_and_normalize(df: pd.DataFrame):
    errors = []
    warnings = []
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    minimal_candidates = ["admission_date", "outcome", "primary_diagnosis"]
    if not any(c in df.columns for c in minimal_candidates):
        errors.append("File must contain at least one of the minimal columns: admission_date, outcome, primary_diagnosis")
        return None, errors, warnings, {}, None

 
    for c in recognized_date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    
    age_days_col = None
    if "age_days" in df.columns:
        age_days_col = "age_days"
    elif "age" in df.columns:
        try:
            sample = pd.to_numeric(df["age"], errors="coerce").dropna()
            if not sample.empty:
                median = sample.median()
                if median <= 30:
                    df["age_days"] = pd.to_numeric(df["age"], errors="coerce")
                elif median < 100:
                    df["age_days"] = (pd.to_numeric(df["age"], errors="coerce") * 30).round().astype("Int64")
                else:
                    df["age_days"] = (pd.to_numeric(df["age"], errors="coerce") * 365).round().astype("Int64")
                age_days_col = "age_days"
        except Exception:
            pass
    elif "age_months" in df.columns:
        df["age_days"] = (pd.to_numeric(df["age_months"], errors="coerce") * 30).round().astype("Int64")
        age_days_col = "age_days"
    elif "age_years" in df.columns:
        df["age_days"] = (pd.to_numeric(df["age_years"], errors="coerce") * 365).round().astype("Int64")
        age_days_col = "age_days"
    if age_days_col is None:
        warnings.append("No recognizable age columns found (age_days, age_months, age_years)")

    
    if "sex" in df.columns:
        df["sex_norm"] = df["sex"].astype(str).str.strip().str.upper().replace({"MALE": "M", "FEMALE": "F"})
        df["sex_norm"] = df["sex_norm"].where(df["sex_norm"].isin(["M", "F"]), "Unknown")
    else:
        df["sex_norm"] = "Unknown"
        warnings.append("No sex column found; created sex_norm = Unknown")

    
    if "outcome" in df.columns:
        df["outcome_norm"] = df["outcome"].astype(str).str.strip().str.lower().map(
            lambda x: "Dead" if "dead" in x or x.startswith("d") else ("Alive" if "alive" in x or x.startswith("a") else x.title())
        )
    else:
        df["outcome_norm"] = pd.NA
        warnings.append("No outcome column found. Please add outcome (Alive/Dead)")

    
    if "primary_diagnosis" not in df.columns:
        alt = col_exists_any(df, ["diagnosis", "dx", "primary_dx"])
        if alt:
            df["primary_diagnosis"] = df[alt].astype(str)
            warnings.append(f"Mapped diagnosis column '{alt}' to primary_diagnosis")
        else:
            df["primary_diagnosis"] = "UNKNOWN"
            warnings.append("No primary_diagnosis found. Filled as UNKNOWN")

    
    date_for_month = None
    if "admission_date" in df.columns and df["admission_date"].notna().any():
        df["month"] = df["admission_date"].dt.to_period("M")
        date_for_month = "admission_date"
    elif "death_date" in df.columns and df["death_date"].notna().any():
        df["month"] = df["death_date"].dt.to_period("M")
        date_for_month = "death_date"
    else:
        df["month"] = pd.NA
        warnings.append("No usable date to derive month")

    missing_report = df.isna().sum().to_dict()
    return df, errors, warnings, missing_report, date_for_month


col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Upload Monthly Datasets")

    st.markdown("📥 **Current Month Data**")
    uploaded_current = st.file_uploader("Upload Current Month CSV", type=["csv", "txt"], key="current")

    st.markdown("📥 **Previous Month Data (Optional)**")
    uploaded_previous = st.file_uploader("Upload Previous Month CSV", type=["csv", "txt"], key="previous")

    st.download_button("📄 Download Sample CSV", data=make_sample_csv_bytes(), file_name="mortality_sample.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("Options")
    anchoring = st.selectbox("Select date anchor", options=["admission_date", "death_date"], index=0)
    auto_store = st.checkbox("Automatically store clean dataset in session", value=True)

with col2:
    st.info("Step 1: Upload and validate CSVs before moving to Step 2 for analysis")
    st.write("Minimum fields: admission_date, death_date/discharge_date, outcome, primary_diagnosis, age")


if uploaded_current:
    try:
        df_current_raw = pd.read_csv(uploaded_current)
        st.subheader("📊 Current Month Data Preview")
        st.dataframe(df_current_raw.head(20))
        df_current_clean, errors, warnings, missing_report, _ = validate_and_normalize(df_current_raw)
        if errors:
            st.error("❌ Validation failed for Current Month:")
            for e in errors:
                st.write(f"- {e}")
        else:
            st.success("✅ Current Month Data Validated!")
            st.metric("Rows", len(df_current_clean))
            if auto_store:
                st.session_state["df_current"] = df_current_clean
    except Exception as e:
        st.error(f"Error reading current month file: {e}")
else:
    st.warning("⚠️ Please upload the **Current Month CSV**")


if uploaded_previous:
    try:
        df_prev_raw = pd.read_csv(uploaded_previous)
        st.subheader("📊 Previous Month Data Preview")
        st.dataframe(df_prev_raw.head(20))
        df_prev_clean, errors_prev, warnings_prev, _, _ = validate_and_normalize(df_prev_raw)
        if errors_prev:
            st.error("❌ Validation failed for Previous Month:")
            for e in errors_prev:
                st.write(f"- {e}")
        else:
            st.success("✅ Previous Month Data Validated!")
            if auto_store:
                st.session_state["df_previous"] = df_prev_clean
    except Exception as e:
        st.error(f"Error reading previous month file: {e}")


if "df_current" in st.session_state:
    st.markdown("---")
    st.success("✅ Data stored in session. Proceed to Step 2: Analysis & Visualization")
    st.write("Debug session keys:", list(st.session_state.keys()))
