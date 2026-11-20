
from financial_engine.account_mapping import extract_accounts
from financial_engine.ratios import calculate_company_ratios


PURE_TRADE_IDS = {
    "ifrs-full_CurrentTradeReceivables",
    "dart_ShortTermTradeReceivable",
}

REQUIRED = (
    "revenue", "operating_income", "net_income",
    "assets", "liabilities", "equity",
    "operating_cash_flow", "receivables", "inventory",
)


def comparable(a, b, account):
    """계정 범위가 비교 가능한지 보수적으로 검사."""
    if not a or not b:
        return False

    id_a = a.get("account_id")
    id_b = b.get("account_id")

    if account == "receivables":
        return id_a in PURE_TRADE_IDS and id_b in PURE_TRADE_IDS

    if id_a == id_b:
        return True

    # 표준 ID에서 비표준 ID로 변경된 경우 자동 승인하지 않음
    return False


def pct_change(current, previous):
    if current is None or previous is None or previous <= 0:
        return None
    return (current / previous - 1) * 100


def evaluate_history(history):
    """
    반환:
      audit: 데이터 품질 및 비교정보 검사
      findings: 회계 이상징후 탐색 결과
      ratios: 기존 재무비율 계산 결과
    """
    ratios = calculate_company_ratios(history)
    extracted = {}

    for year, rows in sorted(history.items()):
        values, issues, sources = extract_accounts(rows)
        extracted[year] = {
            "values": values,
            "sources": sources,
            "issues": issues,
        }

    audit = []
    findings = []

    for year in sorted(extracted):
        current = extracted[year]
        previous = extracted.get(year - 1)

        missing = [
            key for key in REQUIRED
            if current["values"].get(key) is None
        ]

        audit.append({
            "year": year,
            "check": "required_accounts",
            "status": "PASS" if not missing else "REVIEW",
            "details": ", ".join(missing) if missing else "Complete",
        })

        if previous is None:
            continue

        # 당기 공시의 전기 비교금액과 전기 공시의 당기금액 비교
        prior_in_current, _, prior_sources = extract_accounts(
            history[year], "frmtrm_amount"
        )

        for account in REQUIRED:
            old_value = previous["values"].get(account)
            comparison = prior_in_current.get(account)

            old_source = previous["sources"].get(account)
            comparison_source = prior_sources.get(account)

            if (
                old_value is None or comparison is None
                or not comparable(
                    old_source, comparison_source, account
                )
            ):
                status = "NOT_VERIFIED"
                detail = "Missing or non-comparable account"
            elif old_value == comparison:
                status = "PASS"
                detail = "Amounts match"
            else:
                status = "REVIEW"
                detail = (
                    f"Original={old_value}, "
                    f"Comparative={comparison}"
                )

            audit.append({
                "year": year,
                "check": f"prior_year_{account}",
                "status": status,
                "details": detail,
            })

        v = current["values"]
        p = previous["values"]
        s = current["sources"]
        ps = previous["sources"]

        # 매출 성장률
        sales_growth = None
        if comparable(s.get("revenue"), ps.get("revenue"), "revenue"):
            sales_growth = pct_change(
                v["revenue"], p["revenue"]
            )

        # 1. 매출채권과 매출의 성장률 괴리
        if comparable(
            s.get("receivables"), ps.get("receivables"),
            "receivables"
        ):
            ar_growth = pct_change(
                v["receivables"], p["receivables"]
            )

            if (
                sales_growth is not None
                and ar_growth is not None
                and ar_growth - sales_growth >= 15
            ):
                findings.append({
                    "year": year,
                    "signal": "RECEIVABLES_DIVERGENCE",
                    "severity": "REVIEW",
                    "evidence": (
                        f"AR growth={ar_growth:.1f}%, "
                        f"Revenue growth={sales_growth:.1f}%"
                    ),
                    "interpretation": (
                        "Receivables grew substantially "
                        "faster than revenue."
                    ),
                    "follow_up": (
                        "Review collection terms, "
                        "aging and loss allowances."
                    ),
                })

        # 2. 재고 증가율과 매출 성장률 괴리
        if comparable(
            s.get("inventory"), ps.get("inventory"),
            "inventory"
        ):
            inv_growth = pct_change(
                v["inventory"], p["inventory"]
            )

            if (
                sales_growth is not None
                and inv_growth is not None
                and inv_growth - sales_growth >= 15
            ):
                findings.append({
                    "year": year,
                    "signal": "INVENTORY_DIVERGENCE",
                    "severity": "REVIEW",
                    "evidence": (
                        f"Inventory growth={inv_growth:.1f}%, "
                        f"Revenue growth={sales_growth:.1f}%"
                    ),
                    "interpretation": (
                        "Inventory grew substantially "
                        "faster than revenue."
                    ),
                    "follow_up": (
                        "Review demand, inventory turnover "
                        "and write-downs."
                    ),
                })

        # 3. 이익 증가와 영업현금흐름 감소
        if (
            comparable(s.get("net_income"), ps.get("net_income"),
                       "net_income")
            and comparable(
                s.get("operating_cash_flow"),
                ps.get("operating_cash_flow"),
                "operating_cash_flow"
            )
        ):
            ni = v["net_income"]
            prev_ni = p["net_income"]
            ocf = v["operating_cash_flow"]
            prev_ocf = p["operating_cash_flow"]

            if (
                None not in (ni, prev_ni, ocf, prev_ocf)
                and ni > prev_ni
                and ocf < prev_ocf
            ):
                findings.append({
                    "year": year,
                    "signal": "EARNINGS_CASH_DIVERGENCE",
                    "severity": "REVIEW",
                    "evidence": (
                        f"Net income change={ni - prev_ni:,} KRW; "
                        f"OCF change={ocf - prev_ocf:,} KRW"
                    ),
                    "interpretation": (
                        "Net income increased while "
                        "operating cash flow decreased."
                    ),
                    "follow_up": (
                        "Review working capital, "
                        "noncash items and cash flow notes."
                    ),
                })

    return {
        "audit": audit,
        "findings": findings,
        "ratios": ratios,
    }
