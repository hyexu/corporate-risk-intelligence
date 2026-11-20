
"""
Financial Statement Review Report

Accounting and audit-oriented analytical review.
Uses validated pipeline results; does not issue audit opinions.
"""

from datetime import datetime, timezone
from numbers import Real


ACCOUNT_NAMES = {
    "revenue": "매출액",
    "operating_income": "영업이익",
    "net_income": "당기순이익",
    "assets": "총자산",
    "liabilities": "총부채",
    "equity": "자기자본",
    "current_assets": "유동자산",
    "current_liabilities": "유동부채",
    "receivables": "매출채권",
    "inventory": "재고자산",
    "operating_cash_flow": "영업활동현금흐름",
}


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, Real):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return None


def _year_map(data):
    return {str(k): v for k, v in (data or {}).items()}


def _value(accounts, year, account):
    entry = _year_map(accounts).get(str(year), {})
    if not isinstance(entry, dict):
        return None
    return _number(entry.get("values", {}).get(account))


def _trillion(value):
    if value is None:
        return "자료 없음"
    return f"{value / 1_000_000_000_000:,.2f}조 원"


def _percent(value):
    return f"{value:,.2f}%" if value is not None else "산출 불가"


def _ratio(numerator, denominator, multiplier=100):
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator * multiplier


def _change(current, previous):
    if current is None or previous is None:
        return None
    return current - previous


def _verified_change(result, year, account):
    """
    전기 비교금액 검증을 통과한 경우에만 증감액 계산.
    검증 결과가 없거나 불일치하면 None 반환.
    """
    accounts = result.get("accounts", {})
    current = _value(accounts, year, account)

    audit = result.get("comparability", {}).get("audit", [])

    verified_statuses = {
        "PASS",
        "PASS_EQUIVALENT",
        "RESTATED_VERIFIED",
    }

    matching = [
        item for item in audit
        if str(item.get("report_year")) == str(year)
        and item.get("account") == account
    ]

    if len(matching) != 1:
        return None

    item = matching[0]

    if item.get("status") not in verified_statuses:
        return None

    comparative = _number(item.get("comparative"))

    if current is None or comparative is None:
        return None

    return current - comparative


def _verified_change_text(result, year, account):
    change = _verified_change(result, year, account)

    if change is None:
        return "산출 보류(비교금액 검증 필요)"

    return _trillion(change)


def _section(title, observation, interpretation, assertions, procedures):
    return {
        "title": title,
        "observation": observation,
        "interpretation": interpretation,
        "audit_assertions": assertions,
        "follow_up_procedures": procedures,
    }


def _comparability_note(result):
    summary = result.get("comparability", {}).get("summary", {})
    review = summary.get("REVIEW", 0)
    return (
        "비교가능성 점검에서 REVIEW 항목이 존재할 수 있습니다. "
        "성장률과 증감 분석은 원천 비교금액 검증 후 사용해야 합니다."
        if review else
        "비교가능성 감사 결과를 별도로 확인한 뒤 기간 간 수치를 해석합니다."
    )


def build_financial_review_report(result):
    """
    Create a structured analytical review from pipeline output.

    Amounts are KRW; no unverified growth-rate assertions.
    Audit procedures are recommendations, not performed tests.
    """
    metadata = result.get("metadata", {})
    accounts = result.get("accounts", {})
    years = sorted(
        (str(y) for y in metadata.get("years", [])),
        key=lambda y: int(y),
    )

    if not years:
        years = sorted(
            _year_map(accounts),
            key=lambda y: int(y),
        )

    if not years:
        raise ValueError("분석 가능한 사업연도 데이터가 없습니다.")

    year = years[-1]
    previous_year = years[-2] if len(years) > 1 else None
    company = metadata.get("company", "분석 대상 기업")

    revenue = _value(accounts, year, "revenue")
    op = _value(accounts, year, "operating_income")
    ni = _value(accounts, year, "net_income")
    assets = _value(accounts, year, "assets")
    liabilities = _value(accounts, year, "liabilities")
    equity = _value(accounts, year, "equity")
    current_assets = _value(accounts, year, "current_assets")
    current_liabilities = _value(accounts, year, "current_liabilities")
    ar = _value(accounts, year, "receivables")
    inventory = _value(accounts, year, "inventory")
    ocf = _value(accounts, year, "operating_cash_flow")

    margin = _ratio(op, revenue)
    debt_ratio = _ratio(liabilities, equity)
    current_ratio = _ratio(current_assets, current_liabilities)
    cash_to_income = _ratio(ocf, ni)

    sections = []

    # 1. Financial performance
    sections.append(_section(
        "1. 수익성과 재무성과",
        (
            f"{year}년 매출액 {_trillion(revenue)}, "
            f"영업이익 {_trillion(op)}, "
            f"영업이익률 {_percent(margin)}."
        ),
        (
            "영업이익률은 매출 대비 영업성과를 나타냅니다. "
            "추세를 판단하려면 매출원가율, 판매관리비율, "
            "일회성 손익 및 사업부별 수익성을 추가 검토해야 합니다."
        ),
        ["매출의 발생", "매출의 정확성", "매출의 기간귀속"],
        [
            "전년 대비 매출총이익률과 영업이익률 비교",
            "사업부문별 실적 및 회계정책 주석 검토",
            "기말 전후 매출거래의 기간귀속 검토",
        ],
    ))

    # 2. Financial position
    sections.append(_section(
        "2. 재무안정성과 유동성",
        (
            f"{year}년 총자산 {_trillion(assets)}, "
            f"총부채 {_trillion(liabilities)}, "
            f"자기자본 {_trillion(equity)}. "
            f"부채비율 {_percent(debt_ratio)}, "
            f"유동비율 {_percent(current_ratio)}."
        ),
        (
            "부채비율은 재무구조를, 유동비율은 단기 지급능력의 "
            "일부를 보여줍니다. 두 지표만으로 실제 상환능력을 "
            "확정할 수 없으며, 차입금 만기, 이자부담, "
            "현금성자산 및 영업현금흐름을 함께 검토해야 합니다."
        ),
        ["부채의 완전성", "자산·부채의 분류", "평가 및 배분"],
        [
            "차입금 만기구조와 금융약정 주석 검토",
            "유동·비유동 분류의 적정성 검토",
            "이자비용 및 현금창출능력 추가 분석",
        ],
    ))

    # 3. Earnings quality
    earnings_observation = (
        f"{year}년 당기순이익 {_trillion(ni)}, "
        f"영업활동현금흐름 {_trillion(ocf)}. "
    )
    if ni is not None and ni > 0 and ocf is not None:
        earnings_observation += (
            f"영업현금흐름/순이익 비율 {_percent(cash_to_income)}."
        )
    else:
        earnings_observation += (
            "현금흐름/순이익 비율은 해석을 보류합니다."
        )

    if ni is not None and ocf is not None and ni > 0 and ocf < 0:
        earnings_interpretation = (
            "순이익은 양수이나 영업현금흐름은 음수입니다. "
            "발생주의 손익과 현금흐름의 차이를 분해할 필요가 있습니다. "
            "운전자본, 비현금 손익, 세금 및 금융사업 관련 "
            "현금흐름을 확인하기 전에는 원인을 단정할 수 없습니다."
        )
    else:
        earnings_interpretation = (
            "당기순이익과 영업현금흐름의 관계는 이익의 질을 "
            "검토하는 출발점입니다. 단일 연도의 비율만으로 "
            "이익의 질을 확정할 수 없으며 비현금 조정항목과 "
            "운전자본 변동을 함께 검토해야 합니다."
        )

    sections.append(_section(
        "3. 이익의 질과 현금흐름",
        earnings_observation,
        earnings_interpretation,
        ["손익의 발생 및 정확성", "자산·부채의 평가", "표시와 분류"],
        [
            "간접법 현금흐름표의 비현금 조정항목 확인",
            "영업자산·부채 증감 내역 분석",
            "금융사업 포함 여부와 현금흐름 분류 검토",
        ],
    ))

    # 4. Working capital
    working_observation = (
        f"{year}년 매출채권 {_trillion(ar)}, "
        f"재고자산 {_trillion(inventory)}."
    )

    if previous_year:
        ar_change_text = _verified_change_text(
            result, year, "receivables"
        )
        inventory_change_text = _verified_change_text(
            result, year, "inventory"
        )

        working_observation += (
            f" 전년 대비 매출채권 증감액 {ar_change_text}, "
            f"재고자산 증감액 {inventory_change_text}."
        )

    sections.append(_section(
        "4. 운전자본과 회계추정",
        working_observation,
        (
            "매출채권 잔액은 신용판매와 회수조건의 영향을 받으며, "
            "재고자산 잔액은 생산·판매 및 평가정책의 영향을 받습니다. "
            "잔액 증가만으로 회수 지연이나 재고 진부화를 "
            "확정할 수 없습니다."
        ),
        [
            "매출채권의 실재성 및 평가",
            "재고자산의 실재성 및 평가",
            "매출의 기간귀속",
        ],
        [
            "매출채권 연령분석 및 후속 현금회수 확인",
            "기대신용손실충당금 산정 근거 검토",
            "재고 회전기간, 평가손실 및 순실현가능가치 검토",
            "기말 전후 매출·매입 기간귀속 검토",
        ],
    ))

    # 5. Existing screening findings
    findings = result.get("screening", {}).get("findings", [])
    skipped = result.get("screening", {}).get("skipped", [])

    sections.append(_section(
        "5. 이상징후 스크리닝과 후속 검토",
        (
            f"기존 검증 엔진에서 {len(findings)}건의 신호를 "
            f"탐지했고 {len(skipped)}건의 검사를 보류했습니다."
        ),
        (
            "탐지 결과는 추가 검토 대상을 선정하기 위한 "
            "분석적 절차의 단서입니다. 회계부정, "
            "중요왜곡표시위험 또는 감사의견을 "
            "확정하는 증거가 아닙니다."
        ),
        ["관련 계정별 감사 주장에 따라 개별 판단 필요"],
        [
            "탐지 신호의 원천 공시 수치 재확인",
            "관련 재무제표 주석과 사업환경 검토",
            "중요성 및 위험평가에 필요한 추가 정보 확보",
        ],
    ))

    # Short executive summary
    executive = [
        (
            f"{company}의 {year}년 연결재무제표를 기준으로 "
            f"영업이익률 {_percent(margin)}, "
            f"부채비율 {_percent(debt_ratio)}를 확인했습니다."
        ),
        (
            f"당기순이익은 {_trillion(ni)}, "
            f"영업활동현금흐름은 {_trillion(ocf)}로, "
            "발생주의 손익과 현금창출력의 관계를 추가 검토합니다."
        ),
        (
            f"규칙 기반 스크리닝 신호 {len(findings)}건, "
            f"보류 {len(skipped)}건을 확인했습니다. "
            "이 결과는 감사의견이나 회계부정 판정이 아닙니다."
        ),
    ]

    return {
        "title": f"{company} 재무제표 심층 검토 보고서",
        "company": company,
        "fiscal_year": year,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "basis": "OpenDART 연결재무제표(CFS)",
        "executive_summary": executive,
        "sections": sections,
        "screening_findings": findings,
        "screening_skipped": skipped,
        "comparability_note": _comparability_note(result),
        "limitations": [
            "본 보고서는 공개 재무정보 기반 분석적 검토입니다.",
            "감사절차를 실제 수행한 결과가 아닙니다.",
            "공시 주석과 거래 증빙을 직접 검증하지 않았습니다.",
            "재무비율만으로 중요왜곡표시위험을 확정할 수 없습니다.",
            "기업 간 사업구조와 금융사업 포함 여부를 고려해야 합니다.",
        ],
    }


def report_to_markdown(report):
    """Render a report dictionary as readable Markdown."""
    lines = [
        f"# {report['title']}",
        "",
        f"**대상 사업연도:** {report['fiscal_year']}",
        f"**분석 기준:** {report['basis']}",
        "",
        "## Executive Summary",
        "",
    ]

    for item in report["executive_summary"]:
        lines.append(f"- {item}")

    for section in report["sections"]:
        lines.extend([
            "",
            f"## {section['title']}",
            "",
            "### 관찰된 재무적 사실",
            section["observation"],
            "",
            "### 회계적 해석",
            section["interpretation"],
            "",
            "### 관련 감사 주장",
        ])
        for assertion in section["audit_assertions"]:
            lines.append(f"- {assertion}")

        lines.extend(["", "### 권고 후속 검토 절차"])
        for procedure in section["follow_up_procedures"]:
            lines.append(f"- {procedure}")

    lines.extend([
        "",
        "## 데이터 비교가능성",
        report["comparability_note"],
        "",
        "## 분석의 한계",
    ])

    for limitation in report["limitations"]:
        lines.append(f"- {limitation}")

    return "\n".join(lines)
