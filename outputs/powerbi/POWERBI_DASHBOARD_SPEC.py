"""
Power BI Dashboard Specification
Credit Card Spend & Cashback Profitability Analysis

This file documents the recommended Power BI dashboard layout.
Use the CSVs in outputs/powerbi/ as data sources.

DATA SOURCES (outputs/powerbi/):
──────────────────────────────────────────────────────────────
pbi_executive_kpis.csv        → KPI cards
pbi_monthly_trends.csv        → Time-series visuals
pbi_customer_portfolio.csv    → Customer table, slicers
pbi_category_cashback.csv     → Category charts
pbi_segment_summary.csv       → Segment analysis
pbi_campaign_performance.csv  → Campaign ROI table
pbi_channel_summary.csv       → Channel pie/bar charts

DATA MODEL RELATIONSHIPS:
──────────────────────────────────────────────────────────────
pbi_customer_portfolio[customer_id]  → (no direct join needed;
pbi_monthly_trends is pre-aggregated; all tables are fact tables)

DASHBOARD PAGES:
══════════════════════════════════════════════════════════════

PAGE 1 — Executive Overview
──────────────────────────────────────────────────────────────
KPI Cards (top row):
  • Total Customers          (pbi_executive_kpis, Value where KPI='Total Customers')
  • Total Transactions       (pbi_executive_kpis)
  • Total Spend (₹ Cr)       (pbi_executive_kpis → Total Spend / 1e7)
  • Total Net Profit (₹ Cr)  (pbi_executive_kpis → Total Net Profit / 1e7)
  • Portfolio Margin (%)     (pbi_executive_kpis)

Visuals:
  • Line Chart: Monthly Total Spend + Net Revenue trend
    Source: pbi_monthly_trends [year_month, total_spend, net_revenue]
  • Bar Chart: Total Spend by Card Type
    Source: pbi_customer_portfolio → group by card_type, sum total_spend
  • Donut Chart: Spend by Channel
    Source: pbi_channel_summary [channel, total_spend]
  • KPI sparkline: Profitable Customers %
    Source: pbi_executive_kpis

Slicers: card_type, year (from month), city_tier

PAGE 2 — Customer & Portfolio Analysis
──────────────────────────────────────────────────────────────
KPI Cards:
  • Champion Customers     (count where segment='Champion')
  • Dormant Customers      (count where segment='Dormant')
  • Top-10% Profit Share % (pbi_executive_kpis)
  • Avg Net Profit per Customer

Visuals:
  • Clustered Bar: Customer count by Segment
    Source: pbi_segment_summary [segment, customers]
  • Bar Chart: Avg Net Profit by Segment
    Source: pbi_segment_summary [segment, avg_net_profit]
  • Scatter Plot: Total Spend (x) vs Net Profit (y), colored by segment
    Source: pbi_customer_portfolio [total_spend, net_profit, segment]
  • Matrix Table: Segment × Card Type → Avg Net Profit (heatmap conditional fmt)
    Source: pbi_customer_portfolio
  • Histogram: Net Profit Distribution (bin width ₹500)
    Source: pbi_customer_portfolio [net_profit]
  • Bar Chart: Avg Spend by Income Band
    Source: pbi_customer_portfolio → group by income_band, avg total_spend

Slicers: segment, card_type, income_band, city_tier

PAGE 3 — Cashback & Offer Profitability
──────────────────────────────────────────────────────────────
KPI Cards:
  • Total Cashback Cost (₹ Cr)
  • Best Campaign ROI (%)
  • Highest Cashback Category
  • Cashback as % of Gross Revenue

Visuals:
  • Clustered Bar: Interchange Revenue vs Cashback Cost by Category
    Source: pbi_category_cashback [category, interchange_rev, total_cashback]
  • Bar Chart: Net Revenue by Category
    Source: pbi_category_cashback [category, net_revenue]
  • Table: Campaign Performance (name, enrolled, redeemed, redemption_rate, roi_pct)
    Source: pbi_campaign_performance
    Conditional formatting: roi_pct → green (>0), red (<0)
  • Waterfall Chart: P&L Breakdown
    Categories: Interchange Revenue, Annual Fee Revenue, -Cashback Cost, -Service Cost = Net Profit
    Source: pbi_executive_kpis (manually mapped values)
  • Bar Chart: Cashback Rate by Card Type × Category (heat-like)
    Source: pbi_customer_portfolio → group by card_type, avg cashback_pct

Slicers: campaign_id, target_category, card_type

THEMING SUGGESTIONS:
──────────────────────────────────────────────────────────────
  Background  : #F4F6F9
  Primary     : #1A3C5E  (dark navy)
  Accent 1    : #2E86AB  (blue)
  Accent 2    : #F18F01  (amber)
  Danger/Loss : #C73E1D  (red)
  Success     : #44BBA4  (teal)
  Font        : Segoe UI, 10pt base

DAX MEASURES TO CREATE:
──────────────────────────────────────────────────────────────
Total Spend Cr = DIVIDE(SUM(pbi_customer_portfolio[total_spend]), 10000000, 0)
Net Profit Cr  = DIVIDE(SUM(pbi_customer_portfolio[net_profit]),  10000000, 0)
Portfolio Margin % = DIVIDE(
    SUM(pbi_customer_portfolio[net_profit]),
    SUM(pbi_customer_portfolio[gross_revenue]), 0) * 100
Profitable Cust % = DIVIDE(
    COUNTROWS(FILTER(pbi_customer_portfolio, [net_profit] > 0)),
    COUNTROWS(pbi_customer_portfolio), 0) * 100
Top10 Profit Share % = [see calculated column in Q5 of analytical_queries.sql]
"""
