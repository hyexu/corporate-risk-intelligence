
"""
Three-year accounting ratio analysis.

Uses verified OpenDART comparisons where year-over-year
comparability is required.

This module generates analytical observations, not audit opinions.
"""


VERIFIED = {
    "PASS",
    "PASS_EQUIVALENT",
    "RESTATED_VERIFIED",
}


def _value(result, year, account):
    accounts = result.get("accounts", {})
    entry = accounts.get(str(year), accounts.get(year, {}))
    value = entry.get("values", {}).get(account)

    if value is None or isinstance(value, bool):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _audit_item(result, year, account):
    audit = result.get("comparability", {}).get("audit", [])

    matches = [
        item for item in audit
        if str(item.get("report_year")) == str(year)
        and item.get("account") == account
    ]

    if len(matches) != 1:
        return None

    item = matches[0]

    if item.get("status") not in VERIFIED:
        return None

    return item


def _comparable_pair(result, year, account):
    item = _audit_item(result, year, account)

    if item is None:
        return None

    current = _value(result, year, account)

    try:
        previous = float(item["comparative"])
    except (TypeError, ValueError, KeyError):
        return None

    if current is None:
        return None

    return current, previous


def _divide(a, b, scale=1):
    if a is None or b is None or b == 0:
        return None

    return a / b * scale


def _growth(result, year, account):
    pair = _comparable_pair(result, year, account)

    if pair is None:
        return None

    current, previous = pair

    if previous <= 0:
        return None

    return (current / previous - 1) * 100


def _metric(name, value, unit, meaning, limitation):
    return {
        "name": name,
        "value": value,
        "unit": unit,
        "meaning": meaning,
        "limitation": limitation,
    }


def calculate_accounting_ratios(result):
    years = sorted(
        int(year) for year in result.get("accounts", {})
    )

    output = {}

    for year in years:
        revenue = _value(result, year, "revenue")
        operating_income = _value(
            result, year, "operating_income"
        )
        net_income = _value(result, year, "net_income")
        assets = _value(result, year, "assets")
        liabilities = _value(result, year, "liabilities")
        equity = _value(result, year, "equity")
        current_assets = _value(
            result, year, "current_assets"
        )
        current_liabilities = _value(
            result, year, "current_liabilities"
        )
        ocf = _value(
            result, year, "operating_cash_flow"
        )

        average_assets = None

        if year > min(years):
            asset_pair = _comparable_pair(
                result, year, "assets"
            )

            if asset_pair is not None:
                average_assets = (
                    asset_pair[0] + asset_pair[1]
                ) / 2

        metrics = {
            "operating_margin": _metric(
                "영업이익률",
                _divide(operating_income, revenue, 100),
                "%",
                "매출액 대비 영업이익 창출능력",
                "사업구조와 일회성 손익의 영향 고려",
            ),
            "roa": _metric(
                "총자산순이익률(ROA)",
                _divide(net_income, average_assets, 100),
                "%",
                "평균 총자산 대비 순이익 창출능력",
                "평균 총자산이 검증되지 않으면 보류",
            ),
            "debt_ratio": _metric(
                "부채비율",
                _divide(liabilities, equity, 100),
                "%",
                "자기자본 대비 부채 규모",
                "부채 구성과 만기구조 확인 필요",
            ),
            "current_ratio": _metric(
                "유동비율",
                _divide(
                    current_assets,
                    current_liabilities,
                    100,
                ),
                "%",
                "유동자산의 단기부채 대비 규모",
                "유동자산의 실제 현금화 가능성 고려",
            ),
            "ocf_to_income": _metric(
                "영업현금흐름/순이익",
                (
                    _divide(ocf, net_income, 100)
                    if net_income is not None
                    and net_income > 0
                    else None
                ),
                "%",
                "순이익 대비 영업현금창출 수준",
                "비현금손익 및 운전자본 변동 확인 필요",
            ),
            "accrual_ratio": _metric(
                "총발생액 비율",
                (
                    _divide(
                        net_income - ocf,
                        average_assets,
                        100,
                    )
                    if net_income is not None
                    and ocf is not None
                    else None
                ),
                "%",
                "순이익과 영업현금흐름의 차이를 자산 대비 측정",
                "현금흐름 분류와 금융사업 영향을 고려해야 함",
            ),
            "revenue_growth": _metric(
                "매출 성장률",
                _growth(result, year, "revenue"),
                "%",
                "전년 대비 매출액 변화",
                "비교가능성 검증을 통과한 경우만 산출",
            ),
            "receivables_growth": _metric(
                "매출채권 증가율",
                _growth(result, year, "receivables"),
                "%",
                "전년 대비 채권 잔액 변화",
                "순수 매출채권과 기타채권 포함 여부 확인",
            ),
            "inventory_growth": _metric(
                "재고자산 증가율",
                _growth(result, year, "inventory"),
                "%",
                "전년 대비 재고자산 변화",
                "평가손실과 제품 구성 변화 확인 필요",
            ),
        }

        output[year] = metrics

    return output


def build_ratio_interpretations(result):
    ratios = calculate_accounting_ratios(result)
    observations = []

    for year, metrics in ratios.items():
        revenue_growth = metrics["revenue_growth"]["value"]
        ar_growth = metrics["receivables_growth"]["value"]
        inventory_growth = metrics["inventory_growth"]["value"]
        accrual = metrics["accrual_ratio"]["value"]

        if (
            revenue_growth is not None
            and ar_growth is not None
            and ar_growth - revenue_growth >= 15
        ):
            observations.append({
                "year": year,
                "title": "매출채권 증가율이 매출 성장률을 상회",
                "evidence": (
                    f"매출 {revenue_growth:+.2f}%, "
                    f"매출채권 {ar_growth:+.2f}%"
                ),
                "interpretation": (
                    "채권 회수조건, 매출 구성 또는 "
                    "기말 채권 집중 여부를 검토할 필요가 있습니다."
                ),
                "audit_focus": (
                    "채권의 실재성·평가, "
                    "매출의 발생·기간귀속"
                ),
            })

        if (
            revenue_growth is not None
            and inventory_growth is not None
            and inventory_growth - revenue_growth >= 15
        ):
            observations.append({
                "year": year,
                "title": "재고자산 증가율이 매출 성장률을 상회",
                "evidence": (
                    f"매출 {revenue_growth:+.2f}%, "
                    f"재고자산 {inventory_growth:+.2f}%"
                ),
                "interpretation": (
                    "재고 축적, 생산계획 변화 및 "
                    "재고자산 평가의 적정성을 검토해야 합니다."
                ),
                "audit_focus": (
                    "재고자산의 실재성·평가"
                ),
            })

        if accrual is not None and accrual > 10:
            observations.append({
                "year": year,
                "title": "순이익과 영업현금흐름의 차이",
                "evidence": f"총발생액 비율 {accrual:+.2f}%",
                "interpretation": (
                    "순이익이 영업현금흐름을 상회합니다. "
                    "비현금손익과 운전자본 변동을 "
                    "분해해 원인을 확인해야 합니다."
                ),
                "audit_focus": (
                    "관련 손익 및 자산·부채 계정의 "
                    "인식·평가·분류"
                ),
            })

    return observations
