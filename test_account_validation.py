
from financial_engine.dart_client import (
    COMPANIES,
    YEARS,
    fetch_company_history,
)
from financial_engine.validation import (
    validate_financial_data,
)


KEY_ACCOUNTS = [
    "revenue",
    "operating_income",
    "net_income",
    "assets",
    "liabilities",
    "equity",
    "receivables",
    "inventory",
    "operating_cash_flow",
]


def format_amount(value):
    if value is None:
        return "MISSING"

    return f"{value / 100000000:,.1f} KRW 100M"


for company, corp_code in COMPANIES.items():
    print(f"\n{'=' * 55}")
    print(company)
    print("=" * 55)

    history = fetch_company_history(corp_code)

    for year in YEARS:
        result = validate_financial_data(
            history[year], year
        )

        print(f"\nYEAR: {year}")
        print(
            "Completeness:",
            f"{result['completeness']}%"
        )
        print(
            "Balance Sheet:",
            result["balance_sheet_check"]
        )

        for account in KEY_ACCOUNTS:
            value = result["values"][account]
            print(
                f"  {account:25s}",
                format_amount(value)
            )

        if result["issues"]:
            print("Issues:")
            for issue in result["issues"]:
                print(
                    f"  [{issue['type']}]",
                    issue["account"]
                )
