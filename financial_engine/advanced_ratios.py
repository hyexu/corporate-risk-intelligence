
"""
Advanced financial ratios using OpenDART annual statements.

No audit opinion or fraud determination.
"""

from financial_engine.dart_client import fetch_company_history
from financial_engine.account_mapping import parse_amount
from financial_engine.comparability import audit_comparatives


EXTRA_ACCOUNTS = {
    "cost_of_sales": {
        "id": "ifrs-full_CostOfSales",
        "sections": {"IS", "CIS"},
    },
    "cash": {
        "id": "ifrs-full_CashAndCashEquivalents",
        "sections": {"BS"},
    },
    "finance_costs": {
        "id": "ifrs-full_FinanceCosts",
        "sections": {"IS", "CIS"},
    },
    "capex": {
        "id": (
            "ifrs-full_"
            "PurchaseOfPropertyPlantAndEquipment"
            "ClassifiedAsInvestingActivities"
        ),
        "sections": {"CF"},
    },
}


def _extract(rows, config):
    matches = []

    for row in rows:
        if row.get("account_id") != config["id"]:
            continue

        if row.get("sj_div") not in config["sections"]:
            continue

        if row.get("account_detail") not in (None, "", "-"):
            continue

        amount = parse_amount(row.get("thstrm_amount"))

        if amount is not None:
            matches.append(amount)

    distinct = set(matches)

    if len(distinct) == 1:
        return matches[0], "OK"

    if len(distinct) > 1:
        return None, "AMBIGUOUS"

    return None, "MISSING"


def _safe_divide(a, b, scale=1):
    if a is None or b is None or b == 0:
        return None
    return a / b * scale


def _verified_pair(audit, year, account):
    matches = [
        item for item in audit
        if item.get("report_year") == year
        and item.get("account") == account
    ]

    if len(matches) != 1:
        return None

    item = matches[0]

    if item["status"] not in {
        "PASS",
        "PASS_EQUIVALENT",
        "RESTATED_VERIFIED",
    }:
        return None

    return item


def build_advanced_ratios(corp_code):
    history = fetch_company_history(corp_code)
    comparison = audit_comparatives(corp_code, history)
    audit = comparison["audit"]
    extracted = comparison["extracted"]

    results = {}

    for year in sorted(history):
        rows = history[year]
        extra = {}
        statuses = {}

        for name, config in EXTRA_ACCOUNTS.items():
            value, status = _extract(rows, config)
            extra[name] = value
            statuses[name] = status

        base = extracted[year]["values"]

        revenue = base.get("revenue")
        inventory = base.get("inventory")
        current_liabilities = base.get("current_liabilities")
        ocf = base.get("operating_cash_flow")

        cost = extra["cost_of_sales"]
        cash = extra["cash"]
        capex = extra["capex"]

        gross_margin = (
            _safe_divide(revenue - cost, revenue, 100)
            if revenue is not None and cost is not None
            else None
        )

        cash_ratio = _safe_divide(
            cash, current_liabilities, 100
        )

        inventory_turnover = None

        if year - 1 in extracted:
            check = _verified_pair(
                audit, year, "inventory"
            )

            if check is not None:
                previous = check["comparative"]

                if (
                    inventory is not None
                    and previous is not None
                    and cost is not None
                ):
                    average_inventory = (
                        inventory + previous
                    ) / 2

                    if average_inventory > 0:
                        inventory_turnover = (
                            cost / average_inventory
                        )

        # Investing cash outflows can be represented
        # with either sign depending on source conventions.
        # Do not assume negative figures are invalid.
        capex_outflow = (
            abs(capex) if capex is not None else None
        )

        fcf = (
            ocf - capex_outflow
            if ocf is not None
            and capex_outflow is not None
            else None
        )

        results[year] = {
            "extra_accounts": extra,
            "account_status": statuses,
            "metrics": {
                "gross_margin": gross_margin,
                "inventory_turnover": inventory_turnover,
                "cash_ratio": cash_ratio,
                "capex": capex_outflow,
                "simple_fcf": fcf,
                "finance_costs": extra["finance_costs"],
            },
        }

    return results
