
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from financial_engine.dart_client import COMPANIES
from financial_engine.pipeline import run_company_analysis
from financial_engine.comparability import (
    audit_comparatives,
    verified_growth,
)
from financial_engine.dart_client import fetch_company_history


st.set_page_config(
    page_title="Financial Risk Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Corporate Risk Intelligence")
st.caption(
    "OpenDART | FY2022–2024 | Consolidated Financial Statements"
)

st.info(
    "기업의 재무 추세와 추가 검토가 필요한 회계적 신호를 "
    "분석합니다. 탐지 결과는 회계부정이나 부실의 확정 "
    "판정이 아닙니다."
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_analysis():
    results = {}
    errors = {}

    for company, corp_code in COMPANIES.items():
        try:
            results[company] = run_company_analysis(
                company, corp_code
            )
        except Exception:
            errors[company] = "분석 데이터를 불러오지 못했습니다."

    return results, errors


def to_number(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def ratio(numerator, denominator, multiplier=100):
    a = to_number(numerator)
    b = to_number(denominator)

    if a is None or b is None or b == 0:
        return None

    return a / b * multiplier


def build_trend_rows(company, result):
    accounts = result["accounts"]
    audit = result["comparability"]["audit"]

    verified_bases = {}

    for item in audit:
        if item["status"] in {
            "PASS",
            "PASS_EQUIVALENT",
            "RESTATED_VERIFIED",
        }:
            verified_bases[
                (item["report_year"], item["account"])
            ] = item["comparative"]

    rows = []

    for year in sorted(accounts):
        values = accounts[year]["values"]

        revenue = to_number(values.get("revenue"))
        operating_income = to_number(
            values.get("operating_income")
        )
        liabilities = to_number(
            values.get("liabilities")
        )
        equity = to_number(values.get("equity"))
        ocf = to_number(
            values.get("operating_cash_flow")
        )

        growth = verified_growth(
            revenue,
            to_number(
                verified_bases.get((year, "revenue"))
            ),
        )

        rows.append({
            "Company": company,
            "Year": year,
            "Revenue (KRW tn)": (
                revenue / 1e12
                if revenue is not None else None
            ),
            "Operating Margin (%)": ratio(
                operating_income, revenue
            ),
            "Debt Ratio (%)": ratio(
                liabilities, equity
            ),
            "Operating Cash Flow (KRW tn)": (
                ocf / 1e12 if ocf is not None else None
            ),
            "Revenue Growth (%)": growth,
        })

    return rows


with st.spinner("OpenDART 재무정보를 분석하고 있습니다..."):
    analyses, errors = load_analysis()

for company in errors:
    st.warning(f"{company}: 재무정보를 불러오지 못했습니다.")

if not analyses:
    st.error("분석 가능한 기업 데이터가 없습니다.")
    st.stop()


st.subheader("기업 선택")

selected_companies = st.multiselect(
    "비교할 기업",
    options=list(analyses),
    default=list(analyses),
)

if not selected_companies:
    st.warning("기업을 하나 이상 선택해 주세요.")
    st.stop()


trend_rows = []

for company in selected_companies:
    trend_rows.extend(
        build_trend_rows(company, analyses[company])
    )

trend_df = pd.DataFrame(trend_rows)


st.subheader("2024년 주요 재무지표 비교")

latest_df = trend_df[
    trend_df["Year"] == 2024
].copy()

display_columns = [
    "Company",
    "Revenue Growth (%)",
    "Operating Margin (%)",
    "Debt Ratio (%)",
    "Operating Cash Flow (KRW tn)",
]

st.dataframe(
    latest_df[display_columns].round(2),
    use_container_width=True,
    hide_index=True,
)


st.subheader("2022–2024 재무 추이")

st.caption(
    "매출액·영업현금흐름은 조 원, "
    "영업이익률·부채비율은 % 단위입니다."
)


def show_trend(title, column):
    st.markdown(f"**{title}**")

    chart_df = trend_df.pivot(
        index="Year",
        columns="Company",
        values=column,
    ).sort_index()

    st.line_chart(
        chart_df,
        use_container_width=True,
    )


left, right = st.columns(2)

with left:
    show_trend(
        "매출액",
        "Revenue (KRW tn)",
    )

    show_trend(
        "부채비율",
        "Debt Ratio (%)",
    )

with right:
    show_trend(
        "영업이익률",
        "Operating Margin (%)",
    )

    show_trend(
        "영업현금흐름",
        "Operating Cash Flow (KRW tn)",
    )


st.subheader("검증된 매출 성장률 추이")

growth_chart = trend_df.pivot(
    index="Year",
    columns="Company",
    values="Revenue Growth (%)",
).sort_index()

st.line_chart(
    growth_chart,
    use_container_width=True,
)

st.caption(
    "2022년 성장률은 2021년 비교자료가 없어 표시하지 않습니다. "
    "공시 간 비교금액이 검증되지 않은 연도도 공란으로 표시합니다."
)


st.divider()
st.subheader("재무 이상징후 분석")

for company in selected_companies:
    result = analyses[company]

    findings = result["screening"]["findings"]
    skipped = result["screening"]["skipped"]
    explanations = result["explanations"]

    with st.expander(
        f"{company} | 탐지 {len(findings)}건 · "
        f"보류 {len(skipped)}건",
        expanded=False,
    ):
        if not findings:
            st.success(
                "현재 규칙에서 탐지된 신호가 없습니다. "
                "이는 재무위험이 없다는 의미는 아닙니다."
            )

        for explanation in explanations:
            st.markdown(
                f"**{explanation['year']}년 — "
                f"{explanation['title']}**"
            )

            st.write(
                "관찰:",
                explanation["observation"],
            )
            st.write(
                "해석:",
                explanation["interpretation"],
            )

            st.write("추가 확인사항:")
            for question in explanation["verification_needed"]:
                st.write(f"• {question}")

            st.divider()

        if skipped:
            st.warning(
                f"비교금액 미검증 등으로 "
                f"{len(skipped)}개 검사를 보류했습니다."
            )

            for item in skipped:
                st.caption(
                    f"{item['year']}년 "
                    f"{item['signal']}: "
                    f"{item['reason']}"
                )


# Rule-based financial risk summary
from financial_engine.risk_summary import build_risk_summary

st.divider()
st.subheader("Financial Risk Summary")
st.caption(
    "규칙 기반 자동 요약 | OpenDART 재무자료 | "
    "생성형 AI 미사용"
)

summary_company = st.selectbox(
    "요약할 기업 선택",
    options=selected_companies,
    key="risk_summary_company",
)

summary_result = analyses[summary_company]
summary_lines = build_risk_summary(summary_result)

for summary_line in summary_lines:
    st.write(summary_line)

st.caption(
    "본 요약은 재무지표와 사전 정의된 탐지 규칙에 "
    "근거합니다. 회계부정, 신용위험 또는 "
    "기업 부실을 확정적으로 판정하지 않습니다."
)


# Accounting and audit-oriented financial review report
from financial_engine.report import (
    build_financial_review_report,
    report_to_markdown,
)

st.divider()
st.subheader("회계·감사 관점 심층 분석 보고서")

st.caption(
    "OpenDART 연결재무제표 기반 | "
    "재무성과 · 이익의 질 · 감사 관점 · 후속 검토"
)

report_company = st.selectbox(
    "심층 분석할 기업 선택",
    options=selected_companies,
    key="financial_review_company",
)

report_result = analyses[report_company]

try:
    review_report = build_financial_review_report(report_result)
    review_markdown = report_to_markdown(review_report)

    st.markdown(review_markdown)

except Exception as exc:
    st.error("심층 분석 보고서를 생성하지 못했습니다.")
    st.caption(
        f"오류 유형: {type(exc).__name__}"
    )

st.info(
    "본 보고서는 공시 재무정보와 규칙 기반 분석에 "
    "따른 예비 검토 자료입니다. "
    "회계감사 수행 결과나 감사의견이 아니며, "
    "회계부정 또는 중요왜곡표시의 존재를 "
    "확정하지 않습니다."
)



from financial_engine.accounting_insights import (
    build_accounting_insights,
    insights_to_markdown,
)

st.markdown("### 주요 회계적 분석 및 감사 검토사항")

accounting_insights = build_accounting_insights(report_result)

st.markdown(insights_to_markdown(accounting_insights))

st.caption(
    "기간 비교는 기존 비교가능성 검증을 통과한 "
    "계정에 한정합니다. 15%p 기준은 잠정적인 "
    "분석 기준이며 실증적으로 검증되지 않았습니다."
)


from financial_engine.ratio_analysis import (
    calculate_accounting_ratios,
    build_ratio_interpretations,
)

st.divider()
st.subheader("3개년 핵심 재무비율 분석")

ratio_result = calculate_accounting_ratios(report_result)

ratio_rows = []

for year, metrics in ratio_result.items():
    row = {"사업연도": year}

    for metric in metrics.values():
        value = metric["value"]
        row[metric["name"]] = (
            f"{value:,.2f}{metric['unit']}"
            if value is not None
            else "산출 보류"
        )

    ratio_rows.append(row)

st.dataframe(
    ratio_rows,
    use_container_width=True,
    hide_index=True,
)

st.subheader("재무비율 교차 분석")

ratio_insights = build_ratio_interpretations(report_result)

if not ratio_insights:
    st.info(
        "현재 잠정 기준에서 추가 교차 분석 신호가 없습니다. "
        "이는 재무위험이 없다는 의미는 아닙니다."
    )
else:
    for item in ratio_insights:
        with st.expander(
            f"{item['year']}년 | {item['title']}"
        ):
            st.write("관찰:", item["evidence"])
            st.write("회계적 해석:", item["interpretation"])
            st.write("관련 감사 주장:", item["audit_focus"])

st.caption(
    "비율 분석은 공시된 연결재무제표를 기반으로 합니다. "
    "기간 비교는 검증된 비교금액에 한정하며, "
    "15%p 및 총발생액 비율 10% 기준은 잠정 기준입니다. "
    "탐지 결과는 감사의견이나 회계부정 판정이 아닙니다."
)

from financial_engine.advanced_ratios import (
    build_advanced_ratios,
)

st.divider()
st.subheader("확장 회계·재무비율 분석")

st.caption(
    "매출원가·현금성자산·재고회전율·투자지출 분석"
)

advanced_company = st.selectbox(
    "확장 분석 대상 기업",
    options=selected_companies,
    key="advanced_ratio_company",
)

advanced_corp_code = {
    "Samsung Electronics": "00126380",
    "SK Hynix": "00164779",
    "Hyundai Motor": "00164742",
}[advanced_company]

with st.spinner("공시 데이터를 분석하는 중입니다..."):
    advanced = build_advanced_ratios(
        advanced_corp_code
    )

rows = []

for year, data in advanced.items():
    metrics = data["metrics"]

    rows.append({
        "연도": year,
        "매출총이익률(%)": metrics["gross_margin"],
        "재고회전율(회)": metrics["inventory_turnover"],
        "현금비율(%)": metrics["cash_ratio"],
        "CAPEX(조 원)": (
            metrics["capex"] / 1e12
            if metrics["capex"] is not None
            else None
        ),
        "간이 FCF(조 원)": (
            metrics["simple_fcf"] / 1e12
            if metrics["simple_fcf"] is not None
            else None
        ),
    })

st.dataframe(
    rows,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "재고회전율은 검증된 전기 재고자산을 사용합니다. "
    "FCF는 영업현금흐름에서 유형자산 취득액만 차감한 "
    "간이 지표입니다. 금융비용은 이자비용과 동일하지 "
    "않으므로 이자보상배율은 계산하지 않습니다."
)


st.divider()
st.subheader("분석 기준 및 한계")

st.markdown(
    """
    - 자료: 금융감독원 OpenDART 연결재무제표
    - 분석 기간: 2022~2024년 사업연도
    - 재무지표: 매출액, 영업이익률, 부채비율,
      영업현금흐름 및 매출 성장률
    - 비교금액이 검증되지 않은 성장률은 계산 보류
    - 이상징후 기준은 실증적으로 검증되지 않은 임시 규칙
    - 금융사업 포함 여부 등으로 기업 간 비교가능성에 한계
    - 분석 결과는 투자 조언이나 신용등급 평가가 아님
    """
)
