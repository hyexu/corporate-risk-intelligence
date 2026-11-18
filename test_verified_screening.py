
from financial_engine.dart_client import (
    COMPANIES,
    fetch_company_history,
)
from financial_engine.verified_screening import (
    run_verified_screening,
)


for company, corp_code in COMPANIES.items():
    history = fetch_company_history(corp_code)
    result = run_verified_screening(corp_code, history)

    print("\n" + "=" * 65)
    print("COMPANY:", company)

    print("\nVERIFIED SCREENING SIGNALS")
    if not result["findings"]:
        print("No signals under current rules.")

    for finding in result["findings"]:
        print(finding)

    print("\nSKIPPED CHECKS")
    if not result["skipped"]:
        print("None")

    for item in result["skipped"]:
        print(item)
