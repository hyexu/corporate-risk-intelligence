
from financial_engine.dart_client import (
    COMPANIES,
    fetch_company_history,
)
from financial_engine.ratios import (
    METRIC_LABELS,
    calculate_company_ratios,
)


for company, corp_code in COMPANIES.items():
    print("\n" + "=" * 65)
    print("COMPANY:", company)
    print("=" * 65)

    history = fetch_company_history(corp_code)
    results = calculate_company_ratios(history)

    for year, data in results.items():
        print(f"\n--- {year} ---")

        for key, label in METRIC_LABELS.items():
            value = data["metrics"][key]

            if value is None:
                display = "N/A"
            else:
                display = f"{value:,.2f}"

            print(f"{label:30s} {display}")

        if data["warnings"]:
            print("\nData Quality Warnings:")
            for warning in data["warnings"]:
                print(" -", warning)
