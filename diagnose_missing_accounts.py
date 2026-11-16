
import csv
from pathlib import Path

from financial_engine.dart_client import (
    COMPANIES,
    YEARS,
    fetch_company_history,
)
from financial_engine.account_mapping import (
    ACCOUNT_MAPPING,
    extract_accounts,
)


KEYWORDS = {
    "revenue": ["revenue", "sales", "매출", "영업수익"],
    "operating_income": [
        "operatingincomeloss", "영업이익"
    ],
    "net_income": ["profitloss", "당기순이익"],
    "assets": ["assets", "자산총계"],
    "liabilities": ["liabilities", "부채총계"],
    "equity": ["equity", "자본총계"],
    "current_assets": ["currentassets", "유동자산"],
    "current_liabilities": [
        "currentliabilities", "유동부채"
    ],
    "receivables": [
        "receivable", "매출채권", "미수금"
    ],
    "inventory": ["inventor", "재고자산"],
    "operating_cash_flow": [
        "operatingactivities",
        "영업활동현금흐름",
        "영업활동으로인한현금흐름",
    ],
}


def find_candidates(rows, account):
    keywords = KEYWORDS[account]
    sections = ACCOUNT_MAPPING[account]["sections"]
    matches = []

    for row in rows:
        if row.get("sj_div") not in sections:
            continue

        account_id = str(row.get("account_id", ""))
        account_nm = str(row.get("account_nm", ""))

        searchable = (
            account_id + " " + account_nm
        ).lower().replace(" ", "")

        if any(k.lower() in searchable for k in keywords):
            matches.append({
                "account_id": account_id,
                "account_nm": account_nm,
                "sj_div": row.get("sj_div"),
                "account_detail": row.get("account_detail"),
                "amount": row.get("thstrm_amount"),
            })

    return matches


output = []
summary = []

for company, corp_code in COMPANIES.items():
    history = fetch_company_history(corp_code)

    for year in YEARS:
        rows = history[year]
        values, issues, sources = extract_accounts(rows)

        missing = [
            issue["account"]
            for issue in issues
            if issue["type"] in ("MISSING", "AMBIGUOUS")
        ]

        summary.append({
            "company": company,
            "year": year,
            "missing": ", ".join(missing),
        })

        for account in missing:
            candidates = find_candidates(rows, account)

            if not candidates:
                output.append({
                    "company": company,
                    "year": year,
                    "target": account,
                    "account_id": "",
                    "account_nm": "",
                    "sj_div": "",
                    "account_detail": "",
                    "amount": "",
                })

            for candidate in candidates:
                output.append({
                    "company": company,
                    "year": year,
                    "target": account,
                    **candidate,
                })


path = Path("missing_account_diagnosis.csv")

with path.open(
    "w", newline="", encoding="utf-8-sig"
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "company", "year", "target",
            "account_id", "account_nm",
            "sj_div", "account_detail", "amount",
        ],
    )
    writer.writeheader()
    writer.writerows(output)


print("\n=== MISSING ACCOUNT SUMMARY ===")

for item in summary:
    print(
        item["company"],
        item["year"],
        "->",
        item["missing"] or "NONE",
    )

print("\nSaved:", path)
print("Candidate rows:", len(output))
