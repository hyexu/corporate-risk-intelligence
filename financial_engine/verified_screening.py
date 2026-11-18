
from financial_engine.comparability import (
    audit_comparatives,
    verified_growth,
)


THRESHOLD_PP = 15.0


def run_verified_screening(corp_code, history):
    audit_result = audit_comparatives(corp_code, history)
    extracted = audit_result["extracted"]
    bases = audit_result["growth_bases"]

    findings = []
    skipped = []

    for year in sorted(extracted):
        if year - 1 not in extracted:
            continue

        current = extracted[year]["values"]

        def get_growth(account):
            base = bases.get((year, account))
            return verified_growth(
                current.get(account), base
            )

        sales_growth = get_growth("revenue")

        # 매출채권·재고 증가율과 매출 성장률 비교
        for account, signal in [
            ("receivables", "RECEIVABLES_DIVERGENCE"),
            ("inventory", "INVENTORY_DIVERGENCE"),
        ]:
            asset_growth = get_growth(account)

            if sales_growth is None or asset_growth is None:
                skipped.append({
                    "year": year,
                    "signal": signal,
                    "reason": "Unverified comparative base",
                })
                continue

            gap = round(asset_growth - sales_growth, 2)

            if gap >= THRESHOLD_PP:
                findings.append({
                    "year": year,
                    "signal": signal,
                    "status": "SCREENING_SIGNAL",
                    "asset_growth_pct": asset_growth,
                    "revenue_growth_pct": sales_growth,
                    "gap_pp": gap,
                    "interpretation": (
                        "Asset growth exceeds revenue growth. "
                        "This is a review signal, not proof "
                        "of accounting misconduct."
                    ),
                })

        # 순이익 증가 + 영업현금흐름 감소
        previous_ni = bases.get((year, "net_income"))
        previous_ocf = bases.get(
            (year, "operating_cash_flow")
        )
        current_ni = current.get("net_income")
        current_ocf = current.get("operating_cash_flow")

        if None in (
            previous_ni, previous_ocf,
            current_ni, current_ocf
        ):
            skipped.append({
                "year": year,
                "signal": "EARNINGS_CASH_DIVERGENCE",
                "reason": "Unverified comparative base",
            })
        elif (
            current_ni > previous_ni
            and current_ocf < previous_ocf
        ):
            findings.append({
                "year": year,
                "signal": "EARNINGS_CASH_DIVERGENCE",
                "status": "SCREENING_SIGNAL",
                "net_income_change": current_ni - previous_ni,
                "ocf_change": current_ocf - previous_ocf,
                "interpretation": (
                    "Net income increased while operating "
                    "cash flow decreased. Review working "
                    "capital and noncash adjustments."
                ),
            })

    return {
        "audit": audit_result["audit"],
        "findings": findings,
        "skipped": skipped,
    }
