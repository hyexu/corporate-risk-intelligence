
"""
Rule-based financial explanations.

These explanations describe screening signals,
not confirmed causes or accounting misconduct.
"""


def fmt_pct(value):
    if value is None:
        return "확인 불가"
    return f"{value:+.2f}%"


def fmt_pp(value):
    if value is None:
        return "확인 불가"
    return f"{value:+.2f}%p"


def fmt_krw(value):
    if value is None:
        return "확인 불가"
    return f"{value / 1_000_000_000_000:+.2f}조 원"


def explain_receivables(finding):
    asset_growth = finding.get("asset_growth_pct")
    sales_growth = finding.get("revenue_growth_pct")
    gap = finding.get("gap_pp")

    return {
        "title": "매출채권과 매출 성장률의 괴리",
        "observation": (
            f"매출채권 증가율은 {fmt_pct(asset_growth)}, "
            f"매출 성장률은 {fmt_pct(sales_growth)}로 "
            f"차이는 {fmt_pp(gap)}입니다."
        ),
        "interpretation": (
            "매출채권이 매출보다 빠르게 증가했습니다. "
            "매출채권 회수기간 변화나 거래조건 변화 등을 "
            "점검할 필요가 있습니다. 다만 매출 감소기에 "
            "나타나는 분모 효과도 고려해야 합니다."
        ),
        "verification_needed": [
            "매출채권 회수기간(DSO)의 변화",
            "매출채권 연령분석 및 대손충당금",
            "매출채권의 계정 범위와 사업부문 구성",
        ],
        "conclusion_level": "SCREENING_ONLY",
    }


def explain_inventory(finding):
    asset_growth = finding.get("asset_growth_pct")
    sales_growth = finding.get("revenue_growth_pct")
    gap = finding.get("gap_pp")

    return {
        "title": "재고자산과 매출 성장률의 괴리",
        "observation": (
            f"재고자산 증가율은 {fmt_pct(asset_growth)}, "
            f"매출 성장률은 {fmt_pct(sales_growth)}로 "
            f"차이는 {fmt_pp(gap)}입니다."
        ),
        "interpretation": (
            "재고자산 증가 속도가 매출 성장률을 상회합니다. "
            "수요 둔화, 생산 계획, 제품 구성 변화 등 "
            "여러 요인이 가능하지만 현재 수치만으로 "
            "원인을 특정할 수 없습니다."
        ),
        "verification_needed": [
            "재고자산 회전율 및 회전일수",
            "재고자산 평가손실과 충당금",
            "제품별 재고 구성 및 수요 전망",
        ],
        "conclusion_level": "SCREENING_ONLY",
    }


def explain_earnings_cash(finding):
    ni_change = finding.get("net_income_change")
    ocf_change = finding.get("ocf_change")

    return {
        "title": "순이익과 영업현금흐름의 방향 차이",
        "observation": (
            f"순이익은 전년 대비 "
            f"{fmt_krw(ni_change)} 변화했지만, "
            f"영업현금흐름은 "
            f"{fmt_krw(ocf_change)} 변화했습니다."
        ),
        "interpretation": (
            "회계상 이익 증가가 영업현금흐름 증가로 "
            "이어지지 않았습니다. 운전자본 변동, "
            "비현금손익 조정, 이자 및 법인세 현금흐름 "
            "등을 확인해야 합니다. 이 신호만으로 "
            "이익의 질이 낮다고 단정할 수 없습니다."
        ),
        "verification_needed": [
            "영업활동 자산·부채 변동의 세부 구성",
            "비현금손익 조정항목",
            "이자·배당·법인세 현금흐름의 분류",
            "연결대상 금융사업의 영향",
        ],
        "conclusion_level": "SCREENING_ONLY",
    }


EXPLAINERS = {
    "RECEIVABLES_DIVERGENCE": explain_receivables,
    "INVENTORY_DIVERGENCE": explain_inventory,
    "EARNINGS_CASH_DIVERGENCE": explain_earnings_cash,
}


def explain_finding(finding):
    signal = finding.get("signal")
    explainer = EXPLAINERS.get(signal)

    if explainer is None:
        return {
            "title": "미지원 분석 신호",
            "observation": "현재 설명 규칙이 없습니다.",
            "interpretation": "추가 분석이 필요합니다.",
            "verification_needed": [],
            "conclusion_level": "NOT_ANALYZED",
        }

    result = explainer(finding)

    return {
        "year": finding.get("year"),
        "signal": signal,
        **result,
    }


def explain_screening(screening_result):
    explanations = [
        explain_finding(finding)
        for finding in screening_result["findings"]
    ]

    return {
        "explanations": explanations,
        "skipped": screening_result["skipped"],
        "audit": screening_result["audit"],
    }
