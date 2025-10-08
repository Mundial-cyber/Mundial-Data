import streamlit as st

# Configure page
st.set_page_config(page_title="👩‍⚕️👨‍⚕️Mortality Audit App", layout="wide")

# Title
st.title("🧾 Mortality Audit & Analysis App")

# Introduction
st.markdown("""
Welcome to the **Mortality Audit App**🎉.

This tool helps you:
1. Upload and validate monthly admission and outcome data
2. Clean and prepare datasets for analysis
3. Audit mortality patterns by diagnosis, age, and ward
4. Visualize trends and generate actionable insights
""")

# Instructions
st.markdown("---")
st.subheader("🧭 Navigation Guide")
st.markdown("""
Use the sidebar on the left to move through the steps:
-🎗️ **Step 1:** Upload & Validate Data 
-🎗️ **Step 2:** Mortality Audit & Charts  
-🎗️ **Step 3:** Admissions by Diagnosis  
-🎗️ **Step 4:** Mortality by Age Group  
""")

st.info("🫀 Complete Step 1 first to generate the clean dataset needed for other steps.")