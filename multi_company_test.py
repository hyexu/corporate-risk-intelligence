
import os
import json
import urllib.parse
import urllib.request
import urllib.error

# Codespaces Secret에서 인증키 가져오기
api_key = os.getenv("OPENDART_API_KEY")

if not api_key:
    raise RuntimeError("OpenDART API key is missing")

# 분석 대상 기업
companies = {
    "Samsung Electronics": "00126380",
    "SK Hynix": "00164779",
    "Hyundai Motor": "00164742"
}

url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"


def fetch_financials(corp_code):
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": "2024",
        "reprt_code": "11011",
        "fs_div": "CFS"
    }

    query = urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url + "?" + query,
        headers={"User-Agent": "CorporateRiskIntelligence/0.3"}
    )

    try:
        with urllib.request.urlopen(
            request, timeout=20
        ) as response:
            data = json.load(response)

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"HTTP status {error.code}"
        ) from None

    except urllib.error.URLError:
        raise RuntimeError(
            "Network connection failed"
        ) from None

    if data.get("status") != "000":
        raise RuntimeError(
            "OpenDART status: "
            + str(data.get("status"))
            + " - "
            + str(data.get("message"))
        )

    return data.get("list", [])


print("=== Multi-Company OpenDART Test ===")
print("Year: 2024 | Statements: Consolidated")

for company_name, corp_code in companies.items():
    print(f"\nCompany: {company_name}")

    try:
        rows = fetch_financials(corp_code)

        print("Status: SUCCESS")
        print("Financial account rows:", len(rows))

        if not rows:
            print("WARNING: No financial accounts returned")

        # 재무제표 종류 확인
        statement_types = sorted({
            row.get("sj_div", "")
            for row in rows
        })

        print("Statement types:", statement_types)

    except Exception as error:
        print("Status: FAILED")
        print("Error:", error)
