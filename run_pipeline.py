
import json
from pathlib import Path

from financial_engine.dart_client import COMPANIES
from financial_engine.pipeline import run_company_analysis


def main():
    output_dir = Path("analysis_outputs")
    output_dir.mkdir(exist_ok=True)

    summaries = []

    for company, corp_code in COMPANIES.items():
        print(f"\nAnalyzing: {company}")

        result = run_company_analysis(company, corp_code)

        filename = (
            company.lower()
            .replace(" ", "_")
            + "_analysis.json"
        )

        output_path = output_dir / filename

        with output_path.open(
            "w", encoding="utf-8"
        ) as file:
            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

        signal_count = len(
            result["screening"]["findings"]
        )
        skipped_count = len(
            result["screening"]["skipped"]
        )

        summaries.append({
            "company": company,
            "signals": signal_count,
            "skipped": skipped_count,
        })

        print(f"Saved: {output_path}")
        print(f"Signals: {signal_count}")
        print(f"Skipped: {skipped_count}")

    print("\nINTEGRATED PIPELINE SUMMARY")

    for item in summaries:
        print(
            f"{item['company']}: "
            f"{item['signals']} signals, "
            f"{item['skipped']} skipped"
        )

    print(
        "TOTAL SIGNALS:",
        sum(item["signals"] for item in summaries),
    )
    print(
        "TOTAL SKIPPED:",
        sum(item["skipped"] for item in summaries),
    )


if __name__ == "__main__":
    main()
