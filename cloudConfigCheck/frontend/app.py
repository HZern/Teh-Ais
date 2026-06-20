import streamlit as st


st.set_page_config(
    page_title="CloudOps Manager Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.switch_page("pages/workload_analytics.py")
