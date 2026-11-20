
import streamlit as st

st.set_page_config(
    page_title="Corporate Risk Intelligence",
    page_icon="📊",
    layout="wide",
)

dashboard = st.Page(
    "dashboard/financial_risk_dashboard.py",
    title="Financial Risk Dashboard",
    icon="📊",
    default=True,
)

samsung = st.Page(
    "pages/1_Samsung_Analysis.py",
    title="Samsung Analysis",
    icon="🔍",
)

navigation = st.navigation(
    [dashboard, samsung],
    position="sidebar",
)

navigation.run()
