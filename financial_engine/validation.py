
from financial_engine.account_mapping import (
    ACCOUNT_MAPPING,
    extract_accounts,
)


def validate_financial_data(rows, year):
    values, issues, sources = extract_accounts(rows)

    assets = values["assets"]
    liabilities = values["liabilities"]
    equity = values["equity"]

    balance_sheet_check = "NOT_TESTED"

    if all(
        value is not None
        for value in (assets, liabilities, equity)
    ):
        difference = assets - (liabilities + equity)

        if difference == 0:
            balance_sheet_check = "PASS"
        else:
            balance_sheet_check = "FAIL"
            issues.append({
                "account": "balance_sheet",
                "type": "INCONSISTENT",
                "message": (
                    f"Assets - Liabilities - Equity = "
                    f"{difference}"
                ),
            })

    completeness = (
        sum(value is not None for value in values.values())
        / len(ACCOUNT_MAPPING)
        * 100
    )

    return {
        "year": year,
        "values": values,
        "sources": sources,
        "issues": issues,
        "balance_sheet_check": balance_sheet_check,
        "completeness": round(completeness, 1),
    }
