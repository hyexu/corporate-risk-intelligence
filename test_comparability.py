
from collections import Counter

from financial_engine.dart_client import (
    COMPANIES,
    fetch_company_history,
)
from financial_engine.comparability import (
    audit_comparatives,
    verified_growth,
)


TARGETS = {
    "revenue",
    "operating_income",
    "net_income",
    "receivables",
    "inventory",
}


for company, corp_code in COMPANIES.items():
    history = fetch_company_history(corp_code)
    result = audit_comparatives(corp_code, history)

    print("\n" + "=" * 70)
    print("COMPANY:", company)
    print("=" * 70)

    counts = Counter(
        item["status"] for item in result["audit"]
    )

    print("\nAUDIT SUMMARY")
    for status, count in sorted(counts.items()):
        print(f"{status:22s} {count}")

    print("\nTARGET ACCOUNT AUDIT")

    for item in result["audit"]:
        if item["account"] not in TARGETS:
            continue

        print(
            f"{item['report_year']} "
            f"{item['account']:20s} "
            f"{item['status']}"
        )

        if item["status"] in {
            "REVIEW", "NOT_COMPARABLE", "MISSING"
        }:
            print("  Original:", item["original"])
            print("  Comparative:", item["comparative"])
            print("  Original ID:", item["original_id"])
            print("  Comparative ID:", item["comparative_id"])

    print("\nVERIFIED REVENUE GROWTH")

    for year in sorted(history):
        if year - 1 not in history:
            continue

        current = result["extracted"][year]["values"]["revenue"]
        base = result["growth_bases"].get((year, "revenue"))

        growth = verified_growth(current, base)

        print(
            f"{year}: "
            f"{growth:.2f}%"
            if growth is not None
            else f"{year}: NOT VERIFIED"
        )
