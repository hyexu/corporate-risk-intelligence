
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Corporate Risk Intelligence",
    layout="wide"
)

st.title("Corporate Risk Intelligence")
st.caption("AI Financial Risk Monitoring - DEMO")
st.warning("All financial data are fictional.")

# 가상 기업 재무데이터 (단위: 억 원)
data = {
    "Company": ["Demo A", "Demo B", "Demo C"],
    "Revenue_2024": [1000, 2000, 800],
    "Revenue_2025": [1200, 2400, 850],
    "Operating_Profit": [120, 360, 51],
    "Net_Income": [80, 250, 30],
    "Assets": [2000, 3000, 1200],
    "Liabilities": [1400, 1200, 720],
    "Operating_Cash_Flow": [50, 280, 25],
    "Receivables_2024": [100, 200, 80],
    "Receivables_2025": [180, 230, 100]
}

df = pd.DataFrame(data)

# 재무비율 계산
df["Revenue_Growth"] = (
    df["Revenue_2025"] / df["Revenue_2024"] - 1
) * 100

df["Operating_Margin"] = (
    df["Operating_Profit"] / df["Revenue_2025"]
) * 100

df["Equity"] = df["Assets"] - df["Liabilities"]

df["Debt_Ratio"] = (
    df["Liabilities"] / df["Equity"]
) * 100

df["Cash_Conversion"] = (
    df["Operating_Cash_Flow"] / df["Net_Income"]
)

df["Receivables_Growth"] = (
    df["Receivables_2025"] /
    df["Receivables_2024"] - 1
) * 100

# 기업 선택
selected = st.multiselect(
    "Select companies",
    df["Company"].tolist(),
    default=df["Company"].tolist()
)

filtered = df[df["Company"].isin(selected)]

st.subheader("Financial Overview")

st.dataframe(
    filtered[
        ["Company", "Revenue_2025",
         "Operating_Margin", "Debt_Ratio",
         "Cash_Conversion"]
    ],
    use_container_width=True
)

st.subheader("Operating Margin Comparison")
st.bar_chart(
    filtered.set_index("Company")["Operating_Margin"]
)

st.subheader("Debt Ratio Comparison")
st.bar_chart(
    filtered.set_index("Company")["Debt_Ratio"]
)

st.subheader("Risk Signals")

for _, row in filtered.iterrows():
    risks = []

    if row["Debt_Ratio"] > 200:
        risks.append("High Debt Ratio")

    if row["Cash_Conversion"] < 0.8:
        risks.append("Weak Cash Conversion")

    if (
        row["Receivables_Growth"]
        > row["Revenue_Growth"] + 20
    ):
        risks.append("Receivables Growing Faster Than Sales")

    if risks:
        st.error(f"{row['Company']}: {', '.join(risks)}")
    else:
        st.success(f"{row['Company']}: No risk signals detected")
