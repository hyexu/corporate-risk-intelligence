
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# 프로젝트 최상위 폴더의 분석 모듈 가져오기
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from multi_company_analysis import analyze_all_companies

st.set_page_config(
    page_title="Real Company Comparison",
    layout="wide"
)

st.title("Real Company Comparison")
st.caption(
    "OpenDART | FY2024 | Consolidated Financial Statements"
)

st.info(
    "Comparing Samsung Electronics, SK Hynix, "
    "and Hyundai Motor using actual financial filings."
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_comparison():
    return analyze_all_companies()


with st.spinner("Loading financial statements..."):
    results, errors = load_comparison()

if errors:
    for company, error in errors.items():
        # 오류 유형만 표시해 민감한 요청 정보 노출 방지
        st.warning(
            f"{company}: Financial data unavailable."
        )

if not results:
    st.error("No financial data available.")
    st.stop()

df = pd.DataFrame(results)

st.subheader("Financial Ratio Comparison")

selected_companies = st.multiselect(
    "Select companies",
    options=df["Company"].tolist(),
    default=df["Company"].tolist()
)

filtered = df[
    df["Company"].isin(selected_companies)
]

if filtered.empty:
    st.warning("Select at least one company.")
    st.stop()

display_df = filtered.rename(columns={
    "Company": "Company",
    "Revenue_Growth": "Revenue Growth (%)",
    "Operating_Margin": "Operating Margin (%)",
    "Debt_Ratio": "Debt Ratio (%)"
})

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

st.subheader("Revenue Growth")
st.bar_chart(
    filtered.set_index("Company")["Revenue_Growth"]
)

st.subheader("Operating Margin")
st.bar_chart(
    filtered.set_index("Company")["Operating_Margin"]
)

st.subheader("Debt Ratio")
st.bar_chart(
    filtered.set_index("Company")["Debt_Ratio"]
)

st.divider()

st.subheader("Financial Risk Signals")

for _, row in filtered.iterrows():
    risks = []

    if row["Debt_Ratio"] > 200:
        risks.append("High debt ratio")

    if row["Operating_Margin"] < 0:
        risks.append("Operating loss")

    if row["Revenue_Growth"] < 0:
        risks.append("Revenue decline")

    if risks:
        st.warning(
            f"{row['Company']}: {', '.join(risks)}"
        )
    else:
        st.success(
            f"{row['Company']}: No rule-based signals detected"
        )

st.caption(
    "Source: Financial Supervisory Service OpenDART. "
    "FY2024 annual reports, consolidated statements. "
    "Risk thresholds are illustrative and not "
    "empirically validated. Cross-industry comparisons "
    "require caution."
)
