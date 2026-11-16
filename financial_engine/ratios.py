
from financial_engine.account_mapping import (
    extract_accounts,
)


METRIC_LABELS = {
    "revenue_growth": "Revenue Growth (%)",
    "operating_margin": "Operating Margin (%)",
    "roa": "ROA (%)",
    "debt_ratio": "Debt Ratio (%)",
    "current_ratio": "Current Ratio (%)",
    "cash_conversion": "OCF / Net Income (%)",
    "dso": "Receivables Days",
    "inventory_to_sales": "Inventory / Revenue (%)",
    "receivables_growth": "Receivables Growth (%)",
    "inventory_growth": "Inventory Growth (%)",
}


def safe_divide(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def percent(numerator, denominator):
    result = safe_divide(numerator, denominator)
    return None if result is None else round(result * 100, 2)


def growth(current, previous):
    if current is None or previous is None or previous <= 0:
        return None
    return round((current / previous - 1) * 100, 2)


def compatible_source(current, previous, account):
    """
    동일한 경제적 범위의 계정인지 1차 확인.
    매출채권은 순수 유동 매출채권만 허용.
    """
    if not current or not previous:
        return False

    if account == "receivables":
        pure_trade_ids = {
            "ifrs-full_CurrentTradeReceivables",
            "dart_ShortTermTradeReceivable",
        }
        return (
            current.get("account_id") in pure_trade_ids
            and previous.get("account_id") in pure_trade_ids
        )

    # 기타 계정은 동일 ID일 때만 자동 비교 허용
    return (
        current.get("account_id")
        == previous.get("account_id")
    )


def calculate_company_ratios(history):
    """
    history:
        {2022: [OpenDART rows], 2023: [...], ...}

    각 연도별 지표와 데이터 품질 경고 반환.
    """
    extracted = {}

    for year, rows in sorted(history.items()):
        values, issues, sources = extract_accounts(rows)

        extracted[year] = {
            "values": values,
            "sources": sources,
            "issues": issues,
        }

    results = {}

    for year in sorted(extracted):
        current = extracted[year]
        values = current["values"]
        sources = current["sources"]

        previous = extracted.get(year - 1)
        previous_values = (
            previous["values"] if previous else {}
        )
        previous_sources = (
            previous["sources"] if previous else {}
        )

        metrics = {}
        warnings = []

        def comparable(account):
            if previous is None:
                warnings.append(
                    f"{account}: prior-year data unavailable"
                )
                return False

            if not compatible_source(
                sources.get(account),
                previous_sources.get(account),
                account,
            ):
                warnings.append(
                    f"{account}: account scope or ID "
                    "requires review"
                )
                return False

            return True

        # 1. 수익성
        metrics["operating_margin"] = percent(
            values["operating_income"],
            values["revenue"],
        )

        if comparable("assets"):
            avg_assets = safe_divide(
                values["assets"] + previous_values["assets"]
                if (
                    values["assets"] is not None
                    and previous_values["assets"] is not None
                )
                else None,
                2,
            )
            metrics["roa"] = percent(
                values["net_income"], avg_assets
            )
        else:
            metrics["roa"] = None

        # 2. 안정성·유동성
        metrics["debt_ratio"] = percent(
            values["liabilities"], values["equity"]
        )

        metrics["current_ratio"] = percent(
            values["current_assets"],
            values["current_liabilities"],
        )

        # 3. 현금창출력
        net_income = values["net_income"]
        ocf = values["operating_cash_flow"]

        if net_income is not None and net_income > 0:
            metrics["cash_conversion"] = percent(
                ocf, net_income
            )
        else:
            metrics["cash_conversion"] = None
            warnings.append(
                "Cash conversion: net income "
                "is zero, negative, or missing"
            )

        # 4. 재고자산 비중
        metrics["inventory_to_sales"] = percent(
            values["inventory"], values["revenue"]
        )

        # 5. 성장률
        if comparable("revenue"):
            metrics["revenue_growth"] = growth(
                values["revenue"],
                previous_values["revenue"],
            )
        else:
            metrics["revenue_growth"] = None

        # 6. 매출채권 회수기간
        if comparable("receivables"):
            current_ar = values["receivables"]
            previous_ar = previous_values["receivables"]

            if (
                current_ar is not None
                and previous_ar is not None
                and values["revenue"] is not None
                and values["revenue"] > 0
            ):
                average_ar = (current_ar + previous_ar) / 2
                metrics["dso"] = round(
                    average_ar / values["revenue"] * 365,
                    2,
                )
            else:
                metrics["dso"] = None
        else:
            metrics["dso"] = None

        # 7. 매출채권 증가율
        if comparable("receivables"):
            metrics["receivables_growth"] = growth(
                values["receivables"],
                previous_values["receivables"],
            )
        else:
            metrics["receivables_growth"] = None

        # 8. 재고자산 증가율
        if comparable("inventory"):
            metrics["inventory_growth"] = growth(
                values["inventory"],
                previous_values["inventory"],
            )
        else:
            metrics["inventory_growth"] = None

        # 데이터 누락 경고
        for issue in current["issues"]:
            warnings.append(
                f"{issue['account']}: {issue['type']}"
            )

        results[year] = {
            "metrics": metrics,
            "warnings": list(dict.fromkeys(warnings)),
            "values": values,
            "sources": sources,
        }

    return results
