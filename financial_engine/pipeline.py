
"""
Corporate Risk Intelligence
Integrated financial analysis pipeline.
"""

from collections import Counter
from datetime import datetime, timezone

from financial_engine.dart_client import (
    fetch_company_history,
)
from financial_engine.account_mapping import extract_accounts
from financial_engine.ratios import calculate_company_ratios
from financial_engine.verified_screening import (
    run_verified_screening,
)
from financial_engine.explanation import explain_screening


def run_company_analysis(company, corp_code):
    """Run all analytical stages using one DART history fetch."""

    history = fetch_company_history(corp_code)

    if not history:
        raise ValueError(
            f"No financial history returned for {company}"
        )

    accounts = {}
    for year, rows in sorted(history.items()):
        values, issues, sources = extract_accounts(rows)
        accounts[year] = {
            "values": values,
            "issues": issues,
            "sources": sources,
        }

    # Existing modules remain responsible for their own rules.
    ratios = calculate_company_ratios(history)
    screening = run_verified_screening(corp_code, history)
    explanation = explain_screening(screening)

    audit_counts = dict(Counter(
        item["status"] for item in screening["audit"]
    ))

    return {
        "metadata": {
            "company": company,
            "corp_code": corp_code,
            "years": sorted(history),
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "data_source": "OpenDART",
            "statement_scope": "Consolidated (CFS)",
            "analysis_type": "Rule-based screening",
        },
        "accounts": accounts,
        "ratios": ratios,
        "comparability": {
            "audit": screening["audit"],
            "summary": audit_counts,
        },
        "screening": {
            "findings": screening["findings"],
            "skipped": screening["skipped"],
        },
        "explanations": explanation["explanations"],
        "limitations": [
            "Signals are not evidence of fraud.",
            "Screening thresholds are provisional.",
            "Unverified comparisons are excluded.",
            "Cash flow attribution is not yet verified.",
            "Financial services may affect comparability.",
        ],
    }
