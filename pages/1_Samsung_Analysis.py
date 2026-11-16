
import os
import json
import urllib.parse
import urllib.request

import streamlit as st

st.set_page_config(
    page_title="Samsung Financial Analysis",
    layout="wide"
)

st.title("Samsung Electronics")
st.caption("OpenDART | FY2024 | Consolidated Financial Statements")

# Codespaces에서는 환경변수,
# Streamlit Cloud에서는 Secrets 사용
api_key = os.getenv("OPENDART_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["OPENDART_API_KEY"]
    except (KeyError, FileNotFoundError):
        st.error("OpenDART API key is not configured.")
        st.stop()


@st.cache_data(ttl=3600, show_spinner=False)
def load_financial_data(key):
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"

    params = {
        "crtfc_key": key,
        "corp_code": "00126380",
        "bsns_year": "2024",
        "reprt_code": "11011",
        "fs_div": "CFS"
    }

    request = urllib.request.Request(
        url + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "CorporateRiskIntelligence/0.2"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)

    if data.get("status") != "000":
        raise ValueError(
            "OpenDART status: " + str(data.get("status"))
        )

    return data["list"]


def parse_amount(value):
    if value is None:
        return None

    value = str(value).replace(",", "").strip()

    if value in ("", "-"):
        return None

    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]

    return int(value)


def find_account(rows, account_id, statement):
    matches = [
        row for row in rows
        if row.get("account_id") == account_id
        and row.get("sj_div") in statement
        and row.get("account_detail", "-") in ("-", "")
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Account matching failed: {account_id} "
            f"({len(matches)} matches)"
        )

    return matches[0]


try:
    with st.spinner("Loading OpenDART financial statements..."):
        rows = load_financial_data(api_key)

    revenue = find_account(
        rows, "ifrs-full_Revenue", ["IS", "CIS"]
    )

    operating_profit = find_account(
        rows, "dart_OperatingIncomeLoss", ["IS", "CIS"]
    )

    liabilities = find_account(
        rows, "ifrs-full_Liabilities", ["BS"]
    )

    equity = find_account(
        rows, "ifrs-full_Equity", ["BS"]
    )

    rev_2024 = parse_amount(revenue["thstrm_amount"])
    rev_2023 = parse_amount(revenue["frmtrm_amount"])
    op_2024 = parse_amount(operating_profit["thstrm_amount"])
    liab_2024 = parse_amount(liabilities["thstrm_amount"])
    equity_2024 = parse_amount(equity["thstrm_amount"])

    values = [
        rev_2024, rev_2023, op_2024,
        liab_2024, equity_2024
    ]

    if any(value is None for value in values):
        raise ValueError("Missing financial amounts")

    if rev_2023 == 0 or rev_2024 == 0:
        raise ValueError("Revenue denominator is zero")

    if equity_2024 <= 0:
        raise ValueError("Equity is zero or negative")

    growth = (rev_2024 / rev_2023 - 1) * 100
    margin = op_2024 / rev_2024 * 100
    debt_ratio = liab_2024 / equity_2024 * 100

except Exception as error:
    # API 요청 URL이나 인증키는 화면에 출력하지 않음
    st.error(
        "Financial data could not be loaded. "
        "Check the API configuration and account mappings."
    )
    st.caption("Error type: " + type(error).__name__)
    st.stop()


st.success("Financial data loaded successfully")

st.subheader("Key Financial Ratios")

col1, col2, col3 = st.columns(3)

col1.metric("Revenue Growth", f"{growth:.2f}%")
col2.metric("Operating Margin", f"{margin:.2f}%")
col3.metric("Debt Ratio", f"{debt_ratio:.2f}%")

st.subheader("Financial Statement Highlights")

financial_data = {
    "Metric": [
        "Revenue 2024",
        "Revenue 2023",
        "Operating Profit",
        "Total Liabilities",
        "Total Equity"
    ],
    "KRW 100 million": [
        rev_2024 / 1e8,
        rev_2023 / 1e8,
        op_2024 / 1e8,
        liab_2024 / 1e8,
        equity_2024 / 1e8
    ]
}

st.dataframe(financial_data, use_container_width=True)

st.subheader("Revenue Comparison")

st.bar_chart({
    "2023": rev_2023 / 1e8,
    "2024": rev_2024 / 1e8
})

st.info(
    "Source: Financial Supervisory Service OpenDART. "
    "FY2024 annual report, consolidated statements. "
    "Figures are in KRW 100 million."
)

st.caption(
    "Financial ratios are descriptive indicators, "
    "not standalone credit-risk assessments."
)
