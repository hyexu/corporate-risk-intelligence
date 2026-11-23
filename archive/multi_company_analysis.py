
import os
import json
import urllib.parse
import urllib.request
import urllib.error

# 1. OpenDART API 인증키

API_KEY = os.getenv("OPENDART_API_KEY")

if not API_KEY:
    try:
        import streamlit as st
        API_KEY = st.secrets["OPENDART_API_KEY"]
    except (KeyError, FileNotFoundError):
        raise RuntimeError(
            "OpenDART API key is missing"
        ) from None

# 2. 분석 대상 기업
COMPANIES = {
    "Samsung Electronics": "00126380",
    "SK Hynix": "00164779",
    "Hyundai Motor": "00164742"
}

URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"

# 3. 표준 계정 ID 매핑
ACCOUNT_IDS = {
    "Revenue": ["ifrs-full_Revenue"],
    "Operating_Profit": ["dart_OperatingIncomeLoss"],
    "Liabilities": ["ifrs-full_Liabilities"],
    "Equity": ["ifrs-full_Equity"]
}

STATEMENTS = {
    "Revenue": ["IS", "CIS"],
    "Operating_Profit": ["IS", "CIS"],
    "Liabilities": ["BS"],
    "Equity": ["BS"]
}


# 4. OpenDART 데이터 조회
def fetch_financials(corp_code):
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": "2024",
        "reprt_code": "11011",
        "fs_div": "CFS"
    }

    request = urllib.request.Request(
        URL + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "CorporateRiskIntelligence/0.3"}
    )

    try:
        with urllib.request.urlopen(
            request, timeout=20
        ) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"HTTP status: {error.code}"
        ) from None
    except urllib.error.URLError:
        raise RuntimeError(
            "Network connection failed"
        ) from None

    if data.get("status") != "000":
        raise RuntimeError(
            "OpenDART status: " + str(data.get("status"))
        )

    return data.get("list", [])


# 5. 공시 금액을 정수로 변환
def parse_amount(value):
    if value is None:
        return None

    value = str(value).replace(",", "").strip()

    if value in ("", "-"):
        return None

    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]

    return int(value)


# 6. 계정과목 정확하게 찾기
def find_account(rows, metric):
    matches = [
        row for row in rows
        if row.get("account_id") in ACCOUNT_IDS[metric]
        and row.get("sj_div") in STATEMENTS[metric]
        and row.get("account_detail", "-") in ("-", "")
    ]

    if len(matches) != 1:
        raise ValueError(
            f"{metric}: expected 1 account, found {len(matches)}"
        )

    return matches[0]


# 7. 기업별 재무비율 계산
def analyze_company(name, corp_code):
    rows = fetch_financials(corp_code)

    print("\n--- Account ID Diagnostic ---")

    keywords = [
        "매출",
        "수익",
        "영업이익",
        "부채총계",
        "자본총계"
    ]

    for row in rows:
        account_name = row.get("account_nm", "")

        if any(word in account_name for word in keywords):
            print(
                row.get("sj_div"),
                "|",
                row.get("account_nm"),
                "|",
                row.get("account_id"),
                "| detail:",
                row.get("account_detail"),
                "| fs:",
                row.get("fs_div")
            )


    revenue = find_account(rows, "Revenue")
    operating_profit = find_account(rows, "Operating_Profit")
    liabilities = find_account(rows, "Liabilities")
    equity = find_account(rows, "Equity")

    rev_2024 = parse_amount(revenue.get("thstrm_amount"))
    rev_2023 = parse_amount(revenue.get("frmtrm_amount"))

    op_2024 = parse_amount(
        operating_profit.get("thstrm_amount")
    )

    liab_2024 = parse_amount(
        liabilities.get("thstrm_amount")
    )

    equity_2024 = parse_amount(
        equity.get("thstrm_amount")
    )

    values = [
        rev_2024, rev_2023, op_2024,
        liab_2024, equity_2024
    ]

    if any(value is None for value in values):
        raise ValueError("Missing financial values")

    if rev_2023 == 0 or rev_2024 == 0:
        raise ValueError("Revenue denominator is zero")

    if equity_2024 <= 0:
        raise ValueError("Equity is zero or negative")

    revenue_growth = (
        rev_2024 / rev_2023 - 1
    ) * 100

    operating_margin = (
        op_2024 / rev_2024
    ) * 100

    debt_ratio = (
        liab_2024 / equity_2024
    ) * 100

    return {
        "Company": name,
        "Revenue_Growth": round(revenue_growth, 2),
        "Operating_Margin": round(operating_margin, 2),
        "Debt_Ratio": round(debt_ratio, 2)
    }



# 8. 모든 기업 분석
def analyze_all_companies():
    results = []
    errors = {}

    for company_name, corp_code in COMPANIES.items():
        try:
            result = analyze_company(
                company_name, corp_code
            )
            results.append(result)
        except Exception as error:
            errors[company_name] = (
                f"{type(error).__name__}: {error}"
            )

    return results, errors


# 터미널에서 직접 실행할 때만 출력
if __name__ == "__main__":
    results, errors = analyze_all_companies()

    print("=== Real Company Comparison ===")

    for result in results:
        print(result)

    for company, error in errors.items():
        print("FAILED:", company, error)

    print(f"Successfully analyzed: {len(results)}/3")
