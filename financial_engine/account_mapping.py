
from decimal import Decimal, InvalidOperation


# 표준 분석 항목과 OpenDART 계정 ID
ACCOUNT_MAPPING = {
    "revenue": {
        "ids": ["ifrs-full_Revenue"],
        "sections": ["IS", "CIS"],
    },
    "operating_income": {
        "ids": ["dart_OperatingIncomeLoss"],
        "sections": ["IS", "CIS"],
    },
    "net_income": {
        "ids": ["ifrs-full_ProfitLoss"],
        "sections": ["IS", "CIS"],
    },
    "assets": {
        "ids": ["ifrs-full_Assets"],
        "sections": ["BS"],
    },
    "liabilities": {
        "ids": ["ifrs-full_Liabilities"],
        "sections": ["BS"],
    },
    "equity": {
        "ids": ["ifrs-full_Equity"],
        "sections": ["BS"],
    },
    "current_assets": {
        "ids": ["ifrs-full_CurrentAssets"],
        "sections": ["BS"],
    },
    "current_liabilities": {
        "ids": ["ifrs-full_CurrentLiabilities"],
        "sections": ["BS"],
    },

    "receivables": {
        "ids": [
            "ifrs-full_TradeAndOtherCurrentReceivables",
            "ifrs-full_CurrentTradeReceivables",
            "dart_ShortTermTradeReceivable",
        ],
        "sections": ["BS"],
    },
    "inventory": {
        "ids": ["ifrs-full_Inventories"],
        "sections": ["BS"],
    },
    "operating_cash_flow": {
        "ids": [
            "ifrs-full_CashFlowsFromUsedInOperatingActivities"
        ],
        "sections": ["CF"],
    },
}


def parse_amount(value):
    """공시 금액을 정수로 변환. 결측값은 None."""
    if value is None:
        return None

    value = str(value).strip().replace(",", "")

    if value in ("", "-", "–", "—"):
        return None

    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]

    try:
        number = Decimal(value)

        if not number.is_finite():
            return None

        if number != number.to_integral_value():
            return None

        return int(number)

    except InvalidOperation:
        return None


def extract_accounts(rows, amount_field="thstrm_amount"):
    """
    원자료에서 표준 계정 추출.

    반환값:
      values: 계정별 금액 또는 None
      issues: 매핑 관련 문제
      sources: 사용된 공시 원자료 정보
    """
    values = {}
    issues = []
    sources = {}

    for name, config in ACCOUNT_MAPPING.items():
        candidates = []

        for row in rows:
            account_id = row.get("account_id")
            account_nm = str(row.get("account_nm", "")).strip()

            standard_match = account_id in config["ids"]

            # 비표준 계정은 확인된 명칭으로만 제한적 허용
            custom_net_income = (
                name == "net_income"
                and account_id == "-표준계정코드 미사용-"
                and account_nm == "연결당기순이익"
                and row.get("sj_div") in ("IS", "CIS")
                )

            if not (standard_match or custom_net_income):
                continue


            if row.get("sj_div") not in config["sections"]:
                continue

            detail = row.get("account_detail")

            # 세부 사업부문·자본변동 구성요소는 제외
            if detail not in (None, "", "-"):
                continue

            amount = parse_amount(row.get(amount_field))

            if amount is None:
                continue

            candidates.append((row, amount))

        # 순수 유동 매출채권이 존재하면
        # 범위가 더 넓은 합산 계정은 제외
        if name == "receivables":
            preferred_ids = [
                "ifrs-full_CurrentTradeReceivables",
                "dart_ShortTermTradeReceivable",
            ]

            preferred = [
                (row, amount)
                for row, amount in candidates
                if row.get("account_id") in preferred_ids
            ]

            if preferred:
                candidates = preferred

        # 같은 금액이 중복 표기되었다면 하나로 정리
        unique_amounts = set(
            amount for _, amount in candidates
        )

        if len(unique_amounts) == 1:
            row, amount = candidates[0]

            values[name] = amount
            sources[name] = {
                "account_id": row.get("account_id"),
                "account_nm": row.get("account_nm"),
                "sj_div": row.get("sj_div"),
                "amount_field": amount_field,
            }

        elif len(unique_amounts) > 1:
            values[name] = None
            sources[name] = None
            issues.append({
                "account": name,
                "type": "AMBIGUOUS",
                "message": "Conflicting account values",
            })

        else:
            values[name] = None
            sources[name] = None
            issues.append({
                "account": name,
                "type": "MISSING",
                "message": "Account not found",
            })

    return values, issues, sources
