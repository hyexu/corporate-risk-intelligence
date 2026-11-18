
from financial_engine.account_mapping import extract_accounts


TRADE_RECEIVABLE_IDS = {
    "ifrs-full_CurrentTradeReceivables",
    "dart_ShortTermTradeReceivable",
}

# 검증된 계정 정의만 등록한다.
EQUIVALENT_IDS = {
    "receivables": TRADE_RECEIVABLE_IDS,
}

# 기업별 비표준 계정 매핑: 다른 기업에 자동 적용하지 않음.
CUSTOM_EQUIVALENTS = {
    ("00164742", 2022, "net_income"): {
        "account_id": "-표준계정코드 미사용-",
        "account_nm": "연결당기순이익",
        "standard_id": "ifrs-full_ProfitLoss",
    },
}

# 공시 근거를 검토해 승인한 경우에만 여기에 추가한다.
# 아직 자동 승인된 재작성 사례는 없음.
APPROVED_RESTATEMENTS = {}


def account_equivalent(
    account, source_a, source_b,
    corp_code=None, year_a=None, year_b=None
):
    if not source_a or not source_b:
        return False

    id_a = source_a.get("account_id")
    id_b = source_b.get("account_id")

    if id_a == id_b:
        return True

    allowed = EQUIVALENT_IDS.get(account, set())
    if id_a in allowed and id_b in allowed:
        return True

    for year, source, other_id in (
        (year_a, source_a, id_b),
        (year_b, source_b, id_a),
    ):
        rule = CUSTOM_EQUIVALENTS.get(
            (corp_code, year, account)
        )
        if not rule:
            continue

        if (
            source.get("account_id") == rule["account_id"]
            and source.get("account_nm") == rule["account_nm"]
            and other_id == rule["standard_id"]
        ):
            return True

    return False


def audit_comparatives(corp_code, history):
    """
    Compare original annual figures with comparative
    figures reported in the following annual report.
    """
    extracted = {}

    for year, rows in sorted(history.items()):
        values, issues, sources = extract_accounts(rows)
        extracted[year] = {
            "values": values,
            "issues": issues,
            "sources": sources,
        }

    audit = []
    bases = {}

    for year in sorted(history):
        previous_year = year - 1
        if previous_year not in extracted:
            continue

        original = extracted[previous_year]
        comparative_values, comparative_issues, comparative_sources = (
            extract_accounts(
                history[year],
                amount_field="frmtrm_amount",
            )
        )

        for account, original_value in original["values"].items():
            comparative_value = comparative_values.get(account)
            source_a = original["sources"].get(account)
            source_b = comparative_sources.get(account)

            equivalent = account_equivalent(
                account,
                source_a,
                source_b,
                corp_code=corp_code,
                year_a=previous_year,
                year_b=previous_year,
            )

            if original_value is None or comparative_value is None:
                status = "MISSING"
            elif not equivalent:
                status = "NOT_COMPARABLE"
            elif original_value == comparative_value:
                status = (
                    "PASS"
                    if source_a.get("account_id")
                    == source_b.get("account_id")
                    else "PASS_EQUIVALENT"
                )
            else:
                approval = APPROVED_RESTATEMENTS.get(
                    (corp_code, previous_year, year, account)
                )
                status = (
                    "RESTATED_VERIFIED"
                    if approval
                    and approval.get("original") == original_value
                    and approval.get("comparative") == comparative_value
                    and approval.get("source_url")
                    else "REVIEW"
                )

            audit.append({
                "company_code": corp_code,
                "report_year": year,
                "financial_year": previous_year,
                "account": account,
                "status": status,
                "original": original_value,
                "comparative": comparative_value,
                "original_id": (
                    source_a.get("account_id") if source_a else None
                ),
                "comparative_id": (
                    source_b.get("account_id") if source_b else None
                ),
            })

            # Growth calculations can use only verified bases.
            if status in {
                "PASS", "PASS_EQUIVALENT", "RESTATED_VERIFIED"
            }:
                bases[(year, account)] = comparative_value

    return {
        "audit": audit,
        "growth_bases": bases,
        "extracted": extracted,
    }


def verified_growth(current_value, previous_value):
    if (
        current_value is None
        or previous_value is None
        or previous_value <= 0
    ):
        return None

    return round(
        (current_value / previous_value - 1) * 100, 2
    )
