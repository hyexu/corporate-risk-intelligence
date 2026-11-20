"""Rule-based financial risk summary. No LLM API required."""

SIGNAL_LABELS = {
    "RECEIVABLES_DIVERGENCE": "매출채권 증가율과 매출 성장률의 괴리",
    "INVENTORY_DIVERGENCE": "재고자산 증가율과 매출 성장률의 괴리",
    "EARNINGS_CASH_DIVERGENCE": "순이익과 영업현금흐름의 방향 차이",
}


def _number(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _format_pct(value):
    return "확인 불가" if value is None else f"{value:,.1f}%"


def _get_latest_accounts(result):
    accounts = result.get("accounts", {})
    if not accounts:
        return None, {}

    years = sorted(accounts.keys(), key=lambda x: int(x))
    year = years[-1]
    record = accounts[year]

    return int(year), record.get("values", {})


def build_risk_summary(result):
    """Return three grounded Korean summary sentences."""
    year, values = _get_latest_accounts(result)

    if year is None:
        return [
            "재무 현황: 분석 가능한 재무자료가 없습니다.",
            "위험 신호: 분석을 수행할 수 없습니다.",
            "추가 확인: OpenDART 데이터 수집 상태를 확인해야 합니다.",
        ]

    revenue = _number(values.get("revenue"))
    operating_income = _number(values.get("operating_income"))
    liabilities = _number(values.get("liabilities"))
    equity = _number(values.get("equity"))
    net_income = _number(values.get("net_income"))
    ocf = _number(values.get("operating_cash_flow"))

    margin = None
    if revenue is not None and revenue != 0 and operating_income is not None:
        margin = operating_income / revenue * 100

    debt_ratio = None
    if equity is not None and equity > 0 and liabilities is not None:
        debt_ratio = liabilities / equity * 100

    line1 = (
        f"① 재무 현황 ({year}년): "
        f"영업이익률 {_format_pct(margin)}, "
        f"부채비율 {_format_pct(debt_ratio)}."
    )

    findings = result.get("screening", {}).get("findings", [])
    latest_findings = [
        finding
        for finding in findings
        if str(finding.get("year")) == str(year)
    ]

    if latest_findings:
        names = [
            SIGNAL_LABELS.get(
                finding.get("signal"),
                "추가 검토가 필요한 재무 신호",
            )
            for finding in latest_findings
        ]
        names = list(dict.fromkeys(names))
        line2 = (
            f"② 위험 신호 ({year}년): "
            + ", ".join(names)
            + " 탐지."
        )
    else:
        line2 = (
            f"② 위험 신호 ({year}년): "
            "설정된 규칙에서 탐지된 신호가 없습니다. "
            "위험이 없다는 뜻은 아닙니다."
        )

    skipped = result.get("screening", {}).get("skipped", [])
    latest_skipped = [
        item for item in skipped
        if str(item.get("year")) == str(year)
    ]

    if latest_skipped:
        line3 = (
            f"③ 추가 확인: {year}년 비교 검증이 보류된 "
            f"{len(latest_skipped)}개 항목의 공시자료를 확인해야 합니다."
        )
    elif any(
        item.get("signal") == "EARNINGS_CASH_DIVERGENCE"
        for item in latest_findings
    ):
        line3 = (
            "③ 추가 확인: 현금흐름표의 운전자본 변동, "
            "비현금 조정 및 금융사업 영향을 확인해야 합니다."
        )
    elif any(
        item.get("signal") == "RECEIVABLES_DIVERGENCE"
        for item in latest_findings
    ):
        line3 = (
            "③ 추가 확인: 매출채권 회수기간, "
            "신용정책 및 관련 주석을 확인해야 합니다."
        )
    elif any(
        item.get("signal") == "INVENTORY_DIVERGENCE"
        for item in latest_findings
    ):
        line3 = (
            "③ 추가 확인: 재고 회전기간, "
            "평가손실 및 수요 변화를 확인해야 합니다."
        )
    elif net_income is not None and ocf is not None:
        line3 = (
            "③ 추가 확인: 순이익과 영업현금흐름의 차이, "
            "업종 특성 및 공시 주석을 함께 검토해야 합니다."
        )
    else:
        line3 = (
            "③ 추가 확인: 누락된 재무항목과 "
            "공시 주석을 확인해야 합니다."
        )

    return [line1, line2, line3]
