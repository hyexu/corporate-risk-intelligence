
"""
Accounting insights based on verified OpenDART comparisons.

Analytical hypotheses only. Not audit evidence or an audit opinion.
"""

PURE_TRADE_IDS = {
    "ifrs-full_CurrentTradeReceivables",
    "dart_ShortTermTradeReceivable",
}

VERIFIED = {"PASS", "PASS_EQUIVALENT", "RESTATED_VERIFIED"}


def _years(result):
    return sorted(int(y) for y in result.get("accounts", {}))


def _entry(result, year):
    accounts = result.get("accounts", {})
    return accounts.get(str(year), accounts.get(year, {}))


def _value(result, year, name):
    return _entry(result, year).get("values", {}).get(name)


def _source(result, year, name):
    return _entry(result, year).get("sources", {}).get(name) or {}


def _verified(result, year, name):
    audit = result.get("comparability", {}).get("audit", [])
    return any(
        str(item.get("report_year")) == str(year)
        and item.get("account") == name
        and item.get("status") in VERIFIED
        for item in audit
    )


def _growth(result, year, name):
    if not _verified(result, year, name):
        return None

    current = _value(result, year, name)
    previous = _value(result, year - 1, name)

    if current is None or previous is None or previous <= 0:
        return None

    return (current / previous - 1) * 100


def _pct(value):
    return "산출 보류" if value is None else f"{value:+.2f}%"


def _insight(title, observation, meaning, assertions, checks):
    return {
        "title": title,
        "observation": observation,
        "meaning": meaning,
        "assertions": assertions,
        "checks": checks,
    }


def build_accounting_insights(result):
    years = _years(result)
    if len(years) < 2:
        return []

    insights = []

    for year in years[1:]:
        revenue_growth = _growth(result, year, "revenue")
        ar_growth = _growth(result, year, "receivables")
        inventory_growth = _growth(result, year, "inventory")

        # 1. Revenue versus receivables
        if revenue_growth is not None and ar_growth is not None:
            gap = ar_growth - revenue_growth

            if gap >= 15:
                insights.append(_insight(
                    f"{year}년 매출채권·매출 성장률 괴리",
                    (
                        f"매출 성장률 {_pct(revenue_growth)}, "
                        f"매출채권 증가율 {_pct(ar_growth)}, "
                        f"격차 {gap:.2f}%p."
                    ),
                    (
                        "매출에 비해 채권이 빠르게 증가했습니다. "
                        "회수조건, 매출 구성, 기말 거래 집중 또는 "
                        "채권 회수기간의 변화를 검토할 필요가 있습니다. "
                        "이 결과만으로 회수 지연이나 매출 과대계상을 "
                        "판단할 수 없습니다."
                    ),
                    "매출의 발생·기간귀속, 채권의 실재성·평가",
                    (
                        "매출채권 연령분석, 후속 현금회수, "
                        "대손충당금 및 기말 매출거래 검토"
                    ),
                ))

        # 2. Inventory versus revenue
        if revenue_growth is not None and inventory_growth is not None:
            gap = inventory_growth - revenue_growth

            if gap >= 15:
                insights.append(_insight(
                    f"{year}년 재고자산·매출 성장률 괴리",
                    (
                        f"매출 성장률 {_pct(revenue_growth)}, "
                        f"재고자산 증가율 {_pct(inventory_growth)}, "
                        f"격차 {gap:.2f}%p."
                    ),
                    (
                        "재고 증가 속도가 매출 성장률을 상회합니다. "
                        "생산계획, 제품 구성, 재고 축적 및 "
                        "평가손실 가능성을 검토할 필요가 있습니다. "
                        "재고 증가만으로 진부화나 평가 오류를 "
                        "확정할 수 없습니다."
                    ),
                    "재고자산의 실재성·평가, 원가의 정확성",
                    (
                        "재고 연령·품목별 구성, 재고평가손실, "
                        "순실현가능가치 및 생산·판매량 검토"
                    ),
                ))

        # 3. Receivables collection period
        # Both years must use narrowly defined trade receivables.
        ar_current = _value(result, year, "receivables")
        ar_previous = _value(result, year - 1, "receivables")
        revenue = _value(result, year, "revenue")

        pure_ar = (
            _source(result, year, "receivables").get("account_id")
            in PURE_TRADE_IDS
            and _source(result, year - 1, "receivables").get(
                "account_id"
            ) in PURE_TRADE_IDS
        )

        if (
            pure_ar
            and _verified(result, year, "receivables")
            and ar_current is not None
            and ar_previous is not None
            and revenue is not None
            and revenue > 0
        ):
            dso = (ar_current + ar_previous) / 2 / revenue * 365

            insights.append(_insight(
                f"{year}년 매출채권 회수기간(DSO)",
                f"평균 매출채권 기준 DSO 약 {dso:.1f}일.",
                (
                    "연간 매출액과 평균 매출채권을 이용한 "
                    "회수기간 근사치입니다. 기말 잔액의 계절성, "
                    "현금매출 비중 및 매출 구성에 영향을 받습니다. "
                    "단일 연도 수치만으로 회수 지연을 판단할 수 없습니다."
                ),
                "매출채권의 실재성·평가",
                (
                    "전년 DSO 및 동종업계 비교, 채권 연령분석, "
                    "후속 현금회수와 결제조건 확인"
                ),
            ))

        # 4. Net income and operating cash flow
        if (
            _verified(result, year, "net_income")
            and _verified(result, year, "operating_cash_flow")
        ):
            ni_change = (
                _value(result, year, "net_income")
                - _value(result, year - 1, "net_income")
            )
            ocf_change = (
                _value(result, year, "operating_cash_flow")
                - _value(result, year - 1, "operating_cash_flow")
            )

            if ni_change > 0 and ocf_change < 0:
                insights.append(_insight(
                    f"{year}년 순이익 증가·영업현금흐름 감소",
                    (
                        "전년 대비 순이익은 증가했지만 "
                        "영업활동현금흐름은 감소했습니다."
                    ),
                    (
                        "발생주의 손익과 현금창출력의 방향이 "
                        "상반됩니다. 비현금 조정, 영업자산·부채 "
                        "증감 및 금융사업의 영향을 분해해야 합니다."
                    ),
                    "관련 손익·자산·부채 계정별 주장 검토 필요",
                    (
                        "현금흐름표 조정항목, 운전자본 증감, "
                        "금융사업 관련 현금흐름 검토"
                    ),
                ))

    return insights


def insights_to_markdown(insights):
    if not insights:
        return (
            "검증된 데이터에서 추가 심층 검토 신호가 "
            "생성되지 않았습니다. 이는 위험이 없다는 뜻이 아닙니다."
        )

    lines = []

    for item in insights:
        lines.extend([
            f"### {item['title']}",
            "",
            f"**관찰 사실:** {item['observation']}",
            "",
            f"**회계적 함의:** {item['meaning']}",
            "",
            f"**관련 감사 주장:** {item['assertions']}",
            "",
            f"**추가 검토:** {item['checks']}",
            "",
            "---",
            "",
        ])

    return "\n".join(lines)
