
from financial_engine.dart_client import (
    COMPANIES,
    fetch_company_history,
)
from financial_engine.verified_screening import (
    run_verified_screening,
)
from financial_engine.explanation import (
    explain_screening,
)


def main():
    total_signals = 0
    total_skipped = 0

    for company, corp_code in COMPANIES.items():
        history = fetch_company_history(corp_code)

        screening = run_verified_screening(
            corp_code, history
        )
        result = explain_screening(screening)

        print("\n" + "=" * 70)
        print(f"COMPANY: {company}")
        print("=" * 70)

        for explanation in result["explanations"]:
            total_signals += 1

            print(
                f"\n[{explanation['year']}] "
                f"{explanation['title']}"
            )
            print("관찰:", explanation["observation"])
            print("해석:", explanation["interpretation"])

            print("추가 확인:")
            for question in explanation["verification_needed"]:
                print(f" - {question}")

            print(
                "결론 수준:",
                explanation["conclusion_level"],
            )

        for skipped in result["skipped"]:
            total_skipped += 1
            print(
                f"\n[검사 보류] {skipped['year']} "
                f"{skipped['signal']}: "
                f"{skipped['reason']}"
            )

    print("\n" + "=" * 70)
    print("INTEGRATION SUMMARY")
    print("Explained signals:", total_signals)
    print("Skipped checks:", total_skipped)


if __name__ == "__main__":
    main()
