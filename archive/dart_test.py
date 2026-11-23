
import os
import json
import urllib.parse
import urllib.request
import urllib.error

# GitHub Codespaces Secret에서 인증키 읽기
api_key = os.getenv("OPENDART_API_KEY")

if not api_key:
    raise RuntimeError("OPENDART_API_KEY is not configured")

# OpenDART 단일회사 전체 재무제표 API
url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"

params = {
    "crtfc_key": api_key,
    "corp_code": "00126380",  # 삼성전자
    "bsns_year": "2024",
    "reprt_code": "11011",     # 사업보고서
    "fs_div": "CFS"            # 연결재무제표
}

# URL 생성 및 API 호출
query = urllib.parse.urlencode(params)
request = urllib.request.Request(
    url + "?" + query,
    headers={"User-Agent": "CorporateRiskIntelligence/0.1"}
)

try:
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)
except urllib.error.HTTPError as e:
    raise RuntimeError(f"HTTP error: {e.code}") from None
except urllib.error.URLError:
    raise RuntimeError("Network connection failed") from None

# 응답 상태 확인
status = data.get("status")
print("OpenDART Status:", status)

if status != "000":
    print("OpenDART Message:", data.get("message"))
    raise SystemExit(1)

rows = data.get("list", [])

print("Company: Samsung Electronics")
print("Year: 2024")
print("Financial Statements: Consolidated")
print("Total account rows:", len(rows))
print("\n=== Sample Financial Accounts ===")

# 계정과목 15개만 출력
for row in rows[:15]:
    print(
        row.get("sj_div"),
        "|",
        row.get("account_nm"),
        "|",
        row.get("thstrm_amount"),
        row.get("currency", "")
    )
