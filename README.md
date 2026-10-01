# Credit Card Spend & Cashback Profitability Analysis

> **Banking Analytics Portfolio Project** | Python · SQL (PostgreSQL) · Excel · Power BI

---

## Business Problem

A retail bank's credit card portfolio generates revenue through interchange fees and annual charges, but profitability is eroded by rising cashback costs and inefficient marketing spend. This project builds an end-to-end analytics pipeline to:

- Understand **spending behaviour** across 20,000 customers and 500,000+ transactions
- Measure **portfolio profitability** at customer, segment, and card-type level
- Quantify **cashback cost** as a share of revenue and identify leakage categories
- Evaluate **5 marketing campaigns** for incremental spend lift and ROI
- Deliver **actionable recommendations** to improve net interest margin

---

## Dataset Overview

| File | Rows | Key Fields |
|---|---|---|
| `customers.csv` | 20,000 | customer_id, age, gender, city_tier, income_band, card_type, tenure, credit_limit |
| `transactions.csv` | 500,000+ | txn_id, customer_id, date, amount, category, channel, cashback_pct, interchange_revenue |
| `cashback_rules.csv` | 40 | card_type, category, cashback_pct, max_cashback_pm |
| `campaigns.csv` | 5 | campaign_id, name, target_category, dates, bonus_cashback_pct, cost |
| `campaign_assignments.csv` | ~30,000 | campaign_id, customer_id, redeemed |

All data is **synthetically generated** with realistic Indian retail banking distributions (income bands, city tiers, merchants, seasonal spend patterns).

---

## Project Structure

```
DA project/
├── data/
│   ├── raw/                    # Generated source CSVs
│   └── processed/              # Cleaned & feature-engineered datasets
├── sql/
│   ├── schema.sql              # PostgreSQL DDL (5 tables, 1 view, indexes)
│   └── analytical_queries.sql  # 12 business-critical SQL queries
├── scripts/
│   ├── generate_data.py        # Synthetic data generation engine
│   ├── clean_data.py           # Cleaning, RFM scoring, profitability calc
│   └── run_pipeline.py         # Master runner (all phases)
├── notebooks/
│   ├── 01_data_generation.py
│   ├── 03_eda.py
│   └── [more scripts for each analysis phase]
├── outputs/
│   ├── figures/                # 14 publication-quality PNG charts
│   ├── powerbi/                # 7 Power BI-ready CSVs + dashboard spec
│   └── excel/                  # Credit_Card_Analysis_Summary.xlsx (6 tabs)
├── RESUME_BULLETS.txt          # Auto-generated resume bullets from actual results
├── requirements.txt
└── README.md
```

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the complete pipeline (generates data, cleans, analyses, exports)
cd "DA project"
python scripts/run_pipeline.py

# 3. Open Excel workbook
start outputs/excel/Credit_Card_Analysis_Summary.xlsx

# 4. Load Power BI CSVs from outputs/powerbi/ into Power BI Desktop
```

> **Note:** The pipeline takes ~3–5 minutes due to 500K+ transaction generation.

---

## Pipeline Results

### Portfolio KPIs

| KPI | Value |
|---|---|
| Total Customers | **20,000** |
| Total Transactions (valid) | **489,762** |
| Total Gross Revenue | **Rs.9.76 Cr** |
| Total Cashback Cost | **Rs.1.22 Cr** |
| Total Service Cost | **Rs.2.96 Cr** |
| Total Net Profit | **Rs.5.58 Cr** |
| Portfolio Margin | **57.2%** |
| Profitable Customers | **100%** |
| Top-10% Profit Contribution | **40.2%** |

### Customer Segmentation Results

| Segment | Customers | Avg Spend | Avg Net Profit | Total Net Profit |
|---|---|---|---|---|
| **Champion** | 6,024 | Rs.98,154 | Rs.2,925 | Rs.1.76 Cr |
| **Loyal** | 6,213 | Rs.53,249 | Rs.2,835 | Rs.1.76 Cr |
| **At-Risk** | 5,529 | Rs.29,747 | Rs.2,687 | Rs.1.49 Cr |
| **Dormant** | 2,234 | Rs.14,402 | Rs.2,554 | Rs.0.57 Cr |

### SQL Query Coverage

| # | Query | Business Question |
|---|---|---|
| Q1 | Portfolio KPIs | What are the headline metrics? |
| Q2 | Monthly Trends | How has spend grown over 24 months? |
| Q3 | Category Breakdown | Which categories drive spend & cashback cost? |
| Q4 | Card-Type Performance | Which card type is most profitable? |
| Q5 | Profitability Deciles | How concentrated is profit among customers? |
| Q6 | RFM Segmentation | How do customer segments compare? |
| Q7 | Channel Analysis | Where do customers spend most? |
| Q8 | Top-500 Customers | Who are the high-value customers? |
| Q9 | Root-Cause (Bottom-10%) | Why are some customers unprofitable? |
| Q10 | Campaign ROI | Which campaigns delivered the best return? |
| Q11 | City-Tier Analysis | How does geography affect performance? |
| Q12 | YoY Growth | Which categories grew fastest in 2024 vs 2023? |

---

## Outputs

### EDA Figures (`outputs/figures/`)
1. Monthly spend trend
2. Spend by category
3. Spend by channel (pie)
4. Card-type analysis (spend + count)
5. Interchange revenue vs cashback cost by category
6. Transaction amount distribution
7. Segment customer count vs avg profit
8. RFM scatter map (F vs M)
9. Segment × card type heatmap
10. Customer profit distribution
11. P&L waterfall by segment
12. Root-cause: cashback rate (bottom vs top 10%)
13. Profit by card type
14. Campaign ROI comparison

### Excel Workbook (`outputs/excel/Credit_Card_Analysis_Summary.xlsx`)
- **Executive Dashboard** — 10 KPI cards
- **Segment P&L** — revenue, cashback cost, service cost, net profit by segment
- **Category Summary** — spend, cashback, interchange, net revenue
- **Campaign Performance** — enrollment, redemption, ROI table
- **What-If Cashback** — 9-scenario sensitivity table (0.5% – 3.0% cashback rate)
- **Monthly Trends** — 24-month time series

### Power BI CSVs (`outputs/powerbi/`)
- `pbi_executive_kpis.csv`
- `pbi_monthly_trends.csv`
- `pbi_customer_portfolio.csv`
- `pbi_category_cashback.csv`
- `pbi_segment_summary.csv`
- `pbi_campaign_performance.csv`
- `pbi_channel_summary.csv`
- `POWERBI_DASHBOARD_SPEC.py` — 3-page dashboard layout spec with DAX measures

---

## Key Business Insights

1. **Top-10% concentration** — Top 2,000 customers generate 40.2% of the Rs.5.58 Cr total net profit; targeted VIP retention programs for Champion-segment customers (Rs.2,925 avg profit each) should be the #1 priority.

2. **Travel is the top cashback leakage category** — Travel has the highest spend (Rs.12.8M) and proportionally the highest cashback cost on Signature/Platinum cards. Monthly cashback caps can contain this leakage without impacting spend volume.

3. **Campaign redemption rate is 64-66% across all 5 campaigns** — Strong redemption rates but incremental spend lift is low, suggesting customers redeem for existing spend. Future campaigns should target categories with demonstrated elasticity (e.g., Entertainment, Education).

4. **Dormant drag** — 2,234 Dormant customers (avg spend Rs.14,402) still incur Rs.2,554 avg service cost, creating a portfolio drag. A systematic reactivation or card downgrade strategy could save Rs.0.57 Cr in unrecovered service costs.

5. **Channel opportunity** — Online channel (35% of transactions) shows the highest avg transaction values; contactless adoption is at 20%. Incentivising digital channels with targeted offers can raise interchange revenue without increasing cashback cost.

---

## Tech Stack

| Tool | Usage |
|---|---|
| **Python 3.13** | Data generation, cleaning, EDA, segmentation, profitability |
| **Pandas / NumPy** | Data wrangling, RFM scoring, P&L calculation |
| **Matplotlib / Seaborn** | 14 publication-quality charts |
| **PostgreSQL** | Schema design, 12 analytical queries, profitability view |
| **Excel (xlsxwriter)** | 6-tab workbook, what-if sensitivity analysis |
| **Power BI** | 3-page dashboard (Executive, Customer, Cashback/Offer) |

---

## Alignment with Banking Analytics JD

| JD Requirement | Implementation |
|---|---|
| Customer behaviour analysis | RFM segmentation, spend pattern EDA |
| Portfolio performance | Card-type P&L, category profitability |
| Cashback cost management | Cashback vs interchange analysis, what-if model |
| Campaign/offer analysis | 5-campaign ROI evaluation |
| SQL proficiency | 12 production-grade PostgreSQL queries |
| Data visualisation | 14 Matplotlib/Seaborn charts + Power BI dashboard |
| Excel modelling | 6-tab workbook with sensitivity analysis |
| Business storytelling | README insights, executive KPI dashboard |
