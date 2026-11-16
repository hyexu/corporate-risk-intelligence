
# Corporate Risk Intelligence

### Financial Risk Monitoring Dashboard

A Python-based financial analytics dashboard designed to
identify potential corporate financial risk signals.


## Live Demo

[Launch Corporate Risk Intelligence](https://corporate-risk-intelligence.streamlit.app)



## 1. Project Overview

Corporate Risk Intelligence is a personal project
that explores how financial analysis and automation
can support corporate risk monitoring.

The project combines accounting knowledge with
Python-based financial data analysis.

## 2. Problem Statement

Financial analysts often need to review multiple
financial statements to identify potential risks.

This project aims to simplify the process by
automating financial ratio calculations and
highlighting unusual financial patterns.

## 3. Current Features

- Financial ratio calculation
- Multi-company comparison
- Interactive financial dashboard
- Rule-based financial risk detection
- Financial data visualization(
- OpenDART API integration
- Samsung Electronics FY2024 consolidated financial statement analysis
- Real financial data-based ratio calculations
- Secure API key management using environment variables and Streamlit Secrets=
- Real financial ratio comparison across Samsung Electronics, SK Hynix, and Hyundai Motor
- Interactive multi-company charts and rule-based financial risk signals using OpenDART data


### Real Financial Data Integration (v0.2)
- OpenDART API integration
- Samsung Electronics FY2024 consolidated financial statement analysis
- Revenue growth, operating margin, and debt ratio calculations
- Secure API key management using environment variables and Streamlit Secrets

### Multi-Company Financial Comparison (v0.3)
- Real financial data from Samsung Electronics, SK Hynix, and Hyundai Motor
- FY2024 consolidated financial statement comparison
- Interactive comparison of revenue growth, operating margin, and debt ratio
- Multi-company visualization with Streamlit
- Rule-based financial risk signals
- Company selection for interactive analysis



## 4. Financial Metrics

| Metric | Description |
|---|---|
| Revenue Growth | Year-over-year revenue growth |
| Operating Margin | Operating profit / Revenue |
| Debt Ratio | Total liabilities / Equity |
| Cash Conversion | Operating cash flow / Net income |
| Receivables Growth | Year-over-year receivables growth |

## 5. Technology Stack

- Python
- Pandas
- Streamlit
- GitHub Codespaces

## 6. How to Run

Install dependencies:

    python -m pip install -r requirements.txt

Run the dashboard:

    python -m streamlit run app.py

## 7. Data Disclaimer


The original demo dashboard uses fictional company data.

The Samsung Analysis and Real Company Comparison pages use actual FY2024 financial statement data obtained through the Financial Supervisory Service OpenDART API.

Financial risk signals are based on illustrative rules and have not been empirically validated. Financial ratios across different industries may not be directly comparable.

This project is for educational and portfolio purposes only and does not constitute investment advice.


## 8. Development Roadmap

- [o] Basic financial ratio calculator
- [o] Multi-company comparison (demo data)
- [o] Streamlit dashboard
- [o] OpenDART API integration
- [o] Samsung Electronics real financial statement analysis
- [o] Multi-company comparison using real financial data
- [ ] Machine learning anomaly detection
- [ ] LLM-based financial risk analysis
- [ ] Historical backtesting and model evaluation

## 9. Project Status

**Version 0.3 — Real Multi-Company Financial Comparison**
The application currently supports real financial statement analysis and comparison across Samsung Electronics, SK Hynix, and Hyundai Motor using OpenDART data.
The project combines financial ratio analysis, interactive visualization, and rule-based risk detection.
Future development will focus on industry-adjusted risk scoring, anomaly detection, and AI-powered financial risk explanations.


## Dashboard Preview

![Corporate Risk Intelligence Dashboard](dashboard.pdf)

