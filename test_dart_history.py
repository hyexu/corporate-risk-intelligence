
from financial_engine.dart_client import (
    COMPANIES,
    YEARS,
    fetch_company_history,
)


for company_name, corp_code in COMPANIES.items():
    print(f"\nAnalyzing: {company_name}")

    try:
        history = fetch_company_history(corp_code)

        for year in YEARS:
            rows = history[year]

            print(
                f"  {year}: SUCCESS "
                f"({len(rows)} accounts)"
            )

    except Exception as error:
        print(
            "  FAILED:",
            type(error).__name__,
            str(error),
        )
