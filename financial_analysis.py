
import os
import json
import urllib.parse
import urllib.request

# 1. API 인증키 가져오기
api_key = os.getenv("OPENDART_API_KEY")

if not api_key:
    raise RuntimeError("OpenDART Secret is missing")

# 2. 삼성전자 2024년 연결재무제표 요청
url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"

params = {
    "crtfc_key": api_key,
    "corp_code": "00126380",
    "bsns_year": "2024",
    "reprt_code": "11011",
    "fs_div": "CFS"
}

request = urllib.request.Request(
    url + "?" + urllib.parse.urlencode(params),
    headers={"User-Agent": "CorporateRiskIntelligence/0.1"}
)

with urllib.request.urlopen(request, timeout=20) as response:
    data = json.load(response)

if data.get("status") != "000":
    raise RuntimeError(
        "OpenDART error: " + str(data.get("message"))
    )

rows = data["list"]

# 3. 금액을 정수로 변환
def parse_amount(value):
    if value is None:
        return None

    value = str(value).replace(",", "").strip()

    if value in ("", "-"):
        return None

    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]

    return int(value)


# 4. 계정 ID로 정확한 항목 찾기
def find_account(account_ids, statement):
    matches = [
        row for row in rows
        if row.get("account_id") in account_ids
        and row.get("sj_div") in statement
        and row.get("account_detail", "-") in ("-", "")
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected one matching account: {account_ids}, "
            f"found {len(matches)}"
        )

    return matches[0]


# 5. 주요 계정 추출
revenue = find_account(
    ["ifrs-full_Revenue"],
    ["IS", "CIS"]
)

operating_profit = find_account(
    ["dart_OperatingIncomeLoss"],
    ["IS", "CIS"]
)

liabilities = find_account(
    ["ifrs-full_Liabilities"],
    ["BS"]
)

equity = find_account(
    ["ifrs-full_Equity"],
    ["BS"]
)

# 6. 당기 / 전기 금액 추출
revenue_2024 = parse_amount(revenue["thstrm_amount"])
revenue_2023 = parse_amount(revenue["frmtrm_amount"])

op_2024 = parse_amount(operating_profit["thstrm_amount"])
liabilities_2024 = parse_amount(liabilities["thstrm_amount"])
equity_2024 = parse_amount(equity["thstrm_amount"])

values = [
    revenue_2024,
    revenue_2023,
    op_2024,
    liabilities_2024,
    equity_2024
]

if any(value is None for value in values):
    raise ValueError("Some financial amounts are missing")

if revenue_2023 == 0 or revenue_2024 == 0:
    raise ValueError("Revenue denominator is zero")

if equity_2024 <= 0:
    raise ValueError("Equity is zero or negative")

# 7. 재무비율 계산
revenue_growth = (
    revenue_2024 / revenue_2023 - 1
) * 100

operating_margin = (
    op_2024 / revenue_2024
) * 100

debt_ratio = (
    liabilities_2024 / equity_2024
) * 100

# 8. 결과 출력
print("\n=== Samsung Electronics ===")
print("Fiscal Year: 2024")
print("Statements: Consolidated")
print("Unit: KRW 100 million")

print("\n=== Financial Data ===")
print(f"2024 Revenue: {revenue_2024 / 1e8:,.0f}")
print(f"2023 Revenue: {revenue_2023 / 1e8:,.0f}")
print(f"2024 Operating Profit: {op_2024 / 1e8:,.0f}")
print(f"2024 Liabilities: {liabilities_2024 / 1e8:,.0f}")
print(f"2024 Equity: {equity_2024 / 1e8:,.0f}")

print("\n=== Financial Ratios ===")
print(f"Revenue Growth: {revenue_growth:.2f}%")
print(f"Operating Margin: {operating_margin:.2f}%")
print(f"Debt Ratio: {debt_ratio:.2f}%")
