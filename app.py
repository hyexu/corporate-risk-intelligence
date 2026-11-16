
# Corporate Risk Intelligence
# Step 3 - Financial Ratio Analysis

# 가상의 기업 재무데이터 (단위: 억 원)
company = "Demo Corporation"

financials = {
    "revenue_2024": 1000,
    "revenue_2025": 1200,
    "operating_profit": 120,
    "net_income": 80,
    "total_assets": 2000,
    "total_liabilities": 1400,
    "operating_cash_flow": 50,
    "receivables_2024": 100,
    "receivables_2025": 180
}

# 1. 매출액 증가율
revenue_growth = (
    (financials["revenue_2025"]
     / financials["revenue_2024"]) - 1
) * 100

# 2. 영업이익률
operating_margin = (
    financials["operating_profit"]
    / financials["revenue_2025"]
) * 100

# 3. 부채비율 (부채 / 자본)
equity = (
    financials["total_assets"]
    - financials["total_liabilities"]
)

debt_ratio = (
    financials["total_liabilities"] / equity
) * 100

# 4. 영업현금흐름 / 당기순이익
cash_conversion = (
    financials["operating_cash_flow"]
    / financials["net_income"]
)

# 5. 매출채권 증가율
receivables_growth = (
    (financials["receivables_2025"]
     / financials["receivables_2024"]) - 1
) * 100

print("\n=== Corporate Risk Intelligence ===")
print("Company:", company)
print("----------------------------------")
print(f"Revenue Growth: {revenue_growth:.1f}%")
print(f"Operating Margin: {operating_margin:.1f}%")
print(f"Debt Ratio: {debt_ratio:.1f}%")
print(f"OCF / Net Income: {cash_conversion:.2f}")
print(f"Receivables Growth: {receivables_growth:.1f}%")

# 위험 신호 탐지 (학습용 임계값)
print("\n=== Risk Signals ===")

if debt_ratio > 200:
    print("[WARNING] High Debt Ratio")

if cash_conversion < 0.8:
    print("[WARNING] Weak Cash Conversion")

if receivables_growth > revenue_growth + 20:
    print("[WARNING] Receivables Growing Faster Than Sales")
