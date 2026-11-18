
import csv

from financial_engine.dart_client import (
    COMPANIES,
    fetch_company_history,
)


KEYWORDS = [
    "영업활동",
    "당기순이익",
    "비현금",
    "조정",
    "운전자본",
    "영업활동으로 인한 자산",
    "영업활동으로 인한 부채",
    "매출채권",
    "재고자산",
    "감가상각",
    "이자",
    "법인세",
]


def is_relevant(row):
    name = row.get("account_nm", "")
    return any(word in name for word in KEYWORDS)


def diagnose_cashflow():
    output = []

    for company, corp_code in COMPANIES.items():
        history = fetch_company_history(corp_code)

        for year, rows in sorted(history.items()):
            for row in rows:
                if row.get("sj_div") != "CF":
                    continue

                if not is_relevant(row):
                    continue

                output.append({
                    "company": company,
                    "year": year,
                    "account_id": row.get("account_id", ""),
                    "account_nm": row.get("account_nm", ""),
                    "account_detail": row.get(
                        "account_detail", ""
                    ),
                    "current_amount": row.get(
                        "thstrm_amount", ""
                    ),
                    "previous_amount": row.get(
                        "frmtrm_amount", ""
                    ),
                })

    filename = "cashflow_diagnosis.csv"

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "company",
                "year",
                "account_id",
                "account_nm",
                "account_detail",
                "current_amount",
                "previous_amount",
            ],
        )
        writer.writeheader()
        writer.writerows(output)

    print(f"Saved: {filename}")
    print(f"Relevant cash flow rows: {len(output)}")

    for company in COMPANIES:
        count = sum(
            row["company"] == company
            for row in output
        )
        print(f"{company}: {count} rows")


if __name__ == "__main__":
    diagnose_cashflow()
