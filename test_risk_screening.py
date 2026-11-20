
from collections import Counter

from financial_engine.dart_client import (
    COMPANIES,
    fetch_company_history,
)
from financial_engine.risk_screening import evaluate_history


for company, corp_code in COMPANIES.items():
    print("\n" + "=" * 65)
    print("COMPANY:", company)
    print("=" * 65)

    history = fetch_company_history(corp_code)
    result = evaluate_history(history)

    counts = Counter(
        item["status"] for item in result["audit"]
    )

    print("\nDATA QUALITY AUDIT")
    for status in ("PASS", "REVIEW", "NOT_VERIFIED"):
        print(f"  {status}: {counts[status]}")

    for item in result["audit"]:
        if item["status"] != "PASS":
            print(
                f"  [{item['status']}] "
                f"{item['year']} {item['check']}: "
                f"{item['details']}"
            )

    print("\nACCOUNTING RISK SIGNALS")

    if not result["findings"]:
        print("  No signals detected under current rules.")

    for item in result["findings"]:
        print(f"\n  YEAR: {item['year']}")
        print(f"  SIGNAL: {item['signal']}")
        print(f"  EVIDENCE: {item['evidence']}")
        print(f"  INTERPRETATION: {item['interpretation']}")
        print(f"  FOLLOW-UP: {item['follow_up']}")
