
from financial_engine.dart_client import (
    COMPANIES,
    fetch_financial_statement,
)
from financial_engine.account_mapping import extract_accounts


TARGETS = ["revenue", "operating_income", "net_income"]


def show_source(source):
    if not source:
        return "SOURCE NOT FOUND"

    return (
        f"id={source.get('account_id')} | "
        f"name={source.get('account_nm')} | "
        f"statement={source.get('sj_div')} | "
        f"field={source.get('amount_field')}"
    )


def diagnose_company(company, corp_code):
    rows_2022 = fetch_financial_statement(corp_code, 2022)
    rows_2023 = fetch_financial_statement(corp_code, 2023)

    original, issues_2022, sources_2022 = extract_accounts(
        rows_2022,
        amount_field="thstrm_amount",
    )

    comparative, issues_2023, sources_2023 = extract_accounts(
        rows_2023,
        amount_field="frmtrm_amount",
    )

    print("\n" + "=" * 72)
    print(company)
    print("=" * 72)

    for account in TARGETS:
        a = original.get(account)
        b = comparative.get(account)

        print(f"\nACCOUNT: {account}")
        print(f"2022 ORIGINAL: {a:,}" if a is not None
              else "2022 ORIGINAL: MISSING")
        print(f"2023 COMPARATIVE: {b:,}" if b is not None
              else "2023 COMPARATIVE: MISSING")

        if a is not None and b is not None:
            difference = b - a
            pct = difference / abs(a) * 100 if a != 0 else None

            print(f"DIFFERENCE: {difference:,} KRW")
            print(
                f"DIFFERENCE RATE: {pct:.4f}%"
                if pct is not None else
                "DIFFERENCE RATE: N/A"
            )

        print("ORIGINAL SOURCE:")
        print(" ", show_source(sources_2022.get(account)))

        print("COMPARATIVE SOURCE:")
        print(" ", show_source(sources_2023.get(account)))

    for label, issues in [
        ("2022 ORIGINAL ISSUES", issues_2022),
        ("2023 COMPARATIVE ISSUES", issues_2023),
    ]:
        relevant = [
            issue for issue in issues
            if issue.get("account") in TARGETS
        ]
        if relevant:
            print(f"\n{label}")
            for issue in relevant:
                print(" ", issue)


for company, corp_code in COMPANIES.items():
    diagnose_company(company, corp_code)
